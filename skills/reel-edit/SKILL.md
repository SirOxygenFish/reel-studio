---
name: reel-edit
description: Edit raw video clips into a finished Instagram Reel, TikTok or Short. Use for ANY request to edit, cut, trim, clean up, subtitle or animate a talking video, however short or vague, in any language, even with no file named: "edit this", "make it nice", "make it a reel", "cut the bad parts", "add anims", "add animations please", "монтируй", "смонтируй", "сделай рилс", "на монтаж", "edytuj", "zmontuj", "zrób z tego rolkę", "schneide das", "edita esto". Also when a clip was just added or uploaded and the user only says "done", "here it is" or "go".
argument-hint: "[what to do, optional file names]"
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read, Write, Edit, Glob, Grep
---

# Reel Studio: the pipeline

You turn raw clips into a finished 1080x1920 Reel. The user may have written three words. **The quality must come from this process, not from their prompt.** Never ask them for a brief: you write it. Everything machine-like goes through `reel-tool` (run `reel-tool help`), one command at a time, with the **Bash tool** (use PowerShell only if there is no Bash tool). Do not chain it with anything; never write ad-hoc scripts, call ffmpeg directly, or use any other shell command. If a `reel-tool` call needs approval, ask for it once and carry on: do not look for a way around it and do not edit settings.

Talk to the user in the language they wrote in, in plain words, no jargon. Final report: see step 13.

Focused guides, read each when you reach that step: `reel-cutting` (cuts, stutters, eyes), `reel-voice`, `reel-hybrid` (animation and bespoke scenes), `reel-stickers` (face-part visuals), `reel-skits`, `reel-faceless`, `reel-qc` (gate failures).

## Non-negotiable

- **The brief comes first.** No render without a complete `job.md`.
- **The gates decide.** A Reel that fails `reel-tool gate` is not delivered. Fix and re-run; do not argue with a gate, do not edit gate results, do not copy `final.mp4` out by hand. `reel-tool deliver` is the only way out.
- **Original files are never changed or deleted.** Old versions move to `_old/`.
- **On-screen text is the speaker's words only.** Nothing invented: no slogans, no numbers they did not say. Word forms may change; meaning may not.
- **No health or income claims in visuals**, even if spoken: no "cures", no checks next to a product, no before/after results, no earnings figures. Illustrate literally or leave it on the face.
- **No long dashes, no logos of other companies, no real people's faces, no AI video.** No persistent text boxes over the whole Reel unless asked.
- **The voice chain runs once**, on raw voice. Never on a finished Reel.

## Steps

**1. Scan.** `reel-tool scan --note "<their request word for word>"` (add file paths if they named any; it finds the newest unused batch otherwise). Read the output: duplicates are skipped, clips edited before are flagged, notes next to the clips are instructions from the user.
If it says all clips were edited before and the request does not say to redo them, tell the user and stop. If there are no clips at all, tell the user where to put them (`reel-tool config` shows the folders).

**2. Analyze.** `reel-tool analyze <job>` (one to a few minutes). Whisper finds language, takes, false starts; pauses are tightened by the house rule. Read `transcript.txt` and `decisions.md` in the job folder. Check the cut like an editor: does the story hold, was a good line dropped, is a take truncated? Fix with `reel-tool recut` (`reel-tool recut <job>` lists the pieces).
- `voices: 2` or two roles in the text: it is a skit, read `reel-skits`.
- `RETAKE of an earlier job`, kind `reshoot`: same script filmed again; keep the earlier name, delivery moves the old file to `_old/`.
- Kind `correction`, or a note saying a clip fixes a finished Reel: start over with `reel-tool scan <new clip> --extend <old job>`. `analyze` then keeps the finished cut and only swaps in the new takes: a re-said line replaces the old one, a new line goes to the start (`recut --move K POS` puts it elsewhere). Old scenes, title and phrases come along (`old_visuals.json`, move its times to the new cut). Keep the name.
- A note names which clip does what ("take the ending from the second video"): the note wins over the automatic choice; fix it with `recut`.
- Several clips can be several Reels: if the sentences do not connect (two topics, two hooks, two calls to action), make one job per Reel with `reel-tool scan <files> --job name`. A note saying "two videos" settles it.

**3. Questions: almost never.** Ask at most 1 or 2 short questions, and only if the answer truly changes the result: several brand profiles fit equally, or the clips make two opposite Reels. Everything else gets a sensible default that you state in the report. In a non-interactive run, never ask: decide.

**4. Brief.** `reel-tool brief <job>`, then edit `job.md` and replace every TODO. Defaults:
- **Format:** hybrid, unless the user says otherwise ("only face", "no animation" = face; "no face", "only animation" = faceless; two roles = skit). "add anims", "make it nice" = hybrid.
- **Brand:** write the slug after `- Brand:`; with several profiles it decides the look and the variety ledger (`scan` lists devices and languages per brand).
- **Name:** the Reel's idea in the spoken language, short, no long dashes, plus " (hybrid)" or " (emoji)" for skits. Face format and faceless: " (face)" and " (animation)".
- **Title:** 2-3 short lines (under ~16 characters each) made of the speaker's words: the key idea or number.
- **Visual plan:** one line per sentence: FACE or ANIM, and for ANIM the visual metaphor. This is where the Reel is won; think it through.

**5. Cut checks.** If `scan` said hand-held, `reel-tool stabilize <job>` (it keeps the original unless shake drops 30 % or more). Then `reel-tool stutter <job>`: cut every CONFIRMED flag with `reel-tool recut <job> --drop A-B`; judge "listen" flags from the words around them. Repeat until 0 confirmed. Then `reel-tool wordcheck <job>`: no word may be lost by the cut (give it back with `recut --in/--out`). Both run on the final cut, after every recut. Then `reel-tool pieces <job>`, `reel-tool sheets <job>`, Read `qf/eyes.jpg` and `qf/mouth.jpg` (if any) and record what you saw: `reel-tool mark <job> eyes "..."`, `reel-tool mark <job> mouth "..."`. Details in `reel-cutting`.

**6. Words.** Read the whole transcript as a proofreader. For any word that is ungrammatical, odd in context, or a name: `reel-tool vote <job> A-B` hears that stretch 6 ways (give it the whole sentence, from its first word to its last, times from `transcript.txt`). If the votes agree on another word, fix it: `reel-tool recut <job> --fix OLD=NEW` (or `IDX=word` for one occurrence; `recut <job>` shows indexes). If they split, keep the best reading and name it in the report. Subtitles show what was really said, in its normal spelling: names and brands spelled the way the brand does.

**7. Subtitles and title.** `reel-tool subs <job> --title "line one|line two" --title-end <s> --phrases "words that|stay together"`. If the title would sit on the forehead, `--title-margin 120` moves it up (default 205; not under 120). Read the printed lines: a preposition stays with its noun, a number with its unit, "not" with its verb; no line ends on a small word. Add such groups to `--phrases` (exact words, lower case, 2-3 words) and re-run.

**8. Visuals.** Hybrid: `reel-hybrid`. Face part stickers: `reel-stickers`. Write `visuals.json` in the job folder.

**9. Preview.** `reel-tool preview <job> <segment>` for each animation segment, Read `_motion/preview/sheet.jpg`. Fix overflows, tiny text, empty space, wrong timing before the long render.

**10. Render.** `reel-tool render <job>`. It can take several minutes; for a Reel over 60 s run it (and the gate) in the background and wait for the notice. A browser that hangs is restarted automatically.

**11. Look at it.** `reel-tool segsheet <job>`, Read `qf/segs.jpg` and `final_qc_sheet.jpg` after the gate has made it. Nothing on the face, nothing cut off, text readable, no empty slots, the animation actually says what the sentence says. Record: `reel-tool mark <job> visual "..."`.

**12. Gate.** `reel-tool gate <job>`. Any FAIL: fix the cause, re-render if needed, run it again until it says GATE PASS. See `reel-qc`.

**13. Deliver and report.** `reel-tool deliver <job> "<Name>"`. Then tell the user, in their language, in plain words:
- the file and its length;
- what was done, in 2-4 short points (what was cut, what the animations show);
- lines worth re-recording, if any (looked away, mumbled, a weak take): quote the words;
- the defaults you took, if any matter (format, brand, title).
No QC numbers, no tool names, unless they ask.
