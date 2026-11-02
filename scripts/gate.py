"""reel-tool gate <job>: the non-negotiable quality gates. A Reel that fails is not delivered; `deliver` refuses it.

Writes gate.json with the hash of final.mp4, so a later change to the file voids the pass.
Every check prints PASS or FAIL with what to do about a failure.
"""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

import common as C
from autoedit import words as W

# claims that may never appear as on-screen text, whatever was said (health results, income promises)
CLAIMS = [r"\bcures?\b", r"\bheals?\b", r"\btreats?\b", r"\bguarantee", r"\bmiracle", r"\brisk[- ]free\b", r"\bget rich\b", r"\bpassive income\b",
          r"\b\d[\d.,]*\s?(k|€|\$|£|usd|eur|pln|zł)\s*(a|per|/)\s*(day|week|month)", r"\bleczy\b", r"\buzdrawia", r"\bgwarant", r"\bcud(owny|ownie)?\b",
          r"\bлечит\b", r"\bизлеч", r"\bгарант", r"\bзаработ\w* \d", r"\bheilt\b", r"\bgarantiert\b", r"\bcura\b", r"\bgarantizad"]
WANT = {"motion": 1.5, "anim_motion": 1.8, "still": 0.08, "lufs": (-14.6, -13.4), "tp": -0.9, "sim": 0.85}


class Gate:
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail="", fix=""):
        self.rows.append({"check": name, "ok": bool(ok), "detail": detail, "fix": "" if ok else fix})
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}" + ("" if ok or not fix else f"\n      fix: {fix}"), flush=True)


def on_screen_texts(V, E):
    """everything visible that is not a subtitle"""
    out = list(E.get("title") or [])
    for b in V.get("beats", []):
        if "pop" in b:
            out.append(b["pop"])
        for it in b.get("items", []):
            if "label" in it:
                out.append(it["label"])
    KEYS = {"label", "text", "title", "heading", "lines", "sub", "caption", "word", "name", "tag"}

    def walk(o, key=None):
        if isinstance(o, dict):
            for k, v in o.items():
                if k not in ("meta", "icon", "type", "in", "src", "peep", "at"):
                    walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, str) and (key in KEYS or (key or "").endswith("Text")) and not o.startswith(("ph:", "tb:", "noto:")):
            out.append(o)
    for s in (V.get("hybrid") or {}).get("segments", []):
        walk(s.get("scenes"))
    for s in C.load_json("storyboard.json", {}).get("scenes", []) if Path("storyboard.json").exists() else []:
        walk(s)
    return [t for t in out if isinstance(t, str)]


def anim_motion(f, segs):
    """qc.py's motion measure (15 fps, 1/8 scale, subtitle band and bottom strip out), median inside the animation only"""
    import numpy as np
    if not segs:
        return None
    r = subprocess.run([C.FF, "-v", "error", "-i", f, "-vf", "fps=15,scale=135:240:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    g = np.frombuffer(r, np.uint8).reshape(-1, 240, 135).astype(np.float32); m = np.ones((240, 135), bool); m[155:189] = False; m[195:] = False
    d = np.abs(np.diff(g, axis=0))[:, m].mean(1); t = np.arange(1, len(g)) / 15
    sel = np.array([any(s["t0"] + 0.5 <= x < s["t1"] - 0.5 for s in segs) for x in t])
    return round(float(np.median(d[sel])), 2) if sel.any() else None


def kept_split(J, segs):
    """a correction: segments whose scenes are exactly the delivered Reel's (same type and settings) were judged then; the rest are new"""
    if not J.get("extends"):
        return segs, []
    try:
        old = C.load_json(C.job_dir(J["extends"]) / "visuals.json", {}) or {}
    except SystemExit:
        return segs, []
    def bare(o):                                            # times move when the new lines change the cut's length: compare without them
        if isinstance(o, dict):
            return {k: bare(v) for k, v in o.items() if not (k in ("t0", "t1") or (k.lower().endswith("at") and isinstance(v, (int, float))))}
        return [bare(v) for v in o] if isinstance(o, list) else o
    key = lambda sc: json.dumps(bare(sc), sort_keys=True, ensure_ascii=False)
    was = {key(sc) for s in (old.get("hybrid") or {}).get("segments", []) for sc in s.get("scenes", [])}
    new = [s for s in segs if not all(key(sc) in was for sc in s.get("scenes", []))]
    return new, [s for s in segs if s not in new]


def loudness(f):
    r = C.ff("-i", f, "-af", "ebur128=peak=true", "-f", "null", "-")
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr); tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return float(i[-1]) if i else None, float(tp[-1]) if tp else None


def main(argv):
    job = C.job_dir(argv[0]).resolve(); os.chdir(job)
    if not Path("final.mp4").exists():
        C.fail("no final.mp4: run reel-tool render")
    J = C.job_sync(job); V = C.load_json("visuals.json", {}) or {}; E = C.load_json("edit.json", {}) or {}
    fmt = "faceless" if Path("storyboard.json").exists() else J.get("format") or "hybrid"; skit = bool(J.get("skit")) or fmt == "skit"
    B = C.brand(J.get("brand")); G = Gate()
    if fmt == "faceless":                                  # the variety rules apply scene by scene: each scene is a "segment"
        sb, rep = C.load_json("storyboard.json", {}), C.load_json("report.json", {}) or {}
        st = rep.get("scenes") or []
        segs = [{"t0": x.get("start", 0), "t1": x.get("end", 0), "scenes": [sc]} for sc, x in zip(sb.get("scenes", []), st)]
        V = {"hybrid": {"theme": B["slug"], "no_short": True, "segments": segs}}
        C.save_json("visuals_variety.json", V)
    hyb = bool((V.get("hybrid") or {}).get("segments")) and fmt != "faceless"
    name = C.job_name(job, J)

    j = C.probe("final.mp4"); vs = next(s for s in j["streams"] if s["codec_type"] == "video")
    aud = next((s for s in j["streams"] if s["codec_type"] == "audio"), None); fr = vs["avg_frame_rate"].split("/")
    fps = float(fr[0]) / float(fr[1] or 1); dur = float(j["format"]["duration"])
    G.add("format", vs["width"] == 1080 and vs["height"] == 1920 and abs(fps - 30) < 0.1 and vs["pix_fmt"] == "yuv420p" and vs["codec_name"] == "h264" and aud is not None,
          f"{vs['width']}x{vs['height']} {fps:.2f} fps {vs['codec_name']} {vs['pix_fmt']} audio {aud and aud['codec_name']}, {dur:.2f} s",
          "re-render: the output must be 1080x1920 30 fps H.264 yuv420p with audio")

    # QC: motion, dead stretches, coverage, safe zones, circles, variety
    args = [sys.executable, str(C.MOTION / "tools" / "qc.py"), "final.mp4"]
    if Path("report.json").exists() and fmt == "faceless":
        args += ["--report", "report.json", "--visuals", "visuals_variety.json", "--name", name, "--account", B["slug"]]
    elif hyb:
        args += ["--visuals", "visuals.json", "--name", name, "--account", B["slug"]]
    if C.replaced_names(J):
        args += ["--replaces", "|".join(C.replaced_names(J))]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=C.run_env())
    print(r.stdout.rstrip()); (r.returncode and r.stderr.strip()) and print(r.stderr[-800:])
    q = C.load_json("final_qc.json", {}) or {}
    m = q.get("motion") or {}
    if hyb or fmt == "faceless":
        G.add("motion", (m.get("median") or 0) >= WANT["motion"], f"median {m.get('median')} (target >= {WANT['motion']})",
              "scenes too static: add data-idle motion, camera moves, more elements arriving on words")
        if hyb or fmt == "faceless":
            segs = (V.get("hybrid") or {}).get("segments", []) if hyb else [{"t0": 0, "t1": dur}]
            new, kept = kept_split(J, segs) if hyb else (segs, [])
            if kept and not new:                             # a correction that kept every animation of the delivered Reel
                G.add("animation keeps moving", True, f"note: all {len(kept)} animations kept from the delivered Reel "
                      f"(median {anim_motion('final.mp4', kept)}), not judged again")
            else:
                am = anim_motion("final.mp4", new)
                G.add("animation keeps moving", am is not None and am >= WANT["anim_motion"],
                      f"median {am} inside the {'new ' if kept else ''}animation (target >= {WANT['anim_motion']})"
                      + (f"; {len(kept)} kept from the delivered Reel, not judged again" if kept else ""),
                      "the scenes are too calm: things should keep arriving on words, lines draw on, counters roll, objects drift (idle on every element); add a second beat to long scenes")
        G.add("dead stretches", not q.get("dead_runs"), f"{q.get('dead_runs') or 'none'} (> 1 s without motion)", "add idle motion or a visual change in that stretch")
    if "safe_issue_count" in q:
        G.add("safe zones", q["safe_issue_count"] == 0, f"{q['safe_issue_count']} issues", "move the elements listed in final_qc.json out of the subtitle band / top strip / frame edge")
    if "circles" in q:
        c = q["circles"]
        G.add("circles", not c.get("fail_frames"), f"{c['frames']} frames, worst {c['worst'][0] * 100:.2f} %", "a round element is squashed: give it flex:none, aspect-ratio 1, equal width and height, uniform scale")
    elif hyb:
        G.add("circles", False, "no circle data in the render reports", "render again; the engine writes reports next to the clips")
    if hyb or fmt == "faceless":
        v = q.get("variety") or {}
        G.add("variety", bool(v.get("pass")), f"bespoke {round((v.get('bespoke_share') or 0) * 100)} % of {v.get('segments')} segments; " + ("; ".join(v.get("fails", [])[:4]) or "no repeats"),
              "design new scenes; see the failed items")
        warn = [w for w in v.get("warns", []) if w.startswith("text:")]
        G.add("only spoken words on screen", not warn, ("; ".join(warn[:4]) or "ok"), "change the on-screen text to words that are spoken, or show a visual without text")
    if hyb:
        segs = V["hybrid"]["segments"]
        te = E.get("title_end", 7.0)
        if E.get("title"):
            G.add("title before animation", te <= segs[0]["t0"] + 0.01, f"title ends {te}, first animation {segs[0]['t0']}", f"reel-tool subs {job.name} --title-end {segs[0]['t0']}")
        ln = [s["t1"] - s["t0"] for s in segs]
        G.add("animation rhythm", all(2.5 <= x <= 10.5 for x in ln) and segs[0]["t0"] >= 1.5 and segs[-1]["t1"] <= dur - 1.5, "segments " + ", ".join(f"{x:.1f}" for x in ln) + " s",
              "3-8 s per animation, start and end on the face")

    vr_ = C.load_json("visuals_report.json", {}) or {}
    if Path("visuals.json").exists():
        dr = vr_.get("dropped") or []
        G.add("no dropped stickers or pops", not dr, "; ".join(f"{d[0]} s {d[2]} ({d[1]})" for d in dr[:4]) or "all placed",
              "shorten the label, lower the size, move the beat to a calmer moment, or take it out of visuals.json")
    wc = C.load_json("wordcheck.json")
    stale_wc = wc is not None and Path("cut.json").stat().st_mtime > Path("wordcheck.json").stat().st_mtime + 1
    M0 = C.load_json("reviews.json", {}) or {}
    ok_wc = wc is not None and not stale_wc and (not wc["missing"] or M0.get("words_at", 0) > Path("wordcheck.json").stat().st_mtime)
    G.add("no word lost in the cut", ok_wc, "not run" if wc is None else "older than the last recut" if stale_wc else
          ("; ".join(f"{m['at']} s \"{m['words']}\"" for m in wc["missing"][:4]) or f"all words there (similarity {wc['similarity']})") +
          (" (reviewed: " + M0.get("words", "") + ")" if wc["missing"] and ok_wc else ""),
          f"reel-tool wordcheck {job.name}; give a lost word back with recut --in/--out, or after listening record it: reel-tool mark {job.name} words \"...\"")
    import checks
    try:
        checks.jump(job)
        jr = C.load_json("jump_report.json") or {}
        if not skit:
            print(f"note  joins with a body jump on the final cut: {len(jr.get('jumps', []))} (soft blends cover them in a monologue)")
    except Exception as e:
        print("jump check failed:", e)
    # claims, dashes
    txt = on_screen_texts(V, E)
    bad = sorted({t for t in txt if any(re.search(p, t, re.I) for p in CLAIMS)})
    G.add("no health or income claims on screen", not bad, ", ".join(bad[:5]) or f"{len(txt)} texts checked", "remove these texts: claims stay out of the visuals, even when spoken")
    dash = [t for t in txt if re.search(r"[—–]", t)]
    G.add("no long dashes on screen", not dash, ", ".join(dash[:5]) or "ok", "use a comma or a line break")

    # loudness
    i, tp = loudness("final.mp4")
    lo, hi = WANT["lufs"]
    G.add("loudness", i is not None and lo <= i <= hi, f"{i} LUFS, peak {tp} dBFS", "the voice chain must run once on the raw voice; do not normalise twice")
    vr = C.load_json("voice_report.json", {}) or {}
    G.add("voice chain", "DeepFilterNet" in vr.get("denoiser", ""), vr.get("denoiser", "not run"), "run /reel-doctor: the main denoiser did not run (a fallback ran)")

    # speech: stutter passes on the cut and on the final, repeated phrases, coverage
    rep = C.load_json("stutter_report.json")
    stale = rep is not None and Path("cut.json").stat().st_mtime > Path("stutter_report.json").stat().st_mtime + 1
    G.add("stutter passes on the cut", rep is not None and not rep["confirmed"] and not stale, "not run" if rep is None else "older than the last recut" if stale else f"{len(rep['confirmed'])} confirmed, {len(rep['listen'])} to listen",
          f"reel-tool stutter {job.name}, then cut each confirmed flag with recut --drop")
    rc = subprocess.run([sys.executable, str(Path(__file__).parent / "stutter_check.py"), str(job), "--final"], capture_output=True, text=True, encoding="utf-8",
                        errors="replace", env=C.run_env())
    fin = C.load_json("stutter_final.json")
    G.add("stutter passes on the final", fin is not None and not fin["confirmed"], "failed to run: " + rc.stderr[-200:] if fin is None else f"{len(fin['confirmed'])} confirmed",
          "see stutter_final.json (times are final.mp4 seconds)")
    check_text(G, job)

    # picture reviews
    M = C.load_json("reviews.json", {}) or {}
    G.add("eye check", bool(M.get("eyes")), M.get("eyes") or "not reviewed", f"reel-tool sheets {job.name}, read qf/eyes.jpg, then reel-tool mark {job.name} eyes \"...\"")
    G.add("waiting-face check", bool(M.get("mouth")), M.get("mouth") or "not reviewed", f"read qf/mouth.jpg, then reel-tool mark {job.name} mouth \"...\"")
    fresh = M.get("visual_at", 0) >= Path("final.mp4").stat().st_mtime
    G.add("visual review", bool(M.get("visual")) and fresh, (M.get("visual") or "not reviewed") if fresh else "not reviewed since the last render",
          f"read final_qc_sheet.jpg and qf/segs.jpg, then reel-tool mark {job.name} visual \"...\"")
    if skit:
        jr = C.load_json("jump_report.json")
        G.add("no cuts through gestures", jr is not None and not jr["jumps"], "not run" if jr is None else f"{len(jr['jumps'])} jumps", f"reel-tool jump {job.name}, then move the joins")

    ok = all(r["ok"] for r in G.rows)
    h = hashlib.sha256(Path("final.mp4").read_bytes()).hexdigest()
    C.save_json("gate.json", {"pass": ok, "sha256": h, "rows": G.rows, "duration": dur, "lufs": i, "motion": m, "coverage": q.get("coverage"), "circles": q.get("circles"),
                              "bespoke": (q.get("variety") or {}).get("bespoke_share")})
    print(f"\nGATE {'PASS' if ok else 'FAIL'}: {sum(r['ok'] for r in G.rows)}/{len(G.rows)} checks passed")
    sys.exit(0 if ok else 1)


def check_text(G, job):
    """re-transcribe the finished Reel: no phrase may appear twice by accident, nothing may be missing"""
    from autoedit import speech
    exp = C.load_json("words.json")["words"]; expected = " ".join(w[2] for w in exp)
    lang = (C.load_json("cut.json", {}) or {}).get("lang", "en")
    from autoedit import audio as AU
    with speech.WhisperSession(C.config().get("whisper_model", "large-v3")) as sess:
        a = AU.load("final.mp4")
        segs, _ = sess._model.transcribe(a, language=lang, beam_size=5, vad_filter=True, word_timestamps=False, condition_on_previous_text=False)
        heard = " ".join(s.text.strip() for s in segs)
    (Path("final_transcript.txt")).write_text(heard + "\n", encoding="utf-8")
    t = W.tokens(heard); e = W.tokens(expected)
    grams = lambda x: [" ".join(x[i:i + 5]) for i in range(len(x) - 4)]
    from collections import Counter
    h5, e5 = Counter(grams(t)), Counter(grams(e))
    dup = [g for g, n in h5.items() if n > max(1, e5.get(g, 0))]
    G.add("no repeated phrases", not dup, "; ".join(dup[:3]) or "ok", "a phrase is said twice: cut the extra take")
    sim = W.seq_sim(heard, expected)
    G.add("speech matches the cut", sim >= WANT["sim"], f"similarity {sim:.2f}", "words were lost or changed: compare final_transcript.txt with transcript.txt")


if __name__ == "__main__":
    main(sys.argv[1:])
