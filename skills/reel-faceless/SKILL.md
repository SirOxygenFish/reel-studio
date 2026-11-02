---
name: reel-faceless
description: Faceless Reels, the speaker's voice over full-screen motion graphics with no face at all. Use only when the user asks for it ("no face", "only animation", "без лица", "bez twarzy"), including a faceless version of a finished Reel.
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read, Write, Edit, Glob, Grep
---

# Faceless route

Only on request; hybrid is the default. Same process as `reel-edit` up to subtitles (scan, analyze, brief, stutter, subs); eye and waiting-face checks can be marked "no face in this format"; the visual review stays. Then:

1. Write `storyboard.json` in the job folder:
```json
{ "sfx": true, "title": {"lines": ["First line", "Second line"], "to": "end:customers"}, "punch": ["expensive", "only"],
  "scenes": [ {"type": "my_scene", "...": "..."}, {"type": "character", "peep": {"body": "Explaining", "head": "MediumBangs", "faces": {"Calm": 0, "Contempt": "expensive"}},
     "bubble": {"text": "...", "at": "too"}}, {"type": "cta", "in": "iris", "handle": "@handle", "monogram": "A", "actions": [{"kind": "follow", "label": "Follow", "done": "Following", "at": "follow"}]} ] }
```
2. One scene per sentence, in order; each starts at its sentence automatically (`"at"` overrides). All of `reel-hybrid` applies: bespoke metaphors first, variety, spoken words only. Stock types are listed by `reel-tool scene-list`. Vary transitions; `"punch"` on 3-6 key words gives camera punches.
3. `reel-tool preview <job> story --at <one time per scene>`, Read `preview/sheet.jpg`, fix, repeat.
4. `reel-tool faceless <job>` (voice chain once, then the engine). From a finished, already cleaned Reel: `--voice clean.wav`, and the chain is skipped.
5. `reel-tool gate <job>`, `reel-tool deliver <job> "<Name> (animation)"`.

Targets: motion median >= 1.5, still frames near 0, no dead stretches, 0 safe-zone issues, circles PASS. The coverage number counts text and icon boxes only, so drawn scenes read low: judge fill from the sheets, 60-70 % of the box. Banned: the speaker's face, split screen, AI video, paid APIs.
Characters are Open Peeps: bodies Explaining, PointingUp, Coffee, Computer, Paper, Whatever, TeeArmsCrossed...; faces Smile, BigSmile, Calm, Concerned, Fear, Awe, Suspicious, Contempt, Serious, Tired, Cheeky, Angry... They are illustrated people, never real faces.
