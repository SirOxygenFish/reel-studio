"""Whisper and the per-clip speech analysis for the automatic edit (plan T0-T5, T11).

What he said in each clip, with word timings good enough to cut retakes by:

* pass 1: Whisper on the whole clip, no prompt. It is fast and has context, but it
  silently skips repeated words: a retake shows up as one word that "lasts" 3 to 6 s
  («to[3.5-10.0]» in the reference a test clip);
* the speech map (RMS dB per 0.1 s), 10 ms frame levels and Silero regions show where
  the pauses between attempts are;
* pass 2: Whisper again on each window between pauses, still WITHOUT a prompt (a script
  prompt makes Whisper skip exactly the repeated words we are looking for). A window
  whose result still has a LONG word is split at its internal dips and run again;
* pass 3 (transcribe_pieces): only the final pieces, prompted with the neighbouring
  script sentences, for spelling («statycznie» -> «statystycznie»); taken only where it
  agrees with pass 2 or is sure (merge_pass3), never the script's words in his mouth;
* voice_words: the voice-over take's words, timed by what the voice read and shown as he
  typed the text («punkt A», «AI», «5 000 zł»; typed_words).

A word is [start, end, text, p] everywhere (seconds, Whisper's text with punctuation,
probability). One clip's result is a JSON-able ClipSpeech dict (see analyze_clip), cached
in config.SPEECH_DIR, which reel.takes reads without touching audio or Whisper again.

Whisper runs inside a WhisperSession, which loads the model once and frees it on exit.
Everything else here is plain numpy and takes any object with the session's words()
method, so the tests drive it with scripted fake transcripts.
"""
from __future__ import annotations

import gc
import glob
import hashlib
import json
import math
import os
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

from . import audio as A
from . import config
from . import words as W

MODEL = "large-v3"
# bump when the analysis changes: old cache files stop matching. 2: empty windows reach
# the pass-1 fallback, short cores get context, first words start at the local onset
CACHE_V = 2
BEAM = 5
# Whisper keeps only the last 223 tokens of a prompt (max_length // 2 - 1); staying under
# that means we choose what is cut, not Whisper.
PROMPT_TOKENS = 200
VOICE_PROMPT_WORDS = 150
HALLUCINATION_SILENCE = 1.0  # unprompted runs: skip text Whisper invents over silence
MIN_AUDIO = 0.1              # shorter slices are not worth a Whisper call
# physical cores: CTranslate2 int8 gains nothing from SMT siblings
CPU_THREADS = max(1, min(8, (os.cpu_count() or 8) // 2))

# utterance windows (the rest of the thresholds are in config.EDIT)
STRAY_OUTSIDE = 0.3          # a pass-1 word this far outside every Silero region...
STRAY_SOUND = 0.2            # ...with at least this much sound there gets its own window
PAD_MAX = 0.25               # padding around a window, at most half the gap to the next
SPLIT_GAP_MIN = 0.25         # a window over window_max is cut at a pause this long
LONG_HEAD = 0.6              # the first 0.6 s of a long word may be a drawn-out vowel
# LONG retries: (how far from pause_db toward speech_db a dip may reach, min dip length).
# The first retry cuts only at real pauses; the second also at shorter, shallower ones.
DIP_LEVELS = ((0.0, 0.15), (0.5, 0.10))
SOUND_MIN = 0.2              # seconds above speech_db that make a window worth a fallback
# "where the sound begins" (as audio.onset): louder than floor + ONSET_DB AND than the
# stretch's own loud frames (p90) - ONSET_BELOW. The floor alone is not enough: it is the
# quietest tenth of the clip (-70 dB), and the room tone before he speaks sits at -56.
ONSET_DB = 12.0
ONSET_BELOW = 20.0
FIRST_MIN = 0.05             # a first word moved to its sound keeps at least this much
# a window Whisper was unsure it heard speech in at all (hallucination over noise)
DROP_LOGPROB = -1.2
DROP_NO_SPEECH = 0.6
# pass 3 and spelling. Pass 3 is prompted with the script, so it hears the script: at 0.7
# the reference a test clip was taken at 0.857 and «1 albo 2%» became «to jeden, 2%», «albo
# mądrzejszy» «ani mądrzejszy», «po prostu zrobić» «że po prostu zrobisz» (worse against
# the reference transcript than no script at all). Every one of those wrong words had p < 0.25;
# the right pass-3 fixes («jeszcze», «zapytaj») p >= 0.3.
PASS3_MIN_SIM = 0.9          # pass 3 is used only this close to pass 2 (spoken_sim)
PASS3_KEEP_P = 0.3           # a word pass 3 changed to one it is less sure of stays pass 2's
PASS3_MIN_WORD = 0.05        # every pass-3 word lasts at least this long (a 0 s word is lost)
SPELL_MIN = 0.8
SPELL_PREFIX = 3
# spelling alignment scores (piece tokens against the script, see _align_script)
ALIGN_MATCH, ALIGN_NEAR, ALIGN_MISS, ALIGN_GAP = 2.0, 1.0, -1.0, -1.0
VOICE_MIN_WORD = 0.08
VOICE_GUESS_WORD = 0.3       # seconds per word when a voice word has no neighbour to lean on
# the typed text is shown only when its reading matches this share of the spoken tokens
# (else the take was read from another text, and the spoken words are shown)
VOICE_TYPED_MIN = 0.6
NBSP = " "
# language check: a first detection this sure of Polish is taken as it is (no pl/ru run).
# Never of Russian: his Eastern-accented Polish is often detected as ru (or uk/be) with
# high confidence, so a ru detection always goes through the pl/ru comparison.
LANG_SURE = 0.9

_CUDA_MARKERS = ("cublas", "cudnn", "cuda", "nvrtc", "out of memory")


def _cfg(cfg: dict | None = None) -> dict:
    return dict(config.EDIT, **(cfg or {}))


# ================================================================ Whisper session
def _gpu_hidden() -> bool:
    """CUDA_VISIBLE_DEVICES=-1 hides every GPU. An EMPTY value does not on Windows (it
    deletes the variable), which is why only a leading negative id counts."""
    v = os.environ.get("CUDA_VISIBLE_DEVICES")
    return v is not None and v.split(",")[0].strip().startswith("-")


def _add_cuda_dll_dirs() -> list:
    """The Windows CTranslate2 wheel loads cuBLAS / cuDNN by name at the first matmul, so
    the folders of the NVIDIA runtime wheels (installed by setup on GPU machines) must be
    on PATH, or a model loads on "cuda" and then fails."""
    if os.name != "nt":
        return []
    site = Path(sys.prefix) / "Lib" / "site-packages"
    found = [d for d in (Path(os.getenv("WHISPER_CUDA_DLL_DIR", "") or "."),
                         site / "nvidia" / "cublas" / "bin", site / "nvidia" / "cudnn" / "bin",
                         site / "nvidia" / "cuda_nvrtc" / "bin")
             if str(d) != "." and d.is_dir()]
    for d in reversed(found):
        os.environ["PATH"] = str(d) + os.pathsep + os.environ.get("PATH", "")
        try:
            os.add_dll_directory(str(d))
        except OSError:
            pass
    return [str(d) for d in found]


def _resolve_runtime(device: str, compute: str) -> tuple:
    """float16 on the GPU, int8 on the CPU."""
    device = (device or "auto").lower()
    if device == "auto":
        try:
            import ctranslate2
            device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        except Exception:  # noqa: BLE001
            device = "cpu"
    compute = (compute or "auto").lower()
    if compute == "auto":
        compute = "float16" if device == "cuda" else "int8"
    return device, compute


def _runtime_helpers() -> tuple:
    """(resolve_runtime, cuda failure markers); puts the CUDA DLL folders on PATH once."""
    global _DLLS_ADDED
    if not _DLLS_ADDED:
        _add_cuda_dll_dirs()
        _DLLS_ADDED = True
    return _resolve_runtime, _CUDA_MARKERS


_DLLS_ADDED = False


def _finite(x, default: float) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def _collect(segments, offset: float, device: str) -> dict:
    """Whisper segments -> {"words", "avg_logprob", "no_speech", "device"}. avg_logprob
    and no_speech are weighted by segment length (speech-weighted, as the transcriber
    compares languages)."""
    segs = list(segments)
    ws, lp, ns, tot = [], 0.0, 0.0, 0.0
    for s in segs:
        d = max(float(s.end) - float(s.start), 0.0)
        lp += float(s.avg_logprob) * d
        ns += float(s.no_speech_prob) * d
        tot += d
        for w in (s.words or []):
            text = str(w.word).strip()
            if not text:
                continue
            a = round(float(w.start) + offset, 3)
            ws.append([a, round(max(float(w.end) + offset, a), 3), text,
                       round(float(w.probability), 3)])
    if tot > 0:
        avg, nsp = lp / tot, ns / tot
    elif segs:
        avg = sum(float(s.avg_logprob) for s in segs) / len(segs)
        nsp = sum(float(s.no_speech_prob) for s in segs) / len(segs)
    else:
        avg, nsp = float("-inf"), 1.0
    return {"words": ws, "avg_logprob": avg, "no_speech": nsp, "device": device}


def _est_tokens(text: str) -> int:
    """Rough Whisper token count when no tokenizer is at hand: Polish words run 1 to 5
    tokens (letters with diacritics are two bytes), so this errs on the long side."""
    return sum(1 + len(w) // 3 for w in str(text or "").split())


def truncate_prompt(text: str, max_tokens: int = PROMPT_TOKENS, count=None,
                    keep: str = "tail") -> str:
    """The longest run of whole words from the END (keep="tail", what Whisper itself
    would keep) or the START (keep="head") that fits max_tokens."""
    words = str(text or "").split()
    count = count or _est_tokens
    if not words or count(" ".join(words)) <= max_tokens:
        return " ".join(words)
    lo, hi = 0, len(words)                     # largest n whose n words fit
    while lo < hi:
        n = (lo + hi + 1) // 2
        part = words[-n:] if keep == "tail" else words[:n]
        if count(" ".join(part)) <= max_tokens:
            lo = n
        else:
            hi = n - 1
    part = words[-lo:] if (keep == "tail" and lo) else words[:lo]
    return " ".join(part)


class WhisperSession:
    """faster_whisper large-v3 loaded once for a batch of clips, freed on exit.

        with WhisperSession() as sess:
            res = sess.words(audio16k, "pl")

    device / compute default to WHISPER_DEVICE / WHISPER_COMPUTE (else "auto": float16 on
    the GPU, int8 on the CPU). CUDA_VISIBLE_DEVICES=-1 or device="cpu" keeps it on the
    CPU. A CUDA failure (missing DLLs, no free VRAM) at load or at the first transcribe
    reloads the model on the CPU once and carries on, as the transcriber does.
    """

    def __init__(self, model: str = MODEL, device: str | None = None,
                 compute: str | None = None, cpu_threads: int = 0):
        self.model_name = model
        self.want_device = (device or os.getenv("WHISPER_DEVICE") or "auto").lower()
        self.want_compute = (compute or os.getenv("WHISPER_COMPUTE") or "auto").lower()
        self.cpu_threads = int(cpu_threads or CPU_THREADS)
        self.device: str | None = None
        self.compute: str | None = None
        self._model = None
        self._markers = _CUDA_MARKERS
        # pass-1 results choose_language already has, for analyze_audio (see _keep_pass1)
        self.pass1_memo: dict = {}

    # -- lifecycle
    def __enter__(self) -> "WhisperSession":
        return self.load()

    def __exit__(self, *exc) -> bool:
        self.close()
        return False

    def _build(self, device: str, compute: str):
        from faster_whisper import WhisperModel  # noqa: PLC0415 - heavy, only when used
        return WhisperModel(self.model_name, device=device, compute_type=compute,
                            cpu_threads=self.cpu_threads)

    def load(self) -> "WhisperSession":
        if self._model is not None:
            return self
        resolve, self._markers = _runtime_helpers()
        device, compute = resolve(self.want_device, self.want_compute)
        if device != "cpu" and _gpu_hidden():
            device, compute = "cpu", "auto"
        if device == "cpu" and compute in ("auto", "float16", "int8_float16"):
            compute = "int8"
        t0 = time.monotonic()
        try:
            self._model = self._build(device, compute)
        except Exception as exc:  # noqa: BLE001
            if device != "cuda" or not self._cuda_failure(exc):
                raise
            print(f"[speech] GPU failed at load ({str(exc)[:160]}); using the CPU", flush=True)
            gc.collect()
            device, compute = "cpu", "int8"
            self._model = self._build(device, compute)
        self.device, self.compute = device, compute
        print(f"[speech] Whisper {self.model_name} on {device}/{compute} "
              f"loaded in {time.monotonic() - t0:.1f}s", flush=True)
        return self

    def close(self) -> None:
        """Drop the weights (up to 4.5 GB of VRAM) so Ollama or XTTS can have the GPU."""
        self._model = None
        self.pass1_memo = {}
        gc.collect()

    def _cuda_failure(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return any(m in text for m in self._markers)

    def _call(self, fn):
        """fn(model), reloading on the CPU once when the GPU fails mid-run: CTranslate2
        reports a CUDA device even when the DLLs are missing, and only fails at the first
        matmul."""
        if self._model is None:
            self.load()
        try:
            return fn(self._model)
        except Exception as exc:  # noqa: BLE001
            if self.device != "cuda" or not self._cuda_failure(exc):
                raise
            print(f"[speech] GPU failed ({str(exc)[:160]}); using the CPU", flush=True)
            self._model = None
            gc.collect()
            self._model = self._build("cpu", "int8")
            self.device, self.compute = "cpu", "int8"
            return fn(self._model)

    # -- prompts
    def count_tokens(self, text: str) -> int:
        """Whisper tokens in a prompt (the model's own tokenizer when loaded)."""
        try:
            enc = self._model.hf_tokenizer.encode(" " + str(text).strip(),
                                                  add_special_tokens=False)
            return len(enc.ids)
        except Exception:  # noqa: BLE001
            return _est_tokens(text)

    def fit_prompt(self, text: str, keep: str = "tail") -> str:
        return truncate_prompt(text, PROMPT_TOKENS, self.count_tokens, keep)

    # -- transcription
    def words(self, audio16k, lang: str | None, prompt: str | None = None, vad: bool = False,
              cond: bool = False, offset: float = 0.0) -> dict:
        """Word timings for 16 kHz mono audio: {"words": [[s, e, text, p], ...] (+offset),
        "avg_logprob", "no_speech", "device"}. No prompt means hallucination_silence_threshold
        is on; a prompt is cut to its last PROMPT_TOKENS tokens' worth of words."""
        audio = np.asarray(audio16k, dtype=np.float32).ravel()
        if audio.size < int(MIN_AUDIO * A.SR):
            return {"words": [], "avg_logprob": float("-inf"), "no_speech": 1.0,
                    "device": self.device or "cpu"}
        kw = dict(language=lang or None, beam_size=BEAM, word_timestamps=True,
                  vad_filter=bool(vad), condition_on_previous_text=bool(cond))
        if self._model is None:
            self.load()
        prompt = self.fit_prompt(prompt) if prompt and str(prompt).strip() else ""
        if prompt:
            kw["initial_prompt"] = prompt
        else:
            kw["hallucination_silence_threshold"] = HALLUCINATION_SILENCE

        def run(model):
            segments, _info = model.transcribe(audio, **kw)
            return list(segments)

        return _collect(self._call(run), float(offset), self.device or "cpu")

    def detect_language(self, audio16k) -> tuple:
        """(language code, probability) from the first 30 s of speech."""
        audio = np.asarray(audio16k, dtype=np.float32).ravel()
        if audio.size < int(MIN_AUDIO * A.SR):
            return "", 0.0

        def run(model):
            try:
                lang, prob, _ = model.detect_language(audio, vad_filter=True)
            except ValueError:
                # the VAD found no speech at all (np.concatenate of nothing)
                lang, prob, _ = model.detect_language(audio, vad_filter=False)
            return str(lang), float(prob)

        return self._call(run)


# ================================================================ small helpers
def _load_audio(path) -> np.ndarray:
    """16 kHz mono float32; an empty array for a video without a sound track."""
    try:
        return A.load(path)
    except Exception:  # noqa: BLE001
        from . import ffmpeg as ff  # noqa: PLC0415
        if not ff.has_audio(Path(path)):
            return np.zeros(0, np.float32)
        raise


def _silent_dur(path) -> float:
    """The length of a clip that has no sound track (ffprobe), 0 when unknown."""
    try:
        from . import ffmpeg as ff  # noqa: PLC0415
        return round(float(ff.probe_duration(Path(path))), 3)
    except Exception:  # noqa: BLE001
        return 0.0


def _mid(w) -> float:
    return (float(w[0]) + float(w[1])) / 2


def _audio_key(lang: str, audio) -> tuple:
    """(lang, samples, sha1 of the samples): the same clip decoded twice (audio.load is
    deterministic) is the same key, whatever its file is called."""
    a = np.ascontiguousarray(np.asarray(audio, dtype=np.float32).ravel())
    return (str(lang), int(a.size), hashlib.sha1(a.tobytes()).hexdigest())


def _keep_pass1(sess, lang: str, audio, res: dict) -> None:
    """Remember a pass-1 result (Whisper on the whole clip, no prompt) on the session, so
    analyze_audio does not run it again: choose_language's pl/ru comparison already ran
    the longest clip's pass 1 in the language that won."""
    memo = getattr(sess, "pass1_memo", None)
    if not isinstance(memo, dict):
        memo = {}
        try:
            sess.pass1_memo = memo
        except Exception:  # noqa: BLE001 - a session that takes no attributes: no reuse
            return
    memo[_audio_key(lang, audio)] = res


def _reuse_pass1(sess, lang: str, audio) -> dict | None:
    """The remembered pass-1 result of exactly this audio in this language (taken: it is
    used once), or None."""
    memo = getattr(sess, "pass1_memo", None)
    if not isinstance(memo, dict) or not memo:
        return None
    return memo.pop(_audio_key(lang, audio), None)


def _clamp_words(ws: list, lo: float, hi: float) -> list:
    out = []
    for w in ws or []:
        s = min(max(float(w[0]), lo), hi)
        e = min(max(float(w[1]), s), hi)
        out.append([round(s, 3), round(e, 3), str(w[2]),
                    round(float(w[3]) if len(w) > 3 else 1.0, 3)])
    return out


def _map_span(n: int, a: float, b: float, hop: float) -> tuple:
    """Indices [i, j) of the map frames overlapping [a, b] (frame i covers [i*hop, (i+1)*hop));
    at least one frame when a lies inside the map."""
    i = int(math.floor(a / hop + 1e-6))
    j = max(i + 1, int(math.ceil(b / hop - 1e-6)))
    return max(0, min(i, n)), max(0, min(j, n))


def _centre_span(n: int, a: float, b: float, hop: float) -> tuple:
    """Indices [i, j) of the map frames whose CENTRE lies in [a, b]."""
    i = int(math.ceil(a / hop - 0.5 - 1e-6))
    j = int(math.floor(b / hop - 0.5 + 1e-6)) + 1
    return max(0, min(i, n)), max(0, min(j, n))


def in_pause(w, db, pause_db: float, hop: float = 0.1) -> bool:
    """True when every speech-map frame the word touches is below the pause level: Whisper
    put a word where there is no sound (a hallucination or a phantom echo)."""
    db = np.asarray(db, dtype=np.float64)
    i, j = _map_span(db.size, float(w[0]), float(w[1]), hop)
    return j > i and bool(np.all(db[i:j] < pause_db))


def sound_seconds(db, a: float, b: float, thr: float, hop: float = 0.1) -> float:
    """Seconds of speech-map frames (centres inside [a, b]) louder than thr."""
    db = np.asarray(db, dtype=np.float64)
    i, j = _centre_span(db.size, a, b, hop)
    return float(np.sum(db[i:j] > thr)) * hop if j > i else 0.0


_SPOKEN_CACHE: dict = {}


def spoken_len(text: str) -> int:
    """How many words a token stands for when read out: 1 for a word, more for digits
    («1,46%» is five words, «,46%.» three, «000» one), via pl_normalize."""
    t = str(text or "")
    if not re.search(r"\d", t):
        return 1
    if t not in _SPOKEN_CACHE:
        try:
            said = W._pl().normalize(t.strip())
            n = sum(1 for x in str(said).split() if re.search(r"[^\W\d_]", x))
        except Exception:  # noqa: BLE001 - the number reader is a nicety here
            n = len(re.findall(r"\d+", t))
        _SPOKEN_CACHE[t] = max(1, n)
    return _SPOKEN_CACHE[t]


def join_number_parts(ws: list, gap: float = 0.3) -> list:
    """Whisper writes «1,46%.» as two words, «1» and «,46%.», and «1-2» as «1» and «-2»:
    glue a word that starts with a comma, point or dash plus digits onto the digit word
    right before it (a dash becomes a plain hyphen: no en/em dashes anywhere)."""
    out: list = []
    for w in ws or []:
        w = list(w)
        text = str(w[2])
        if (out and re.match(r"^[.,\-–—]\d", text) and re.search(r"\d$", str(out[-1][2]))
                and float(w[0]) - float(out[-1][1]) <= gap):
            prev = out[-1]
            p = min(float(prev[3]) if len(prev) > 3 else 1.0, float(w[3]) if len(w) > 3 else 1.0)
            text = re.sub(r"^[–—]", "-", text)
            out[-1] = [prev[0], max(float(prev[1]), float(w[1])), str(prev[2]) + text, p]
            continue
        out.append(w)
    return out


def long_words(ws: list, db, speech_db: float, hop: float = 0.1, cfg: dict | None = None) -> list:
    """Words Whisper stretched over speech it did not write out: at least long_word s long
    (times the words a number token stands for), and speech (map frames above speech_db)
    in at least long_word_speech of the span after the first LONG_HEAD seconds. A drawn-out
    word followed by a pause is not one of them, nor «1,46%» read out over two seconds."""
    c = _cfg(cfg)
    db = np.asarray(db, dtype=np.float64)
    out = []
    for w in ws or []:
        s, e = float(w[0]), float(w[1])
        if e - s < c["long_word"] * spoken_len(w[2]):
            continue
        i, j = _centre_span(db.size, s + LONG_HEAD, e, hop)
        if j > i and float(np.mean(db[i:j] > speech_db)) >= c["long_word_speech"]:
            out.append(w)
    return out


def dips(fdb, a: float, b: float, thr: float, min_len: float, hop: float = A.HOP,
         win: float = A.WIN) -> list:
    """Runs of 10 ms frames below thr inside [a, b], at least min_len long:
    [(start, end, mean dB), ...] in seconds (frame centres +- hop/2)."""
    fdb = np.asarray(fdb, dtype=np.float64)
    i0 = max(0, int(math.ceil((a - win / 2) / hop - 1e-6)))
    i1 = min(fdb.size, int(math.floor((b - win / 2) / hop + 1e-6)) + 1)
    out, k = [], i0
    while k < i1:
        if fdb[k] < thr:
            s = k
            while k < i1 and fdb[k] < thr:
                k += 1
            if (k - s) * hop >= min_len - 1e-9:
                t0 = s * hop + win / 2 - hop / 2
                out.append((round(t0, 3), round(t0 + (k - s) * hop, 3),
                            float(np.mean(fdb[s:k]))))
        else:
            k += 1
    return out


# ================================================================ windows
def _merge(iv: list, gap: float) -> list:
    out: list = []
    for s, e in sorted([float(x[0]), float(x[1])] for x in iv if float(x[1]) > float(x[0])):
        if out and s - out[-1][1] < gap:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def _uncovered(s: float, e: float, regions: list) -> list:
    """Parts of [s, e] outside every region."""
    parts = [[s, e]]
    for rs, re_ in regions:
        nxt = []
        for a, b in parts:
            if re_ <= a or rs >= b:
                nxt.append([a, b])
                continue
            if rs > a:
                nxt.append([a, rs])
            if re_ < b:
                nxt.append([re_, b])
        parts = nxt
    return parts


def stray_spans(pass1: list, regions: list, db, pause_db: float, hop: float = 0.1,
                cfg: dict | None = None) -> list:
    """Spans of pass-1 words Silero missed: more than STRAY_OUTSIDE s of the word outside
    every region, with at least STRAY_SOUND s of sound there (a word Whisper merely placed
    over silence gets no window). A LONG word counts only its first LONG_HEAD seconds; the
    rest of it is exactly what cannot be trusted."""
    c = _cfg(cfg)
    out = []
    for w in pass1 or []:
        s, e = float(w[0]), float(w[1])
        if e - s >= c["long_word"] * spoken_len(w[2]):
            e = s + LONG_HEAD
        parts = _uncovered(s, e, regions)
        if sum(b - a for a, b in parts) <= STRAY_OUTSIDE:
            continue
        if sum(sound_seconds(db, a, b, pause_db, hop) for a, b in parts) >= STRAY_SOUND - 1e-9:
            out.append([s, e])
    return out


def _split_long(s: float, e: float, fdb, pause_db: float, speech_db: float,
                max_len: float) -> list:
    """Cut a window longer than max_len at its deepest pause of at least SPLIT_GAP_MIN s
    (else the deepest shorter dip, else the quietest frame in its middle third)."""
    if e - s <= max_len:
        return [[s, e]]
    inner = [d for d in dips(fdb, s + 0.5, e - 0.5, pause_db, SPLIT_GAP_MIN)]
    if not inner:
        inner = dips(fdb, s + 0.5, e - 0.5, (pause_db + speech_db) / 2, 0.05)
    if inner:
        d = min(inner, key=lambda x: (x[2], abs((x[0] + x[1]) / 2 - (s + e) / 2)))
        left, right = [s, d[0]], [d[1], e]
    else:
        fdb = np.asarray(fdb, dtype=np.float64)
        a = s + (e - s) / 3
        i0 = int(a / A.HOP)
        i1 = max(i0 + 1, int((s + 2 * (e - s) / 3) / A.HOP))
        seg = fdb[i0:i1]
        t = (i0 + int(np.argmin(seg))) * A.HOP + A.WIN / 2 if seg.size else (s + e) / 2
        left, right = [s, t], [t, e]
    return (_split_long(left[0], left[1], fdb, pause_db, speech_db, max_len)
            + _split_long(right[0], right[1], fdb, pause_db, speech_db, max_len))


def build_windows(regions: list, pass1: list, dur: float, fdb, db, speech_db: float,
                  pause_db: float, hop: float = 0.1, cfg: dict | None = None) -> list:
    """Utterance windows for pass 2: [{"a", "b" (padded slice), "cs", "ce" (speech core)}].

    Silero regions plus stray pass-1 words, merged when closer than window_merge_gap; then
    cut again wherever the 10 ms levels show a pause at least that long which Silero glued
    over (it did so at the restart in the reference a test clip, 3.64-4.13 s); windows longer than
    window_max are cut at their deepest pause. Each window is padded by at most PAD_MAX,
    never past half the gap to its neighbour, so neighbouring slices never overlap."""
    c = _cfg(cfg)
    gap = c["window_merge_gap"]
    cores = _merge([list(r) for r in regions] + stray_spans(pass1, regions, db, pause_db, hop, c),
                   gap)
    parts = []
    for s, e in cores:
        cur = s
        for d0, d1, _ in dips(fdb, s, e, pause_db, gap):
            if d0 - cur > 0:
                parts.append([cur, d0])
            cur = d1
        if e - cur > 0:
            parts.append([cur, e])
    final = []
    for s, e in parts:
        final += _split_long(s, e, fdb, pause_db, speech_db, c["window_max"])
    final = [[max(0.0, s), min(dur, e)] for s, e in final if min(dur, e) - max(0.0, s) >= 0.05]
    out = []
    for k, (s, e) in enumerate(final):
        before = s - final[k - 1][1] if k else s
        after = final[k + 1][0] - e if k + 1 < len(final) else dur - e
        pa = min(PAD_MAX, before / 2 if k else before)
        pb = min(PAD_MAX, after / 2 if k + 1 < len(final) else after)
        out.append({"a": round(max(0.0, s - max(pa, 0.0)), 3),
                    "b": round(min(dur, e + max(pb, 0.0)), 3),
                    "cs": round(s, 3), "ce": round(e, 3)})
    return out


# ================================================================ pass 2 per clip
class _Clip:
    """One clip's audio and measurements while pass 2 runs over its windows."""

    def __init__(self, sess, wav: np.ndarray, lang: str, pass1: dict, db, fdb, speech_db: float,
                 pause_db: float, hop: float, cfg: dict, floor_db: float = -60.0):
        self.sess, self.wav, self.lang, self.c = sess, wav, lang, cfg
        self.dur = wav.size / A.SR
        self.p1 = pass1
        self.db, self.fdb = np.asarray(db, dtype=np.float64), np.asarray(fdb, dtype=np.float64)
        self.speech_db, self.pause_db, self.hop = speech_db, pause_db, hop
        self.floor = float(floor_db)
        self.quiet = self.floor + ONSET_DB
        self.calls = 0

    def sound_level(self, a: float, b: float) -> float:
        """What "sound" means inside [a, b]: louder than the room (floor + ONSET_DB) and
        than the stretch's own loud frames - ONSET_BELOW, the rule audio.onset uses."""
        i0 = max(0, int(math.ceil((a - A.WIN / 2) / A.HOP - 1e-6)))
        i1 = min(self.fdb.size, int(math.floor((b - A.WIN / 2) / A.HOP + 1e-6)) + 1)
        if i1 <= i0:
            return self.quiet
        return max(self.quiet, float(np.percentile(self.fdb[i0:i1], 90)) - ONSET_BELOW)

    def sound_from(self, t: float, limit: float, thr: float | None = None) -> float:
        """The first 10 ms frame at or after t louder than thr (default:
        sound_level(t, limit)); t when there is none before limit."""
        thr = self.sound_level(t, limit) if thr is None else thr
        n = self.fdb.size
        k = max(0, int(math.ceil((t - A.WIN / 2) / A.HOP - 1e-6)))
        while k < n and k * A.HOP + A.WIN / 2 <= limit:
            if self.fdb[k] > thr:
                return max(t, round(k * A.HOP, 3))
            k += 1
        return t

    def sound_until(self, t: float, limit: float, thr: float | None = None) -> float:
        """The end of the last frame at or before t louder than thr (default:
        sound_level(limit, t)); t when none."""
        thr = self.sound_level(limit, t) if thr is None else thr
        k = min(self.fdb.size - 1, int(math.floor((t - A.WIN / 2) / A.HOP + 1e-6)))
        while k >= 0 and k * A.HOP + A.WIN / 2 >= limit:
            if self.fdb[k] > thr:
                return min(t, round(k * A.HOP + A.WIN, 3))
            k -= 1
        return t

    def first_sound(self, w: list) -> float:
        """Where word w is first heard: the first frame of its span above its sound_level
        (the audio.onset threshold, so a soft «s» 20 dB under the vowel still counts), but
        never less than FIRST_MIN before its end. A short word Whisper stretched over the
        room tone may have only its last 30 to 60 ms of sound («A» 5.318-5.618 with the
        vowel at 5.56 in a test clip, «I» 1.385-1.525 with it at 1.49 in a test clip): it moves
        as close to that sound as its minimum length allows."""
        s, e = float(w[0]), float(w[1])
        t = self.sound_from(s, e, self.sound_level(s, e))
        return max(s, min(t, round(e - FIRST_MIN, 3))) if t > s else s

    def whisper(self, win: dict) -> dict:
        """Pass 2 on the window's slice [a, b]: no prompt, no VAD, no conditioning.

        A window whose SPEECH (the core cs..ce, not the padded slice) is shorter than
        window_min gets window_context seconds of audio each side (Whisper guesses wildly on
        a bare «Tak.» or «Stop.») and keeps only the words whose middle lies in [a, b]. The
        context never reaches past the window's "lo"/"hi" limits: a part of a LONG split
        must not hear the attempt it was split from again."""
        a, b = float(win["a"]), float(win["b"])
        core = float(win.get("ce", b)) - float(win.get("cs", a))
        short = core < self.c["window_min"]
        ctx = self.c["window_context"] if short else 0.0
        lo = max(0.0, min(a, float(win.get("lo", 0.0))))
        hi = min(self.dur, max(b, float(win.get("hi", self.dur))))
        i0 = int(round(max(lo, a - ctx) * A.SR))
        i1 = int(round(min(hi, b + ctx) * A.SR))
        self.calls += 1
        res = self.sess.words(self.wav[i0:i1], self.lang, prompt=None, vad=False, cond=False,
                              offset=i0 / A.SR)
        ws = join_number_parts(res.get("words") or [])
        if i0 < round(a * A.SR) - 1 or i1 > round(b * A.SR) + 1:   # context was added
            ws = [w for w in ws if a <= _mid(w) <= b]
        return {"words": _clamp_words(ws, 0.0, self.dur),
                "avg_logprob": _finite(res.get("avg_logprob"), float("-inf")),
                "no_speech": _finite(res.get("no_speech"), 1.0)}

    def cuts_for(self, longs: list, a: float, b: float, level: int) -> list:
        """Where to split a window around its LONG words at retry `level`: dips inside a
        LONG word with speech on both sides (the silence a LONG word also spans at the
        window's edges would only cut off a crumb)."""
        frac, min_len = DIP_LEVELS[min(level, len(DIP_LEVELS) - 1)]
        thr = self.pause_db + frac * (self.speech_db - self.pause_db)
        cuts: list = []
        for w in longs:
            lo, hi = max(float(w[0]), a + 0.1), min(float(w[1]), b - 0.1)
            for d0, d1, _ in dips(self.fdb, lo, hi, thr, min_len):
                t = round((d0 + d1) / 2, 3)
                if (a + 0.1 < t < b - 0.1 and all(abs(t - x) > 0.2 for x in cuts)
                        and sound_seconds(self.db, a, d0, self.speech_db, self.hop) >= SOUND_MIN
                        and sound_seconds(self.db, d1, b, self.speech_db, self.hop) >= SOUND_MIN):
                    cuts.append(t)
        return sorted(cuts)

    def fallback(self, a: float, b: float) -> list:
        """Pass-1 words in [a, b] (by their middles)."""
        return [list(w) for w in self.p1["words"] if a <= _mid(w) <= b]

    def run(self, win: dict, tries: int = 0) -> list:
        """Utterances for one window (several when a LONG word made it split)."""
        a, b = float(win["a"]), float(win["b"])
        if b - a < MIN_AUDIO:
            return []
        res = self.whisper(win)
        # Whisper unsure it heard speech at all: a hallucination over noise. Only a window
        # WITH words can be one; an empty result (always -inf / 1.0) goes on to leaf(),
        # whose pass-1 fallback is for exactly that case when there is sound there.
        if (res["words"] and res["avg_logprob"] < DROP_LOGPROB
                and res["no_speech"] > DROP_NO_SPEECH):
            return []
        ws = res["words"]
        longs = long_words(ws, self.db, self.speech_db, self.hop, self.c)
        levels = range(tries, int(self.c["long_retries"])) if longs else range(0)
        for level in levels:
            cuts = self.cuts_for(longs, a, b, level)
            if not cuts:
                continue
            edges = [a] + cuts + [b]
            lo, hi = float(win.get("lo", 0.0)), float(win.get("hi", self.dur))
            out = []
            for k, (sa, sb) in enumerate(zip(edges, edges[1:])):
                # the part's own speech: a cut lies in a dip, not where the talking starts
                cs = max(float(win["cs"]), self.sound_from(sa, sb))
                ce = min(float(win["ce"]), self.sound_until(sb, sa))
                if ce <= cs:
                    cs, ce = sa, sb
                # context may come from outside the window, never across a cut
                out += self.run({"a": sa, "b": sb, "cs": cs, "ce": ce,
                                 "lo": lo if k == 0 else sa,
                                 "hi": hi if k == len(edges) - 2 else sb}, level + 1)
            return out
        return self.leaf(win, res)

    def leaf(self, win: dict, res: dict) -> list:
        """Guards, cleanup and the utterance record for a window that is not split again."""
        a, b = float(win["a"]), float(win["b"])
        c = self.c
        ws = [w for w in res["words"] if not in_pause(w, self.db, self.pause_db, self.hop)]
        source, avg, nsp = "pass2", res["avg_logprob"], res["no_speech"]
        too_fast = ws and len(ws) / max(b - a, 1.0) > c["max_words_per_sec"]
        empty = not ws and sound_seconds(self.db, float(win["cs"]), float(win["ce"]),
                                         self.speech_db, self.hop) >= SOUND_MIN
        if too_fast or empty:
            # Whisper looping on a phrase, or hearing nothing where there is speech:
            # what pass 1 heard there, with the whole clip as context, is the better guess
            fb = [w for w in self.fallback(a, b)
                  if not in_pause(w, self.db, self.pause_db, self.hop)]
            if fb or too_fast:
                ws, source = fb, "pass1"
                avg, nsp = self.p1["avg_logprob"], self.p1["no_speech"]
        ws = W.clean_words(ws, self.lang, c["echo_max"])
        ws = [w for w in _clamp_words(ws, 0.0, self.dur)
              if not in_pause(w, self.db, self.pause_db, self.hop)]
        if not ws:
            return []
        # Whisper starts a slice's first word at the slice start, over the padding's
        # room tone: move it to where the sound begins
        first = ws[0]
        t = self.first_sound(first)
        if t - first[0] > 0.02:
            ws[0] = [round(t, 3)] + list(first[1:])
        unresolved = [[w[0], w[1], w[2]]
                      for w in long_words(ws, self.db, self.speech_db, self.hop, c)]
        # the utterance spans its sound (a stray pass-1 word may have stretched the core
        # over silence) and its words
        cs, ce = float(win["cs"]), float(win["ce"])
        s = min(self.sound_from(cs, ce), ws[0][0])
        e = max(self.sound_until(ce, cs), ws[-1][1])
        return [{"s": round(s, 3), "e": round(e, 3),
                 "words": ws,
                 "avg_logprob": round(_finite(avg, -5.0), 4),
                 "no_speech": round(_finite(nsp, 1.0), 4),
                 "unresolved_long": unresolved,
                 "source": source}]


def analyze_audio(sess, wav, lang: str, file: str = "", regions: list | None = None,
                  cfg: dict | None = None) -> dict:
    """The ClipSpeech of 16 kHz mono audio (see analyze_clip). `regions` replaces Silero
    (tests); `sess` is anything with WhisperSession.words()."""
    c = _cfg(cfg)
    wav = np.asarray(wav, dtype=np.float32).ravel()
    dur = wav.size / A.SR
    hop = float(c["map_hop"])
    m = A.speech_map(wav, hop=hop, p90_drop=c["map_p90_drop"], lo=c["map_speech_lo"],
                     hi=c["map_speech_hi"], gap=c["map_pause_gap"])
    # stored rounded; computed from the same rounded values, so reel.takes reading the
    # cache sees exactly what the analysis saw
    fdb = A.to_list(A.frame_db(wav), 1)
    floor = A.noise_floor(fdb) if fdb else -120.0
    if regions is None:
        regions = A.vad_regions(wav, threshold=c["vad_threshold"],
                                min_silence=c["vad_min_silence"]) if wav.size else []
    regions = [[round(float(s), 3), round(float(e), 3)] for s, e in regions]

    if wav.size >= int(MIN_AUDIO * A.SR):
        # choose_language may have run exactly this pass already (the longest clip)
        r1 = _reuse_pass1(sess, lang, wav)
        if r1 is None:
            r1 = sess.words(wav, lang, prompt=None, vad=False, cond=False, offset=0.0)
    else:
        r1 = {"words": [], "avg_logprob": float("-inf"), "no_speech": 1.0}
    pass1 = {"words": _clamp_words(join_number_parts(r1.get("words") or []), 0.0, dur),
             "avg_logprob": _finite(r1.get("avg_logprob"), -5.0),
             "no_speech": _finite(r1.get("no_speech"), 1.0)}

    clip = _Clip(sess, wav, lang, pass1, m["db"], fdb, m["speech"], m["pause"], hop, c, floor)
    wins = build_windows(regions, pass1["words"], dur, fdb, m["db"], m["speech"], m["pause"],
                         hop, c)
    utts = []
    for w in wins:
        utts += clip.run(w)
    utts.sort(key=lambda u: (u["s"], u["e"]))
    return {"version": CACHE_V, "file": file, "dur": round(dur, 3), "lang": lang,
            "hop": hop, "db": m["db"], "speech_db": m["speech"], "pause_db": m["pause"],
            "fdb": fdb, "floor_db": round(float(floor), 1), "regions": regions,
            "pass1": pass1["words"], "utterances": utts,
            "words": [w for u in utts for w in u["words"]],
            "device": getattr(sess, "device", None) or "cpu"}


# ================================================================ cache
_CACHE_NAME = re.compile(r"-[0-9a-f]{10}\.json$")


def _stamp(path: Path) -> str:
    st = path.stat()
    return f"{path.resolve()}|{st.st_size}|{st.st_mtime_ns}"


def cache_key(path, lang: str, model: str = MODEL, extra: str = "") -> str:
    """sha1(abs path|size|mtime_ns|model|lang|CACHE_V[|extra])[:10]: a re-recorded or
    re-exported clip, another model or language, or a new analysis version misses."""
    raw = f"{_stamp(Path(path))}|{model}|{lang}|{CACHE_V}" + (f"|{extra}" if extra else "")
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def cache_path(path, lang: str, model: str = MODEL, cache_dir=None) -> Path:
    p = Path(path)
    return Path(cache_dir or config.SPEECH_DIR) / f"{p.stem}-{cache_key(p, lang, model)}.json"


def _read_json(p: Path):
    try:
        with open(p, "rb") as fh:
            return json.loads(fh.read().decode("utf-8"))
    except (OSError, ValueError):
        return None


def _write_json(p: Path, data) -> None:
    """Atomic: a crash mid-write never leaves half a cache file behind."""
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f"{p.name}.{os.getpid()}.tmp")
    with open(tmp, "wb") as fh:
        fh.write(json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8"))
    os.replace(tmp, p)


def load_cached(path, lang: str, model: str = MODEL, cache_dir=None) -> dict | None:
    """The cached ClipSpeech, or None (lets the caller skip loading Whisper at all)."""
    try:
        got = _read_json(cache_path(path, lang, model, cache_dir))
    except OSError:
        return None
    ok = isinstance(got, dict) and got.get("version") == CACHE_V and "utterances" in got
    return got if ok else None


def drop_cache(path, cache_dir=None) -> int:
    """Delete every cached analysis of this clip (any key); returns how many."""
    p = Path(path)
    n = 0
    for f in glob.glob(str(Path(cache_dir or config.SPEECH_DIR) / f"{glob.escape(p.stem)}-*.json")):
        if _CACHE_NAME.search(f) and Path(f).name[:-16] == p.stem:
            try:
                os.remove(f)
                n += 1
            except OSError:
                pass
    return n


def analyze_clip(sess, path, lang: str, cache_dir=None, use_cache: bool = True) -> dict:
    """ClipSpeech of one clip (cache_dir defaults to config.SPEECH_DIR):

        {"version", "file", "dur", "lang",
         "hop": 0.1, "db": [dB per 0.1 s], "speech_db", "pause_db",   # speech map
         "fdb": [dB per 10 ms frame], "floor_db",                     # frame levels
         "regions": [[s, e], ...],                                     # Silero
         "pass1": [word, ...],                                         # whole clip, no prompt
         "utterances": [{"s", "e", "words", "avg_logprob", "no_speech",
                         "unresolved_long": [[s, e, text]], "source": "pass2"|"pass1"}],
         "words": [word, ...],                                         # all utterances
         "device"}

    Cached per file (path, size, mtime, model, language, version); `sess` may be None when
    the cache already has it."""
    path = Path(path)
    model = getattr(sess, "model_name", None) or MODEL
    cp = cache_path(path, lang, model, cache_dir)
    if use_cache:
        got = load_cached(path, lang, model, cache_dir)
        if got is not None:
            return got
    if sess is None:
        raise RuntimeError(f"no cached speech for {path.name} and no Whisper session")
    t0 = time.monotonic()
    wav = _load_audio(path)
    out = analyze_audio(sess, wav, lang, file=path.name)
    if not wav.size:
        out["dur"] = _silent_dur(path)
    _write_json(cp, out)
    print(f"[speech] {path.name}: {out['dur']:.1f}s of audio, {len(out['utterances'])} "
          f"utterances, {len(out['words'])} words on {out['device']} in "
          f"{time.monotonic() - t0:.1f}s", flush=True)
    return out


# ================================================================ T0 / T1
def quick_talk_probe(path) -> dict:
    """{"speech_ratio", "speech_s", "dur"}: how much of the clip Silero hears as speech.
    CPU only, no Whisper, a second or two per clip."""
    c = config.EDIT
    wav = _load_audio(path)
    dur = wav.size / A.SR
    regs = A.vad_regions(wav, threshold=c["vad_threshold"],
                         min_silence=c["vad_min_silence"]) if wav.size else []
    speech = float(sum(e - s for s, e in regs))
    return {"speech_ratio": round(speech / dur, 3) if dur > 0 else 0.0,
            "speech_s": round(speech, 2), "dur": round(dur, 3) if wav.size else _silent_dur(path)}


def probe_is_talk(probe: dict, cfg: dict | None = None) -> bool:
    """T0 first look: at least talk_speech_ratio of the clip and talk_speech_min s."""
    c = _cfg(cfg)
    return (float(probe.get("speech_ratio") or 0) >= c["talk_speech_ratio"]
            and float(probe.get("speech_s") or 0) >= c["talk_speech_min"])


def words_confirm_talk(ws: list, cfg: dict | None = None) -> bool:
    """T0 after pass 1: at least talk_min_words words with mean p >= talk_min_p."""
    c = _cfg(cfg)
    ws = [w for w in ws or [] if W.norm_token(w[2])]
    if len(ws) < c["talk_min_words"]:
        return False
    return float(np.mean([float(w[3]) if len(w) > 3 else 1.0 for w in ws])) >= c["talk_min_p"]


NEIGHBOUR_LANGS = ("pl", "ru", "uk", "be")


def choose_language(sess, audios: dict, script: str | None = None) -> str:
    """T1. A Cyrillic script means ru. Otherwise Whisper's
    detection, longest clip first: pl detected with at least LANG_SURE on it is the
    answer right away (ru never is: accented Polish is often detected as ru, sure or
    not). Else the 3 longest clips vote, weighted by length; when that lands
    on pl/ru/uk/be (an Eastern accent confuses the detector: 43 of 99 Polish reels came out
    ru/uk in the transcriber), pass 1 of the longest clip runs in Polish and in
    Russian and the higher speech-weighted avg_logprob wins. The winner's pass 1 is kept
    on the session (_keep_pass1): analyze_clip of that clip in that language reuses it
    instead of running the same pass again."""
    if script and str(script).strip():
        if W.is_cyrillic(script):
            return "ru"
    items = sorted(((k, np.asarray(v, dtype=np.float32).ravel()) for k, v in (audios or {}).items()),
                   key=lambda kv: -kv[1].size)
    items = [kv for kv in items if kv[1].size >= int(MIN_AUDIO * A.SR)][:3]
    if not items:
        return "pl"
    votes: dict = {}
    for k, (_name, a) in enumerate(items):
        lang, prob = sess.detect_language(a)
        if k == 0 and lang == "pl" and float(prob) >= LANG_SURE:
            return lang                     # sure of Polish on the longest clip: no pl/ru run
        if lang:
            votes[lang] = votes.get(lang, 0.0) + float(prob) * a.size
    if not votes:
        return "pl"
    best = max(votes, key=votes.get)
    if best not in NEIGHBOUR_LANGS:
        return best
    longest = items[0][1]
    score, runs = {}, {}
    for lang in ("pl", "ru"):
        r = sess.words(longest, lang, prompt=None, vad=False, cond=False, offset=0.0)
        runs[lang] = r
        score[lang] = _finite(r.get("avg_logprob"), float("-inf")) if r.get("words") \
            else float("-inf")
    if score["pl"] == score["ru"] == float("-inf"):
        return best if best in ("pl", "ru") else "pl"
    win = max(("pl", "ru"), key=lambda k: score[k])
    _keep_pass1(sess, win, longest, runs[win])
    return win


# ================================================================ pass 3
def _bare(raw: str) -> str:
    return re.sub(r"^[\W_]+|[\W_]+$", "", str(raw))


def _respell(orig: str, spelling: str) -> str:
    """Whisper's word with the script's letters, keeping its punctuation and whether it
    started with a capital."""
    m = re.match(r"^([\W_]*)(.*?)([\W_]*)$", str(orig), re.S)
    lead, core, trail = m.group(1), m.group(2), m.group(3)
    if not core or not spelling:
        return orig
    first = spelling[0].upper() if core[0].isupper() else spelling[0].lower()
    return lead + first + spelling[1:] + trail


def _near(x: str, y: str) -> float:
    """tok_sim, computed only where it can matter: the same first SPELL_PREFIX letters (a
    spelling slip) or two numbers («pięć» == «5»); 0 otherwise."""
    if x == y:
        return 1.0
    if x[:SPELL_PREFIX] == y[:SPELL_PREFIX]:
        return W.tok_sim(x, y)
    if W._value(x.rstrip("%")) is not None and W._value(y.rstrip("%")) is not None:
        return W.tok_sim(x, y)
    return 0.0


def _align_script(a: list, b: list) -> list:
    """Semi-global alignment of ALL of the piece's tokens `a` against the one stretch of
    the script's tokens `b` it fits best (the script before and after that stretch is
    free): [(i, j), ...] aligned pairs in order.

    A plain SequenceMatcher over the whole script anchors a common word («a», «to», «nie»)
    to its first occurrence, far from the piece, and then compares the misspelled word
    with unrelated script words. Scoring every pair (match > near miss > mismatch, gaps
    cost) puts the piece where most of it agrees."""
    n, m = len(a), len(b)
    if not n or not m:
        return []
    memo: dict = {}

    def score(x: str, y: str) -> float:
        key = (x, y)
        if key not in memo:
            s = _near(x, y)
            memo[key] = ALIGN_MATCH if s >= 1.0 else ALIGN_NEAR if s >= SPELL_MIN else ALIGN_MISS
        return memo[key]

    h = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]        # 0 diagonal, 1 skip a[i], 2 skip b[j]
    for i in range(1, n + 1):
        h[i][0], back[i][0] = h[i - 1][0] + ALIGN_GAP, 1
        hi, hp, bi = h[i], h[i - 1], back[i]
        ai = a[i - 1]
        for j in range(1, m + 1):
            d = hp[j - 1] + score(ai, b[j - 1])
            u = hp[j] + ALIGN_GAP
            left = hi[j - 1] + ALIGN_GAP
            if d >= u and d >= left:
                hi[j], bi[j] = d, 0
            elif u >= left:
                hi[j], bi[j] = u, 1
            else:
                hi[j], bi[j] = left, 2
    j = max(range(m + 1), key=lambda x: h[n][x])        # the script after the piece is free
    i, pairs = n, []
    while i > 0 and j >= 0:
        step = back[i][j] if j > 0 else 1
        if step == 0:
            pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif step == 1:
            i -= 1
        else:
            j -= 1
    return pairs[::-1]


def fix_spelling(ws: list, script) -> list:
    """Words Whisper misspelled against the script: aligned to the script's tokens (the
    whole script or a few sentences; _align_script finds the piece's place), a word whose
    tok_sim with its aligned script word is in [SPELL_MIN, 1) and shares the first
    SPELL_PREFIX letters takes the script's spelling («statycznie» -> «statystycznie»).
    Only aligned pairs are compared, so an inflection he really said that the script has
    elsewhere is left alone."""
    text = " ".join(str(s) for s in script) if isinstance(script, (list, tuple)) \
        else str(script or "")
    stoks = [(W.norm_token(r), _bare(r)) for r in text.split()]
    stoks = [t for t in stoks if t[0]]
    out = [list(w) for w in ws or []]
    idx = [(k, W.norm_token(w[2])) for k, w in enumerate(out)]
    idx = [(k, n) for k, n in idx if n]
    if not stoks or not idx:
        return out
    a = [n for _, n in idx]
    b = [n for n, _ in stoks]
    for i, j in _align_script(a, b):
        if a[i] == b[j] or not a[i].isalpha():
            continue
        sim = W.tok_sim(a[i], b[j])
        if SPELL_MIN <= sim < 1.0 and a[i][:SPELL_PREFIX] == b[j][:SPELL_PREFIX]:
            k = idx[i][0]
            out[k][2] = _respell(out[k][2], stoks[j][1])
    return out


def spoken_sim(a: list, b: list, lang: str = "pl") -> float:
    """seq_sim of two word lists with the numbers read out first: pass 2 (no prompt) writes
    «73 tysiące», pass 3 (prompted with the script) «siedemdziesiąt trzy tysiące», and the
    same sentence must not look different because of it. Polish only (pl_normalize)."""
    if lang == "pl":
        try:
            norm = W._pl().normalize
            ta = W.tokens(norm(" ".join(str(w[2]) for w in a)))
            tb = W.tokens(norm(" ".join(str(w[2]) for w in b)))
            return W.seq_sim(ta, tb)
        except Exception:  # noqa: BLE001 - fall back to the plain comparison
            pass
    return W.seq_sim(a, b)


def _said_tokens(ws: list, lang: str = "pl") -> list:
    """[(comparison key, word index), ...] of a word list, a word with digits read out
    first (Polish: «1,46%» is five tokens, the way pass 3 writes it)."""
    norm = None
    if lang == "pl":
        try:
            norm = W._pl().normalize
        except Exception:  # noqa: BLE001 - numbers then compare as written
            norm = None
    out = []
    for k, w in enumerate(ws or []):
        text = str(w[2])
        if norm is not None and re.search(r"\d", text):
            try:
                text = norm(text)
            except Exception:  # noqa: BLE001
                pass
        out += [(_key(t), k) for t in W.tokens(text)]
    return out


def _word_blocks(ta: list, na: int, tb: list, nb: int) -> list:
    """Two word lists aligned block by block: [(same, (a0, a1), (b0, b1))], word ranges
    that cover both lists in order. ta / tb are _said_tokens of the lists (na / nb words).
    A block ends only where a word ends on BOTH sides, so «1,46%» against «jeden przecinek
    czterdzieści sześć procent» is one block; same is True when every token in it matched."""
    ops = SequenceMatcher(None, [t for t, _ in ta], [t for t, _ in tb], autojunk=False).get_opcodes()

    def edge(toks: list, i: int) -> bool:
        return i <= 0 or i >= len(toks) or toks[i][1] != toks[i - 1][1]

    def word(toks: list, i: int, n: int) -> int:
        return toks[i][1] if i < len(toks) else n

    out, a0, b0, same = [], 0, 0, True
    for tag, _i1, i2, _j1, j2 in ops:
        same = same and tag == "equal"
        if edge(ta, i2) and edge(tb, j2):
            a1, b1 = word(ta, i2, na), word(tb, j2, nb)
            out.append((same, (a0, a1), (b0, b1)))
            a0, b0, same = a1, b1, True
    if a0 < na or b0 < nb:                       # words with no tokens at the very end
        out.append((False, (a0, na), (b0, nb)))
    return out


def merge_pass3(p2: list, p3: list, lang: str = "pl") -> list:
    """Pass 3 (prompted with the script) over pass 2 (unprompted), word by word: where both
    heard the same (numbers read out on both sides) pass 3's words are taken, with the
    script's punctuation; where pass 3 changed, added or dropped words, its words are
    taken only when it is sure of every one of them (p >= PASS3_KEEP_P), else pass 2's
    stay. A word pass 3 dropped is kept: a script prompt makes Whisper skip words."""
    ta, tb = _said_tokens(p2, lang), _said_tokens(p3, lang)
    out: list = []
    for same, (a0, a1), (b0, b1) in _word_blocks(ta, len(p2), tb, len(p3)):
        mine = [list(w) for w in p3[b0:b1]]
        sure = bool(mine) and all((float(w[3]) if len(w) > 3 else 1.0) >= PASS3_KEEP_P
                                  for w in mine)
        out += mine if (same or sure) else [list(w) for w in p2[a0:a1]]
    return out


def _min_length(ws: list, hi: float, min_len: float = PASS3_MIN_WORD) -> list:
    """Words in order, none shorter than min_len (a 0 s word never reaches the subtitles:
    model.words_on_timeline keeps a word by its middle): each starts at or after the end
    of the one before and is stretched to min_len; words pushed past hi (the piece's end,
    or the last word's own end when later) are moved back before it."""
    out, prev = [], float("-inf")
    for w in ws or []:
        s = max(float(w[0]), prev)
        e = max(float(w[1]), s + min_len)
        out.append([s, e, str(w[2]), float(w[3]) if len(w) > 3 else 1.0])
        prev = e
    limit = max([float(hi)] + [float(w[1]) for w in ws or []])
    for w in reversed(out):
        if w[1] > limit:
            w[1] = limit
        if w[1] - w[0] < min_len:
            w[0] = w[1] - min_len
        limit = w[0]
    return [[round(w[0], 3), round(w[1], 3), w[2], round(w[3], 3)] for w in out]


def transcribe_pieces(sess, audio_by_file: dict, ranges: list, lang: str,
                      script_sentences=None) -> list:
    """Pass 3 (plan T11): the final pieces only, each prompted with ONLY its neighbouring
    script sentences (the whole script would be cut by Whisper and makes it skip repeats).

    ranges: reel.takes Pieces plus their prompt sentences, [{"file", "start", "end"
    (source s), "words": [the piece's pass-2 words], "prompt_sentences": [str]}]. "words"
    is REQUIRED (ValueError without it): pass 3 is prompted, so it is only trusted when it
    agrees with what the unprompted pass heard, and a piece with no pass-2 words is not
    run at all. Returns one word list per range in SOURCE seconds. A pass-3 result is used
    only when its seq_sim with the pass-2 words is at least PASS3_MIN_SIM (numbers read out
    on both sides, see spoken_sim), else the pass-2 words stay; and even then only word by
    word (merge_pass3: a word pass 3 changed to one it has p < PASS3_KEEP_P for stays pass
    2's), each pass-3 word at least PASS3_MIN_WORD long. Either way the spelling is fixed
    against the script (script_sentences, the whole script is fine, else the range's
    prompt sentences). audio_by_file maps a file name to 16 kHz audio (or to a path,
    loaded once)."""
    c = config.EDIT
    loaded: dict = {}
    out = []
    for n, r in enumerate(ranges or []):
        if not isinstance(r.get("words"), list):
            raise ValueError(f"transcribe_pieces: range {n} ({r.get('file')}) has no pass-2 "
                             f"'words' to check pass 3 against")
        p2 = [list(w) for w in r["words"]]
        sents = [str(s).strip() for s in (r.get("prompt_sentences") or []) if str(s).strip()]
        prompt = " ".join(sents)
        a, b = float(r.get("start", 0.0)), float(r.get("end", 0.0))
        name = r.get("file")
        wav = None
        if prompt and p2 and b - a >= MIN_AUDIO:              # pass 3 can run: its audio
            wav = loaded.get(name)
            if wav is None and name in (audio_by_file or {}):
                src = audio_by_file[name]
                wav = _load_audio(src) if isinstance(src, (str, Path)) else \
                    np.asarray(src, dtype=np.float32).ravel()
                loaded[name] = wav
        got = None
        if wav is not None:
            i0, i1 = int(round(max(0.0, a) * A.SR)), int(round(b * A.SR))
            res = sess.words(wav[i0:i1], lang, prompt=prompt, vad=False, cond=False,
                             offset=i0 / A.SR)
            cand = W.clean_words(_clamp_words(join_number_parts(res.get("words") or []), a, b),
                                 lang, c["echo_max"])
            if cand and spoken_sim(cand, p2, lang) >= PASS3_MIN_SIM:
                got = _min_length(merge_pass3(p2, cand, lang), b)
        ws = got if got is not None else p2
        script = script_sentences if script_sentences else sents
        out.append(fix_spelling(ws, script) if script else ws)
    return out


# ================================================================ voice-over words
_TRAIL_PUNCT = re.compile(r"^[.,!?…:;\"'»”)]+$")


def _display_tokens(spoken: str) -> list:
    """[[shown text, normalised token], ...] of the text the voice was made from: dashes
    removed, a lone punctuation mark joined to the word before it."""
    out: list = []
    for raw in W.strip_dashes(spoken).split():
        n = W.norm_token(raw)
        if n:
            out.append([raw, n])
        elif out and _TRAIL_PUNCT.match(raw):
            out[-1][0] += raw
    return out


def _key(tok: str) -> str:
    """Comparison key: a single number word and its digits are the same key."""
    val = getattr(W, "_value", None)
    try:
        v = val(tok.rstrip("%")) if val and not tok.endswith("%") else None
    except Exception:  # noqa: BLE001
        v = None
    return f"#{v:g}" if v is not None else tok


def _share(lo: float, hi: float, toks: list) -> list:
    """Split [lo, hi] among tokens by their length in characters."""
    lens = [max(1, len(t)) for t in toks]
    tot = float(sum(lens))
    out, t = [], lo
    for n in lens:
        d = (hi - lo) * n / tot
        out.append((t, t + d))
        t += d
    return out


def align_voice(whisper_words: list, spoken: str, dur: float | None = None,
                min_word: float = VOICE_MIN_WORD, text: str | None = None,
                lang: str = "pl") -> list:
    """Whisper's words on a voice-over take -> the spoken text's tokens with times.

    SequenceMatcher (autojunk off) over normalised tokens: equal -> copy the times; a
    replace of equal size -> 1:1; any other replace -> the Whisper span shared by
    character length; spoken tokens Whisper missed -> interpolated between their
    neighbours; Whisper tokens not in the text -> dropped. Then times are made monotonic
    with at least min_word s per word (and kept inside dur). The shown text is the spoken
    token with its own punctuation, so the spelling is exact; with `text` (the text as
    he typed it) the words are shown as typed instead (typed_words: «A», «AI», «m.in.»,
    digits), each with the time of what the voice read for it."""
    disp = _display_tokens(spoken)
    if not disp:
        return []
    ww = [list(w) for w in whisper_words or [] if W.norm_token(w[2])]
    a = [_key(W.norm_token(w[2])) for w in ww]
    b = [_key(n) for _, n in disp]
    times: list = [None] * len(disp)
    probs = [0.0] * len(disp)
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for i, j in zip(range(i1, i2), range(j1, j2)):
                times[j] = (float(ww[i][0]), float(ww[i][1]))
                probs[j] = float(ww[i][3]) if len(ww[i]) > 3 else 1.0
        elif tag == "replace":
            lo, hi = float(ww[i1][0]), float(ww[i2 - 1][1])
            p = float(np.mean([float(w[3]) if len(w) > 3 else 1.0 for w in ww[i1:i2]]))
            for j, span in zip(range(j1, j2), _share(lo, hi, [disp[j][1] for j in range(j1, j2)])):
                times[j] = span
                probs[j] = p
    # spoken tokens Whisper did not hear: between their neighbours
    j = 0
    n = len(disp)
    while j < n:
        if times[j] is not None:
            j += 1
            continue
        k = j
        while k < n and times[k] is None:
            k += 1
        lo = times[j - 1][1] if j > 0 else None
        hi = times[k][0] if k < n else None
        cnt = k - j
        if lo is None and hi is None:
            lo, hi = 0.0, (float(dur) if dur else cnt * VOICE_GUESS_WORD)
        elif lo is None:
            lo = max(0.0, hi - cnt * VOICE_GUESS_WORD)
        elif hi is None:
            hi = lo + cnt * VOICE_GUESS_WORD
            if dur and float(dur) > lo:
                hi = min(hi, float(dur))
        hi = max(hi, lo)
        for jj, span in zip(range(j, k), _share(lo, hi, [disp[x][1] for x in range(j, k)])):
            times[jj] = span
        j = k
    out = _settle([[s, e, shown, p] for (s, e), (shown, _), p in zip(times, disp, probs)],
                  dur, min_word)
    return typed_words(out, text, lang, dur, min_word) if text else out


def _settle(ws: list, dur: float | None, min_word: float) -> list:
    """Monotonic, at least min_word each, inside [0, dur]."""
    out, prev = [], 0.0
    for w in ws:
        s = max(float(w[0]), prev)
        e = max(float(w[1]), s + min_word)
        out.append([s, e, w[2], round(float(w[3]), 3)])
        prev = e
    if dur:
        limit = float(dur)
        for w in reversed(out):
            w[1] = min(w[1], limit)
            w[0] = max(0.0, min(w[0], w[1] - min_word))
            limit = w[0]
    return [[round(w[0], 3), round(w[1], 3), w[2], w[3]] for w in out]


# ---------------------------------------------------------------- the text as he typed it
# «5 000», «12 500 000»: one number, one word on screen (a no-break space inside)
_DIGIT_GROUP = re.compile(r"(?<![\d.,])\d{1,3}(?: \d{3})+(?!\d)")
_SPLIT_WS = re.compile(r"[ \t\r\n\f\v]+")        # not the no-break space of a digit group
_NOT_SHOWN = re.compile(r"[()\[\]{}\"„”“«»]")    # brackets and quotes never reach the screen
_READ_CACHE: dict = {}


def _typed_tokens(text: str) -> list:
    """[[shown text, normalised token], ...] of the text as he TYPED it, cleaned the way
    the voice engine cleans it before reading it (speech_text.clean_for_speech: part
    labels, [notes], stage directions, links and emoji out), dashes removed, brackets and
    quotes off, a digit group «5 000» one token, a lone punctuation mark joined to the
    word before it."""
    t = str(text or "")
    try:
        t = W._st().clean_for_speech(t)
    except Exception:  # noqa: BLE001 - the text as it is then
        pass
    t = _DIGIT_GROUP.sub(lambda m: m.group(0).replace(" ", NBSP), W.strip_dashes(t))
    out: list = []
    for raw in _SPLIT_WS.split(t):
        raw = _NOT_SHOWN.sub("", raw)
        n = W.norm_token(raw)
        if n:
            out.append([raw, n])
        elif out and _TRAIL_PUNCT.match(raw):
            out[-1][0] += raw
    return out


def _reading(raw: str, lang: str = "pl") -> list:
    """The tokens a typed token is read as: «AI» -> [ej, aj], «m.in.» -> [między, innymi],
    «5 000» -> [pięć, tysięcy] (pl_normalize, the voice engine's own reader). A plain word
    («Pokażę», «tak») reads as itself; other languages have no reader here."""
    n = W.norm_token(raw)
    core = _bare(raw)
    if lang != "pl" or (len(core) > 1 and core.isalpha()
                        and (core.islower() or core[1:].islower())):
        return [n] if n else []
    if raw not in _READ_CACHE:
        try:
            said = W.tokens(W._pl().normalize(raw))
        except Exception:  # noqa: BLE001 - read as written
            said = []
        _READ_CACHE[raw] = said or ([n] if n else [])
    return _READ_CACHE[raw]


def _cuts(m: int, counts: list) -> list:
    """m items cut into len(counts) consecutive runs sized by counts, each at least one
    (m >= len(counts)): the end index of every run."""
    q, tot = len(counts), float(sum(counts))
    ends, acc = [], 0.0
    for k, c in enumerate(counts):
        acc += c
        lo = (ends[-1] if ends else 0) + 1
        hi = m - (q - k - 1)
        ends.append(min(hi, max(lo, int(round(acc / tot * m)))))
    ends[-1] = m
    return ends


def typed_words(words: list, text: str, lang: str = "pl", dur: float | None = None,
                min_word: float = VOICE_MIN_WORD) -> list:
    """Voice words (align_voice: the SPOKEN tokens with their times) shown as he TYPED the
    text: «punkt a i punkt be» -> «punkt A i punkt B.», «Ej aj» -> «AI», «między innymi
    pięć tysięcy złotych» -> «m.in. 5 000 zł.»; digits he typed stay digits.

    Each typed token is read out (_reading) and the readings are aligned to the spoken
    tokens (SequenceMatcher, number words and digits equal): a typed token takes the time
    from the first to the last spoken token its reading matched; where the reading and
    the speech differ (a case ending, «r.» read «roku») the spoken span is shared among
    the typed tokens there by the length of their readings, and spoken words nobody typed
    go to the typed token before them. A typed token the voice never said is left out.
    When the readings match less than VOICE_TYPED_MIN of the spoken tokens (the take was
    read from another text), or less than VOICE_TYPED_MIN of the typed text's own readings
    (only a part of it was read: a mismatch would spread the unsaid rest over the words
    that were said), the spoken words come back unchanged."""
    ws = [list(w) for w in words or [] if W.norm_token(w[2])]
    typed = _typed_tokens(text)
    if not ws or not typed:
        return [list(w) for w in words or []]
    rk, owner = [], []
    for i, (raw, _n) in enumerate(typed):
        for t in _reading(raw, lang):
            rk.append(_key(t))
            owner.append(i)
    sk = [_key(W.norm_token(w[2])) for w in ws]
    got: list = [[] for _ in typed]                  # per typed token: [(s, e, p), ...]

    def give(i: int, j: int) -> None:
        w = ws[j]
        got[i].append((float(w[0]), float(w[1]), float(w[3]) if len(w) > 3 else 1.0))

    equal = 0
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, rk, sk, autojunk=False).get_opcodes():
        if tag == "equal":
            equal += j2 - j1
            for k in range(j2 - j1):
                give(owner[i1 + k], j1 + k)
        elif tag == "insert":
            i = owner[i1 - 1] if i1 > 0 else owner[i1] if i1 < len(owner) else None
            for j in range(j1, j2):
                if i is not None:
                    give(i, j)
        elif tag == "replace":
            who = list(dict.fromkeys(owner[i1:i2]))
            counts = [owner[i1:i2].count(i) for i in who]
            m = j2 - j1
            if m >= len(who):
                start = j1
                for i, end in zip(who, _cuts(m, counts)):
                    for j in range(start, j1 + end):
                        give(i, j)
                    start = j1 + end
            else:                                    # fewer words said than typed tokens
                lo, hi = float(ws[j1][0]), float(ws[j2 - 1][1])
                p = min(float(w[3]) if len(w) > 3 else 1.0 for w in ws[j1:j2])
                for i, (s, e) in zip(who, _share(lo, hi, ["x" * c for c in counts])):
                    got[i].append((s, e, p))
    if equal < VOICE_TYPED_MIN * len(ws) or equal < VOICE_TYPED_MIN * len(rk):
        return [list(w) for w in words or []]
    out = []
    for (raw, _n), g in zip(typed, got):
        if g:
            out.append([min(x[0] for x in g), max(x[1] for x in g), raw,
                        round(min(x[2] for x in g), 3)])
    return _settle(out, dur, min_word)


def voice_cache_path(path, spoken: str, lang: str, model: str = MODEL, cache_dir=None) -> Path:
    p = Path(path)
    sp = hashlib.sha1(str(spoken or "").encode("utf-8")).hexdigest()[:12]
    return Path(cache_dir or config.SPEECH_DIR) / \
        f"voice-{p.stem}-{cache_key(p, lang, model, extra=sp)}.json"


def voice_words(sess, wav_path, spoken: str, lang: str, cache_dir=None,
                text: str | None = None) -> list:
    """Word timings of a voice-over take, spelled exactly as `spoken` (the text the take was
    synthesised from): Whisper with the start of that text as its prompt and conditioning
    on (a take is one continuous read), then align_voice. Cached per take file (size,
    mtime) and spoken text; `sess` may be None when the cache has it.

    `text`, the text as he TYPED it (voice["text"]), shows the words as typed: «punkt A»,
    «AI», «m.in.», «5 000 zł» instead of how the voice read them (typed_words, on every
    call, so the cache holds only the spoken words and never goes stale).

    The prompt is the first ~VOICE_PROMPT_WORDS words cut from the HEAD to the token budget:
    the prompt only steers the first 30 s window, which is the start of the text."""
    path = Path(wav_path)
    if not _display_tokens(spoken):
        return []
    model = getattr(sess, "model_name", None) or MODEL
    cp = voice_cache_path(path, spoken, lang, model, cache_dir)
    got = _read_json(cp)
    if isinstance(got, dict) and got.get("version") == CACHE_V and isinstance(got.get("words"), list):
        if text and str(text).strip():
            return typed_words(got["words"], text, lang, _finite(got.get("dur"), 0.0) or None)
        return got["words"]
    if sess is None:
        raise RuntimeError(f"no cached voice words for {path.name} and no Whisper session")
    wav = _load_audio(path)
    dur = wav.size / A.SR
    head = " ".join(W.strip_dashes(spoken).split()[:VOICE_PROMPT_WORDS])
    prompt = truncate_prompt(head, PROMPT_TOKENS, getattr(sess, "count_tokens", None), "head")
    res = sess.words(wav, lang, prompt=prompt or None, vad=False, cond=True)
    out = align_voice(res.get("words") or [], spoken, dur)
    _write_json(cp, {"version": CACHE_V, "file": path.name, "dur": round(dur, 3),
                     "lang": lang, "whisper": res.get("words") or [], "words": out,
                     "device": getattr(sess, "device", None) or "cpu"})
    if text and str(text).strip():
        return typed_words(out, text, lang, dur or None)
    return out


# ================================================================ CLI
def main(argv: list | None = None) -> int:
    """Analyse clips into a folder (CPU, cache in a temp folder), from the scripts folder:

        CUDA_VISIBLE_DEVICES=-1 python -m autoedit.speech --cpu --lang pl --out speech_out "clips/*.mov"
    """
    import argparse  # noqa: PLC0415
    import shutil  # noqa: PLC0415
    import tempfile  # noqa: PLC0415

    # the Windows console is cp1252: a Polish or Cyrillic clip name would stop the run
    # right after its cache file was written
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(description=main.__doc__)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--lang", default="pl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args(argv)
    files = sorted({str(Path(f)) for pat in args.files for f in (glob.glob(pat) or [pat])})
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="speech-")
    try:
        with WhisperSession(args.model, device="cpu" if args.cpu else None,
                            compute="int8" if args.cpu else None) as sess:
            for f in files:
                t0 = time.monotonic()
                analyze_clip(sess, f, args.lang, cache_dir=tmp, use_cache=False)
                shutil.copyfile(cache_path(f, args.lang, args.model, tmp),
                                out_dir / f"{Path(f).stem}.json")
                print(f"{Path(f).name}: {time.monotonic() - t0:.1f}s wall", flush=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
