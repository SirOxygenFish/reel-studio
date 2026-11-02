---
description: Install everything Reel Studio needs (5-8 GB, into the plugin's data folder). Safe to run again.
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read
---

Install Reel Studio's dependencies.

1. In one short sentence, tell the user what happens: private copies of Python, ffmpeg, Node, a headless browser, the speech model (about 3 GB) and the voice clean-up model go into the plugin's data folder; nothing changes system-wide; the first run takes 10-30 minutes depending on the connection.
2. Run `reel-tool setup` with the Bash tool. Use run_in_background and a long timeout, because it can take many minutes. It prints one line per stage and skips finished stages, so it is safe to re-run. Give the user a short progress line when a stage finishes.
3. If a stage fails, read the message. Checksum mismatch or a network error: run it again once. Otherwise explain the problem in plain words.
4. When it says "setup finished", run `reel-tool doctor --full` and report the result in plain words.
5. Say what is next: `/reel-brand` to create a brand profile (optional, a neutral look works without one), then put clips in the project folder and say `/reel`.
6. Tip for the user: approving `reel-tool` with "always allow" the first time it asks avoids repeated permission prompts.
