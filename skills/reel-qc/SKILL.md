---
name: reel-qc
description: What each quality gate of Reel Studio measures and how to fix a failure. Read when reel-tool gate prints FAIL or a Reel looks wrong.
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read, Write, Edit
---

# The gates

`reel-tool gate <job>` must end in GATE PASS. Fix the cause and run it again; never bypass it.

| Check | Means | Fix |
|---|---|---|
| format | 1080x1920, 30 fps, H.264 yuv420p, audio | re-render |
| motion | median frame change >= 1.5 in the graphics area | more idle motion, camera moves, more elements arriving on words |
| animation keeps moving | median motion inside the animation segments >= 1.8 | more beats per scene: drifting objects, draw-ons, rolling numbers, reactions on keywords |
| dead stretches | over 1 s with nothing moving | add motion or a change there |
| safe zones | content in the subtitle band (y 1240-1510), under Instagram's top strip (y < 120) or outside the frame for 0.5 s or more | move or shrink it; `final_qc.json` lists boxes and times |
| icons (render stops) | an icon name does not exist, it would draw an empty box | `reel-tool icon --find word`, use an existing name |
| circles | a round element off by more than 2 % on any frame | `flex:none`, equal width and height, `aspect-ratio:1`, uniform scale only; text must not stretch a badge |
| variety | bespoke share, repeats, ledger, frame similarity | new scene, new layout, new metaphor; read the failed lines. Never just rename a scene: the frames are compared too |
| only spoken words | on-screen words that are not in the speech | use the speaker's words or a visual without text; if a word is a real form of a spoken word, rephrase closer to it |
| title before animation | title still on when animation starts | `reel-tool subs <job> --title-end <t0>` |
| animation rhythm | 2.5-10.5 s segments, start and end on the face | move `t0`/`t1` to other sentence boundaries |
| no dropped stickers or pops | a beat found no room or would flash under 0.8 s | shorter label, smaller size, other moment, or remove it |
| no word lost in the cut | `wordcheck` re-heard the cut and a word is gone | give it back with `recut --in/--out`; a false alarm after listening: `reel-tool mark <job> words "..."` |
| no claims | health or income wording in visuals | remove the text, keep it in speech only |
| loudness | -14 LUFS +- 0.6 | the chain ran twice, or sound effects are too hot; re-render |
| voice chain | DeepFilterNet ran | a fallback ran: `/reel-doctor` |
| stutter | confirmed flags on the cut or the final | `recut --drop`, stutter again, subs, render |
| no repeated phrases | a 5-word run appears twice in the final speech | an extra take stayed: cut it |
| speech matches | final speech differs from the cut | compare `final_transcript.txt` with `transcript.txt` |
| eye / waiting-face / visual review | you must have looked | Read the sheets, then `reel-tool mark` with what you saw |
| no cuts through gestures (skit) | jump flags | `reel-tool jump`, `bestcut` |

After any change to the cut: `stutter`, `subs`, `render`, `gate`, in that order. Changing only a scene: `render`, `gate` (clips are cached).

## Reading the contact sheet

`final_qc_sheet.jpg` shows a frame every 2 s. Check: nothing on the face, subtitles readable on every background, no text cut by the frame edge, nothing waiting empty, each animation clearly about its sentence. In animation segments the brand's soft shadow sits under the subtitle line.

## Reference numbers

Good hybrids: motion median 1.5-2.6, still frames under 5 %, 0 dead runs, 0 safe-zone issues, circles 0.00 %, -14.0 LUFS, bespoke 100 %.
