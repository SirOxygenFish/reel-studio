"""Noto Emoji (Apache 2.0) SVG -> transparent 512 px PNG, rendered with resvg, cached in <data>/env/stickers.
    reel-tool emoji name [name ...]        make PNGs
    reel-tool emoji --find word            search names (e.g. leg, bone, droplet, money-bag)
Names are the Noto / iconify ones: light-bulb, money-with-wings, stopwatch, thumbs-up, ...
"""
import gzip, io, json, sys
from pathlib import Path

import common as C

SIZE = 512
OUT = C.ENVD / "stickers"
_N = None


def noto():
    global _N
    if _N is None:
        _N = json.load(gzip.open(C.MOTION / "assets" / "icons" / "noto.json.gz", "rt", encoding="utf-8"))
    return _N


def ensure(name) -> str:
    out = OUT / (name + ".png")
    if out.exists():
        return str(out)
    import resvg_py
    from PIL import Image
    d = noto(); icons, aliases = d["icons"], d.get("aliases", {})
    key = name if name in icons else aliases.get(name, {}).get("parent")
    if key not in icons:
        C.fail(f"no emoji named {name}: try reel-tool emoji --find {name.split('-')[0]}")
    ic = icons[key]; w, h = ic.get("width", d.get("width", 16)), ic.get("height", d.get("height", 16))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}">{ic["body"]}</svg>'
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=SIZE, height=SIZE))
    OUT.mkdir(parents=True, exist_ok=True)
    Image.open(io.BytesIO(png)).convert("RGBA").save(out)
    return str(out)


def main(argv):
    if argv and argv[0] == "--find":
        d = noto(); w = argv[1].lower()
        print(" ".join(sorted(n for n in list(d["icons"]) + list(d.get("aliases", {})) if w in n)[:80]) or "nothing found")
        return
    for n in argv:
        print(ensure(n))


if __name__ == "__main__":
    main(sys.argv[1:])
