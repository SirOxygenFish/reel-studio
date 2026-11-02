---
description: Check Reel Studio's dependencies and diagnose problems.
argument-hint: "[--full | --clear-cache]"
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read
---

Run `reel-tool doctor $ARGUMENTS` and explain the result in plain words, in the user's language. For each FAIL say what it means and do the fix: most are solved by `/reel-setup`. If everything passes, say so in one line. `--full` also renders a test scene and loads the speech model. `--clear-cache` removes the render caches of every job in this project (clips, finished Reels and job notes stay); say how much space came back.
