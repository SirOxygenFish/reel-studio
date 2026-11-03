"""ReelsMotion quality checks.
    python qc.py <video.mp4> [--report report.json] [--every 2] [--dead 1.0] [--thr 0.25] [--sub 1240,1510] [--out <dir>]
    python qc.py <hybrid.mp4> --visuals visuals.json [--name "Reel"]   (hybrid: reports of the current render + VARIETY check)
Writes <out>/<name>_qc.json and <name>_qc_sheet.jpg and prints a summary:
  motion      per-frame motion energy (mean abs difference of consecutive frames, 0-255 scale) in the graphics area
              (subtitle band and Instagram's bottom strip excluded, so changing subtitles never count as motion)
  dead        runs where motion stays under --thr for longer than --dead seconds ("nothing moves")
  coverage    share of the safe box covered by content boxes (from the renderer's --report); target 0.6-0.7
  safe        content boxes inside the subtitle band, outside the frame, or under Instagram's top strip
Only numpy + Pillow; ffmpeg from the Reel Studio setup.
"""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import common as C
FF, FP = C.FF, C.FP


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def probe(src):
    out = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", src], capture_output=True, text=True).stdout
    j = json.loads(out); s = j["streams"][0]; a, b = s["r_frame_rate"].split("/")
    return s["width"], s["height"], float(a) / float(b), float(j["format"]["duration"])


TUTORIAL = "--tutorial" in sys.argv     # tutorials: no subtitles and not an Instagram post, so the Instagram zones do not apply


def motion(src, W, H, sub, fps_in):
    """motion energy per frame at 15 fps on a 1/8 scale gray image, graphics area only"""
    w, h = W // 8, H // 8
    raw = subprocess.run([FF, "-v", "error", "-i", src, "-vf", f"fps=15,scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    mask = np.ones((h, w), bool)
    if sub:
        mask[int(sub[0] / 8):int(sub[1] / 8)] = False              # subtitle band
    if H > 1500 and not TUTORIAL:
        mask[int(1560 / 8):] = False                              # Instagram caption/buttons strip
    d = np.abs(np.diff(fr, axis=0))[:, mask].mean(1)
    return np.concatenate([[d[0] if len(d) else 0], d]), 15.0


def runs(t, ok, min_len):
    out, start = [], None
    for i, v in enumerate(ok):
        if v and start is None:
            start = i
        if (not v or i == len(ok) - 1) and start is not None:
            end = i if not v else i + 1
            if t[min(end, len(t) - 1)] - t[start] >= min_len:
                out.append((round(float(t[start]), 2), round(float(t[min(end, len(t) - 1)]), 2)))
            start = None
    return out


def coverage(rep):
    x0, y0, x1, y1 = rep["box"]; g = 10
    gw, gh = int((x1 - x0) / g), int((y1 - y0) / g); cov, safe = [], []
    sub = (1240, 1510) if rep["H"] > 1500 and not TUTORIAL else None
    cuts = [s["start"] for s in rep.get("scenes") or []][1:]
    edges = rep.get("edges") or []                               # hybrid clips: iris in from the face / zoom out into it
    for t, boxes in rep["samples"]:
        in_trans = any(abs(t - c) < 0.35 for c in cuts) or any(-0.05 <= t - a < 0.5 for a, b in edges) or any(-0.05 <= b - t < 0.45 for a, b in edges)
        m = np.zeros((gh, gw), bool)
        for a, b, c, d in boxes:
            m[max(0, int((b - y0) / g)):max(0, int((d - y0) / g)), max(0, int((a - x0) / g)):max(0, int((c - x0) / g))] = True
            if in_trans:                                          # transitions sweep through everything on purpose
                continue
            if sub and d > sub[0] + 6 and b < sub[1]:
                safe.append([t, "subtitle band", [a, b, c, d]])
            if a < -4 or c > rep["W"] + 4 or b < -4 or d > rep["H"] + 4:
                safe.append([t, "outside frame", [a, b, c, d]])
            if rep["H"] > 1500 and not TUTORIAL and b < 120 and d > 20:
                safe.append([t, "instagram top strip", [a, b, c, d]])
        cov.append([t, round(float(m.mean()), 3)])
    # an issue counts only if it persists >= 0.5 s in one continuous run (entrances from off-screen are fine)
    keep, runs = [], {}
    for t, kind, bx in safe:
        key = (kind, round(bx[0] / 80), round(bx[1] / 80))
        rs = runs.setdefault(key, [])
        if rs and t - rs[-1][-1][0] <= 0.3:
            rs[-1].append([t, kind, bx])
        else:
            rs.append([[t, kind, bx]])
    for rs in runs.values():
        for r in rs:
            if r[-1][0] - r[0][0] >= 0.5:
                keep += r
    return cov, sorted(keep)


def sheet(src, dur, every, dead, out, wide=False):
    n = int(dur / every) + 1; tiles = []
    tw, th = (384, 216) if wide else (216, 384)                  # tiles keep the video's own shape
    for i in range(n):
        t = min(dur - 0.05, i * every + every / 2)
        raw = subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", f"scale={tw}:{th}", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(raw) == tw * th * 3:
            tiles.append((t, Image.fromarray(np.frombuffer(raw, np.uint8).reshape(th, tw, 3))))
    cols = 5 if wide else 8; rows = (len(tiles) + cols - 1) // cols
    S = Image.new("RGB", (cols * (tw + 4), rows * (th + 28)), "white"); D = ImageDraw.Draw(S)
    f = ImageFont.truetype(C.sub_font()[1], 18)
    for i, (t, im) in enumerate(tiles):
        x, y = i % cols * (tw + 4), i // cols * (th + 28)
        S.paste(im, (x + 2, y + 26))
        bad = any(a - 0.2 <= t <= b + 0.2 for a, b in dead)
        D.text((x + 6, y + 3), f"{t:.1f} s" + ("  DEAD" if bad else ""), fill=(200, 0, 0) if bad else (0, 0, 0), font=f)
    S.save(out, quality=86)


def main():
    src = sys.argv[1]; W, H, fps, dur = probe(src)
    sub = tuple(int(x) for x in arg("--sub", "1240,1510").split(",")) if H > 1500 else None
    if "--no-sub" in sys.argv:
        sub = None
    out_dir = arg("--out", os.path.dirname(os.path.abspath(src))); base = os.path.splitext(os.path.basename(src))[0]
    thr, dead_len = float(arg("--thr", "0.25")), float(arg("--dead", "1.0"))
    e, mfps = motion(src, W, H, sub, fps); t = np.arange(len(e)) / mfps
    dead = runs(t, e < thr, dead_len)
    res = {"video": src, "duration": round(dur, 2), "motion": {"median": round(float(np.median(e)), 3), "p10": round(float(np.percentile(e, 10)), 3),
           "p90": round(float(np.percentile(e, 90)), 3), "still_share": round(float((e < thr).mean()), 3)}, "dead_runs": dead,
           "thr": thr, "dead_len": dead_len}
    rp = arg("--report")
    vj = arg("--visuals")                                       # hybrid: segment reports of THIS render + the variety check
    if vj and not rp and os.path.exists(os.path.join(os.path.dirname(os.path.abspath(vj)), "_motion", "current.json")):
        rp = ",".join(c["report"] for c in json.load(open(os.path.join(os.path.dirname(os.path.abspath(vj)), "_motion", "current.json"))))
    reps = [json.load(open(p)) for p in (rp or "").split(",") if p and os.path.exists(p)]
    if reps:
        rep = reps[0]
        for r in reps[1:]:                                       # hybrid: one report per segment (reel time)
            rep = dict(rep, samples=rep["samples"] + r["samples"], scenes=(rep.get("scenes") or []) + (r.get("scenes") or []))
        if len(reps) > 1 or reps[0].get("t0"):
            rep["edges"] = [[r["t0"], r["t1"]] for r in reps if r.get("t1")]
        cov, safe = coverage(rep)
        circ = [r.get("circles") for r in reps if r.get("circles")]
        if circ:
            worst = max((c["max"] for c in circ), key=lambda m: m[0])
            res["circles"] = {"frames": sum(c["frames"] for c in circ), "worst": worst, "fail_frames": sum(c["failCount"] for c in circ),
                              "fails": [f for c in circ for f in c["fails"]][:20]}
        cv = np.array([c for _, c in cov])
        res["coverage"] = {"mean": round(float(cv.mean()), 3), "min": round(float(cv.min()), 3), "under_40": round(float((cv < 0.4).mean()), 3),
                           "lowest": sorted(cov, key=lambda x: x[1])[:5]}
        res["safe_issues"] = safe[:40]; res["safe_issue_count"] = len(safe)
        res["scenes"] = rep.get("scenes")
    sheet(src, dur, float(arg("--every", "2")), dead, os.path.join(out_dir, base + "_qc_sheet.jpg"), wide=W > H)
    json.dump(res, open(os.path.join(out_dir, base + "_qc.json"), "w"), indent=1)
    m = res["motion"]
    print(f"QC {base}: {dur:.1f} s | motion median {m['median']} p10 {m['p10']} | still {m['still_share']*100:.0f} % | "
          f"dead runs (> {dead_len} s): {dead or 'none'}")
    if "coverage" in res:
        c = res["coverage"]
        print(f"   coverage mean {c['mean']*100:.0f} % min {c['min']*100:.0f} % (under 40 %: {c['under_40']*100:.0f} % of samples) | "
              f"safe-zone issues: {res['safe_issue_count']}")
        for s in res["safe_issues"][:8]:
            print("   ", s)
    if "circles" in res:
        c = res["circles"]
        print(f"   circles: {c['frames']} frames checked, worst {c['worst'][0]*100:.2f} % at {c['worst'][1]} s ({c['worst'][2]}) -> "
              + (f"FAIL on {c['fail_frames']} frames (> 2 %)" if c["fail_frames"] else "PASS"))
    print("   sheet:", os.path.join(out_dir, base + "_qc_sheet.jpg"))
    fail = bool(res.get("circles", {}).get("fail_frames"))
    if vj:
        import variety
        here = os.getcwd(); os.chdir(os.path.dirname(os.path.abspath(vj)))
        try:
            vr, _ = variety.check(os.path.basename(vj), arg("--name"), arg("--account"), skip=[x for x in (arg("--replaces") or "").split("|") if x])
        finally:
            os.chdir(here)
        res["variety"] = vr; json.dump(res, open(os.path.join(out_dir, base + "_qc.json"), "w"), indent=1)
        fail = fail or not vr["pass"]
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
