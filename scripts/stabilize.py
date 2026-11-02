"""reel-tool stabilize <job> [--force]: two-pass vidstab on each hand-held source clip, kept only when it clearly helps.

Shake is measured on the background (the top strip of the frame, frame-to-frame shift, high-passed so slow pans do not count).
A stabilised copy is used only if that shake drops by 30 % or more: on a selfie without a tripod vidstab often locks onto the
head and makes the background worse, so the measurement decides, not habit. The copy is cropped 4 % to hide the moving edges.
Pieces are then rebuilt from the stabilised copies (job.json "stab").
"""
import subprocess, sys
from pathlib import Path
import numpy as np

import common as C

GAIN = 0.70          # stabilised shake must be at most this share of the original


def jitter(path, frames=600):
    import cv2
    v = cv2.VideoCapture(str(path)); pv, D = None, []; sc = 1080 / max(1, v.get(3))
    while len(D) < frames:
        ok, f = v.read()
        if not ok:
            break
        h = f.shape[0]; g = cv2.cvtColor(f[int(h * .02):int(h * .22)], cv2.COLOR_BGR2GRAY).astype(np.float32)
        g = cv2.resize(g, (g.shape[1] // 2, g.shape[0] // 2))
        if pv is not None:
            D.append(cv2.phaseCorrelate(pv, g)[0])
        pv = g
    if len(D) < 20:
        return 0.0
    d = np.array(D) * sc * 2; hf = d - np.apply_along_axis(lambda x: np.convolve(x, np.ones(15) / 15, "same"), 0, d)
    return round(float(np.sqrt((hf ** 2).sum(1).mean())), 2)


def main(argv):
    job = C.job_dir(argv[0]).resolve(); J = C.load_json(job / "job.json") or C.fail("no job.json")
    cut = C.load_json(job / "cut.json") or C.fail("no cut.json")
    out = job / "stab"; out.mkdir(exist_ok=True); stab = J.get("stab") or {}
    for src in sorted({p["file"] for p in cut["pieces"]}):
        name = Path(src).stem; trf, dst = out / f"{name}.trf", out / f"{name}.mov"
        w = next((x["width"] for x in J["info"] if x["file"] == src), 1080)
        r = C.ff("-i", src, "-vf", f"vidstabdetect=shakiness=6:accuracy=15:result={trf.name}", "-f", "null", "-", cwd=str(out))
        if r.returncode:
            C.fail("vidstab is missing in this ffmpeg: " + r.stderr[-300:])
        r = C.ff("-i", src, "-vf", f"vidstabtransform=input={trf.name}:smoothing=20:optzoom=0:zoom=4:maxshift={round(w * .018)}:maxangle=0.02:interpol=bicubic:crop=keep",
                 "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-c:a", "copy", dst.name, cwd=str(out))
        j0, j1 = jitter(src), jitter(dst)
        keep = j0 > 0 and j1 <= j0 * GAIN
        print(f"{Path(src).name}: shake {j0} px -> {j1} px stabilised: {'USE stabilised' if keep else 'keep the original (less than 30 % better)'}")
        if keep:
            stab[src] = str(dst)
        else:
            stab.pop(src, None)
    J["stab"] = stab; C.save_json(job / "job.json", J)


if __name__ == "__main__":
    main(sys.argv[1:])
