"""reel-tool wordcheck <job>: re-hear the whole cut (raw kept audio, Reel seconds) and compare it with the words the cut should
contain. Tightening pauses must never clip a quiet word ("that", "it", an ending); this is the proof. Writes wordcheck.json.

A missing word is re-heard 4 ways around its place before it counts, so Whisper's own slips on a long file do not raise alarms.
If a word is really gone: `reel-tool recut <job> --in/--out` to give it back (the table shows where), then run this again.
"""
import re, sys, wave
from difflib import SequenceMatcher
import numpy as np

import common as C
from autoedit import words as W

SR = 16000


def kept_audio(job, cut):
    from autoedit import audio as AU
    parts, cache = [], {}
    for p in cut["pieces"]:
        a = cache.setdefault(p["file"], AU.load(p["file"]))
        n = int(round((p["b"] - p["a"]) * SR)); s = int(round(p["a"] * SR)); parts.append(a[s:s + n])
    x = np.concatenate(parts)
    with wave.open(str(job / "kept16k.wav"), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    return x


def main(argv):
    job = C.job_dir(argv[0]); cut = C.load_json(job / "cut.json") or C.fail("no cut.json")
    lang = cut.get("lang") or "en"
    exp, o = [], 0.0
    for p in cut["pieces"]:
        for w in p["words"]:
            for t in W.tokens(w[2]):
                exp.append((t, o + max(w[0], p["a"]) - p["a"], w[2]))
        o += p["b"] - p["a"]
    A = kept_audio(job, cut)
    from autoedit import speech
    with speech.WhisperSession(C.config().get("whisper_model", "large-v3")) as sess:
        segs, _ = sess._model.transcribe(A, language=lang, beam_size=5, vad_filter=False, condition_on_previous_text=False)
        heard = W.tokens(" ".join(s.text for s in segs))
        E = [e[0] for e in exp]
        miss = []
        for tag, i1, i2, j1, j2 in SequenceMatcher(None, E, heard, autojunk=False).get_opcodes():
            if tag in ("delete", "replace") and i2 > i1 and (tag == "delete" or (i2 - i1) > (j2 - j1)):
                miss.append((i1, i2))
        confirmed = []
        pad = np.zeros(8000, np.float32)
        for i1, i2 in miss:
            t0 = max(0.0, exp[max(0, i1 - 3)][1] - 0.2); t1 = exp[min(len(exp) - 1, i2 + 2)][1] + 0.8
            want = [e[0] for e in exp[i1:i2]]; hits = 0
            for off in (0.0, 0.08):
                for T in (0.0, 0.3):
                    s2, _ = sess._model.transcribe(np.concatenate([pad, A[int((t0 + off) * SR):int((t1 - off) * SR)], pad]), language=lang, beam_size=5,
                                                   temperature=T, vad_filter=False, condition_on_previous_text=False)
                    got = W.tokens(" ".join(s.text for s in s2))
                    hits += all(any(W.tok_sim(w, g) >= 0.8 for g in got) for w in want)
            if hits < 2:
                confirmed.append({"at": round(exp[i1][1], 2), "words": " ".join(exp[k][2] for k in range(i1, i2)), "heard_in": f"{hits}/4"})
    sim = W.seq_sim(" ".join(E), " ".join(heard))
    C.save_json(job / "wordcheck.json", {"missing": confirmed, "similarity": round(sim, 3), "expected": len(E), "heard": len(heard)})
    for m in confirmed:
        print(f"MISSING at {m['at']:6.2f} s: \"{m['words']}\" (heard in {m['heard_in']} re-listens)")
    print(f"WORDS: {len(confirmed)} missing, similarity {sim:.2f} ({len(heard)} heard of {len(E)} expected)")


if __name__ == "__main__":
    main(sys.argv[1:])
