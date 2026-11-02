---
description: Turn raw clips into a finished Reel. Works from any short request, in any language.
argument-hint: "[what you want, optional file names]"
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read, Write, Edit, Glob, Grep, Skill
---

Use the `reel-edit` skill and follow it exactly, from step 1, for this request: $ARGUMENTS

If the request is empty, treat it as "edit the newest clips". If `reel-tool` says Reel Studio is not set up, tell the user to run /reel-setup and stop.
