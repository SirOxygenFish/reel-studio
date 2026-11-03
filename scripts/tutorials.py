"""reel-tool tutorials: rebuilds the two bundled tutorials (motion graphics made with the engine, no voice, soft clicks).

    reel-tool tutorials build [t1|t2|all] [en|ru|pl|all] [--preview 1.5,8,20]   render + QC + gate; copies a passing video into the plugin
    reel-tool tutorials mark t1|t2 en|ru|pl|all "what I checked"                    record the visual review of the frame sheet
    reel-tool tutorials gate [t1|t2|all] [en|ru|pl|all]                             the gate alone (after a mark)

Sources: motion/tutorials/kit.js (drawings + action player), t1.json / t2.json (timelines), strings.json (all texts).
Tutorial 1 (PC, 16:9) goes to docs/tutorials/, Tutorial 2 (iPhone, 9:16) to upload-page/tutorials/ (played offline by the page).
The tutorial gate keeps the Reel gate's rules where they apply (format, motion never dead for > 1 s, nothing outside the frame,
round things round, no long dashes, sound peaks, a visual review) and drops the Instagram ones (subtitle band, caption strip).
"""
import json, os, re, shutil, subprocess, sys, wave
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


def storyboard(tut, lang):
    sp, tb = spec(tut), texts(tut, lang)
    W, H = sp["size"]
    scenes, cues = [], []
    for sc in sp["scenes"]:
        s = resolve({k: v for k, v in sc.items()}, tb)
        s["labels"] = tb
        s["camera"] = {"z0": 1.0, "z1": 1.025}                  # calm: a slow push-in only
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
    add("length", WANT["len"][0] <= dur <= WANT["len"][1], f"{dur:.1f} s (30-45 s)")
    m = qc.get("motion", {})
    add("calm but never still", m.get("median", 0) >= WANT["motion"] and not qc.get("dead_runs"),
        f"motion median {m.get('median')} (>= {WANT['motion']}), dead stretches > {WANT['dead']} s: {qc.get('dead_runs') or 'none'}")
    add("inside the frame", qc.get("safe_issue_count", 0) == 0, f"{qc.get('safe_issue_count', '?')} issues")
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
            r = C.ff("-i", str(f), "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-tune", "animation", "-pix_fmt", "yuv420p",
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
