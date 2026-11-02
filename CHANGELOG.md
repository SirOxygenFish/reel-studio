# Changelog

## 1.0.0 (2026-11-02)

First public release.

### Editing
- `reel-tool`: one command for every machine step of a Reel, called by the skills
- Automatic take selection; pause tightening that trims only true silence measured from the audio, never soft words
- Stutter passes (0.12 s and 0.04 s) and a body-jump check, run again on the final cut after tightening
- Word check: the kept audio is heard again and every word of the transcript must still be there
- Smooth camera: a slow push-in only, soft 4-frame blends on face cuts, no zoom jumps or shakes
- Optional stabilisation, used only when the measured shake drops by 30 % or more
- Voice chain with DeepFilterNet, plus `phone` and `outdoor` presets for weak recordings
- Corrections keep the finished cut and swap only the re-said lines
- Skit pauses shortened at calm frames

### Look
- Motion engine with stock scenes and a seed library of bespoke scenes; a per-brand variety ledger
- Hybrid, face-only, faceless and skit formats
- Brand wizard with WCAG contrast checks and a palette sheet; several profiles; two example brands (`reel-tool brand example`)
- Word-timed subtitles with backgrounds that stay readable on light themes

### Quality gates
- Format, motion, animation that keeps moving, dead stretches, safe zones, round circles, scene variety, dropped stickers,
  minimum text hold, only spoken words on screen, no health or income claims, -14 LUFS, stutter, lost words, eye contact,
  idle mouth, and a visual review

### Setup
- Windows x64, Linux x86-64 (Ubuntu 22.04/24.04 and derivatives) and macOS on Apple Silicon
- Everything goes into the plugin's data folder, pinned by SHA-256; nothing system-wide, no sudo
- `/reel-doctor` prints the exact command that fixes each missing piece; `--clear-cache` frees render caches
- Render caches of jobs delivered more than 14 days ago are cleaned automatically; the newest 5 always keep theirs (both settable)
