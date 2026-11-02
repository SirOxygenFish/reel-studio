---
name: reel-skits
description: Editing skits and dialogues with two characters (a phone call, two roles, a voice off camera). Read when analyze reports two voices or the script has two roles.
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read, Write, Edit
---

# Skits

Timing is the joke, so skits are cut differently. `analyze` does not tighten pauses on a clip it detects as a skit (`--skit` forces it, `--no-skit` overrides it).

- **Open on the hook of the situation.** If the skit is a phone call: about 1 s of real frames before the first line (best the moment a hand reaches for the headset or phone), plus a synthesised double ring. `reel-tool ring <job>` writes `ring.wav`, 400 + 450 Hz, 0.4 s on, 0.2 s off, 0.4 s on, ending before the first word and about 5 dB under the voice. The render mixes it inside the voice chain. The title starts with the ring; the first subtitle starts exactly on the first word.
- **Long pauses drag even in a skit.** Run `reel-tool skit-pauses <job> --apply`: it shortens every pause over 0.5 s to about 0.45 s at the calmest pair of frames; when no full cut is calm it takes the longest calm part, and leaves a pause whole only if nothing is calm. Keep more only where the wait is the joke (`--keep 0.9`). Then `reel-tool jump`, `stutter`, `subs`.
- **Never cut a pause in the middle of a gesture.** After any change run `reel-tool jump <job>`: every `<-- JUMP` is a hand jumping. Keep the pause whole, or find the calm point with `reel-tool bestcut`. A join between two takes only where the hands are still in both.
- **End** without freeze frames or added silence: the last shot runs until the motion settles, about 0.5-0.8 s after the last word (`recut --tail`).
- **Roles.** Second voice lines get their own subtitle colour: `reel-tool subs <job> --second-voice "T0-T1,T0-T1"` (times from `transcript.txt`, role from the words; `job.json` has pitch per sentence under `voices.assign`).
- **Visuals:** emoji accents only, placed away from faces, no zooms, no animation segments:
  `{"title_end": 7.0, "keywords": [], "sfx": true, "zoom": {"auto": false, "levels": [1, 1], "extra": [], "emph": []}, "beats": [{"t": 2.0, "d": 1.4, "items": [{"emoji": "telephone-receiver", "size": 210}]}]}`
- Whisper drops short replies between two voices. Compare `decisions.md` and the raw story: a one-word answer it called a fragment is usually a line. Put it back with `recut`.
- Script prompts make Whisper invent phrases over pauses and the ring ("thanks for watching"): drop any that were not spoken.
- Name: "<name> (emoji)". Format in job.md: skit.
