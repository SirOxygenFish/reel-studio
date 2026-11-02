"""reel-tool preview <job> <segment> [--at t1,t2,...]: stills of one animation segment before the long render.
Default times: start + 0.6 s, then every 1.2 s. -> _motion/preview/sheet.jpg (a page error names the scene code line).
<segment> is the index in visuals.json hybrid.segments, or "story" for storyboard.json (faceless).
"""
import json, os, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import common as C

sys.path.insert(0, str(C.MOTION / "tools"))


def main(argv):
    job = C.job_dir(argv[0]).resolve(); os.chdir(job)
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    (job / "_motion").mkdir(exist_ok=True); J = C.job_sync(job)
    B = C.brand(J.get("brand"))
    if argv[1] == "story":
        board = job / "storyboard.json"; dur = C.load_json("words.json")["total"]; t0, t1 = 0, dur
        sb = board
        pdir = job / "preview"
    else:
        import hybrid
        V = C.load_json("visuals.json"); seg = V["hybrid"]["segments"][int(argv[1])]
        t0, t1 = seg["t0"], seg["t1"]
        sc = seg["scenes"]
        d = {"theme": seg.get("theme", V["hybrid"].get("theme", B["theme"])), "words": str(job / "words.json"), "size": [1080, 1920], "t0": t0, "t1": t1, "scenes": sc, "noMark": True}
        js = [os.path.abspath(p) for p in seg.get("extra_js", [])] + hybrid.library_js(sc)
        if js:
            d["extra_js"] = js
        sb = job / "_motion" / "prev.json"; C.save_json(sb, d)
        pdir = job / "_motion" / "preview"
    pdir.mkdir(exist_ok=True)
    for f in pdir.glob("*.png"):
        f.unlink()
    at = [float(x) for x in opt("--at").split(",")] if opt("--at") else [round(t0 + 0.6 + i * 1.2, 2) for i in range(int((t1 - t0 - 0.6) / 1.2) + 1)]
    r = subprocess.run([C.node(), str(C.MOTION / "engine" / "render.mjs"), str(sb), "--preview", ",".join(str(t) for t in at)], env=C.run_env(),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout[-600:]);
    if r.returncode:
        C.fail("preview failed:\n" + r.stderr[-1500:])
    pics = sorted(pdir.glob("t_*.png"), key=lambda p: float(p.stem[2:]))
    cols = min(6, len(pics)); rows = (len(pics) + cols - 1) // cols; w, h = 270, 480
    S_ = Image.new("RGB", (cols * w, rows * h), "white"); D = ImageDraw.Draw(S_); f = ImageFont.truetype(C.sub_font()[1], 20)
    for i, p in enumerate(pics):
        im = Image.open(p).convert("RGB").resize((w - 2, h - 2)); x, y = i % cols * w, i // cols * h
        S_.paste(im, (x + 1, y + 1)); D.text((x + 6, y + 4), p.stem[2:], fill=(220, 0, 0), font=f)
    S_.save(pdir / "sheet.jpg", quality=88)
    print(pdir / "sheet.jpg")


if __name__ == "__main__":
    main(sys.argv[1:])
