"""reel-tool vote <job> A-B [A-B ...]: re-hear a doubtful stretch of the cut, Reel seconds, 6 ways (paddings, temperatures, no context,
no prompt), and print each reading. Unanimous = that is what was said. Split = keep the best reading and name it in the report.
"""
import sys, wave
from collections import Counter
import numpy as np

import common as C

SR = 16000


def main(argv):
    job = C.job_dir(argv[0]); cut = C.load_json(job / "cut.json") or C.fail("no cut.json")
    lang = cut.get("lang") or "en"
    wav = job / "kept16k.wav"
    from autoedit import speech, audio as AU
    if not wav.exists():
        parts, cache = [], {}
        for p in cut["pieces"]:
            a = cache.setdefault(p["file"], AU.load(p["file"]))
            n = int(round((p["b"] - p["a"]) * SR)); s = int(round(p["a"] * SR)); parts.append(a[s:s + n])
        x = np.concatenate(parts)
        with wave.open(str(wav), "w") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    w = wave.open(str(wav)); A = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; w.close()
    pad = np.zeros(8000, np.float32)
    with speech.WhisperSession(C.config().get("whisper_model", "large-v3")) as sess:
        for ab in argv[1:]:
            a, b = map(float, ab.split("-")); got = []
            for edge in (0.0, 0.25):
                for T in (0.0, 0.3, 0.6):
                    x = A[int(max(0, a - edge) * SR):int((b + edge) * SR)]
                    segs, _ = sess._model.transcribe(np.concatenate([pad, x, pad]), language=lang, beam_size=5, temperature=T, vad_filter=False, condition_on_previous_text=False)
                    got.append(" ".join(s.text.strip() for s in segs))
            print(f"{ab}:")
            for t, n in Counter(got).most_common():
                print(f"  {n}/6  {t}")


if __name__ == "__main__":
    main(sys.argv[1:])
