---
name: reel-stickers
description: Retention visuals on the face parts of a Reel: zooms, sticker combos, big text pops, sound effects. Read when writing the beats of visuals.json, or for a face-only edit.
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read, Write, Edit
---

# Face-part visuals

Goal: something changes on screen every 1-2 s, without covering the face.

## Weight

- **Hybrid face parts:** light. 1-2 combos or pops per face part, plus zooms.
- **Face-only format** ("only face", "no animations"): subtitles, title, zooms on every sentence, light sound effects and light stickers (a combo or pop every 6-10 s). No full-screen cards or animation. Only if the user also rules out stickers or effects ("just subtitles") leave those out. Asked for a busy face edit instead: combos, pops and 2-4 `cutaways` (`vs`, `list`, `chart`, `flow`, `stat`, 1-3 s each, formats at the top of `scripts/visuals.py`).
- **Skits:** emoji accents only, see `reel-skits`.

## Elements

- **Combo:** emoji + short bold label + optional arrow pointing at the speaker: `{"t": 1.34, "d": 1.4, "items": [{"emoji": "leg", "size": 270}, {"label": "JOINTS"}], "arrow": true}`. Elements land 0.12 s apart.
- **Text pop:** 1-2 key words, huge, 0.6-1 s: `{"t": 3.4, "pop": "SURGERY?", "size": 150, "d": 0.9}`, `"color": "white"` optional. Add the time to `zoom.emph` for a punch.
- **Sign:** `{"sign": "≠", "size": 240}` for ≠ VS ✓ % ?.
- Options: `"enter": "pop"|"slide"`, `"zone": "UL|UR|ML|MR|LO|TOP"`, `"badge": "x"` on an emoji (small red cross = "not").
- Emoji names: `reel-tool emoji --find money`. Only literal illustration: nothing that adds a claim. Never the red cross, no medical symbols of results.

## Placement

The script places everything and picks free zones. Banned: the face and eyes (tracked, grown during zooms), the subtitle line, the title while it shows. Allowed: shoulders, chest, hands, edges, the band above the head, below the subtitles. Zones rotate; the same zone twice in a row only if nothing else fits. A beat that finds no room, or would show for under 0.8 s before an animation, is dropped and the gate fails with its time: shorten the label, lower the size, move it, or take it out. In a tight frame (head over half the width) most things go low or above the head; that is fine.

## Camera

No zoom jumps, kicks or shakes: the render applies one slow push-in and pull-out (3.5 % over 6 s) and soft 4-frame blends on face cuts by itself. Zoom keys in visuals.json are ignored. Energy comes from the pace of stickers, pops, animation and tight pauses, never from camera moves.

## Sound effects

`"sfx": true`. Synthesised, nothing to license, about 21 dB under the voice, after the voice chain. Each hit is re-synthesised, no recipe twice in a row or within 10 s, and thinned (at most one per 1.2 s; accents 2.5 s apart; dings 8 s apart). Less is more: not every sticker sounds.

## Photos and music

Photos next to the clips (`scan` counts them): look at each one and use the fitting ones in the `image` scene (`"frame": "card"`, `"src"` = absolute path) for 2-6 s on the sentence they illustrate; hold them inside a bespoke scene when you can. Music only if the user asks or supplies it: `reel-tool render <job> --music file.mp3 --music-db -24`; it is mixed after the voice chain.

## Never

- Whole-video text boxes or watermarks, unless the user asks. Title for the first seconds, subtitles, pops and stickers only.
- Text the speaker did not say.
