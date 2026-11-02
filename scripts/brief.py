"""reel-tool brief <job>: writes job.md, the full job brief, from what scan and analyze found.

The facts are filled in; decisions Claude must make are marked TODO. reel-tool render refuses while a TODO line remains, so
no Reel is ever made without a complete brief, however short the user's request was.
"""
import json, sys
from pathlib import Path

import common as C


def main(argv):
    job = C.job_dir(argv[0]); J = C.load_json(job / "job.json") or C.fail("no job.json")
    if (job / "job.md").exists() and "--force" not in argv:
        print(f"job.md already exists: {job / 'job.md'} (--force rewrites it)"); return
    cut = C.load_json(job / "cut.json") or C.fail("no cut.json: run reel-tool analyze first")
    cfg = C.config(); skit = cut.get("skit"); re_of = J.get("retake_of")
    br = C.brand_list(); lang = cut.get("lang")
    best = None                                            # the brand whose device and language fit the clips; else the default
    for m in J.get("brands_available") or []:
        score = 2 * m.get("device_hits", 0) + (1 if lang in (m.get("languages") or []) else 0)
        if score and (best is None or score > best[0]):
            best = (score, m["brand"], m)
    B = C.brand(J.get("brand") or (best[1] if best else None))
    why = f"matched by {'device' if best[2].get('device_hits') else ''}{' and ' if best[2].get('device_hits') and lang in best[2].get('languages', []) else ''}{'language ' + lang if lang in best[2].get('languages', []) else ''}" if best else "the default"
    v = J.get("voices") or {}
    clips = "\n".join(f"- {x['name']}: {x['duration']} s, {x['width']}x{x['height']}, {x['fps']} fps, {x['device'] or 'device unknown'}"
                      + (", HDR" if x.get("hdr") else "") + (f", DUPLICATE of {x['duplicate_of']} (skipped)" if x.get("duplicate_of") else "")
                      + (f", edited before in job {x['seen_before'].get('job')}" if x.get("seen_before") else "") for x in J.get("info", []))
    notes = "\n".join("- " + n["text"].replace("\n", " ") for n in J.get("notes", [])) or "- none"
    fmt_default = "skit" if skit else (J.get("format") or cfg.get("default_format", "hybrid"))
    phone = any(x.get("audio_kbps") and x["audio_kbps"] < 100 or (x.get("height") or 9999) <= 854 and not x.get("device") for x in J.get("info", []))
    voice = "phone" if phone else "normal"
    pause = "not tightened: skit pauses are timing" if skit else "tightened: edges 0.12/0.15 s, silences >= 0.36 s cut to 0.3 s, last piece +0.55 s"
    doc = f"""# Job brief: {J['job']}

## Request
- User said: {J.get('user_request') or 'TODO: copy the request word for word'}
- Report language: TODO: the language the user wrote in
- Notes next to the clips:
{notes}

## Inputs
- Picked: {J.get('picked_by')}
{clips}
- Duplicates skipped: {', '.join(J.get('duplicates') or []) or 'none'}
- Retake of an earlier Reel: {json.dumps(re_of, ensure_ascii=False) if re_of else 'no'}
- Photos next to the clips: {len(J.get('photos') or [])}

## What was detected
- Language: {cut.get('lang')}
- Speech: {J.get('raw_seconds')} s raw -> {J.get('cut_seconds')} s kept, {J.get('pieces')} pieces
- Voices: {v.get('voices', 1)} ({v.get('low_hz', '?')} / {v.get('high_hz', '?')} Hz)
- Room floor of the clips: {J.get('noise_floor_db')} dBFS
- Brand profiles: {', '.join(br) or 'none, the neutral default look is used'}

## Decisions
- Format: {fmt_default}. TODO: confirm hybrid | face | faceless | skit (hybrid unless the user asked otherwise; skit only with two roles)
- Brand: {B['slug']} ({why}). TODO: confirm (ask only if several profiles fit equally)
- Subtitle language: {cut.get('lang')} (what is spoken)
- Voice: {voice}. TODO: confirm normal | phone (messenger-compressed copy) | outdoor (wind, street)
- Output name: TODO: the Reel's name in the spoken language, no long dashes, "(hybrid)" suffix for hybrids, "(emoji)" for skits
- Title: TODO: 2-3 short lines, words of the speaker, the key idea or number
- Title ends at: TODO: seconds; before the first animation segment in a hybrid, else 7

## Cut rules
- Keep the last complete clean take of every sentence; false starts, spoken notes to self and fillers go
- Pauses: {pause}
- Stutter: both passes (gap 0.12 and 0.04); every confirmed flag cut; the same on the final
- Eyes on camera for every kept piece; waiting-face check on every pause over 0.35 s
- Never cut through a gesture in a skit; a skit ends when the motion settles

## Visual plan (one line per sentence: FACE or ANIM, and the metaphor)
TODO: from transcript.txt. Hook, personal lines, opinions and the CTA stay on the FACE; facts, numbers, lists, comparisons, processes go to ANIM. Start and end on the face, animation 3-8 s, face 2-4 s between, switches only at sentence boundaries. At least 60 % of the animation segments are new bespoke scenes.

## Checks to pass before delivery
reel-tool gate {J['job']}: format, motion >= 1.5, no dead stretches, safe zones, circles, variety, only spoken words on screen, no claims, loudness -14 LUFS, stutter 0, no repeated phrases, eye and waiting-face reviews, visual review.

## Defaults taken (list every assumption for the final report)
TODO: list them, or write "none"
"""
    (job / "job.md").write_text(doc, encoding="utf-8")
    print(f"written: {job / 'job.md'}\nComplete every TODO (keep the headings), then continue.")


if __name__ == "__main__":
    main(sys.argv[1:])
