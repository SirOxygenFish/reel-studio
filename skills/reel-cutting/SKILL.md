---
name: reel-cutting
description: The cutting rules for Reels: retakes, false starts, pauses, the waiting face, stutter passes, eye contact, gesture jumps. Read during a reel-edit job, or when asked to tighten a cut, remove stumbles or fix a jump.
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read
---

# Cutting

`reel-tool analyze` proposes the cut; you check it. Every change goes through `reel-tool recut`, so words, subtitles and picture never drift.

## Takes

- Keep the **last complete clean take** of every sentence, in story order. Inside one clip there are often 2-3 attempts (a full take, an aborted start, a clean one): the last complete one wins unless it is clearly worse.
- A clip can be the unfinished version of its neighbour. A word that "lasts" 2+ seconds in Whisper's timing means Whisper skipped a take: the analysis re-reads such spots, but check `decisions.md` anyway.
- Spoken notes to self ("one more time", "sorry", "stop") go.
- If there is a script, put it in `<job>/script.txt` before analyze: it orders the takes. Subtitles still show what was really said; tell the user where the speech differs.
- Check the first 1.5 s of each piece: false starts hide there.
- Whisper fills in names and brand words wrongly, and its grammar can be off where the audio is not: `reel-tool vote <job> A-B` is how you listen. Unanimous votes settle it; if they split, keep the best reading and say so in the report.

## Pauses (house rule, every monologue)

Target: tight natural pauses of 0.2-0.35 s. Only true silence is ever removed: it is measured from the audio (10 ms frames under -46 dB), never from speech-burst edges or word times, because a quiet word ("that", "it", an ending) can sit inside a "pause". `reel-tool wordcheck` re-hears the whole cut after every change. `analyze` does this: piece in at first sound - 0.12 s, out at last sound + 0.15 s, last piece + 0.55 s; silences of 0.36 s or more cut down to 0.15 s on each side. Longer pauses stay only for a gesture or an emotion that needs them.

**The idle mouth.** Lips parted and still in a silent pause look wrong even when the sound is fine: at most 0.15 s of it before a word. `reel-tool sheets` puts the last 0.4 s of every face pause from 0.2 s into `qf/mouth.jpg` (0.1 s apart, one row per pause). More than 2 tiles of parted, still lips before a word: move the in-point closer to the word (`recut --in K T`, T = word start - 0.10, never into the word) or drop the middle of the pause in silence (`recut --drop A-B`), then `wordcheck` again. If that would clip the word, leave it and name the spot in the report.

## Stutter passes (always both)

Whisper on a whole piece hides restarts ("Only, only that today" comes out once). `reel-tool stutter <job>` runs gap 0.12 and gap 0.04 on the raw audio and votes every flag.
- CONFIRMED: `reel-tool recut <job> --drop A-B` with the suggested span, then run it again.
- "listen": unclear short bursts at the start of a piece: read the words around them; cut if it is a stumble.
- false alarm: words split in two by the fine pass; ignore.
Repeat until 0 confirmed. The gate runs the same on the final.

## Eye contact (every kept piece)

Viewers feel it when the speaker reads. `reel-tool sheets` makes `qf/eyes.jpg`: strips at eye height, 2.5 per second, time on each tile.
- A blink is one frame. **Several frames in a row with lids half down = looking down.** That piece looked away.
- If so: look for another take of that line with eyes on camera (`decisions.md` lists the dropped ones; `recut` can swap pieces with `--in`/`--out`). If there is none, keep the best one and name the exact words in the report as worth re-recording.
- Animation segments can hide a weak stretch: use that when the sentence belongs in animation anyway.
Then `reel-tool mark <job> eyes "<what you saw>"`.

## Camera

Never a jump of scale on the face: the render does one slow eased push-in and pull-out (3.5 % over 6 s) and a 4-frame soft blend placed on the exact frame of every face cut; zoom keys in visuals.json are ignored. Hand-held clips: `reel-tool stabilize`, used only when the measured background shake drops 30 % or more (on a selfie it often gets worse).

## Gestures

`reel-tool jump <job>` compares the body across each join; the gate runs it again on the final cut. `<-- JUMP` is a cut through a moving hand. In a monologue with zooms a small jump is fine when the join falls on a zoom change; in a skit never. Move it: `reel-tool bestcut <job> K` shows the calmest pair of frames near join K, then `recut --out K T1 --in K+1 T2`.

## Source rules

- Horizontal or square footage is cropped to 9:16 around the face automatically; tell the user if a lot is lost.
- HDR iPhone footage is tone-mapped automatically, once, when the pieces are built (GPU libplacebo if available, else CPU zscale; `reel-tool doctor` says which).
- Duplicate uploads: `scan` compares audio hashes, so a re-export of the same clip is recognised. Trust it over file names.
