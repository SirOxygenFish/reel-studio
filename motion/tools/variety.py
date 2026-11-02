"""VARIETY check + usage ledger for hybrid Reels: viewers notice reused assets across a series.

    python variety.py check <visuals.json> [--name "Reel name"] [--account <brand>] [--window 5]
    python variety.py add   <visuals.json> --name "Reel name" [--account <brand>] [--date YYYY-MM-DD] [--force]
    --replaces "Old name|..."  (check and add) a correction: the Reels it replaces are left out, and their ledger entry goes
    python variety.py show  [--account <brand>]

The ledger is <data>/brands/<brand>/usage_ledger.json: per finished Reel its segments, and per scene: type, bespoke
(yes/no), layout, metaphor, key assets, restricted family, plus frame fingerprints (dHash 16x16 at 30/55/80 % of each
segment clip). `check` runs in the Reel's work folder (it reads words.json and _motion/current.json written by hybrid.py)
and FAILS on:
  bespoke   < 60 % of the animation segments are bespoke (bespoke scenes cover >= half of the segment's time)
  repeat    two scenes in one Reel share a type or a layout; a restricted family (phone chat, list rows/3-item tiles,
            versus cards, quote card) more than once in the Reel
  ledger    in the last N (5) Reels of the same account: the same bespoke type, layout, metaphor or key asset; a
            restricted family used at all (each at most once per ~5 Reels)
  frames    a segment whose frames look too close (high-passed dHash, < 0.30) to another segment of this Reel or of the last N Reels
  short     a word ref (an element appearing on a word) less than 0.8 s before its segment ends (pops must stay >= 0.8 s)
and WARNS on on-screen words that are not in the speech (invented text; fix it or use a visual without text).
Scene meta: bespoke scenes declare it in their library header (/* @scene {...} */); stock scenes get a default layout
per type; any scene can override with "meta": {"layout", "metaphor", "assets"}.
"""
import json, os, re, subprocess, sys, datetime
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import common as C
FF = C.FF

STOCK = {"chat": "phone-chat", "steps": "list-rows", "versus": "two-cards", "quote": "quote-card", "icongrid": "tile-stack",
         "bigword": "kinetic-type", "stat": "counter-ring", "hero": "disc-object", "flow": "node-flow", "timeline": "vertical-timeline",
         "chart": "bar-chart", "character": "peep-bust", "beforeafter": "wipe-split", "level": "vial", "joint": "knee",
         "cta": "profile-buttons", "image": "still-photo"}
RESTRICTED = {"chat": "chat", "steps": "list", "versus": "versus", "quote": "quote"}
BESPOKE_MIN, SHORT_POP, FP_THR, WINDOW = 0.6, 0.8, 0.30, 5      # FP_THR: min high-passed dHash distance between segments
TEXT_KEYS = {"label", "text", "title", "heading", "lines", "sub", "caption", "words", "word", "name"}


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def norm(s):
    return re.sub(r"[^\w%]", "", (s or "").lower())


def lib_meta(ty):
    f = next((os.path.join(str(d), ty + ".js") for d in C.libraries() if os.path.exists(os.path.join(str(d), ty + ".js"))), None)
    if not f:
        return None
    m = re.search(r"/\*\s*@scene\s*(\{.*?\})\s*\*/", open(f, encoding="utf-8").read(), re.S)
    return json.loads(m.group(1)) if m else {"type": ty}


def scene_meta(sc):
    ty = sc.get("type", "")
    lm = lib_meta(ty) if ty not in STOCK else None
    meta = {"type": ty, "bespoke": lm is not None, "layout": None, "metaphor": None, "assets": [], "family": None}
    if lm:
        meta.update({k: lm.get(k) for k in ("layout", "metaphor")}); meta["assets"] = lm.get("assets", []); meta["tags"] = lm.get("tags", [])
    else:
        meta["layout"] = STOCK.get(ty, ty)
        meta["family"] = RESTRICTED.get(ty)
        if ty == "icongrid" and sc.get("items"):
            meta["family"] = "list"; meta["layout"] = "tile-stack" if len(sc["items"]) <= 3 else "tile-grid"
    meta.update({k: v for k, v in (sc.get("meta") or {}).items() if k in ("layout", "metaphor", "assets")})
    meta["assets"] = sorted(set(meta["assets"] or []))
    return meta


# ---------- frames ----------
def fingerprints(clip, t0, t1):
    """3 frames (30/55/80 %) -> high-passed dHash 16x16: the blurred background (theme gradient, vignette) is subtracted first,
    so the hash follows the scene's content. Plain dHash could not tell scenes apart on dark themes (2026-10-27 calibration:
    the same stock versus cards in two Reels 0.285, different bespoke scenes 0.305 and up)."""
    out = []
    for u in (0.3, 0.55, 0.8):
        raw = subprocess.run([FF, "-v", "error", "-ss", f"{(t1 - t0) * u:.3f}", "-i", clip, "-frames:v", "1",
                              "-vf", "crop=1080:1010:0:196,scale=136:128:flags=area,format=gray", "-f", "rawvideo", "-"],
                             capture_output=True).stdout
        if len(raw) < 136 * 128:
            continue
        g = np.frombuffer(raw[:136 * 128], np.uint8).reshape(128, 136).astype(float)
        r, kern = 12, np.ones(25) / 25
        bl = np.apply_along_axis(lambda x: np.convolve(np.pad(x, r, mode="edge"), kern, "valid"), 0, g)
        bl = np.apply_along_axis(lambda x: np.convolve(np.pad(x, r, mode="edge"), kern, "valid"), 1, bl)
        s16 = (g - bl).reshape(16, 8, 17, 8).mean((1, 3))
        bits = (s16[:, 1:] > s16[:, :-1]).flatten()
        out.append("".join("%x" % int("".join(str(int(b)) for b in bits[i:i + 4]), 2) for i in range(0, 256, 4)))
    return out


def fp_dist(a, b):
    """smallest normalised Hamming distance between any frame pair of two segments (0 = identical, ~0.5 = unrelated)"""
    best = 1.0
    for x in a:
        for y in b:
            d = bin(int(x, 16) ^ int(y, 16)).count("1") / 256
            best = min(best, d)
    return best


# ---------- words ----------
def load_words(path="words.json"):
    W = json.load(open(path, encoding="utf-8"))
    return [(w[0], w[1], w[2], norm(w[2])) for w in (W["words"] if isinstance(W, dict) else W)]


def resolve(ref, words, ctx):
    if ref is None:
        return None
    if isinstance(ref, (int, float)):
        return float(ref)
    s, off = str(ref).strip(), 0.0
    m = re.match(r"^(.*?)([+-]\d+(?:\.\d+)?)$", s)
    if m and m.group(1) and not re.match(r"^@?\d+$", s):
        s, off = m.group(1), float(m.group(2))
    end = s.startswith("end:")
    s = s[4:] if end else s
    if re.match(r"^@\d+$", s):
        w = words[int(s[1:])]
    elif re.match(r"^-?\d+(\.\d+)?$", s):
        return float(s) + off
    else:
        txt, _, nth = s.partition("#"); n = norm(txt)
        if nth:
            hits = [w for w in words if w[3] == n]; w = hits[int(nth) - 1] if len(hits) >= int(nth) else None
        else:
            w = next((w for w in words if w[3] == n and w[0] >= ctx - 0.05), None) or \
                next((w for w in words if w[3].startswith(n) and w[0] >= ctx - 0.05), None)
        if w is None:
            return None
    return (w[1] if end else w[0]) + off


def refs(o, key=None):
    """every word ref in a scene spec: values of 'at'/'*At' keys"""
    if isinstance(o, dict):
        for k, v in o.items():
            if (k == "at" or k.endswith("At")) and isinstance(v, (str, int, float)):
                yield k, v
            else:
                yield from refs(v, k)
    elif isinstance(o, list):
        for v in o:
            if isinstance(v, list) and len(v) == 2 and isinstance(v[1], (str, int, float)) and isinstance(v[0], (int, float)) and key in ("levels",):
                yield "level", v[1]
            else:
                yield from refs(v, key)


def texts(o, key=None):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("meta", "icon", "type", "in", "mode", "shape", "hl", "headingHl", "at", "src", "peep", "kind", "layout", "side"):
                continue
            yield from texts(v, k)
    elif isinstance(o, list):
        for v in o:
            yield from texts(v, key)
    elif isinstance(o, str) and key in TEXT_KEYS:
        yield o


def invented(s, vocab):
    bad = []
    for tok in re.findall(r"[\w%]+", s.lower()):
        n = norm(tok)
        if len(n) < 3 or n.isdigit() and any(n == v for v in vocab):
            continue
        need = 3 if len(n) <= 5 else 4                       # word endings change: bajki ~ bajek, kraj ~ kraju
        if not any(v == n or (len(v) >= need and os.path.commonprefix([v, n]).__len__() >= max(need, min(len(n), len(v)) - 3)) for v in vocab):
            bad.append(tok)
    return bad


# ---------- check ----------
def analyse(vj):
    V = json.load(open(vj, encoding="utf-8")); hy = V.get("hybrid") or {}
    segs = hy.get("segments", [])
    cur = json.load(open("_motion/current.json")) if os.path.exists("_motion/current.json") else []
    words = load_words() if os.path.exists("words.json") else []
    out = []
    for i, sg in enumerate(segs):
        rep = json.load(open(cur[i]["report"])) if i < len(cur) and os.path.exists(cur[i]["report"]) else {}
        sct = rep.get("scenes") or []
        scenes = []
        for j, sc in enumerate(sg.get("scenes", [])):
            m = scene_meta(sc)
            if j < len(sct):
                m["dur"] = round(sct[j]["end"] - sct[j]["start"], 2)
            scenes.append(m)
        dur = sg["t1"] - sg["t0"]
        bes = sum(m.get("dur", dur / max(1, len(scenes))) for m in scenes if m["bespoke"])
        fp = fingerprints(cur[i]["clip"], sg["t0"], sg["t1"]) if i < len(cur) and os.path.exists(cur[i]["clip"]) and \
            abs(cur[i]["t0"] - sg["t0"]) < 0.01 and abs(cur[i]["t1"] - sg["t1"]) < 0.01 else []
        out.append({"t0": sg["t0"], "t1": sg["t1"], "scenes": scenes, "bespoke": bes >= 0.5 * dur, "fp": fp, "spec": sg})
    return V, out, words


def ledger(account):
    return C.load_json(C.ledger_path(account), {"about": __doc__.split("\n")[0], "reels": []})


def check(vj, name=None, account=None, window=WINDOW, quiet=False, skip=()):
    V, segs, words = analyse(vj)
    account = account or (V.get("hybrid") or {}).get("theme", "default")
    fails, warns = [], []
    # bespoke share
    n = len(segs); nb = sum(s["bespoke"] for s in segs)
    share = nb / n if n else 1.0
    if n and share < BESPOKE_MIN:
        fails.append(f"bespoke: {nb}/{n} segments bespoke ({share*100:.0f} % < {BESPOKE_MIN*100:.0f} %)")
    # repeats inside the Reel
    allsc = [(i, m) for i, s in enumerate(segs) for m in s["scenes"]]
    for key in ("type", "layout"):
        seen = {}
        for i, m in allsc:
            v = m.get(key)
            if v and v in seen:
                fails.append(f"repeat: {key} '{v}' in segments {seen[v]} and {i}")
            seen.setdefault(v, i)
    fam = [m["family"] for _, m in allsc if m["family"]]
    for f in set(fam):
        if fam.count(f) > 1:
            fails.append(f"repeat: restricted '{f}' {fam.count(f)}x in this Reel")
    # ledger window
    L = ledger(account)
    prev = [r for r in L["reels"] if r.get("account") == account and r.get("name") != name and r.get("name") not in skip][-window:]
    for r in prev:
        used = [m for s in r["segments"] for m in s["scenes"]]
        for i, m in allsc:
            for u in used:
                if m["bespoke"] and u.get("type") == m["type"]:
                    fails.append(f"ledger: bespoke scene '{m['type']}' was used in «{r['name']}»")
                if m.get("layout") and u.get("layout") == m["layout"] and (m["bespoke"] or m["family"]):
                    fails.append(f"ledger: layout '{m['layout']}' (seg {i}) was used in «{r['name']}»")
                if m.get("metaphor") and u.get("metaphor") and norm(u["metaphor"]) == norm(m["metaphor"]):
                    fails.append(f"ledger: metaphor '{m['metaphor']}' (seg {i}) was used in «{r['name']}»")
                for a in set(m.get("assets") or []) & set(u.get("assets") or []):
                    fails.append(f"ledger: key asset '{a}' (seg {i}) was used in «{r['name']}»")
                if m["family"] and u.get("family") == m["family"]:
                    fails.append(f"ledger: restricted '{m['family']}' (seg {i}) was used in «{r['name']}» (max once per ~{window} Reels)")
                if not m["bespoke"] and not m["family"] and u.get("type") == m["type"]:
                    warns.append(f"stock scene '{m['type']}' (seg {i}) also in «{r['name']}»")
    # frames
    for i, s in enumerate(segs):
        for j in range(i):
            if s["fp"] and segs[j]["fp"]:
                d = fp_dist(s["fp"], segs[j]["fp"])
                if d < FP_THR:
                    fails.append(f"frames: segment {i} looks like segment {j} (dHash {d:.3f} < {FP_THR})")
        for r in prev:
            for k, ps in enumerate(r["segments"]):
                if s["fp"] and ps.get("fp"):
                    d = fp_dist(s["fp"], ps["fp"])
                    if d < FP_THR:
                        fails.append(f"frames: segment {i} looks like «{r['name']}» segment {k} (dHash {d:.3f} < {FP_THR})")
    # short pops + invented text
    vocab = {w[3] for w in words}
    for i, s in enumerate(segs):
        for sc in s["spec"].get("scenes", []):
            for k, ref in refs(sc):
                t = resolve(ref, words, s["t0"]) if words else None
                if t is not None and s["t1"] - t < SHORT_POP and t > s["t0"] and not (V.get("hybrid") or {}).get("no_short"):
                    fails.append(f"short: '{ref}' ({k}) appears {s['t1'] - t:.2f} s before segment {i} ends (< {SHORT_POP})")
            if vocab:
                for tx in texts(sc):
                    b = invented(tx, vocab)
                    if b:
                        warns.append(f"text: «{tx}» (seg {i}) has words that are not spoken: {', '.join(b)}")
    fails = list(dict.fromkeys(fails)); warns = list(dict.fromkeys(warns))
    res = {"pass": not fails, "bespoke_share": round(share, 2), "segments": n, "fails": fails, "warns": warns}
    if not quiet:
        print(f"variety: {'PASS' if not fails else 'FAIL'} | bespoke {nb}/{n} segments ({share*100:.0f} %) | "
              f"compared with {len(prev)} earlier {account} Reels")
        for f in fails:
            print("   FAIL", f)
        for w in warns:
            print("   warn", w)
    return res, segs


def add(vj, name, account=None, date=None, force=False, skip=()):
    res, segs = check(vj, name, account, quiet=True, skip=skip)
    if not res["pass"] and not force:
        print("not added: variety FAIL"); [print("  ", f) for f in res["fails"]]; sys.exit(1)
    V = json.load(open(vj, encoding="utf-8"))
    account = account or (V.get("hybrid") or {}).get("theme", "default")
    L = ledger(account)
    L["reels"] = [r for r in L["reels"] if not ((r.get("name") == name or r.get("name") in skip) and r.get("account") == account)]
    L["reels"].append({"name": name, "account": account, "date": date or datetime.date.today().isoformat(),
                       "bespoke_share": res["bespoke_share"],
                       "segments": [{"t0": s["t0"], "t1": s["t1"], "bespoke": s["bespoke"], "fp": s["fp"],
                                     "scenes": [{k: m.get(k) for k in ("type", "bespoke", "layout", "metaphor", "assets", "family")} for m in s["scenes"]]}
                                    for s in segs]})
    C.save_json(C.ledger_path(account), L)
    print(f"ledger: added «{name}» ({account}), {len(L['reels'])} Reels in the ledger")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1]
    if cmd == "check":
        r, _ = check(sys.argv[2], arg("--name"), arg("--account"), int(arg("--window", WINDOW)), skip=[x for x in (arg("--replaces") or "").split("|") if x])
        sys.exit(0 if r["pass"] else 1)
    elif cmd == "add":
        add(sys.argv[2], arg("--name"), arg("--account"), arg("--date"), "--force" in sys.argv, skip=[x for x in (arg("--replaces") or "").split("|") if x])
    elif cmd == "show":
        for r in ledger(arg("--account") or C.brand()["slug"])["reels"]:
            if not arg("--account") or r["account"] == arg("--account"):
                print(r["date"], r["account"], r["name"], [m["type"] + "/" + str(m["layout"]) for s in r["segments"] for m in s["scenes"]])
