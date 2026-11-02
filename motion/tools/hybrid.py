"""Hybrid Reels: motion-graphics segments rendered by the ReelsMotion engine.

visuals.py calls clips(...) once; each segment becomes a transparent clip (ffv1 bgra) made by engine/render.mjs and is
served frame by frame as RGBA (frame(t)). In the full layout the clip opens with an iris from the speaker's face and closes
with a zoom/blur into it; visuals.py alpha-composites it over the face video, so the transitions are real, not cuts.

visuals.json:
  "hybrid": {"layout": "full"|"split", "theme": "<brand slug>",
             "segments": [{"t0": 9.62, "t1": 17.55, "scenes": [<engine scenes>], "extra_js": []}, ...]}
Scene types that are not stock (engine/scenes.js) are bespoke scenes: <data>/library/<type>.js (this user's) or the plugin's
seed motion/library/<type>.js; they are loaded with library/_kit.js automatically.
Clips are cached in _motion/ by a hash of the storyboard and the engine files: re-rendering after a subtitle or cut-only
change costs nothing.
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import common as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER = os.path.join(ROOT, "engine", "render.mjs")
FF = C.FF
FPS = 30


def library_js(scenes):
    """bespoke scenes used by these scenes, plus the kit they share; stock scenes need nothing"""
    stock = open(os.path.join(ROOT, "engine", "scenes.js"), encoding="utf-8").read()
    libs = [str(p) for p in C.libraries()]
    out = []
    for sc in scenes:
        ty = sc.get("type", "")
        if f"def('{ty}'" in stock:
            continue
        f = next((os.path.join(d, ty + ".js") for d in libs if os.path.exists(os.path.join(d, ty + ".js"))), None)
        if not f:
            raise FileNotFoundError(f"scene type '{ty}' is neither stock nor in {libs}")
        if f not in out:
            out.append(f)
    return ([os.path.join(libs[-1], "_kit.js")] + out) if out else []


class EngineClip:
    def __init__(self, seg, h, W=1080, theme="default", words="words.json", face=None, workdir="_motion", idx=0, alpha_edges=True):
        self.t0, self.t1, self.W, self.h, self.s = seg["t0"], seg["t1"], W, h, seg
        os.makedirs(workdir, exist_ok=True)
        scenes = seg["scenes"]
        sb = {"theme": seg.get("theme", theme), "words": os.path.abspath(words), "size": [W, h], "t0": self.t0, "t1": self.t1,
              "scenes": scenes, "noMark": True}
        js = [os.path.abspath(p) for p in seg.get("extra_js", [])] + library_js(scenes)
        if js:
            sb["extra_js"] = js
        if seg.get("placeholders"):
            sb["placeholders"] = True
        if seg.get("box"):
            sb["box"] = seg["box"]
        if alpha_edges and h > 1500:
            sb["alpha"] = {"in": {"focus": [round(face[0]), round(face[1])]} if face else {}, "out": True}
        eng = "".join(open(os.path.join(ROOT, "engine", f), encoding="utf-8").read() for f in ("runtime.js", "scenes.js", "base.css", "render.mjs"))
        eng += "".join(open(p, encoding="utf-8").read() for p in sb.get("extra_js", []))     # bespoke code is part of the cache key
        key = hashlib.sha1((json.dumps(sb, sort_keys=True) + eng).encode()).hexdigest()[:12]
        base = os.path.join(workdir, f"seg{idx}_{key}")
        self.path = base + ".mkv"
        if not os.path.exists(self.path):
            json.dump(sb, open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"motion: rendering segment {idx} ({self.t0:.2f}-{self.t1:.2f}) ...", flush=True)
            subprocess.run([C.node(), RENDER, base + ".json", "--out", self.path, "--alpha", "--workers", "4", "--report", base + ".report.json"], check=True, env=C.run_env())
        self.report = base + ".report.json"                    # layout + per-frame circle check (qc.py --report)
        self.proc, self.i, self.cur = None, -1, np.zeros((h, W, 4), np.uint8)

    def frame(self, t):
        """RGBA frame for reel time t (frames are requested in increasing order)"""
        want = int(round((t - self.t0) * FPS))
        if self.proc is None:
            self.proc = subprocess.Popen([FF, "-v", "error", "-i", self.path, "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
        n = self.W * self.h * 4
        while self.i < want:
            buf = self.proc.stdout.read(n)
            if len(buf) < n:
                break
            self.cur = np.frombuffer(buf, np.uint8).reshape(self.h, self.W, 4); self.i += 1
        return self.cur


def clips(hy, h, W=1080, words="words.json", face=None, theme=None):
    th = theme or hy.get("theme", "default")
    cl = [EngineClip(sg, h, W, th, words, face, idx=i, alpha_edges=hy.get("layout", "full") == "full") for i, sg in enumerate(hy["segments"])]
    # the clips of THIS render (qc.py --visuals / variety.py read it, so stale clips of earlier renders are never checked)
    json.dump([{"t0": c.t0, "t1": c.t1, "clip": os.path.abspath(c.path), "report": os.path.abspath(c.report)} for c in cl],
              open(os.path.join("_motion", "current.json"), "w"), indent=1)
    return cl


def over(base_rgb, rgba):
    """alpha-composite an RGBA engine frame over an RGB frame of the same size"""
    a = rgba[:, :, 3:4].astype(np.float32) / 255.0
    if a.min() >= 0.999:
        return np.ascontiguousarray(rgba[:, :, :3])
    return (base_rgb.astype(np.float32) * (1 - a) + rgba[:, :, :3].astype(np.float32) * a).astype(np.uint8)
