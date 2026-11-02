"""reel-tool stutter <job> [--final]: stutter and false-start passes on the kept audio.

Why: Whisper on a whole piece often writes a false start or a doubled word only once ("Tylko, tylko że dziś" ->
"Tylko, że dziś"), so re-transcribing the finished Reel cannot see it. This pass looks at the audio itself: it splits the
kept speech into bursts at short gaps, transcribes each burst on its own, and compares neighbouring bursts.

Two passes, always: gap 0.12 s, then gap 0.04 s. A quick restart with only ~0.06 s pause merges into one burst at 0.12 and
only shows at 0.04; the fine pass also splits words into parts, so every flag is VOTED: the stretch around it is
transcribed three more times (different temperatures, no context) and the flag stands only if the repeat is heard at least
twice. Confirmed flags carry a suggested cut in Reel seconds (reel-tool recut <job> --drop A-B).

Flags: RESTART (B starts like A), DOUBLE (A's last word = B's first), WORDREP (word repeated or word prefix repeated inside a
burst, within 1 s), SHORT? (an unclear burst under 0.6 s in the first 1.5 s of a piece, followed by a pause).
With --final the same passes run on the audio of final.mp4 (must also be 0).
Writes stutter_report.json.
"""
import re, sys, wave
from difflib import SequenceMatcher
import numpy as np

import common as C

SR = 16000
PAT = re.compile(r"[^\w]", re.UNICODE)


def norm(t):
    return PAT.sub("", t.lower())


def same_start(a, b):
    """a, b: first words. True if b begins like a (false start / repeat)."""
    if not a or not b:
        return False
    if a == b:
        return True
    if len(a) >= 2 and b.startswith(a):
        return True
    k = min(len(a), len(b), 4)
    return k >= 3 and SequenceMatcher(None, a[:k], b[:k]).ratio() >= 0.75


class Pass:
    def __init__(self, model, A, lang):
        self.m, self.A, self.lang = model, A, lang

    def bursts(self, s0, s1, gap, step, thr=-40):
        A, st = self.A, int(step * SR)
        db = [20 * np.log10(np.sqrt(np.mean(A[i:i + st] ** 2)) + 1e-9) for i in range(int(s0 * SR), int(s1 * SR), st)]
        sp = [x > thr for x in db]; g = max(1, round(gap / step)); out = []; i = 0
        while i < len(sp):
            if sp[i]:
                j = i
                while j < len(sp) and (sp[j] or any(sp[j:j + g])):
                    j += 1
                out.append([round(s0 + i * step, 2), round(s0 + j * step, 2)]); i = j
            else:
                i += 1
        return [b for b in out if b[1] - b[0] >= 0.1]

    def words_of(self, b0, b1, pad=0.06):
        A = self.A
        segs, _ = self.m.transcribe(A[int(max(0, b0 - pad) * SR):int((b1 + pad) * SR)], language=self.lang, beam_size=5,
                                    vad_filter=False, condition_on_previous_text=False, word_timestamps=True)
        return [(x.start + b0 - pad, x.end + b0 - pad, norm(x.word)) for s in segs for x in s.words if norm(x.word)]

    def vote(self, a, b, needle):
        """transcribe the stretch whole, three ways: is the repeat really heard?"""
        pad = np.zeros(8000, np.float32); hits = 0; heard = []
        for T in (0.0, 0.3, 0.6):
            segs, _ = self.m.transcribe(np.concatenate([pad, self.A[int(max(0, a) * SR):int(b * SR)], pad]), language=self.lang, beam_size=5,
                                        temperature=T, vad_filter=False, condition_on_previous_text=False)
            ws = [w for w in (norm(x) for s in segs for x in s.text.split()) if w]; heard.append(" ".join(ws))
            if any(same_start(x, y) and (not needle or x.startswith(needle[:3]) or y.startswith(needle[:3])) for x, y in zip(ws, ws[1:])):
                hits += 1
        return hits, heard


def flags_in(P, spans, gap, known=()):
    """known: (start, end, normalised word) of the kept words; a short burst that is simply one of them is not a problem"""
    step = 0.02 if gap < 0.1 else 0.05; out = []
    near = lambda t: {w[2] for w in known if t - 0.7 <= w[0] <= t + 0.7}
    for c0, c1 in spans:
        bs = P.bursts(c0, c1, gap, step); tx = [P.words_of(b0, b1) for b0, b1 in bs]; fl = []
        for k in range(len(bs) - 1):
            (a0, a1), (b0, b1) = bs[k], bs[k + 1]; wa, wb = tx[k], tx[k + 1]; g = b0 - a1
            fa, fb = (wa[0][2] if wa else ""), (wb[0][2] if wb else "")
            two_a, two_b = [x[2] for x in wa[:2]], [x[2] for x in wb[:2]]
            if wa and wb and same_start(fa, fb) and (len(wa) <= 3 or two_a == two_b):
                fl.append({"type": "RESTART", "at": a0, "cut": [a0, round(b0 - 0.08, 2)], "key": fa,
                           "heard": f"{' '.join(x[2] for x in wa)} | {' '.join(x[2] for x in wb[:4])}"})
            elif wa and wb and wa[-1][2] == fb and len(fb) >= 2:
                fl.append({"type": "DOUBLE", "at": a1, "cut": [round(wa[-1][0] - 0.03, 2), round(b0 - 0.08, 2)], "key": fb,
                           "heard": f"...{wa[-1][2]} | {' '.join(x[2] for x in wb[:3])}"})
            elif (a1 - a0) < 0.6 and a0 - c0 < 1.5 and g >= 0.25 and gap > 0.1 and not (wa and all(x[2] in near(a0) for x in wa)):
                fl.append({"type": "SHORT?", "at": a0, "cut": [a0, round(b0 - 0.08, 2)], "key": "",
                           "heard": f"[{' '.join(x[2] for x in wa) or '?'}] | {' '.join(x[2] for x in wb[:3])}"})
        for ws in tx:
            for i in range(len(ws) - 1):
                x, y = ws[i], ws[i + 1]
                if y[0] - x[0] < 1.0 and (x[2] == y[2] or (len(x[2]) >= 2 and y[2].startswith(x[2]) and len(y[2]) > len(x[2]))):
                    fl.append({"type": "WORDREP", "at": round(x[0], 2), "cut": [round(x[0] - 0.03, 2), round(y[0] - 0.05, 2)], "key": x[2],
                               "heard": f"{x[2]} {y[2]}"})
        out += fl
    return out


def main(argv):
    job = C.job_dir(argv[0]); final = "--final" in argv
    J = C.load_json(job / "job.json", {}); cut = C.load_json(job / "cut.json") or {}
    lang = cut.get("lang") or J.get("lang") or "en"
    from autoedit import speech                               # puts the GPU runtime on PATH
    with speech.WhisperSession(C.config().get("whisper_model", "large-v3")) as sess:
        wav = job / ("final16k.wav" if final else "kept16k.wav")
        if final:
            C.ff("-i", str(job / "final.mp4"), "-vn", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(wav))
        else:
            from autoedit import audio as AU
            parts, cache = [], {}                             # the raw kept audio, back to back = Reel time
            for p in cut["pieces"]:
                a = cache.setdefault(p["file"], AU.load(p["file"]))
                n = int(round((p["b"] - p["a"]) * SR)); s = int(round(p["a"] * SR)); parts.append(a[s:s + n])
            x = np.concatenate(parts)
            with wave.open(str(wav), "w") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
        w = wave.open(str(wav)); A = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; w.close()
        if final:
            spans = [(0.0, len(A) / SR)]
        else:
            spans, o = [], 0.0
            for p in cut["pieces"]:
                L = p["b"] - p["a"]; spans.append((o, o + L)); o += L
        P = Pass(sess._model, A, lang); rep = []
        W = (C.load_json(job / "words.json", {}) or {}).get("words", [])
        known = [(w[0], w[1], norm(w[2])) for w in W]
        for gap in (0.12, 0.04):
            for f in flags_in(P, spans, gap, known):
                f["gap"] = gap
                if f["type"] == "SHORT?":
                    f["verdict"] = "listen"
                else:
                    hits, heard = P.vote(max(0, f["at"] - 0.6), min(len(A) / SR, f["cut"][1] + 1.2), f["key"])
                    f["votes"], f["voted_text"] = hits, heard
                    f["verdict"] = "CONFIRMED" if hits >= 2 else "false alarm"
                rep.append(f)
    seen, uniq = set(), []                                    # the same flag from both passes counts once
    for f in rep:
        k = (f["type"], round(f["at"]), f.get("key"))
        if k not in seen:
            seen.add(k); uniq.append(f)
    conf = [f for f in uniq if f["verdict"] == "CONFIRMED"]; lst = [f for f in uniq if f["verdict"] == "listen"]
    C.save_json(job / ("stutter_final.json" if final else "stutter_report.json"), {"confirmed": conf, "listen": lst, "all": uniq})
    for f in uniq:
        print(f"{f['verdict']:12s} {f['type']:8s} at {f['at']:6.2f} s  cut {f['cut'][0]}-{f['cut'][1]}  heard: {f['heard']}"
              + (f"  votes {f['votes']}/3" if "votes" in f else ""))
    print(f"FLAGS: {len(conf)} confirmed, {len(lst)} to listen, {len(uniq) - len(conf) - len(lst)} false alarms ({'final' if final else 'cut'})")


if __name__ == "__main__":
    main(sys.argv[1:])
