---
name: reel-hybrid
description: Hybrid Reels, face plus full-screen bespoke motion graphics: how to split a script into face and animation, invent visual metaphors, write new scenes for the engine, and keep a series from looking templated. Read during any hybrid job, or when asked for animations.
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read, Write, Edit, Glob, Grep
---

# Hybrid: face and full-screen animation

The default format. The Reel alternates the speaker's face with full-screen animation drawn **for this script**. Reference numbers from Reels that worked: 3-4 animation segments in 45-50 s, about 40-50 % of the runtime, 100 % bespoke.

## Split the sentences

- **FACE:** the hook (first 2-3 s), personal lines and trust ("let me be honest", "I'm not a doctor"), opinions and emotion, the question to the viewer, the call to action.
- **ANIMATION:** facts and how things work, numbers, lists, steps, comparisons, processes, "what is missing".
- **Rhythm:** start on the face, end on the face. Animation 3-8 s, face 2-4 s between (personal stretches may run longer, under 10 s). Switch only at sentence boundaries, using word times from `words.json`. The title ends before the first animation: `--title-end <t0 of segment 0>`.

## Think in metaphors, not templates

The stock scenes are a fallback and a toolbox. **Invent a new visual for what each sentence says.** Ask: what would a good explainer artist draw here? Not "which template fits".
- "20 years in one company" = a tree growing year rings, not a counter.
- "fast-money projects collapse" = a falling line of domino shops, not a list.
- "reputation takes years" = bricks stacking into a wall, not a card.
- "hours turn into people" = an hourglass whose sand becomes small figures.
Look at what exists: `reel-tool scene-list`, `reel-tool scene-list money`. These seed scenes show the craft level to reach. Do not reuse one unchanged; make a new one.

## The rules the variety check enforces

- At least 60 % of the animation segments are bespoke (new code in `scenes/`, a stock scene with new text does not count).
- No two scenes in a Reel share a type or a layout.
- Nothing from the last ~5 Reels of the same brand: scene, layout, metaphor, key asset (the ledger remembers; only delivered Reels count).
- Phone chat, list rows or 3 tiles, versus cards, quote card: each at most once per ~5 Reels, and only if nothing better fits.
- Frames of a segment must look different from the others (image hash).
- A word that pops in stays at least 0.8 s: if the sentence ends sooner, extend the segment into the next face part (`t1` later).
- No empty frames or slots waiting to be filled: elements appear when they are named.
- Only spoken words on screen, or a visual with no text.

## Writing a scene

1. `reel-tool scene-kit` prints the API and the template. Read one or two seed scenes for the level of detail: `reel-tool scene-list`, then `reel-tool scene-show <type>`.
2. One file per scene: `<job>/scenes/<type>.js`, first line the `@scene` header with a unique `type`, `layout`, `metaphor`, `assets`.
3. It is a pure function of `t`: no timers, no random without a seed, no state across frames.
4. Keep it moving the whole time: the gate measures the motion inside the animation (median at least 1.8). A scene that builds once and then sits fails. Plan a second and third beat for any scene over 3 s: objects drift and turn, lines draw on, numbers roll, something reacts to each spoken keyword, the scene's camera moves.
5. Draw in SVG/HTML/CSS with theme tokens only (`var(--c1)`...): it must look right in any brand. Big shapes, 60-70 % of the box above the subtitle line. Everything moves: idle motion on every element, a line drawing on, a counter rolling. Nothing still for over 1 s.
6. Elements enter on the word they show: pass word refs through params, `"moneyAt": "money"`.
7. Text comes in through params, never hard-coded, so scenes stay reusable and only spoken words reach the screen. Fit it: `R.fitFont`. Long words in other languages must not overflow.
8. Round things are `.round`/`.badge`/`.disc` with equal width and height, scaled uniformly. The circle check measures every frame.
9. Illustrate literally for health topics: no result claims, no medical symbols, no red cross.
10. Icons (`ph:name` Phosphor duotone first, for one consistent style) and Open Peeps characters are available; emoji `noto:` rarely. AI stills only as raw material inside a bespoke scene, and only if the user supplied them.

## visuals.json

```json
{ "title_end": 5.9, "keywords": [], "sfx": true,
  "zoom": {"auto": true, "levels": [1.0, 1.12], "extra": [], "emph": [12.4]},
  "beats": [ {"t": 2.1, "d": 1.4, "items": [{"emoji": "money-bag", "size": 270}, {"label": "FAST MONEY"}]},
             {"t": 12.4, "pop": "TEN YEARS", "size": 150, "d": 0.9} ],
  "hybrid": {"layout": "full", "segments": [
     {"t0": 5.95, "t1": 10.45, "scenes": [ {"type": "my_scene", "title": "Only promises", "titleAt": "promises", "fallAt": "gone"} ]},
     {"t0": 13.3, "t1": 19.3, "scenes": [ {"type": "other_scene", "...": "..."}, {"type": "second_scene", "at": 16.2} ]} ]} }
```

- `t0`/`t1` sit on sentence boundaries (a word's start minus ~0.05 s, the next face word's start).
- A segment can hold 1-2 scenes; a later one starts with `"at"`, a word ref or a number. Word refs: `"money"` (first at or after the scene start), `"money#2"` (2nd in the Reel), `"end:money"`, `"@14"` (word index), `"money+0.2"`. If a word repeats nearby, use the number.
- Any scene takes `"in"` (transition: push, whip, zoom, iris, wipe, rise, match, blur, cut), `"heading"` (kinetic heading, spoken words only), `"bg"` (background index; the last index is the dark scene on light themes, use for one dramatic beat).
- `"layout": "full"` always, unless the user asks for split screen. The engine opens each segment with a circle growing from the speaker's face, closes with a zoom and blur back, plus a quiet whoosh.
- Subtitles stay over the animation; the brand theme adds a soft shadow under them on light scenes.

Render caches each segment by content, so a fix to one scene re-renders only that segment.

## Check before the render

`reel-tool preview <job> <i>` for every segment. Then the render, then look at `qf/segs.jpg`. Common failures and fixes are in `reel-qc`.
