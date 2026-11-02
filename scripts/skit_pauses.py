"""reel-tool skit-pauses <job> [--keep 0.45] [--min 0.5] [--apply]

Skits keep their pauses, because the pause is the timing; but a pause over ~0.5 s usually drags. For every such pause inside a piece
this looks for the calmest pair of frames (smallest body difference at 15 fps) that shortens it to about --keep seconds, so the cut
cannot be seen in the hands. Under 2.5 = invisible. It prints the options; --apply cuts those under 3.0 and leaves the others whole.
Read the transcript first: a beat that is the joke ("checking the system...") may keep a bit more, set --keep for the job.
"""
import subprocess, sys
import numpy as np

import common as C
from autocut import derive, out_time_map
from recut import drop_range

CALM = 3.0


def frames(f, a, b, fps=15):
    r = subprocess.run([C.FF, "-hide_banner", "-loglevel", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(f), "-vf",
                        f"fps={fps},scale=270:480,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    x = np.frombuffer(r, np.uint8).reshape(-1, 480, 270).astype(np.float32)[:, 120:400]
    return [(a + i / fps, x[i]) for i in range(len(x))]


def main(argv):
    opt = lambda k, d: float(argv[argv.index(k) + 1]) if k in argv else d
    keep, minp = opt("--keep", 0.45), opt("--min", 0.5)
    job = C.job_dir(argv[0]); cut = C.load_json(job / "cut.json") or C.fail("no cut.json")
    merged = []                                              # back-to-back pieces of one clip count as one: their pause is a pause too
    for p in cut["pieces"]:
        if merged and merged[-1]["file"] == p["file"] and abs(merged[-1]["b"] - p["a"]) < 0.03:
            merged[-1] = dict(merged[-1], b=p["b"], words=merged[-1]["words"] + p["words"])
        else:
            merged.append(p)
    cut["pieces"] = merged
    P = merged; offs, _ = out_time_map(P); plan = []
    for k, p in enumerate(P):
        ws = p["words"]
        for w, n in zip(ws, ws[1:]):
            gap = n[0] - w[1]
            if gap < minp:
                continue
            a, b = w[1] + 0.12, n[0] - 0.12                  # stay off the words
            fr = frames(p["file"], a, b); best = None
            if len(fr) < 4:
                continue
            need = gap - keep; best = None; part = None
            for i, (ta, x) in enumerate(fr):
                for tb, y in fr[i + 1:]:
                    if tb - ta < 0.12:
                        continue
                    d = float(np.mean(np.abs(x - y)))
                    if tb - ta >= need - 0.04 and (best is None or d < best[0]):
                        best = (d, ta, tb)
                    if d < CALM and (part is None or tb - ta > part[2] - part[1]):
                        part = (d, ta, tb)                    # the longest calm cut, when the full one is not calm
            if best and best[0] >= CALM and part:
                best = part
            if best:
                d, ta, tb = best
                o0 = offs[k] + ta - p["a"]; o1 = offs[k] + tb - p["a"]
                print(f"pause {gap:.2f} s after \"{w[2]}\" (reel {offs[k] + w[1] - p['a']:.2f}): cut {o0:.2f}-{o1:.2f}, leaves {gap - (tb - ta):.2f} s, body diff {d:.1f}"
                      f"{'' if d < CALM else '  NOT CALM: stays whole'}")
                if d < CALM:
                    plan.append((o0, o1))
    if "--apply" in argv and plan:
        for a, b in sorted(plan, reverse=True):              # from the end: earlier times stay valid
            drop_range(cut, a, b)
        total, _ = derive(job, cut)
        (job / "gate.json").unlink(missing_ok=True)
        print(f"applied {len(plan)} cuts; now {total:.2f} s. Run reel-tool jump, then stutter and subs again.")
    elif not plan:
        print("nothing to shorten")


if __name__ == "__main__":
    main(sys.argv[1:])
