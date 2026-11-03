---
description: Start the phone upload page, so clips can be sent from a phone on the same network (LAN or Tailscale only), and show its link as a QR code.
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read
---

Run `reel-tool phone-link --start --open`. It starts the page in the background if it is not running yet (it keeps running after this session), prints the links and a QR code, and opens a page with a big QR code on the computer. Show the user the link and the QR code from the output in a code block.

Say in plain words: scan the code with the phone camera (same Wi-Fi, or Tailscale when away from home); on an iPhone open it in Safari, tap Share, then Add to Home Screen. Clips land in the videos folder, each batch in its own dated folder, with an optional note saying what to do; finished Reels appear on the same page, and on an iPhone the To gallery button saves them to Photos through the SaveReel shortcut. The How to button on the page plays the iPhone tutorial. The page only answers devices on the local network or the user's own tailnet, and the link contains a private key, so it should not be shared.

If `reel-tool autostart status` says autostart is off, offer once: `reel-tool autostart on` starts the page at every login (user level, no administrator rights), and `reel-tool shortcut on` puts an icon on the desktop that shows this QR code again. If the port is taken by another program, the output names the line that picks another port.
