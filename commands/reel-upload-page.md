---
description: Start the phone upload page, so clips can be sent from a phone on the same network (LAN or Tailscale only).
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read
---

Start the upload page: run `reel-tool upload-page` with the Bash tool using run_in_background, then read the first lines it prints and give the user the address.

Say in plain words: open this address on the phone, on the same Wi-Fi or over Tailscale; clips land in the input folder, each batch in its own dated folder, with an optional note saying what to do; finished Reels can be downloaded from the same page. It only answers devices on the local network or the user's own tailnet, and the link contains a private key, so it should not be shared. It stops when the session ends or when the user asks.
