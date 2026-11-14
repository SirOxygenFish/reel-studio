# Changelog

## 1.3.1 (2026-11-14)

Phone uploads survive interruptions and are never sent twice: the page sends 16 MB pieces and continues from the last byte that arrived after a dropped connection, a page reload or a computer restart (a half file is a hidden .part until complete; stale ones move to `_deleted` after 24 h); a file that already arrived (same name and size) is answered "already received" instead of being uploaded again; each file shows uploading %, received, already received or error, retrying; the page says when the iPhone is still preparing long videos; every upload start, finish, abort and duplicate is logged in `_deleted/uploads-log.txt` in the output folder.

## 1.3.0 (2026-11-09)

Finished videos on the phone page: watch them inline in full quality as poster cards, with a "New" badge until first played; the delete button moves a video to `_deleted` in the output folder with Undo and "Recently deleted" to restore it, and after 30 days it goes to the Recycle Bin / Trash (never a permanent delete). Delete, restore and played are POST only, from the page itself. English, Russian and Polish.

## 1.2.0 (2026-11-05)

Setup that shows every click, in one chat from start to finish.

- Tutorial 1 rebuilt (about 80 s, English, Russian, Polish): the </> Code tab, the two Remote Control switches, a new chat on This computer in a folder you create (it becomes the videos folder), Opus 5.5 with Effort High, Auto permissions, pasting the install prompt, then /reload-plugins
- The install prompt installs the plugin first (seconds), then runs the long setup, and uses the chat's own folder as the videos folder
- No more "close this session and start a new one": the install chat stays the everyday chat; /reload-plugins turns Reel Studio on in it (fallback: quit and reopen the app, then open the same chat)
- Start here guides follow the video step by step; after setup Effort can go down to Medium; questions later, Tailscale included, go to the same chat
- Tutorial gate allows up to 90 s for Tutorial 1

## 1.1.0 (2026-11-03)

For people who only use their phone.

### Getting started
- "Start here" guides in English, Russian and Polish: every step in order, from the desktop app to the daily routine
- An install prompt (three languages) to paste into Claude Code: it checks the computer, shows (never runs) any step that needs administrator rights, installs the plugin and its tools, turns on the upload page autostart and ends with the phone link as a QR code
- Two tutorials made with the motion engine, in three languages: the computer settings (16:9) and the iPhone routine (9:16, played offline by the upload page)

### Phone
- Upload page in English, Russian and Polish, picked from the phone's language, with a How to button and a Home Screen icon
- SaveReel from the page: it serves a signed SaveReel shortcut (Install SaveReel, Open in Shortcuts, Add Shortcut); without it, a share-sheet Save to Photos over HTTPS or a plain download with four steps. `reel-tool savereel build|sign|check` rebuilds and re-signs it on a Mac
- `reel-tool autostart on|off|status`: the page starts at every login without a session (Task Scheduler or the Startup folder on Windows, a LaunchAgent on macOS, systemd --user or desktop autostart on Linux), user level only
- `reel-tool shortcut on|off`: a desktop icon that starts the page and shows the phone link as a QR code
- `reel-tool phone-link`: the link plus a QR code in the terminal and as a page
- The page never shares a port with another program and says how to pick another one; a second start only prints the link

### Video quality
- Explicit BT.709 on every RGB/YUV conversion and on the output. Before, the sticker layer encoded with the BT.601 matrix and no tags (skin a little redder, up to 20 levels off on reds and greens) and the engine's files missed two of the colour tags
- One lossless 4K intermediate (2160x3840): the push-in is done on the 4K frame, then one Lanczos downscale to 1080x1920
- Final encode: x264 slow, CRF 16, maxrate 20M, faststart, BT.709 tags (Reels and the engine's faceless renders)
- HDR clips (iPhone HLG / Dolby Vision, PQ) are tone-mapped once, at the start: libplacebo when the ffmpeg has it and a Vulkan device works, else zscale + tonemap on the CPU
- More disk: about 1.3 GB of render cache per 30 s Reel (2.3 GB from HDR originals) plus the same again while rendering, and files roughly 2x bigger; `--old-quality` or `reel-tool config quality v1` gives the 1.0 settings back; doctor shows which HDR path this computer uses

### Engine
- Storyboards without words (tutorials), explicit sound cues, a fixed sound reference when there is no voice
- A plain `fade` transition and a still camera (`camera.still`) for screens with text to read
- Fixed: a frame landing exactly on the start of a transition showed the next scene for one frame (A-B-A flash)
- `qc.py` reports stray A-B-A frames on every run; `qc.py --flash <videos>` checks any video read-only
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
