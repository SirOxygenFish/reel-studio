"""reel-tool analyze <job>: from raw clips to a proposed cut.

Whisper (three passes, see autoedit/speech.py) -> takes (retakes, false starts, spoken notes to self, fillers;
autoedit/takes.py) -> tightened pieces (the pause rule below) -> cut.json + derived words.json, transcript.txt, decisions.md.
It also reports what the brief needs: language, one voice or two (skit), and whether this is a retake of an earlier Reel.

cut.json is the single source of truth of the edit, in SOURCE seconds:
    {"lang": "en", "skit": false, "pieces": [{"file": <abs path>, "a": 1.2, "b": 4.8, "joint": "clip|take|jump",
                                              "words": [[s, e, text, p], ...]}, ...]}
`reel-tool recut` changes it and everything derived is rebuilt, so subtitles can never drift from the picture.

The pause rule (house rule, every monologue): a piece starts at the first sound - 0.12 s and ends at the last sound + 0.15 s
(the final piece + 0.55 s, so the Reel does not end on a clipped breath); silences >= 0.36 s inside a piece are cut down to
0.15 s on each side, so pauses land at 0.2-0.35 s and no "waiting face" (mouth open, silent, before a word) survives.
Silence is measured from the audio itself (10 ms frames under -46 dB), never from speech-burst edges or Whisper word times:
a quiet word inside a "pause" would be cut. `reel-tool wordcheck` then re-hears the whole cut and lists any word that went missing.
Skits are never tightened: the pauses are timing, and cutting them jumps the hands.
"""
import json, os, re, sys, wave
from pathlib import Path
import numpy as np

import common as C
from autoedit import speech, takes, words as W

SR = 16000
MIN_SIL, EDGE_KEEP, FIRST_PAD, TAIL_PAD, END_TAIL = 0.36, 0.15, 0.12, 0.15, 0.55


def load_audio(path):
    from autoedit import audio as A
    return A.load(path)


def out_time_map(pieces):
    offs, o = [], 0.0
    for p in pieces:
        offs.append(o); o += p["b"] - p["a"]
    return offs, o


def derive(job: Path, cut: dict):
    """cut.json -> words.json (Reel time), cuts.json ([[file, a, b], ...]), transcript.txt"""
    pieces = cut["pieces"]
    for p in pieces:                                       # whole frames: Reel time = picture time, no drift over many joins
        p["b"] = round(p["a"] + max(1, round((p["b"] - p["a"]) * 30)) / 30, 4)
    C.save_json(job / "cut.json", cut)
    offs, total = out_time_map(pieces)
    out = []
    for p, off in zip(pieces, offs):
        for w in p["words"]:
            s = max(w[0], p["a"]) - p["a"] + off; e = min(w[1], p["b"]) - p["a"] + off
            out.append([round(s, 3), round(max(e, s + 0.05), 3), w[2], (w[3] if len(w) > 3 else 1.0)])
    C.save_json(job / "words.json", {"total": round(total, 3), "words": out})
    C.save_json(job / "cuts.json", [[p["file"], round(p["a"], 3), round(p["b"], 3)] for p in pieces])
    sents, cur = [], []
    for w in out:
        cur.append(w)
        if re.search(r"[.?!…]$", w[2]):
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    lines = [f"{c[0][0]:6.2f}-{c[-1][1]:6.2f}  " + " ".join(x[2] for x in c) for c in sents]
    (job / "transcript.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return total, sents


def tighten(pieces, clips, skit=False):
    """the pause rule, on the frame levels of the clip's speech analysis"""
    out = []
    for k, p in enumerate(pieces):
        cs = clips[Path(p["file"]).name]; fdb = np.asarray(cs.get("fdb") or [], float); hop = 0.01
        if skit or not fdb.size:
            out.append(p); continue
        loud = fdb[fdb > -70]
        shift = min(0.0, float(np.percentile(loud, 90)) + 30) if loud.size else 0.0    # only quiet recordings move the thresholds
        voice_thr, sil_thr = -42 + shift, -46 + shift           # cut only TRUE silence: quiet words ("that", "it", endings) sit at -40..-45
        a, b = p["a"], p["b"]
        i0, i1 = int(a / hop), min(int(b / hop), fdb.size)
        seg = fdb[i0:i1]
        voiced = np.where(seg > voice_thr)[0]
        if not voiced.size:
            continue
        on, of = a + voiced[0] * hop, a + voiced[-1] * hop + 0.02
        last = k == len(pieces) - 1 or Path(pieces[k + 1]["file"]) != Path(p["file"]) and k == len(pieces) - 1
        a2 = round(on - FIRST_PAD, 3) if on - a > FIRST_PAD + 0.02 else a
        keep = END_TAIL if last else TAIL_PAD
        b2 = round(of + keep, 3) if b - of > keep + 0.02 else b
        if last and b - of < END_TAIL:                      # the clip's own tail, up to END_TAIL, when the take cut it short
            b2 = round(min(of + END_TAIL, float(cs.get("dur") or b)), 3)
        runs, s = [], None
        for j, v in enumerate(seg < sil_thr):
            t = a + j * hop
            if v and s is None:
                s = t
            if not v and s is not None:
                if t - s >= MIN_SIL and s > a2 + 0.3 and t < b2 - 0.3:
                    runs.append((s, t))
                s = None
        st = a2; parts = []
        for s0, s1 in runs:
            parts.append((st, round(s0 + EDGE_KEEP, 3))); st = round(s1 - EDGE_KEEP, 3)
        parts.append((st, b2))
        # a word goes to the part it overlaps most: Whisper's word edges are loose, so a word's middle can fall in a removed pause
        share = [[] for _ in parts]
        for w in p["words"]:
            ov = [min(w[1], y) - max(w[0], x) for x, y in parts]
            k2 = int(np.argmax(ov))
            x, y = parts[k2]
            s_, e_ = max(w[0], x), min(w[1], y)
            share[k2].append([s_, e_ if e_ > s_ else s_ + 0.05] + list(w[2:]))
        for j, (x, y) in enumerate(parts):
            out.append({"file": p["file"], "a": x, "b": y, "joint": p.get("joint", "clip") if j == 0 else "jump", "words": share[j]})
    return out


def f0_track(x):
    """median pitch per 40 ms voiced frame, simple normalised autocorrelation, 70-400 Hz"""
    n, hop = int(0.04 * SR), int(0.02 * SR); lo, hi = SR // 400, SR // 70; out = []
    for i in range(0, len(x) - n - hi, hop):
        f = x[i:i + n + hi]; e = float(np.sqrt(np.mean(f[:n] ** 2)))
        if e < 0.008:
            continue
        f = f - f.mean(); a = f[:n]
        c = np.array([np.dot(a, f[l:l + n]) for l in range(lo, hi, 2)])
        d = np.sqrt(np.sum(a ** 2) * np.array([np.sum(f[l:l + n] ** 2) for l in range(lo, hi, 2)])) + 1e-9
        r = c / d; k = int(np.argmax(r))
        if r[k] > 0.6:
            out.append(SR / (lo + 2 * k))
    return out


def voices(audio_by_file, units):
    """one speaker or two? pitch per sentence unit, 2-means on log f0"""
    pts = []
    for u in units:
        if u.get("gone") or not u.get("words"):
            continue
        a = audio_by_file.get(u["file"])
        if a is None:
            continue
        s, e = u["words"][0][0], u["words"][-1][1]
        if e - s < 0.4:
            continue
        f = f0_track(a[int(s * SR):int(e * SR)])
        if len(f) >= 6:
            pts.append((float(np.median(f)), e - s, u))
    if len(pts) < 4:
        return {"voices": 1, "f0": [round(p[0]) for p in pts], "split": None}
    v = np.log(np.array([p[0] for p in pts])); c0, c1 = np.percentile(v, 15), np.percentile(v, 85)
    for _ in range(12):
        m = np.abs(v - c0) <= np.abs(v - c1)
        if m.all() or (~m).all():
            break
        c0, c1 = v[m].mean(), v[~m].mean()
    share = float(min(m.mean(), 1 - m.mean())); ratio = float(np.exp(abs(c1 - c0)))
    two = share >= 0.2 and ratio >= 1.7       # measured: a skit 1.92; monologues up to 1.56 (octave errors of the tracker)
    return {"voices": 2 if two else 1, "low_hz": round(float(np.exp(min(c0, c1)))), "high_hz": round(float(np.exp(max(c0, c1)))),
            "minor_share": round(share, 2), "ratio": round(ratio, 2),
            "assign": [{"file": Path(p[2]["file"]).name, "s": round(p[2]["words"][0][0], 2), "hz": round(p[0]),
                        "voice": "low" if (m[i] == (c0 < c1)) else "high"} for i, p in enumerate(pts)] if two else None}


def retake_of(text, lang):
    """does this repeat an earlier job? whole script = a re-shoot; a short part of it = a correction of that Reel"""
    best = None
    for j in (C.load_json(C.JOBS_LEDGER, {"jobs": []}) or {}).get("jobs", []):
        old = j.get("transcript", "")
        sim = W.seq_sim(text, old); part = W.contains(text, old) if len(W.tokens(text)) >= 4 else 0.0
        kind = "reshoot" if sim >= 0.6 else "correction" if part >= 0.6 else None
        if kind and (best is None or max(sim, part) > best["similarity"]):
            best = {"kind": kind, "job": j.get("job"), "name": j.get("name"), "output": j.get("output"), "similarity": round(max(sim, part), 2)}
    return best


def merge_correction(old_cut, new_pieces):
    """A correction keeps the finished cut: each new sentence replaces the old lines it re-says; what matches nothing goes first, for
    Claude to place (recut --move). Returns the cut and a list of what happened."""
    from recut import drop_range
    cut = {"lang": old_cut.get("lang"), "skit": old_cut.get("skit"), "pieces": [dict(p) for p in old_cut["pieces"]]}
    flat = [(k, w) for k, p in enumerate(new_pieces) for w in p["words"]]
    sents, cur = [], []
    for it in flat:
        cur.append(it)
        if re.search(r"[.?!…]$", it[1][2]):
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    log, top = [], 0

    def slices(S):
        out = []
        for k in sorted({x[0] for x in S}):
            ws = [x[1] for x in S if x[0] == k]; p = new_pieces[k]
            a = p["a"] if ws[0] is p["words"][0] else ws[0][0] - 0.1
            b = p["b"] if ws[-1] is p["words"][-1] else ws[-1][1] + 0.12
            out.append({"file": p["file"], "a": round(a, 3), "b": round(b, 3), "joint": "take", "words": ws})
        return out
    for S in sents:
        T = W.tokens(" ".join(x[1][2] for x in S))
        offs, _ = out_time_map(cut["pieces"]); olds = []
        for p, off in zip(cut["pieces"], offs):
            for w in p["words"]:
                olds.append((w, off + w[0] - p["a"], off + w[1] - p["a"]))
        O = [(tok, i) for i, x in enumerate(olds) for tok in W.tokens(x[0][2])]
        from difflib import SequenceMatcher
        blocks = [b for b in SequenceMatcher(None, T, [t for t, _ in O], autojunk=False).get_matching_blocks() if b.size >= 2]
        hit = sum(b.size for b in blocks) / max(1, len(T))
        text = " ".join(x[1][2] for x in S)
        if blocks and hit >= 0.6 and len(T) >= 3:
            i0, i1 = O[blocks[0].b][1], O[blocks[-1].b + blocks[-1].size - 1][1]
            a, b = max(0, olds[i0][1] - 0.1), olds[i1][2] + 0.12
            said = " ".join(x[0][2] for x in olds[i0:i1 + 1])
            drop_range(cut, a, b)
            offs, _ = out_time_map(cut["pieces"])
            k = next((n for n, o in enumerate(offs) if o >= a - 0.02), len(cut["pieces"]))
            cut["pieces"][k:k] = slices(S)
            log.append(f'replaced "{said}" with "{text}"')
        else:
            cut["pieces"][top:top] = slices(S); top += len(slices(S))
            log.append(f'NEW LINE, placed at the start: "{text}" (move it with recut --move if it belongs elsewhere)')
    return cut, log


def main(argv):
    job = C.job_dir(argv[0]); J = C.load_json(job / "job.json") or C.fail(f"no job.json in {job}: run reel-tool scan first")
    clips = [str(c) for c in J["clips"]]; cfg = C.config()
    base = None
    if J.get("extends"):                                   # a correction: only the new clips are analysed, the finished cut stays
        od = C.job_dir(J["extends"]); base = C.load_json(od / "cut.json") or C.fail("the corrected job has no cut.json")
        now = {Path(c).name: str(c) for c in J["clips"]}
        for p in base["pieces"]:
            p["file"] = now.get(Path(p["file"]).name, p["file"])    # the clips may have moved since
        had = {Path(p["file"]).name for p in base["pieces"]}
        clips = [c for c in clips if Path(c).name not in had]
        J["lang"] = J.get("lang") or base.get("lang")
        if not clips:
            C.fail("no new clip in this correction")
    lang = next((argv[i + 1] for i, a in enumerate(argv) if a == "--lang"), None) or J.get("lang")
    script = None
    sp = job / "script.txt"
    if sp.exists():
        script = sp.read_text(encoding="utf-8")
    model = cfg.get("whisper_model", "large-v3")
    auds = {}
    print(f"analyze: {len(clips)} clip(s)", flush=True)
    with speech.WhisperSession(model) as sess:
        for f in clips:
            auds[f] = load_audio(f)
        if not lang or lang == "auto":
            lang = speech.choose_language(sess, {Path(f).name: a for f, a in auds.items()}, script)
        print("language:", lang, flush=True)
        cs = {}
        for f in clips:
            r = speech.analyze_clip(sess, f, lang, use_cache=True)
            r["file"] = Path(f).name; cs[Path(f).name] = r
    res = takes.analyze(cs, script=script, lang=lang)
    paths = {Path(f).name: f for f in clips}
    v = voices({Path(f).name: a for f, a in auds.items()}, res["units"])
    skit = v["voices"] == 2 or "--skit" in argv
    if "--no-skit" in argv:
        skit = False
    raw = [{"file": paths[p["file"]], "a": p["start"], "b": p["end"], "joint": p["joint"], "words": p["words"]} for p in res["pieces"]]
    if not raw:
        C.fail("no speech found in these clips: Reel Studio edits talking videos. Check the clips have sound.")
    pieces = tighten(raw, cs, skit)
    cut = {"lang": lang, "skit": skit, "pieces": pieces}
    merged_log = []
    if base is not None:
        cut, merged_log = merge_correction(base, pieces); skit = bool(base.get("skit"))
        for m in merged_log:
            print("correction:", m)
    total, sents = derive(job, cut)
    before = sum(float(c.get("dur") or 0) for c in cs.values())
    dec = ["# What the automatic pass left out", ""] + ["- " + d for d in merged_log + res["decisions"]]
    if res["questions"]:
        dec += ["", "# Decisions it was unsure about (default taken)", ""]
        for q in res["questions"]:
            dec.append(f"- {q.get('text', q)}  options: {[o.get('label') for o in q.get('options', [])]}")
    (job / "decisions.md").write_text("\n".join(dec) + "\n", encoding="utf-8")
    text = " ".join(" ".join(x[2] for x in s) for s in sents)
    re_of = None if base is not None else retake_of(text, lang)
    pieces = cut["pieces"]
    if base is not None:
        before = sum(pp["b"] - pp["a"] for pp in base["pieces"])
    noise = [float(c.get("floor_db") or -90) for c in cs.values()]
    J.update({"lang": lang, "skit": skit, "voices": v, "retake_of": re_of, "raw_seconds": round(before, 2), "cut_seconds": total,
              "pieces": len(pieces), "noise_floor_db": round(min(noise), 1) if noise else None, "questions": res["questions"]})
    C.save_json(job / "job.json", J)
    print(f"cut: {before:.1f} s raw -> {total:.2f} s, {len(pieces)} pieces, {len(sents)} sentences")
    print("voices:", json.dumps({k: x for k, x in v.items() if k != "assign"}))
    if re_of:
        print("RETAKE of an earlier job:", json.dumps(re_of, ensure_ascii=False))
    if res["questions"]:
        print("unsure decisions:", len(res["questions"]), "(see decisions.md)")
    print("next: read transcript.txt and decisions.md, then reel-tool brief", job.name)


if __name__ == "__main__":
    main(sys.argv[1:])
