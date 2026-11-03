# Install prompt (English)

Copy everything in the box below and paste it into a new Claude Code session (the desktop app's Code tab or `claude` in a terminal). Two lines near the end can be changed before you send it.

```text
Please install Reel Studio on this computer for me. I am not technical: do every step yourself, say in one short line what you are doing, and talk to me in English.

Rules:
- Change nothing that this list does not need: no system settings, no other programs, no files outside the folders named here.
- Never run anything that needs administrator rights (sudo, a Windows permission prompt, "Run as administrator"). When such a step is needed, show me the exact command, tell me where to paste it, and wait until I say it is done.
- If a step fails, read the error, fix it the simplest way, and tell me in one line what happened.

1. Check this computer: operating system and version, processor type, free disk space, and whether git is installed. Tell me the result in two lines. Reel Studio needs Windows 10 or 11 (64-bit), macOS on Apple Silicon (M1 or newer) or a 64-bit Ubuntu-based Linux (Ubuntu 22.04/24.04, Zorin OS, Mint), and about 10 GB of free disk. If this computer does not qualify, stop and tell me why.

2. Install what is missing:
   - Windows without Git: show me the command  winget install --id Git.Git -e  (it may ask for permission), wait for me, then continue.
   - Linux without git, curl or tar: show me  sudo apt install -y git curl tar  and wait for me.
   - Mac without the developer tools: run  xcode-select --install  (a window opens and I click Install), wait for me.

3. If the claude command does not work in a terminal, install Claude Code for this user only (no administrator rights needed):
   - Windows, in PowerShell:  irm https://claude.ai/install.ps1 | iex
   - Mac or Linux:  curl -fsSL https://claude.ai/install.sh | bash

4. Install the plugin:
   claude plugin marketplace add SirOxygenFish/reel-studio
   claude plugin install reel-studio@siroxygenfish
   If it is already installed, run  claude plugin update reel-studio@siroxygenfish  instead.

5. Find the installed copy: the newest folder ~/.claude/plugins/cache/siroxygenfish/reel-studio/<version>. Use its bin/reel-tool (on Windows in PowerShell: bin\reel-tool.cmd) for the next steps. Run  reel-tool setup  in the background: it downloads 5-8 GB and takes 10 to 30 minutes. Every few minutes tell me in one line how far it is. When it has finished, run  reel-tool doctor  and fix what it reports (administrator steps: show them to me as above).

6. Videos folder: use the folder I name here: [leave empty for the default]. The default is Reels inside my Videos folder (Windows and Linux) or Movies folder (Mac). Then run
   reel-tool autostart on --folder "<that folder>"
   so the phone upload page starts by itself every time I log in. Autostart: [yes]  (if I changed this to no, skip the command and tell me that  reel-tool phone-link --start  starts the page by hand). Then run  reel-tool shortcut on  so I get a desktop icon that starts the page and shows the phone link.

7. Run  reel-tool phone-link --start --open . In your reply, show me the phone link and the QR code from its output (in a code block), and tell me: scan it with the iPhone camera, open the page in Safari, tap Share, then Add to Home Screen.

8. Tell me clearly: plugins load only in a new session. I should close this session and start a new one in the videos folder (show me the full path). In the desktop app: Code, New session, choose that folder.

9. End with this cheat sheet, exactly:
   Every day:
   1. iPhone: Reel Studio icon, choose the clips, Send.
   2. Claude app: Code, my computer's session.
   3. Write: make a Reel (add anything special you want).
   4. Wait for Claude to say it is done.
   5. Upload page: To gallery. The Reel is in Photos.

Touch nothing else.
```
