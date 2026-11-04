"""reel-tool tutorials: rebuilds the two bundled tutorials (motion graphics made with the engine, no voice, soft clicks).

    reel-tool tutorials build [t1|t2|all] [en|ru|pl|all] [--preview 1.5,8,20]   render + QC + gate; copies a passing video into the plugin
    reel-tool tutorials mark t1|t2 en|ru|pl|all "what I checked"                    record the visual review of the frame sheet
    reel-tool tutorials gate [t1|t2|all] [en|ru|pl|all]                             the gate alone (after a mark)

Sources: motion/tutorials/kit.js (drawings + action player), t1.json / t2.json (timelines), strings.json (all texts).
Tutorial 1 (PC, 16:9) goes to docs/tutorials/, Tutorial 2 (iPhone, 9:16) to upload-page/tutorials/ (played offline by the page).
Tutorial 2 is a list of steps (one screen, one tap); its page screens are real renders of upload-page/index.html taken by
motion/tutorials/shots.mjs against a scratch copy of the page on a free local port, so every button sits where it really is.
The tutorial gate keeps the Reel gate's rules where they apply (format, motion never dead for > 1 s, nothing outside the frame,
round things round, no long dashes, sound peaks, no stray A-B-A frames, a visual review) and drops the Instagram ones (subtitle band, caption strip).
"""
import importlib, json, os, re, secrets, shutil, subprocess, sys, threading, wave
from pathlib import Path

import common as C

SRC = C.MOTION / "tutorials"
BUILD = C.DATA / "tutorials"
LANGS = ("en", "ru", "pl")
WANT = {"len": (30.0, 45.0), "motion": 0.5, "dead": 1.0, "caption_px": {"t1": 46, "t2": 54}, "peak_db": -1.0}


def spec(tut):
    return json.load(open(SRC / f"{tut}.json", encoding="utf-8"))


def strings():
    return json.load(open(SRC / "strings.json", encoding="utf-8"))


def resolve(obj, table):
    """every "$key" string becomes table[key] (lists and objects too)"""
    if isinstance(obj, dict):
        return {k: resolve(v, table) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve(v, table) for v in obj]
    if isinstance(obj, str) and obj.startswith("$"):
        if obj[1:] not in table:
            C.fail(f"missing text {obj}")
        return table[obj[1:]]
    return obj


def texts(tut, lang):
    S = strings()
    return {**S["ui"][tut], **S["en"][tut], **S[lang][tut]}


def steps_scenes(sp, tb, shots):
    """a "steps" timeline (Tutorial 2): one screen and one tap per scene, plain fades, a still camera"""
    rects = json.loads((shots / "rects.json").read_text(encoding="utf-8"))["shots"] if (shots / "rects.json").exists() else {}
    icon = (C.ROOT / ".claude-plugin" / "icon.png").as_uri()
    shot = lambda name: (shots / f"{name}.png").as_uri()
    still, fade = {"still": True}, sp.get("fade", 0.2)
    ti = resolve(sp["title"], tb)
    scenes = [{"type": "tut_title", "at": 0, "title": ti["title"], "sub": ti["sub"], "src": shot(ti["shot"]), "camera": still}]
    at, cues = ti["d"], []
    for st in sp["steps"]:
        s = {**resolve(st, tb), "type": "t2s", "at": round(at, 3), "in": "fade", "inDur": fade, "labels": tb, "camera": still, "icon": icon}
        if st.get("shot"):
            s["src"], s["rects"] = shot(st["shot"]), rects.get(st["shot"], {})
        n = len(st.get("taps", []))                                 # the same tap times as kit.js
        cues += ([[round(at + st["tapAt"], 3), "tick"]] if "tapAt" in st else
                 [[round(at + st["d"] - 0.75 - (n - 1 - i) * 0.7, 3), "tick"] for i in range(n)])
        scenes.append(s); at += st["d"]
    en = resolve(sp["end"], tb)
    scenes.append({"type": "tut_end", "at": round(at, 3), "in": "fade", "inDur": 0.35, "title": en["title"], "rows": en["rows"], "camera": still})
    cues.append([round(at - sp["steps"][-1]["d"] + 0.5, 3), "ding"])
    return scenes, cues, round(at + en["d"], 3)


SHOT_SERVER = {}


def make_shots(tut, lang):
    """real screenshots of the upload page in this language, against a scratch copy of the page on a free local port"""
    out = BUILD / f"{tut}-{lang}" / "shots"; up, ready, clips = out / "up", out / "ready", out / "clips"
    for d in (up, ready, clips):
        d.mkdir(parents=True, exist_ok=True)
    for old in up.iterdir():                                     # the batches the last run uploaded go to the Recycle Bin / Trash
        C.trash(old)
    if not SHOT_SERVER:
        sys.path.insert(0, str(C.ROOT / "upload-page")); srv = importlib.import_module("server")
        s = srv.Server(("127.0.0.1", 0), srv.Handler)
        srv.KEY, srv.PORT = secrets.token_urlsafe(12), s.server_address[1]
        threading.Thread(target=s.serve_forever, daemon=True).start()
        SHOT_SERVER.update(mod=srv, port=srv.PORT, key=srv.KEY)
    srv = SHOT_SERVER["mod"]; srv.UPLOADS, srv.READY = str(up), str(ready)
    names = []
    for name, size in (("IMG_4021.MOV", 31_400_000), ("IMG_4022.MOV", 24_800_000)):   # sizes the page shows; the bytes are zeros
        f = clips / name
        if not f.exists() or f.stat().st_size != size:
            with open(f, "wb") as h:
                h.truncate(size)
        names.append(str(f))
    sample = C.ROOT / "docs" / "tutorials" / "tutorial1-pc.en.mp4"
    url = f"http://127.0.0.1:{SHOT_SERVER['port']}/?k={SHOT_SERVER['key']}"
    r = subprocess.run([C.node(), str(SRC / "shots.mjs"), url, lang, str(out), str(ready), str(sample), texts(tut, lang)["reelName"], *names],
                       env=C.run_env(), timeout=240)
    if r.returncode:
        C.fail(f"page screenshots failed: {tut} {lang}")
    return out


def storyboard(tut, lang):
    sp, tb = spec(tut), texts(tut, lang)
    W, H = sp["size"]
    if "steps" in sp:
        scenes, cues, t1 = steps_scenes(sp, tb, BUILD / f"{tut}-{lang}" / "shots")
        return {"theme": "default", "size": [W, H], "fps": 30, "t0": 0, "t1": t1, "box": [40, 40, W - 40, H - 40], "noMark": True,
                "tin": "none", "scenes": scenes, "extra_js": [str(SRC / "kit.js")], "voice": "silence.wav", "sfx": True, "sfxLevel": -8,
                "cues": sorted(cues), "css": "#substrip{display:none}", "textSel": ".tut .ct, .tut .ttl, .tut .tsub, .tut .er"}
    scenes, cues = [], []
    for sc in sp["scenes"]:
        s = resolve({k: v for k, v in sc.items()}, tb)
        s["labels"] = tb
        s["camera"] = {"still": True}                            # no push-in, drift or tilt: text stays sharp
        for a in s.get("acts", []):
            if "click" in a:
                cues.append([round(sc["at"] + a["t"], 3), "tick"])
        scenes.append(s)
    cues += [[t, "ding"] for t in sp.get("dings", [])]
    return {"theme": "default", "size": [W, H], "fps": 30, "t0": 0, "t1": sp["t1"], "box": [40, 40, W - 40, H - 40], "noMark": True,
            "tin": "none", "scenes": scenes, "extra_js": [str(SRC / "kit.js")], "voice": "silence.wav", "sfx": True, "sfxLevel": -8,
            "cues": sorted(cues), "css": "#substrip{display:none}", "textSel": ".tut .ct, .tut .ttl, .tut .tsub, .tut .er"}


def silence(path, secs):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000)
        w.writeframes(b"\x00\x00" * int(secs * 48000))


def all_text(tut, lang):
    """every string the viewer can see in this tutorial (for the long dash check)"""
    out = []
    def walk(o):
        if isinstance(o, str):
            out.append(o)
        elif isinstance(o, dict):
            [walk(v) for v in o.values()]
        elif isinstance(o, list):
            [walk(v) for v in o]
    walk(texts(tut, lang))
    return out


def build(tut, lang, preview=None):
    d = BUILD / f"{tut}-{lang}"; d.mkdir(parents=True, exist_ok=True)
    if spec(tut).get("shots"):
        make_shots(tut, lang)
    sb = storyboard(tut, lang)
    C.save_json(d / "storyboard.json", sb)
    silence(d / "silence.wav", sb["t1"])
    ev = C.run_env()
    args = [C.node(), str(C.MOTION / "engine" / "render.mjs"), str(d / "storyboard.json")]
    if preview:
        r = subprocess.run(args + ["--preview", preview], env=ev, cwd=d)
        if r.returncode:
            C.fail("preview failed")
        print("stills:", d / "preview"); return
    (d / "gate.json").unlink(missing_ok=True)
    r = subprocess.run(args + ["--out", str(d / "final.mp4"), "--report", str(d / "report.json"), "--crf", "20"], env=ev, cwd=d)
    if r.returncode:
        C.fail(f"render failed: {tut} {lang}")
    subprocess.run([sys.executable, str(C.MOTION / "tools" / "qc.py"), str(d / "final.mp4"), "--report", str(d / "report.json"),
                    "--tutorial", "--no-sub", "--every", "1.5"], env=ev)
    gate(tut, lang)


def audio_peak(f):
    r = C.ff("-i", str(f), "-af", "volumedetect", "-vn", "-f", "null", "-")
    m = re.search(r"max_volume: (-?[\d.]+) dB", r.stderr)
    return float(m.group(1)) if m else None


def gate(tut, lang):
    d = BUILD / f"{tut}-{lang}"; f = d / "final.mp4"
    if not f.exists():
        C.fail(f"no render for {tut} {lang}: reel-tool tutorials build {tut} {lang}")
    sp = spec(tut); W, H = sp["size"]
    pr = C.probe(f); v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = [s for s in pr["streams"] if s["codec_type"] == "audio"]
    qc = C.load_json(d / "final_qc.json", {}) or {}; rep = C.load_json(d / "report.json", {}) or {}
    rows = []
    add = lambda name, ok, detail: rows.append({"check": name, "ok": bool(ok), "detail": detail})
    num, _, den = v["r_frame_rate"].partition("/"); fps = float(num) / float(den or 1)
    add("format", v["width"] == W and v["height"] == H and abs(fps - 30) < 0.01 and v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p" and a and a[0]["codec_name"] == "aac",
        f"{v['width']}x{v['height']} {fps:.2f} fps {v['codec_name']} {v['pix_fmt']} audio {a[0]['codec_name'] if a else 'none'}")
    dur = C.duration(f)
    top = sp.get("max_len", WANT["len"][1])
    add("length", WANT["len"][0] <= dur <= top, f"{dur:.1f} s ({WANT['len'][0]:.0f}-{top:.0f} s)")
    m = qc.get("motion", {})
    add("calm but never still", m.get("median", 0) >= WANT["motion"] and not qc.get("dead_runs"),
        f"motion median {m.get('median')} (>= {WANT['motion']}), dead stretches > {WANT['dead']} s: {qc.get('dead_runs') or 'none'}")
    add("inside the frame", qc.get("safe_issue_count", 0) == 0, f"{qc.get('safe_issue_count', '?')} issues")
    fl = qc.get("flash_frames")
    add("no flash frames", fl == [], "none" if fl == [] else (f"stray frames at {[f['t'] for f in fl][:8]} s" if fl else "not measured: rerun qc"))
    c = qc.get("circles") or {}
    add("circles stay round", c and not c.get("fail_frames"), f"{c.get('frames', '?')} frames, worst {round(100 * (c.get('worst') or [0])[0], 2)} %")
    tm = rep.get("textMin"); need = WANT["caption_px"][tut]
    add("big readable text", tm is not None and tm >= need, f"smallest caption/title text {tm} px (>= {need} px at {W}x{H})")
    dash = [s for s in all_text(tut, lang) if re.search("[\\u2013\\u2014]", s)]
    add("no long dashes", not dash, "ok" if not dash else "; ".join(dash[:3]))
    pk = audio_peak(f)
    add("soft sound", pk is not None and -40 < pk <= WANT["peak_db"], f"peak {pk} dBFS (clicks present, <= {WANT['peak_db']} dBFS)")
    mk = C.load_json(d / "review.json", {}) or {}
    fresh = mk.get("mtime") == round(f.stat().st_mtime, 1)
    add("visual review", fresh, mk.get("note", "not reviewed") if fresh else "not reviewed since the last render: reel-tool tutorials mark " + f"{tut} {lang} \"...\"")
    ok = all(r["ok"] for r in rows)
    C.save_json(d / "gate.json", {"pass": ok, "rows": rows})
    for r in rows:
        print(f"{'PASS' if r['ok'] else 'FAIL'}  {r['check']}: {r['detail']}")
    print(f"GATE {tut} {lang}: {'PASS' if ok else 'FAIL'} ({sum(r['ok'] for r in rows)}/{len(rows)})   sheet: {d / 'final_qc_sheet.jpg'}")
    machine_ok = all(r["ok"] for r in rows if r["check"] != "visual review")
    if machine_ok:                                              # the copy in the plugin is replaced only by a render that passes
        out = C.ROOT / sp["out"].replace("{lang}", lang); out.parent.mkdir(parents=True, exist_ok=True)
        ship = d / "ship.mp4"                                   # compact copy of the gated master: flat graphics compress well
        if not ship.exists() or ship.stat().st_mtime < f.stat().st_mtime:
            r = C.ff("-i", str(f), "-c:v", "libx264", "-preset", "slow", "-crf", str(sp.get("ship_crf", 28)), "-tune", "animation", "-pix_fmt", "yuv420p",
                     "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(ship))
            if r.returncode:
                C.fail("could not encode the shipped copy: " + r.stderr[-300:])
        if not out.exists() or out.read_bytes() != ship.read_bytes():
            shutil.copyfile(ship, out)
        print("copied to", out, f"({out.stat().st_size / 1e6:.1f} MB)")
    return ok


def mark(tut, lang, note):
    d = BUILD / f"{tut}-{lang}"; f = d / "final.mp4"
    if not f.exists():
        C.fail(f"no render for {tut} {lang}")
    C.save_json(d / "review.json", {"note": note, "mtime": round(f.stat().st_mtime, 1)})
    print(f"review recorded for {tut} {lang}")


def main(argv):
    if not argv or argv[0] not in ("build", "mark", "gate"):
        print(__doc__); return
    cmd, rest = argv[0], argv[1:]
    pre = rest[rest.index("--preview") + 1] if "--preview" in rest else None
    pos = [x for x in rest if not x.startswith("--") and x != pre]
    tuts = ["t1", "t2"] if not pos or pos[0] == "all" else [pos[0]]
    langs = LANGS if len(pos) < 2 or pos[1] == "all" else [pos[1]]
    for t in tuts:
        for l in langs:
            if cmd == "build":
                build(t, l, pre)
            elif cmd == "gate":
                gate(t, l)
            else:
                mark(t, l, pos[2] if len(pos) > 2 else "looked at the frame sheet")


if __name__ == "__main__":
    main(sys.argv[1:])
