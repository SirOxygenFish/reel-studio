# Changelog

## 1.1.0 (2026-11-03)

For people who only use their phone.

### Getting started
- "Start here" guides in English, Russian and Polish: every step in order, from the desktop app to the daily routine
- An install prompt (three languages) to paste into Claude Code: it checks the computer, shows (never runs) any step that needs administrator rights, installs the plugin and its tools, turns on the upload page autostart and ends with the phone link as a QR code
- Two tutorials made with the motion engine, in three languages: the computer settings (16:9) and the iPhone routine (9:16, played offline by the upload page)

### Phone
- Upload page in English, Russian and Polish, picked from the phone's language, with a How to button and a Home Screen icon
- `reel-tool autostart on|off|status`: the page starts at every login without a session (Task Scheduler or the Startup folder on Windows, a LaunchAgent on macOS, systemd --user or desktop autostart on Linux), user level only
- `reel-tool shortcut on|off`: a desktop icon that starts the page and shows the phone link as a QR code
- `reel-tool phone-link`: the link plus a QR code in the terminal and as a page
- The page never shares a port with another program and says how to pick another one; a second start only prints the link

### Engine
- Storyboards without words (tutorials), explicit sound cues, a fixed sound reference when there is no voice
- `qc.py --tutorial`: the Instagram-only zones are skipped; frame sheets keep the video's shape

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
