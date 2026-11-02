"""reel-tool brand: brand profiles (several are allowed). /reel-brand is the wizard; this is the machine part.

  brand new --name "Acme" --primary "#2F6F73" [--secondary "#..."] [--accent "#..."] [--mode light|dark]
            [--font "Montserrat"] [--body-font "Plus Jakarta Sans"] [--font-file a.ttf] [--wordmark "acme"] [--logo logo.png]
            [--handle "@acme"] [--language en] [--devices "iPhone 15|Pixel 9"] [--avoid "purple"]
            [--sub-color "#FFFFFF"] [--sub-active "#FFF176"] [--sub-font "Segoe UI Black"] [--sub-outline 7] [--title-color "#FFF59D"]
            [--default]
  brand list | show <slug> | use <slug> | palette <slug>
  brand example [northwind|sunrise]     installs a generic example profile (templates/example_brands.json) to try the looks

From 1-3 colours it derives every engine token, checks every text/graphic pair against WCAG (normal text 4.5:1, large text and
graphics 3:1), nudges colours until they pass, guards hues to avoid, and draws a swatch sheet (palette.png).
Subtitles keep their own colours; on light themes a soft dark ellipse goes under the subtitle line, in animation frames only,
because a yellow fill on a light background has no contrast of its own (a full-width strip reads as a grey bar).
"""
import colorsys, json, re, shutil, subprocess, sys, urllib.request
from pathlib import Path

import common as C

sys.path.insert(0, str(C.MOTION / "tools"))
import palette as P

HUES = {"purple": (255, 335), "violet": (255, 300), "pink": (300, 345), "red": (345, 15), "orange": (15, 45), "yellow": (45, 70), "green": (70, 170), "teal": (170, 195), "blue": (195, 255)}
FONT_PKGS = {"Montserrat": "montserrat", "Plus Jakarta Sans": "plus-jakarta-sans", "Inter": "inter", "Poppins": "poppins", "Manrope": "manrope", "Nunito": "nunito",
             "Raleway": "raleway", "Roboto": "roboto", "Open Sans": "open-sans", "Lato": "lato", "Rubik": "rubik", "Oswald": "oswald", "Bebas Neue": "bebas-neue",
             "Playfair Display": "playfair-display", "Lora": "lora", "Merriweather": "merriweather", "DM Sans": "dm-sans", "Sora": "sora", "Outfit": "outfit", "Work Sans": "work-sans"}


def hls(h):
    r, g, b = (v / 255 for v in C.rgb(h))
    return colorsys.rgb_to_hls(r, g, b)


def hexof(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h % 1, max(0, min(1, l)), max(0, min(1, s)))
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def ramp(base, l, sat=None):
    h, _, s = hls(base)
    return hexof(h, l, s if sat is None else sat)


def fit(fg, bg, need, darker=True):
    """move fg's lightness until it reaches `need` against bg"""
    h, l, s = hls(fg); step = -0.01 if darker else 0.01
    for _ in range(100):
        c = hexof(h, l, s)
        if P.ratio(c, bg) >= need:
            return c
        l += step
    return hexof(h, l, s)


def rgba(h, a):
    r, g, b = C.rgb(h)
    return f"rgba({r},{g},{b},{a})"


def font_block(display, body, font_file=None):
    if font_file:
        fam = display
        return {"display": {"family": fam, "weight": 800}, "head": {"family": fam, "weight": 800}, "body": {"family": fam, "weight": 700},
                "files": {fam: {"pkg": "", "weights": [700], "ttf": {"700": str(font_file)}}}}
    files = {}
    for fam in {display, body}:
        files[fam] = {"pkg": "@fontsource/" + FONT_PKGS.get(fam, fam.lower().replace(" ", "-")), "prefix": FONT_PKGS.get(fam, fam.lower().replace(" ", "-")), "weights": [600, 700, 800]}
    return {"display": {"family": display, "weight": 800}, "head": {"family": display, "weight": 800}, "body": {"family": body, "weight": 700}, "files": files}


def build(a) -> dict:
    prim, mode = a["primary"], a.get("mode", "light")
    h, l, s = hls(prim)
    sec = a.get("secondary"); acc = a.get("accent")
    if not acc:                                                # the complement, muted, moved off any avoided hue
        for off in (150, 210, 120, 240, 90, 270):
            cand = (h * 360 + off) % 360
            if not in_avoid(cand, a.get("avoid")):
                break
        acc = hexof(cand / 360, 0.40 if mode == "light" else 0.68, min(0.45, max(0.25, s * 0.8)))
    if mode == "light":
        bg, bg2 = ramp(prim, 0.925, min(s, 0.42)), ramp(prim, 0.975, min(s, 0.5))
        ink, muted = ramp(prim, 0.12, min(s, 0.42)), ramp(prim, 0.30, min(s, 0.34))
        paper = ramp(prim, 0.992, 0.7)
        c1 = fit(prim, paper, 3.2); on = ramp(prim, 0.985, 0.6)
        c1 = fit(c1, on, 3.2)
        c2 = fit(sec or ramp(prim, 0.30, s), bg, 4.5)
        acc = fit(acc, on, 4.5)
        good, bad = fit("#3E8A4A", on, 4.0), fit("#B5452F", on, 4.0)
        disc_a, disc_b = fit(ramp(c1, min(0.62, hls(c1)[1] + 0.12)), on, 3.1), ramp(c1, hls(c1)[1] - 0.08)
        C_ = {"bgDeep": ramp(prim, 0.84, min(s, 0.4)), "c1": c1, "c1l": ramp(prim, 0.72, min(s, 0.5)), "c1x": ramp(prim, 0.895, min(s, 0.5)), "c2": c2, "acc": acc, "acc2": ramp(acc, 0.60),
              "acc-soft": ramp(acc, 0.88, min(0.4, hls(acc)[2])), "ink": ink, "paper": paper, "surface": rgba(paper, .78), "text": ink, "muted": muted, "good": good, "bad": bad,
              "line": rgba(ink, .20), "on-acc": on, "on-c1": on, "on-c2": on, "on-good": on, "on-bad": on, "on-disc": on, "hero-ic": on, "hl": ink, "mark-bg": acc, "mark-ink": on,
              "title-c": ink, "title-2": c2, "mark": c2, "disc-a": disc_a, "disc-b": disc_b, "chat-bg": ramp(prim, 0.955, 0.4), "phone": ink, "msg-them": "#FFFFFF", "head2": c2,
              "dim": ramp(prim, 0.70, min(s, 0.4)), "bar": c1, "struct": c2, "outline": c2, "orb1": ramp(prim, 0.78, min(s, 0.55)), "orb2": ramp(prim, 0.92, 0.5),
              "orb3": ramp(acc, 0.88, min(0.4, hls(acc)[2])), "orb-op": "0.55", "sweep": "rgba(255,255,255,.45)", "grid-dot": rgba(ink, .30), "vig": rgba(c2, .16),
              "hard-shadow": rgba(ink, .16), "wipe-a": c2, "wipe-b": acc, "wipe-c": ramp(c1, 0.6), "peep-line": ink, "peep-skin": "#F2CBA6", "peep-top": ramp(acc, 0.88), "peep-hair": ramp(prim, 0.2, 0.3),
              "substrip": f"radial-gradient(ellipse 78% 36% at 50% 52%, {rgba(ink, .46)} 0%, {rgba(ink, .30)} 42%, {rgba(ink, 0)} 76%)"}
        bgs = [{"a": bg, "b": bg2}, {"a": ramp(prim, 0.905, min(s, 0.42)), "b": ramp(prim, 0.96, 0.5)}, {"a": ramp(prim, 0.915, min(s, 0.36)), "b": ramp(prim, 0.97, 0.45)},
               {"a": ramp(acc, 0.92, min(0.3, hls(acc)[2])), "b": ramp(acc, 0.97, 0.3)}, {"a": ink, "b": ramp(prim, 0.22, min(s, 0.4)), "alt": True}]
        alt_t, alt_m = ramp(prim, 0.93, 0.5), ramp(prim, 0.78, 0.4)
        alt = {"text": alt_t, "muted": alt_m, "hl": alt_t, "line": rgba(alt_t, .24), "grid-dot": rgba(alt_t, .3)}
        parts = [rgba(c1, .35), rgba(acc, .3)]
    else:
        ink = ramp(prim, 0.10, min(s, 0.55)); bg, bg2 = ink, ramp(prim, 0.20, min(s, 0.5)); text = "#FFFFFF"
        paper = ramp(prim, 0.97, 0.5)
        c1 = fit(ramp(prim, max(l, 0.55)), bg, 4.0, darker=False)
        acc = fit(acc, bg, 4.5, darker=False)
        c2 = fit(sec or ramp(prim, 0.45), bg, 3.0, darker=False)
        muted = ramp(prim, 0.85, 0.35); on_d = ink
        C_ = {"bgDeep": ramp(prim, 0.06, min(s, 0.6)), "c1": c1, "c1l": ramp(c1, 0.72), "c1x": ramp(c1, 0.88), "c2": c2, "acc": acc, "acc-soft": ramp(acc, 0.86), "acc2": ramp(acc, 0.76), "ink": ink, "paper": paper,
              "surface": "rgba(255,255,255,.08)", "text": text, "muted": muted, "good": fit("#A7F3D0", bg, 4.5, False), "bad": fit("#FF8A70", bg, 4.5, False), "line": rgba(c1, .25), "on-acc": on_d,
              "on-c1": on_d, "on-c2": "#FFFFFF", "on-good": on_d, "on-bad": on_d, "on-disc": "#FFFFFF", "hero-ic": acc, "hl": acc, "mark-bg": acc, "mark-ink": on_d, "title-c": "#FFFFFF", "title-2": "#FFFFFF",
              "mark": muted, "disc-a": ramp(c1, 0.55), "disc-b": ramp(c1, 0.30), "chat-bg": ramp(prim, 0.94, 0.4), "phone": ramp(prim, 0.08, 0.5), "msg-them": "#FFFFFF", "head2": ramp(c1, 0.88),
              "dim": ramp(c1, 0.85), "bar": ramp(c1, 0.72), "struct": ramp(c1, 0.88), "outline": "#FFFFFF", "orb1": c1, "orb2": c2, "orb3": ramp(c1, 0.72), "orb-op": "0.42", "sweep": "rgba(255,255,255,.10)",
              "grid-dot": "rgba(255,255,255,.55)", "vig": "rgba(0,0,0,.45)", "hard-shadow": "rgba(0,0,0,.25)", "wipe-a": c2, "wipe-b": acc, "wipe-c": c1, "peep-line": ink, "peep-skin": "#E9B98F", "peep-top": ramp(c1, 0.8),
              "peep-hair": "#2B2B2B"}
        bgs = [[bg, bg2], [ramp(prim, 0.08, min(s, 0.55)), ramp(prim, 0.24, min(s, 0.5))], [ramp(prim, 0.095, min(s, 0.55)), ramp(prim, 0.22, min(s, 0.5))], [ramp(prim, 0.11, min(s, 0.5)), ramp(prim, 0.26, min(s, 0.45))]]
        alt = None; parts = [rgba(c1, .5), rgba(acc, .55)]
    th = {"name": a["slug"], "label": a["name"], "about": a.get("about", ""), "wordmark": a.get("wordmark", ""), "colors": C_, "bgs": bgs,
          "fonts": font_block(a.get("font") or "Montserrat", a.get("body_font") or a.get("font") or "Plus Jakarta Sans", a.get("font_file")),
          "radius": {"s": 16, "m": 28, "l": 48}, "shadow": "0 30px 60px " + rgba(ink, .22 if mode == "light" else .45), "grid": 0.18, "title": {"fs": 96, "top": 214},
          "particles": {"count": 22, "colors": parts}, "motion": {"enter": 0.46, "overshoot": 1.5, "letter": 0.02, "stagger": 0.1, "trans": 0.4, "lead": 0.12, "camZ": 1.07, "idleAmp": 1.15},
          "transitions": ["push", "zoom", "rise", "iris"],
          "swatches": [["Background", "background", bg if mode == "light" else bg], ["Glow", "background glow", bg2], ["Primary", "discs, buttons", c1], ["Secondary", "structure, wordmark", c2], ["Accent", "the one accent", acc],
                       ["Accent soft", "soft fills", C_["acc-soft"]], ["Ink", "text, outlines", ink], ["Muted", "secondary text", muted], ["Paper", "cards", paper], ["Positive", "good", C_["good"]], ["Negative", "bad", C_["bad"]]]}
    if alt:
        th["alt"] = alt
    return th


def in_avoid(hue, avoid):
    for nm in re.split(r"[,| ]+", (avoid or "").lower()):
        if nm in HUES:
            a, b = HUES[nm]
            if (a <= hue <= b) if a < b else (hue >= a or hue <= b):
                return True
    return False


def check(th, avoid=None) -> tuple:
    c = dict(th["colors"]); b0 = th["bgs"][0]; c["bg"] = b0["a"] if isinstance(b0, dict) else b0[0]
    al = next((b for b in th["bgs"] if isinstance(b, dict) and b.get("alt")), None)
    if al:
        c["alt-bg"] = al["a"]; c["alt-text"] = th.get("alt", {}).get("text", "#ffffff")
    rows = []
    for fg, bgk, need, what in P.PAIRS:
        if fg in c and bgk in c and str(c[fg]).startswith("#") and str(c[bgk]).startswith("#"):
            r = P.ratio(c[fg], c[bgk]); rows.append((fg, bgk, round(r, 2), need, what, r >= need))
    bad_hues = []
    for hx in sorted(set(re.findall(r"#[0-9A-Fa-f]{6}", json.dumps(th)))):
        hh, ll, ss = hls(hx)
        if ss > 0.15 and 0.08 < ll < 0.95 and in_avoid(hh * 360, avoid):
            bad_hues.append(hx)
    return rows, bad_hues


def font_ready(fam):
    pkg = FONT_PKGS.get(fam, fam.lower().replace(" ", "-"))
    d = C.ENVD / "fonts" / "node_modules" / "@fontsource" / pkg
    if d.exists():
        return True
    import setup_env
    setup_env.fontsource(pkg)
    return d.exists()


def new(args):
    a = dict(args); a["slug"] = C.slugify(a["name"]); slug = a["slug"]
    if "primary" not in a:
        C.fail("--primary is required")
    d = C.BRANDS / slug; d.mkdir(parents=True, exist_ok=True)
    if a.get("logo"):
        dst = d / ("logo" + Path(a["logo"]).suffix.lower()); shutil.copy(a["logo"], dst); a["logo"] = str(dst)
    if a.get("font_file"):
        dst = d / Path(a["font_file"]).name; shutil.copy(a["font_file"], dst); a["font_file"] = str(dst)
    elif not a.get("skip_fonts"):
        for fam in {a.get("font"), a.get("body_font")} - {None}:
            font_ready(fam)
    th = build(a)
    rows, hues = check(th, a.get("avoid"))
    C.save_json(d / "theme.json", th)
    subs = {}
    for k, key in (("sub_color", "color"), ("sub_active", "active_color"), ("sub_font", "font"), ("title_color", "title_color")):
        if a.get(k):
            subs[key] = a[k]
    if a.get("sub_outline"):
        subs["outline"] = int(a["sub_outline"])
    B = {"slug": slug, "name": a["name"], "wordmark": a.get("wordmark", ""), "handle": a.get("handle", ""), "logo": a.get("logo"), "language": a.get("language"), "subs": subs,
         "match": {"languages": [x for x in (a.get("language") or "").split("|") if x], "devices": [x for x in (a.get("devices") or "").split("|") if x]},
         "colors_in": {k: a.get(k) for k in ("primary", "secondary", "accent", "mode")}, "avoid": a.get("avoid")}
    C.save_json(d / "brand.json", B)
    cfg = C.load_json(C.CONFIG_FILE, {}) or {}
    if a.get("default") or not cfg.get("default_brand") or cfg.get("default_brand") == "default":
        cfg["default_brand"] = slug; C.save_json(C.CONFIG_FILE, cfg)
    sw(d, th)
    fails = [r for r in rows if not r[5]]
    for r in rows:
        print(f"{'PASS' if r[5] else 'FAIL'} {r[2]:5.2f}:1 (need {r[3]})  {r[0]} on {r[1]} - {r[4]}")
    print("avoided hues found:", hues or "none")
    print(f"brand {slug}: {len(rows) - len(fails)}/{len(rows)} contrast pairs pass; palette sheet: {d / 'palette.png'}")
    if fails or hues:
        sys.exit(1)


def sw(d, th):
    sys.argv = ["palette", str(d / "theme.json"), str(d / "palette.png")]
    P.main()


def main(argv):
    if not argv or argv[0] == "list":
        cfg = C.config()
        for s in C.brand_list():
            print(("* " if s == cfg.get("default_brand") else "  ") + s, json.dumps((C.load_json(C.BRANDS / s / "brand.json") or {}).get("match"), ensure_ascii=False))
        print("(* = default)" if C.brand_list() else "no brands yet: the neutral default look is used")
        return
    cmd = argv[0]
    if cmd == "new":
        o, i = {}, 1
        while i < len(argv):
            k = argv[i].lstrip("-").replace("-", "_")
            if k in ("default", "skip_fonts"):
                o[k] = True; i += 1
            else:
                o[k] = argv[i + 1]; i += 2
        new(o)
    elif cmd == "example":
        ex = C.load_json(C.ROOT / "templates" / "example_brands.json")
        if len(argv) < 2 or argv[1] not in ex:
            for k, v in ex.items():
                print(f"  {k:10} {v['about']}")
            print("reel-tool brand example <name> installs one"); return
        new({k: v for k, v in ex[argv[1]].items() if k != "about"})
    elif cmd == "show":
        print(json.dumps(C.brand(argv[1]), ensure_ascii=False, indent=1))
    elif cmd == "use":
        cfg = C.load_json(C.CONFIG_FILE, {}) or {}; cfg["default_brand"] = argv[1]; C.save_json(C.CONFIG_FILE, cfg); print("default brand:", argv[1])
    elif cmd == "palette":
        d = C.BRANDS / argv[1]; sw(d, C.load_json(d / "theme.json")); print(d / "palette.png")
    else:
        C.fail("brand new|example|list|show|use|palette")


if __name__ == "__main__":
    main(sys.argv[1:])
