"""reel-tool scan [files...] [--job NAME] [--note "what the user asked"] [--extend OLD_JOB]

Step 1 of every job: work out what the user means when they say "edit this".
Finds the clips (named ones, or the newest unused batch in the input folder), reads their metadata, hashes their audio, and
compares against everything seen before, so a re-upload or a duplicate is never edited twice by accident.
Creates <work>/<job>/job.json and prints a digest for the brief.

A batch = video files in one folder, filmed or copied within 45 minutes of each other. Notes next to the clips (any .txt)
are read as the user's instructions for that batch.
"""
import hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

import common as C

BATCH_GAP = 45 * 60
SKIP_DIRS = {"reels-done", "reels-work", "_old", "node_modules", ".git", ".claude", "__pycache__"}


def audio_hash(path) -> str:
    """md5 of the decoded-free audio packets: survives re-exports that only change metadata or container"""
    r = subprocess.run([C.FF, "-v", "error", "-i", str(path), "-map", "0:a:0", "-c", "copy", "-f", "streamhash", "-hash", "md5", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"MD5=([0-9a-f]+)", r.stdout)
    return m.group(1) if m else ""


def info(path) -> dict:
    p = Path(path); j = C.probe(p); fmt = j.get("format", {}); tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
    vs = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in j.get("streams", []) if s.get("codec_type") == "audio"), None)
    st = {k.lower(): v for k, v in (vs.get("tags") or {}).items()}
    rot = 0
    for sd in vs.get("side_data_list") or []:
        rot = int(sd.get("rotation", rot) or rot)
    rot = int(st.get("rotate", rot) or rot)
    w, h = int(vs.get("width") or 0), int(vs.get("height") or 0)
    if abs(rot) % 180 == 90:
        w, h = h, w
    fr = str(vs.get("avg_frame_rate") or "0/1").split("/")
    fps = round(float(fr[0]) / float(fr[1]), 2) if len(fr) == 2 and float(fr[1] or 0) else 0
    device = " ".join(x for x in (tags.get("com.apple.quicktime.make"), tags.get("com.apple.quicktime.model")) if x) or \
        " ".join(x for x in (tags.get("make"), tags.get("model")) if x) or tags.get("com.android.manufacturer") or None
    return {"file": str(p), "name": p.name, "size_mb": round(p.stat().st_size / 1048576, 1), "mtime": p.stat().st_mtime,
            "duration": round(float(fmt.get("duration") or 0), 2), "width": w, "height": h, "fps": fps, "rotation": rot,
            "audio_kbps": round(int(a.get("bit_rate") or 0) / 1000) if a else None, "audio_ch": a.get("channels") if a else None,
            "codec": vs.get("codec_name"), "hdr": vs.get("color_transfer") in ("arib-std-b67", "smpte2084"),
            "transfer": vs.get("color_transfer"), "has_audio": a is not None, "device": device,
            "created": tags.get("com.apple.quicktime.creationdate") or tags.get("creation_time")}


def is_render(path) -> bool:
    """our own finished Reels (tagged at render) and files recorded as delivered are never sources"""
    tags = {k.lower(): v for k, v in (C.probe(path).get("format", {}).get("tags") or {}).items()}
    if "reel studio" in str(tags.get("comment", "")).lower():
        return True
    outs = {str(Path(j.get("output", ""))).lower() for j in (C.load_json(C.JOBS_LEDGER, {"jobs": []}) or {}).get("jobs", [])}
    return str(Path(path)).lower() in outs or Path(path).name.lower() == "final.mp4"


def walk(folder):
    out = []
    for r, ds, fs in os.walk(folder):
        if "job.json" in fs:                               # a job folder, wherever it sits: renders, not sources
            ds[:] = []
            continue
        ds[:] = [d for d in ds if d not in SKIP_DIRS and not d.startswith(".")]
        for f in fs:
            if Path(f).suffix.lower() in C.VIDEO_EXT and not is_render(Path(r) / f):
                out.append(Path(r) / f)
    return out


def batches(files):
    by = {}
    for f in files:
        by.setdefault(f.parent, []).append(f)
    out = []
    for parent, fl in by.items():
        fl = sorted(fl, key=lambda p: p.stat().st_mtime); cur = [fl[0]]
        for f in fl[1:]:
            if f.stat().st_mtime - cur[-1].stat().st_mtime > BATCH_GAP:
                out.append(cur); cur = []
            cur.append(f)
        out.append(cur)
    return sorted(out, key=lambda b: b[-1].stat().st_mtime, reverse=True)


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    drop = set()
    for k in ("--job", "--note", "--brand", "--format", "--input", "--extend"):
        if k in argv:
            i = argv.index(k); drop |= {i, i + 1}
    named = [a for i, a in enumerate(argv) if i not in drop and not a.startswith("--")]
    cfg = C.config(); F = C.folders(cfg)
    ledger = C.load_json(C.INPUTS_LEDGER, {"clips": {}}) or {"clips": {}}
    picked_by = "named"
    if named:
        clips = []
        for n in named:
            p = (C.PROJECT / n).resolve()                  # absolute: later steps run from the job folder
            clips += sorted(q for q in p.rglob("*") if q.suffix.lower() in C.VIDEO_EXT) if p.is_dir() else [p]
        missing = [str(c) for c in clips if not c.exists()]
        if missing:
            C.fail("not found: " + ", ".join(missing))
    else:
        folder = Path(opt("--input") or F["input"])
        all_files = walk(folder)
        if not all_files:
            C.fail(f"no video files in {folder}: name a file or set input_folder with /reel-setup")
        bs = batches(all_files); clips = None
        for b in bs:                                       # the newest batch that was not edited yet
            if not all(audio_hash(f) in ledger["clips"] for f in b):
                clips, picked_by = b, "newest unused batch"
                break
        if clips is None:
            clips, picked_by = bs[0], "newest batch (ALL its clips were edited before)"
    if not clips:
        C.fail("no clips")
    old = None
    if opt("--extend"):                                    # a correction: the new takes join the old clips, the last clean take wins
        od = C.job_dir(opt("--extend")); old = C.load_json(od / "job.json") or C.fail("no such job: " + opt("--extend"))
        moved = []
        for c in map(Path, old["clips"]):
            if not c.exists():
                hits = [q for q in C.PROJECT.rglob(c.name) if q.is_file() and "reels-work" not in q.parts]
                if not hits:
                    C.fail(f"the original clip {c.name} is gone from {c.parent}: put it back in the project folder, or use a new job with the clips you have")
                c = hits[0]
            moved.append(c)
        clips = moved + [c for c in clips if str(c) not in old["clips"] and c not in moved]
    infos = [info(c) for c in clips]
    try:
        import stabilize
        for x in infos:
            x["shake_px"] = stabilize.jitter(x["file"], frames=300)
    except Exception:
        pass
    seen_here, dups = {}, []
    for x in infos:
        h = audio_hash(x["file"]) if x["has_audio"] else ""
        x["audio_md5"] = h
        if h and h in seen_here:
            x["duplicate_of"] = seen_here[h]; dups.append(x["name"])
        elif h:
            seen_here[h] = x["name"]
        prev = ledger["clips"].get(h) if h else None
        if prev and not old:
            x["seen_before"] = prev
    use = [x for x in infos if not x.get("duplicate_of")]
    notes = []
    for d in {Path(x["file"]).parent for x in infos}:
        for t in d.glob("*.txt"):
            try:
                notes.append({"file": str(t), "text": t.read_text(encoding="utf-8-sig", errors="replace").strip()[:2000]})
            except OSError:
                pass
    photos = sorted({str(q) for x in infos for q in Path(x["file"]).parent.iterdir() if q.suffix.lower() in C.IMAGE_EXT})[:40]
    stamp = time.strftime("%Y-%m-%d_%H%M")
    name = opt("--job") or f"{stamp}_{C.slugify(Path(use[0]['name']).stem)}"
    job = F["work"] / name; job.mkdir(parents=True, exist_ok=True)
    wants = C.brand_list()
    match = []
    for slug in wants:
        b = C.load_json(C.BRANDS / slug / "brand.json", {}) or {}
        m = b.get("match") or {}
        s = sum(1 for x in use if x["device"] and x["device"] in (m.get("devices") or []))
        match.append({"brand": slug, "name": b.get("name"), "device_hits": s, "languages": m.get("languages") or [], "devices": m.get("devices") or []})
    J = {"job": name, "created": stamp, "picked_by": picked_by, "clips": [x["file"] for x in use], "info": infos, "duplicates": dups, "notes": notes,
         "photos": photos, "user_request": opt("--note", ""), "format": opt("--format"), "brand": opt("--brand"),
         "brands_available": match, "default_brand": cfg.get("default_brand")}
    if old:
        import shutil
        J.update({"extends": old["job"], "brand": J["brand"] or old.get("brand"), "format": J["format"] or old.get("format"), "picked_by": "correction of " + old["job"]})
        for f in ("visuals.json", "edit.json", "script.txt"):
            if (od / f).exists():
                shutil.copy2(od / f, job / (("old_" + f) if f == "visuals.json" else f))
        if (od / "scenes").is_dir() and not (job / "scenes").exists():
            shutil.copytree(od / "scenes", job / "scenes")
    C.save_json(job / "job.json", J)
    print(f"job: {name}\nfolder: {job}\npicked: {J['picked_by']}")
    for x in infos:
        flags = [k for k in ("hdr",) if x.get(k)] + (["DUPLICATE of " + x["duplicate_of"]] if x.get("duplicate_of") else []) + \
            ([f"EDITED BEFORE in job {x['seen_before'].get('job')}"] if x.get("seen_before") else []) + ([] if x["has_audio"] else ["NO AUDIO"])
        ar = x["width"] / x["height"] if x["height"] else 0
        if (x.get("shake_px") or 0) > 0.8:
            flags.append(f"hand-held, shake {x['shake_px']} px (try reel-tool stabilize)")
        if abs(ar - 9 / 16) > 0.02:
            flags.append("not 9:16 (will be cropped around the face)")
        print(f"  {x['name']}: {x['duration']:.1f} s {x['width']}x{x['height']} {x['fps']} fps {x['codec']} {x['size_mb']} MB "
              f"device={x['device']} {' | '.join(flags)}")
    for n in notes:
        print("  note:", n["text"][:300].replace("\n", " / "))
    if photos:
        print(f"  photos next to the clips: {len(photos)}")
    if not wants:
        print("brands: none yet (the neutral default look will be used; /reel-brand makes one)")
    for m in match:
        print(f"brand {m['brand']}: languages {', '.join(m['languages']) or 'any'}; devices {', '.join(m['devices']) or 'any'}; "
              f"{m['device_hits']} of {len(use)} clips from its device" + ("  (default)" if m["brand"] == cfg.get("default_brand") else ""))
    print("next: reel-tool analyze", name)


if __name__ == "__main__":
    main(sys.argv[1:])
