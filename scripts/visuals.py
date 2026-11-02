"""Visual layer for talking-head Reels: "retention editing".

Called by render.py when visuals.json exists:  python visuals.py <_base.mkv> visuals.json subs.ass <_draft.mkv>
_base.mkv = the cut (video + raw voice, no subtitles). Output = zooms + stickers + text pops + cutaways, then the subtitles
burned on top; voice copied raw (the voice chain runs afterwards, once). Also writes <_draft>_sfx.json for sfx.py.

visuals.json (v2):
{ "title_end": 7.0,
  "keywords": ["without", "JOINTS"],                    # subtitle underline (make_ass.py, exact text)
  (zoom is automatic: a slow eased push-in/pull-out, 3.5 % over 6 s; face cuts get a 4-frame soft blend, see cut_frames)
  "beats": [
    {"t": 1.34, "items": [{"emoji": "leg", "size": 320}, {"label": "JOINTS"}], "arrow": true},   # combo, staggered 0.12 s
    {"t": 3.42, "pop": "SURGERY?"},                       # big keyword text pop (0.9 s), lemon; "color": "white"
    {"t": 7.6, "items": [{"emoji": "light-bulb"}], "enter": "slide"},          # enter: pop | slide (default: random 30% slide)
    {"t": 24.0, "items": [{"sign": "≠", "size": 260}, {"label": "NOT A REPLACEMENT"}]} ],
    # beat options: "d" (default 1.6 s; pops 0.9 s), "arrow": true (points at the speaker), "zone": force one of ZONES
  "cutaways": [                                           # full-screen code-drawn cards, 1-2.5 s, the voice keeps playing
    {"t": 10.4, "d": 2.0, "type": "chart", "title": "HYALURONIC ACID", "xlabel": "AGE", "trend": "down"},
    {"t": 23.9, "d": 2.0, "type": "list", "items": [["red-question-mark", "ASK QUESTIONS", 0.0], ["clipboard", "YOUR OPTIONS", 1.3]]},
    {"t": 4.4, "d": 1.9, "type": "vs", "left": ["syringe", "INJECTION"], "right": ["glass-of-milk", "DRINK"]},
    {"t": 28.3, "d": 3.0, "type": "flow", "rows": [["TREATMENT", "MY DOCTOR", "health-worker", 0.0], ["DAILY HABITS", "ME", "person-raising-hand", 1.9]]},
    {"t": 9.0, "d": 1.8, "type": "stat", "big": "12", "caption": "WEEKS", "emoji": "spiral-calendar"} ],
  "sfx": true }
No-go zones: the face/eyes (YuNet box + margin, grown during zooms), the subtitle line, the title while it shows. Everything
else (shoulders, chest, hands, edges, lower third, beside/above the head) is allowed. Zones rotate; never the same twice in a row.
"""
import json, math, os, random, re, subprocess, sys
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")

import common as C

FF = C.FF
PNG = str(C.ENVD / "stickers")
YUNET = str(C.ENVD / "models" / "face_detection_yunet_2023mar.onnx")   # OpenCV zoo, MIT
B = C.brand((C.load_json("job.json", {}) or {}).get("brand"))
SUBS = B["subs"]
FONT = C.sub_font(SUBS)[1]
SYMBOL_FONT = C.symbol_font()
W, H, FPS = 1080, 1920, 30
SUB_BAND = (1255, 1585)            # subtitle line (MarginV 470) - never covered
SPLIT_TOP = 1152                   # hybrid split layout: scene panel height (60 %); face panel below (40 %)
TITLE_BOTTOM = 470                 # title block while t < title_end
LEMON, INK, WHITE, RED = C.rgb(SUBS["sticker_color"]), C.rgb(SUBS["sticker_ink"]), (255, 255, 255), (229, 57, 53)
ZONES = {                          # rectangles for sticker CENTRES
    "UL": (40, 150, 380, 720), "UR": (700, 150, 1040, 720),
    "ML": (40, 720, 380, 1250), "MR": (700, 720, 1040, 1250),
    "LO": (120, 1600, 960, 1880), "TOP": (200, 130, 880, 430)}
RNG = random.Random(7)
ZOOM_AMP, ZOOM_PERIOD = 0.035, 12.0      # no scale jumps, kicks or shakes on the face: one slow eased push-in and pull-out


def cut_frames(src):
    """exact first frame of every piece after the first: nominal time from cuts.json, then the biggest picture change within 4 frames of it"""
    if not os.path.exists("cuts.json"):
        return []
    cl = json.load(open("cuts.json", encoding="utf-8")); t_ = np.cumsum([b_ - a_ for _, a_, b_ in cl])[:-1]
    r_ = subprocess.run([FF, "-v", "error", "-i", src, "-vf", "scale=135:240,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    g_ = np.frombuffer(r_, np.uint8).reshape(-1, 240, 135).astype(np.float32); d_ = np.r_[0, np.abs(g_[1:] - g_[:-1]).mean((1, 2))]
    out_ = []
    for x in t_:
        n0 = round(x * FPS); lo = max(1, n0 - 4); out_.append(lo + int(np.argmax(d_[lo:n0 + 5])))
    return out_


def soft_cut(fr, n, cuts_):
    """4-frame cross-dissolve on a cut, made from the frames around it: the timeline does not change"""
    for c_ in cuts_:
        o = n - c_
        if -2 <= o <= 1 and c_ - 1 in fr and c_ in fr:
            w_ = {-2: .2, -1: .4, 0: .6, 1: .8}[o]
            return cv2.addWeighted(fr[n] if o < 0 else fr[c_ - 1], 1 - w_, fr[c_] if o < 1 else fr[n], w_, 0)
    return fr[n]
SCALES = (1.0, 0.86, 0.74, 0.64)
MIN_HOLD = 0.8                     # seconds: shorter text pops and stickers read as a flash


# ---------- art (RGBA numpy arrays with a shadow pad) ----------
def finish(img, outline=10, shadow=0.35):
    """white sticker outline + soft shadow"""
    pad = outline + 18
    a = np.pad(np.array(img)[:, :, 3], pad); base = np.pad(np.array(img), ((pad, pad), (pad, pad), (0, 0)))
    ring = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * outline + 1, 2 * outline + 1))) if outline else a
    sh = np.roll(cv2.GaussianBlur(ring.astype(np.float32), (0, 0), 9) * shadow, 8, axis=0)
    out = np.zeros(base.shape, np.float32); out[:, :, 3] = sh
    wa = ring.astype(np.float32) / 255
    out[:, :, :3] = out[:, :, :3] * (1 - wa[..., None]) + 255 * wa[..., None]
    out[:, :, 3] = np.maximum(out[:, :, 3], ring)
    ia = base[:, :, 3:4].astype(np.float32) / 255
    out[:, :, :3] = out[:, :, :3] * (1 - ia) + base[:, :, :3] * ia
    return out.clip(0, 255).astype(np.uint8)


def emoji(name, size, badge=None):
    import emoji_png
    im = Image.open(emoji_png.ensure(name)).convert("RGBA").resize((size, size), Image.LANCZOS)
    if badge == "x":                                          # small red ✕ in a white disc = "not / without"
        r = int(size * 0.22); d = ImageDraw.Draw(im); cx, cy = size - r - 2, size - r - 2
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE + (255,), outline=RED, width=max(4, r // 5))
        q = int(r * 0.5)
        for a, b in (((cx - q, cy - q), (cx + q, cy + q)), ((cx - q, cy + q), (cx + q, cy - q))):
            d.line((a, b), fill=RED, width=max(6, r // 3))
    return finish(im)


def sign(symbol, size=220):
    """bold symbol (≠ + = % ? ✓ VS) in a lemon disc"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size - 1, size - 1), fill=LEMON + (255,))
    fnt = ImageFont.truetype(FONT if all(ord(c) < 0x2000 for c in symbol) else SYMBOL_FONT, int(size * (0.62 if len(symbol) < 2 else 0.42)))
    bb = d.textbbox((0, 0), symbol, font=fnt)
    d.text(((size - (bb[2] - bb[0])) / 2 - bb[0], (size - (bb[3] - bb[1])) / 2 - bb[1]), symbol, font=fnt, fill=INK)
    return finish(im)


def label(text, fs=62):
    """bold word label: lemon pill, near-black Segoe UI Black, uppercase"""
    f = ImageFont.truetype(FONT, fs); text = text.upper(); tw = f.getlength(text)
    w, h = int(tw + fs * 0.9), int(fs * 1.45)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=LEMON + (255,))
    d.text(((w - tw) / 2, h * 0.12), text, font=f, fill=INK)
    return finish(im, outline=6)


def big_text(text, fs=170, color=LEMON):
    """keyword text pop: huge Segoe UI Black, lemon or white, thick black outline (title/subtitle style)"""
    f = ImageFont.truetype(FONT, fs); text = text.upper(); st = int(fs * 0.09)
    bb = ImageDraw.Draw(Image.new("RGBA", (8, 8))).textbbox((0, 0), text, font=f, stroke_width=st)
    im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), text, font=f, fill=color + (255,), stroke_width=st, stroke_fill=(0, 0, 0, 255))
    return finish(im, outline=0, shadow=0.55)


def arrow(length=190):
    """curved arrow pointing right (white, black outline); rotated toward the speaker at placement"""
    w, h = length, int(length * 0.55); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(int(w * 0.05 + w * 0.72 * u), int(h * 0.72 - math.sin(u * math.pi) * h * 0.38)) for u in np.linspace(0, 1, 24)]
    ex, ey = pts[-1]; tip = (int(w * 0.97), ey + 4)
    d.line(pts, fill=(0, 0, 0, 255), width=30, joint="curve"); d.polygon([tip, (ex - 14, ey - 40), (ex - 22, ey + 34)], fill=(0, 0, 0, 255))
    d.line(pts, fill=WHITE + (255,), width=18, joint="curve"); d.polygon([(tip[0] - 9, tip[1]), (ex - 9, ey - 29), (ex - 15, ey + 25)], fill=WHITE + (255,))
    return finish(im, outline=0, shadow=0.4)


def item_art(it):
    if "emoji" in it: return emoji(it["emoji"], int(it.get("size", 220)), it.get("badge"))
    if "sign" in it: return sign(it["sign"], int(it.get("size", 220)))
    if "label" in it: return label(it["label"], int(it.get("size", 62)))
    raise ValueError(it)


def fit_text(text, fs, maxw, color=WHITE):
    """text_plain shrunk until it is at most maxw px wide"""
    while fs > 36 and ImageFont.truetype(FONT, fs).getlength(text) > maxw:
        fs -= 4
    return text_plain(text, fs, color)


def text_plain(text, fs, color=WHITE):
    f = ImageFont.truetype(FONT, fs); bb = ImageDraw.Draw(Image.new("RGBA", (8, 8))).textbbox((0, 0), text, font=f)
    im = Image.new("RGBA", (bb[2] - bb[0] + 6, bb[3] - bb[1] + 6), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((3 - bb[0], 3 - bb[1]), text, font=f, fill=color + (255,)); return np.array(im)


# ---------- face track ----------
def face_track(src):
    det = cv2.FaceDetectorYN.create(YUNET, "", (540, 960), 0.7)
    raw = subprocess.run([FF, "-v", "error", "-i", src, "-vf", "fps=2,scale=540:960", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 960, 540, 3); track = []
    for i, g in enumerate(fr):
        _, fs = det.detect(np.ascontiguousarray(g))
        if fs is not None and len(fs):
            x, y, w, h = (max(fs, key=lambda b: b[2] * b[3])[:4] * 2).tolist()
            track.append((i / 2, (x - 0.06 * w, y - 0.12 * h, x + 1.06 * w, y + 1.06 * h)))   # face + eyes, brow..chin
    return track or [(0, (W * 0.3, H * 0.2, W * 0.7, H * 0.6))]


def face_box(track, t0, t1):
    bs = [b for t, b in track if t0 - 0.25 <= t <= t1] or [min(track, key=lambda tb: abs(tb[0] - t0))[1]]
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


def overlap(a, b, m=0):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])


def ease_back(u):
    u = min(max(u, 0), 1); c = 1.7; return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


def paste(frame, art, cx, cy, scale=1.0, rot=0.0, op=1.0):
    """alpha-blend an RGBA art centred at (cx, cy), scaled and rotated (degrees)"""
    if scale <= 0.02 or op <= 0.01:
        return
    h, w = art.shape[:2]; R = int(math.hypot(w, h) * scale / 2) + 2
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale); M[0, 2] += R - w / 2; M[1, 2] += R - h / 2
    a = cv2.warpAffine(art, M, (2 * R, 2 * R), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    x0, y0 = int(cx) - R, int(cy) - R; FH, FW = frame.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(FW, x0 + 2 * R), min(FH, y0 + 2 * R)
    if xb <= xa or yb <= ya:
        return
    sub = a[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32); al = sub[:, :, 3:4] / 255 * op
    frame[ya:yb, xa:xb] = (frame[ya:yb, xa:xb].astype(np.float32) * (1 - al) + sub[:, :, :3] * al).astype(np.uint8)


# ---------- cutaways: full-screen code-drawn cards (face-only format; hybrids use the motion engine) ----------
class Cutaway:
    def __init__(self, c):
        self.c, self.t, self.d, self.T = c, c["t"], c.get("d", 2.0), c["type"]
        bg = np.zeros((H, W, 3), np.float32); bg[:] = (24, 24, 27); bg += np.linspace(0, 14, H)[:, None, None]
        cv2.circle(bg, (W // 2, 760), 520, (44, 42, 34), -1); bg = cv2.GaussianBlur(bg, (0, 0), 120)
        self.bg = bg.clip(0, 255).astype(np.uint8); P = self.parts = []      # (start, art, x, y, motion)
        if self.T == "vs":
            (li, lt), (ri, rt) = c["left"], c["right"]
            P += [(0.05, emoji(li, 300), 290, 650, "pop"), (0.15, text_plain(lt.upper(), 88, LEMON), 290, 930, "up"),
                  (0.20, emoji(ri, 300), 790, 650, "pop"), (0.30, text_plain(rt.upper(), 88, WHITE), 790, 930, "up"),
                  (0.38, sign("VS", 170), W // 2, 650, "pop")]
        elif self.T == "list":
            if c.get("title"):
                P.append((0.0, text_plain(c["title"].upper(), 70, LEMON), W // 2, 300, "up"))
            for k, (ic, tx, at) in enumerate(c["items"]):
                y = 520 + k * 260
                P += [(at, emoji(ic, 190), 180, y, "pop"), (at + 0.08, fit_text(tx.upper(), 76, 590), 300, y, "left"),
                      (at + 0.22, sign("✓", 96), 975, y, "pop")]
        elif self.T == "flow":
            for k, (a, b, ic, at) in enumerate(c["rows"]):
                y = 560 + k * 360
                P += [(at, fit_text(a.upper(), 74, 470, WHITE), 60, y, "left"), (at + 0.15, arrow(150), 610, y, "pop"),
                      (at + 0.28, emoji(ic, 170), 820, y - 20, "pop"), (at + 0.36, text_plain(b.upper(), 62, LEMON), 820, y + 130, "up")]
        elif self.T == "stat":
            if c.get("emoji"):
                P.append((0.3, emoji(c["emoji"], 200), W // 2, 380, "pop"))
            P += [(0.0, text_plain(c["big"], 330, LEMON), W // 2, 660, "pop"), (0.2, text_plain(c["caption"].upper(), 88, WHITE), W // 2, 930, "up")]
        elif self.T == "chart":
            P += [(0.0, text_plain(c["title"].upper(), 80, LEMON), W // 2, 330, "up"),
                  (0.1, text_plain(c.get("xlabel", "").upper() + " →", 62, WHITE), 760, 1110, "up")]

    def frame(self, u):
        k = min(1, u / 0.15)
        f = self.bg.copy() if k >= 1 else cv2.resize(self.bg, None, fx=1.06 - 0.06 * k, fy=1.06 - 0.06 * k)[:H, :W].copy()
        if self.T == "chart":                                 # axes + line drawn progressively
            x0, y0, x1, y1 = 170, 1040, 930, 470; p = min(1, max(0, (u - 0.2) / 0.9))
            cv2.line(f, (x0, y0), (x1, y0), (200, 200, 200), 6, cv2.LINE_AA); cv2.line(f, (x0, y0), (x0, y1), (200, 200, 200), 6, cv2.LINE_AA)
            down = self.c.get("trend", "down") == "down"
            pts = [(int(x0 + 30 + (x1 - x0 - 60) * v), int(y1 + 60 + (y0 - y1 - 130) * (v ** 1.3 if down else 1 - v ** 1.3)))
                   for v in np.linspace(0, p, max(2, int(60 * p)))]
            if p > 0:
                cv2.polylines(f, [np.array(pts, np.int32)], False, LEMON, 16, cv2.LINE_AA); cv2.circle(f, pts[-1], 18, LEMON, -1, cv2.LINE_AA)
        for at, art, x, y, mv in self.parts:
            a = u - at
            if a < 0:
                continue
            if mv == "pop":
                paste(f, art, x, y, scale=max(0.01, ease_back(a / 0.28)), op=min(1, a / 0.08))
            elif mv == "up":
                paste(f, art, x, y + (1 - min(1, a / 0.25)) * 60, op=min(1, a / 0.15))
            else:                                             # "left": left-aligned at x, slides in from the left
                paste(f, art, x + art.shape[1] / 2 - (1 - min(1, a / 0.25)) * 120, y, op=min(1, a / 0.15))
        return f


def make_face_panel(fcx, fcy, s=0.70, nose_y=496):
    """split layout: head-and-shoulders crop (70 %), eyes just below the subtitle line, blurred fill at the sides"""
    ph = H - SPLIT_TOP
    Mb = np.float32([[1.25, 0, W / 2 - 1.25 * fcx], [0, 1.25, nose_y - 1.25 * fcy]])
    def panel(frame, a):
        z = s * (1 + 0.02 * min(1, a / 4))                    # slow push-in keeps it alive
        M = np.float32([[z, 0, W / 2 - z * fcx], [0, z, nose_y - z * fcy]])
        mask = cv2.warpAffine(np.ones((H, W), np.float32), M, (W, ph))[:, :, None]
        sharp = cv2.warpAffine(frame, M, (W, ph), flags=cv2.INTER_LINEAR)
        blur = cv2.GaussianBlur(cv2.warpAffine(frame, Mb, (W, ph), flags=cv2.INTER_LINEAR), (0, 0), 25) * 0.55
        return (sharp * mask + blur * (1 - mask)).astype(np.uint8)
    return panel


# ---------- main ----------
def main():
    src, vj, ass, out = sys.argv[1:5]
    cfg = json.load(open(vj, encoding="utf-8"))
    dur = C.duration(src)
    title_end = cfg.get("title_end", 7.0); track = face_track(src)
    fcx = float(np.median([(b[0] + b[2]) / 2 for _, b in track])); fcy = float(np.median([(b[1] + b[3]) / 2 for _, b in track]))
    cuts = [Cutaway(c) for c in cfg.get("cutaways", [])]
    in_cut = lambda t: next((c for c in cuts if c.t <= t < c.t + c.d), None)
    hy = cfg.get("hybrid") or {}; layout = hy.get("layout", "full"); anims = []
    if hy:                                                    # hybrid: the ReelsMotion engine
        sys.path.insert(0, str(C.MOTION / "tools")); import hybrid
        hy.setdefault("theme", B["theme"])
        anims = hybrid.clips(hy, H if layout == "full" else SPLIT_TOP, W, words="words.json", face=(fcx, fcy))
    in_anim = lambda t: next((a for a in anims if a.t0 <= t < a.t1), None)
    switches = sorted({a.t0 for a in anims} | {a.t1 for a in anims} | {c.t for c in cuts} | {c.t + c.d for c in cuts})
    face_panel = make_face_panel(fcx, fcy) if layout == "split" else None

    pts, emph = [], []                                        # "zoom" keys levels/extra/emph are ignored: the camera never jumps

    def zoom(t):
        return 1 + ZOOM_AMP * 0.5 * (1 - math.cos(2 * math.pi * t / ZOOM_PERIOD)), 0.0, 0.0
    zmax = lambda a, b: max(zoom(a + k * 0.1)[0] for k in range(int((b - a) * 10) + 1))

    items, sfx, last_zones, last_x, busy, dropped = [], [], [], [], [], []
    for bt in sorted(cfg.get("beats", []), key=lambda b: b["t"]):
        t0 = bt["t"]
        if in_cut(t0) or in_cut(t0 + 0.3) or in_anim(t0) or in_anim(t0 + 0.3):
            print(f"SKIP {t0:.2f} (cutaway / animation segment)"); continue
        if "pop" in bt:
            d = bt.get("d", 0.9); arts = [big_text(bt["pop"], int(bt.get("size", 170)), WHITE if bt.get("color") == "white" else LEMON)]
        else:
            d = bt.get("d", 1.6); arts = [item_art(it) for it in bt["items"]]
        nxt = min([c.t for c in cuts if c.t > t0] + [a.t0 for a in anims if a.t0 > t0] + [1e9]); d = min(d, nxt - t0)   # never run into a cutaway
        if d < MIN_HOLD:
            dropped.append([round(t0, 2), "too short before the next animation", bt.get("pop") or [list(i.values())[0] for i in bt.get("items", [])]])
            continue
        fb = face_box(track, t0, t0 + d); z = zmax(t0, t0 + d)
        fb = (fcx + (fb[0] - fcx) * z, fcy + (fb[1] - fcy) * z, fcx + (fb[2] - fcx) * z, fcy + (fb[3] - fcy) * z)
        live = [b for b in busy if b[0] < t0 + d and t0 < b[1]]
        others = [(0, SUB_BAND[0], W, SUB_BAND[1])] + ([(0, 0, W, TITLE_BOTTOM)] if t0 < title_end else [])
        placed = None
        zones = [bt["zone"]] if bt.get("zone") else RNG.sample(list(ZONES), len(ZONES))
        lays = ("v", "h") if len(arts) > 1 else ("v",)
        fresh = [z_ for z_ in zones if z_ not in last_zones[-1:]]; stale = [z_ for z_ in zones if z_ in last_zones[-1:]]
        order = [(z_, sc, ly) for sc in SCALES for z_ in fresh for ly in lays] + \
                [(z_, sc, ly) for sc in SCALES for z_ in stale for ly in lays]     # biggest size first; never the same zone twice
        cache = {}
        for (zn, sc, ly), shift in [(o, 320) for o in order] + [(o, 120) for o in order]:   # strict spot change, then relaxed
            if placed:
                break
            if sc not in cache:
                if "items" in bt and sc < 1:                 # re-render smaller: emoji/signs scale, labels keep >= 50 px type
                    cache[sc] = [item_art({**it, "size": max(50, int(it.get("size", 62) * sc))} if "label" in it else
                                          {**it, "size": int(it.get("size", 220) * sc)}) for it in bt["items"]]
                else:
                    cache[sc] = arts if sc == 1 else [cv2.resize(a, (int(a.shape[1] * sc), int(a.shape[0] * sc)), interpolation=cv2.INTER_AREA) for a in arts]
            arts_sc = cache[sc]; sz = [(a.shape[1], a.shape[0]) for a in arts_sc]
            if ly == "v":                                    # vertical stack (side columns), slight overlap
                gw = max(s[0] for s in sz); gh = sum(s[1] for s in sz) - 40 * (len(sz) - 1)
            else:                                            # horizontal row (lower third, band above the head)
                gw = sum(s[0] for s in sz) - 40 * (len(sz) - 1); gh = max(s[1] for s in sz)
            vw, vh = (gw / 2 - 22 * sc) * 1.08, (gh / 2 - 22 * sc) * 1.08                      # visible half-size incl. rotation
            fw, fh = vw * 1.12 + 10, vh * 1.12 + 10                                            # + overshoot: must stay in frame
            x0, y0, x1, y1 = ZONES[zn]; cand = []
            for cy in range(int(y0), int(y1) + 1, 20):
                for cx in range(int(x0), int(x1) + 1, 20):
                    if cx - fw < 0 or cx + fw > W or cy - fh < 0 or cy + fh > H:
                        continue
                    box = (cx - vw, cy - vh, cx + vw, cy + vh)
                    if overlap(box, fb, 14) or any(overlap(box, b, 6) for b in others) or any(overlap(box, b[2], 10) for b in live):
                        continue
                    if last_zones and zn == last_zones[-1] and abs(cx - last_x[-1]) < shift:    # same zone -> clearly different spot
                        continue
                    cand.append((math.hypot(cx - fcx, cy - fcy) + RNG.random() * 160, cx, cy, box))
            if cand:
                cand.sort(); _, cx, cy, box = cand[min(len(cand) - 1, RNG.randrange(4))]; placed = (zn, cx, cy, box, sc, sz, gw, gh, arts_sc, ly); break
        if not placed:
            what = bt.get('pop') or [list(i.values())[0] for i in bt['items']]
            print(f"NO ROOM {t0:.2f} {what}"); dropped.append([round(t0, 2), "no room beside the face", what]); continue
        zn, cx, cy, box, sc, sz, gw, gh, arts, ly = placed; last_zones.append(zn); last_x.append(cx); busy.append((t0, t0 + d, box))
        enter = bt.get("enter", "slide" if RNG.random() < 0.3 else "pop")
        x, y = cx - gw / 2, cy - gh / 2; rot0 = RNG.choice([-1, 1]) * RNG.uniform(8, 12)
        for k, (art, s) in enumerate(zip(arts, sz)):
            px, py = (cx, y + s[1] / 2) if ly == "v" else (x + s[0] / 2, cy)
            items.append({"t0": t0 + 0.12 * k, "t1": t0 + d, "art": art, "x": px, "y": py, "rot": rot0 if k == 0 else -rot0 * 0.5,
                          "enter": enter, "edge": -1 if cx < W / 2 else 1, "ph": RNG.random() * 6})
            y += s[1] - 40; x += s[0] - 40
        if bt.get("arrow"):                                   # arrow from the combo toward the face edge
            ang = math.atan2(fcy - cy, fcx - cx); ex, ey = cx + math.cos(ang) * gw * 0.55, cy + math.sin(ang) * gh * 0.55
            ab = (ex - 75, ey - 75, ex + 75, ey + 75)
            if not overlap(ab, fb, 6) and not overlap(ab, others[0], 0):
                items.append({"t0": t0 + 0.12 * len(arts), "t1": t0 + d, "art": arrow(int(170 * max(sc, 0.8))), "x": ex, "y": ey,
                              "rot": -math.degrees(ang), "enter": "pop", "edge": 0, "ph": 0, "noswing": True})
        sfx.append([t0, "ding" if "pop" in bt else ("whoosh" if enter == "slide" else ("tick" if len(sfx) % 2 else "pop"))])
        print(f"{t0:6.2f}-{t0 + d:5.2f}  {zn:3s} ({cx},{cy}) x{sc:.2f} {enter:5s}  "
              f"{bt.get('pop') or ' + '.join(str(list(i.values())[0]) for i in bt['items'])}{' + arrow' if bt.get('arrow') else ''}")
    for c in cuts:
        sfx.append([c.t, "whoosh"]); print(f"{c.t:6.2f}-{c.t + c.d:5.2f}  CUTAWAY {c.T}")
    for a in anims:
        sfx += [[a.t0, "swell"], [a.t1, "whoosh"]]                  # swell rises into the iris, whoosh back to the face
        print(f"{a.t0:6.2f}-{a.t1:5.2f}  ANIM {a.s.get('scene') or '+'.join(s['type'] for s in a.s['scenes'])} ({layout})")
    changes = sorted([i["t0"] for i in items] + [c.t for c in cuts] + [c.t + c.d for c in cuts])
    still = [(a, b) for a, b in zip([0] + changes, changes + [dur]) if b - a > 2.2]
    print("pace - still stretches over 2.2 s:", ", ".join(f"{a:.1f}-{b:.1f}" for a, b in still) or "none")
    json.dump(sfx if cfg.get("sfx") else [], open(os.path.splitext(out)[0] + "_sfx.json", "w"))
    json.dump({"dropped": dropped, "still_over_2_2": [[round(a, 2), round(b, 2)] for a, b in still]}, open("visuals_report.json", "w"), ensure_ascii=False)

    dec = subprocess.Popen([FF, "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    import shutil
    fd = Path("_fonts"); fd.mkdir(exist_ok=True)
    if FONT and not (fd / Path(FONT).name).exists():
        shutil.copy(FONT, fd / Path(FONT).name)
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", src, "-map", "0:v", "-map", "1:a", "-vf", f"ass={ass}:fontsdir=_fonts",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy", out],
                           stdin=subprocess.PIPE)
    n = 0; cf = cut_frames(src); fr = {}; eof = None

    def fill(upto):                                           # frames n-2 .. n+2 stay in memory for the cut blends
        nonlocal eof
        while eof is None and max(fr, default=-1) < upto:
            b_ = dec.stdout.read(W * H * 3)
            if len(b_) < W * H * 3:
                eof = max(fr, default=-1) + 1
            else:
                fr[max(fr, default=-1) + 1] = np.frombuffer(b_, np.uint8).reshape(H, W, 3)

    while True:
        fill(n + 2)
        if n not in fr:
            break
        for k_ in [k_ for k_ in fr if k_ < n - 2]:
            del fr[k_]
        buf = soft_cut(fr, n, cf).tobytes()
        t = n / FPS; c = in_cut(t); an = in_anim(t)
        if an:
            if layout == "full":                              # engine clip (RGBA): iris in from the face, zoom out into it
                g = np.frombuffer(buf, np.uint8).reshape(H, W, 3); z, sx, sy = zoom(t)
                if z > 1.0005 or sx or sy:
                    g = cv2.warpAffine(g, np.float32([[z, 0, fcx * (1 - z) + sx], [0, z, fcy * (1 - z) + sy]]), (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
                f = hybrid.over(g, an.frame(t))
            else:                                             # split: scene on top 60 %, the face below 40 %
                f = np.empty((H, W, 3), np.uint8); f[:SPLIT_TOP] = hybrid.over(np.zeros((SPLIT_TOP, W, 3), np.uint8), an.frame(t))
                f[SPLIT_TOP:] = face_panel(np.frombuffer(buf, np.uint8).reshape(H, W, 3), t - an.t0)
                f[SPLIT_TOP - 3:SPLIT_TOP + 3] = LEMON
        elif c:
            f = c.frame(t - c.t)
        else:
            f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            z, sx, sy = zoom(t)
            if z > 1.0005 or sx or sy:
                M = np.float32([[z, 0, fcx * (1 - z) + sx], [0, z, fcy * (1 - z) + sy]])
                f = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            else:
                f = f.copy()
            for it in items:
                a = t - it["t0"]
                if a < 0 or t > it["t1"]:
                    continue
                left = it["t1"] - t; x, y, rot = it["x"], it["y"], it["rot"]
                if not it.get("noswing"):                     # wiggle + float while visible
                    rot += 3 * math.sin(a * 6 + it["ph"]); y += 5 * math.sin(a * 3.3 + it["ph"])
                sc, op = 1.0, 1.0
                if a < 0.3:                                   # enter: pop with overshoot, or slide in from the side edge
                    if it["enter"] == "slide":
                        x += (1 - ease_back(a / 0.26)) * it["edge"] * (W / 2 + it["art"].shape[1])
                    else:
                        sc = max(0.01, ease_back(a / 0.26))
                    op = min(1, a / 0.06)
                if left < 0.13:                               # fast exit: scale-out, or slide back out
                    u = left / 0.13
                    if it["enter"] == "slide":
                        x += (1 - u) * it["edge"] * 260
                    else:
                        sc *= 0.35 + 0.65 * u
                    op = min(op, u)
                paste(f, it["art"], x, y, sc, rot, op)
        enc.stdin.write(np.ascontiguousarray(f).tobytes()); n += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print(f"visuals: {len(items)} elements, {len(dropped)} dropped, {len(cuts)} cutaways, {n} frames -> {out}")


if __name__ == "__main__":
    main()
