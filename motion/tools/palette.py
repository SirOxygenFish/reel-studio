"""Theme palette check + swatch sheet.
    python palette.py <theme.json> [out.png]
Prints WCAG 2.x contrast for every pair that carries text or graphics and renders a swatch image.
Normal text needs >= 4.5:1, large text (>= 24 px, or bold >= 18.7 px; everything in our Reels is far larger) >= 3:1,
UI graphics/icons >= 3:1.
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont


def rgb(h):
    h = h.strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# (foreground token, background token, need, what it is)
PAIRS = [("text", "bg", 4.5, "body text on the background"), ("muted", "bg", 4.5, "secondary text on the background"),
         ("hl", "bg", 3.0, "big headline words on the background"), ("ink", "paper", 4.5, "text on cards"),
         ("on-acc", "acc", 3.0, "tag / button text on the accent (large, bold)"), ("acc", "bg", 3.0, "accent graphics on the background"),
         ("acc", "paper", 3.0, "accent icons on cards"), ("c1", "paper", 3.0, "primary icons on cards"), ("on-c1", "c1", 3.0, "button text on the primary"),
         ("on-disc", "disc-b", 3.0, "icons on the disc (dark end)"), ("on-disc", "disc-a", 3.0, "icons on the disc (light end)"),
         ("mark-ink", "mark-bg", 3.0, "highlighted word on the marker"), ("on-good", "good", 3.0, "check on positive badge"),
         ("on-bad", "bad", 3.0, "cross on negative badge"), ("title-c", "bg", 3.0, "title line 1"), ("title-2", "bg", 3.0, "title line 2"),
         ("alt-text", "alt-bg", 4.5, "text on the dark (alt) scene"), ("ink", "chat-bg", 4.5, "chat message text"),
         ("mark", "bg", 3.0, "wordmark on the background")]


def main():
    th = json.load(open(sys.argv[1], encoding="utf-8")); C = dict(th["colors"])
    bg0 = th["bgs"][0]; C["bg"] = bg0["a"] if isinstance(bg0, dict) else bg0[0]
    alt = next((b for b in th["bgs"] if isinstance(b, dict) and b.get("alt")), None)
    if alt:
        C["alt-bg"] = alt["a"]; C["alt-text"] = th.get("alt", {}).get("text", "#ffffff")
    rows = []
    for fg, bgk, need, what in PAIRS:
        if fg in C and bgk in C and C[fg].startswith("#") and C[bgk].startswith("#"):
            r = ratio(C[fg], C[bgk]); rows.append((fg, bgk, r, need, what))
            print(f"{'PASS' if r >= need else 'FAIL'}  {r:5.2f}:1 (need {need})  {fg} {C[fg]} on {bgk} {C[bgk]}  - {what}")
    # hue guard: no violet/purple anywhere in the theme (hue 255-335 deg with real saturation)
    import colorsys, re
    hexes = set(re.findall(r"#[0-9A-Fa-f]{6}", json.dumps(th))) | {"#%02x%02x%02x" % tuple(int(v) for v in m)
                                                                  for m in re.findall(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", json.dumps(th))}
    purple = []
    for h in sorted(hexes):
        r_, g_, b_ = (v / 255 for v in rgb(h)); hh, ll, ss = colorsys.rgb_to_hls(r_, g_, b_)
        if 255 <= hh * 360 <= 335 and ss > 0.15 and 0.08 < ll < 0.95:
            purple.append(h)
    print("purple/violet colours:", purple or "none")
    if len(sys.argv) < 3:
        return
    sw = th.get("swatches") or []
    W = 1600; H = 260 + 150 * ((len(sw) + 4) // 5) + 46 * len(rows) + 60
    im = Image.new("RGB", (W, H), rgb(C["bg"])); d = ImageDraw.Draw(im)
    import sys as _s, pathlib as _p
    _s.path.insert(0, str(_p.Path(__file__).resolve().parents[2] / "scripts")); import common as _C
    F = lambda s, b=True: ImageFont.truetype(_C.sub_font()[1], s)
    d.text((60, 50), th.get("label", th["name"]), fill=rgb(C["text"]), font=F(64))
    d.text((60, 140), th.get("about", ""), fill=rgb(C["muted"]), font=F(30, False))
    y = 220
    for i, (name, role, hexv) in enumerate(sw):
        x = 60 + (i % 5) * 300; yy = y + (i // 5) * 150
        d.rounded_rectangle((x, yy, x + 270, yy + 90), radius=22, fill=rgb(hexv), outline=rgb(C["line"]) if C["line"].startswith("#") else None)
        ink = (255, 255, 255) if lum(hexv) < 0.3 else (20, 24, 31)      # label readable on the swatch itself, in light and dark themes
        d.text((x + 16, yy + 12), name, fill=ink, font=F(28))
        d.text((x + 16, yy + 50), hexv.upper(), fill=ink, font=F(24, False))
        d.text((x, yy + 98), role, fill=rgb(C["muted"]), font=F(22, False))
    y += 150 * ((len(sw) + 4) // 5) + 30
    d.text((60, y), "WCAG contrast (normal text 4.5:1, large text and graphics 3:1)", fill=rgb(C["text"]), font=F(30)); y += 50
    for fg, bgk, r, need, what in rows:
        d.rounded_rectangle((60, y, 330, y + 38), radius=10, fill=rgb(C[bgk]))
        d.text((76, y + 2), "Aa  Text", fill=rgb(C[fg]), font=F(26))
        d.text((350, y + 4), f"{r:4.1f}:1  {'PASS' if r >= need else 'FAIL'}   {fg} on {bgk} - {what}", fill=rgb(C["text"]), font=F(24, False))
        y += 46
    im.save(sys.argv[2])
    print("swatch ->", sys.argv[2])


if __name__ == "__main__":
    main()
