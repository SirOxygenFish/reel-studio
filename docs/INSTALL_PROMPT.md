# Install prompt (English)

Copy everything in the box below and paste it into the new chat you set up as in Tutorial 1 (Code tab, This computer, your new folder, Opus 5.5 with Effort High, Auto). The folder of that chat becomes your videos folder. One line near the end can be changed before you send it.

```text
Please install Reel Studio on this computer for me. I am not technical: do every step yourself, say in one short line what you are doing, and talk to me in English.

Rules:
- Change nothing that this list does not need: no system settings, no other programs, no files outside the folders named here.
- Never run anything that needs administrator rights (sudo, a Windows permission prompt, "Run as administrator"). When such a step is needed, show me the exact command, tell me where to paste it, and wait until I say it is done.
- If a step fails, read the error, fix it the simplest way, and tell me in one line what happened.
- This chat stays my Reel Studio chat for every day, also from my phone. Remember what you set up here: I will come back to this same chat with questions (Tailscale, errors, changes). Never tell me to start a new session.

1. Check this computer: operating system and version, processor type, free disk space, and whether git is installed. Tell me the result in two lines. Reel Studio needs Windows 10 or 11 (64-bit), macOS on Apple Silicon (M1 or newer) or a 64-bit Ubuntu-based Linux (Ubuntu 22.04/24.04, Zorin OS, Mint), and about 10 GB of free disk. If this computer does not qualify, stop and tell me why.

2. Install what is missing:
   - Windows without Git: show me the command  winget install --id Git.Git -e  (it may ask for permission), wait for me, then continue.
   - Linux without git, curl or tar: show me  sudo apt install -y git curl tar  and wait for me.
   - Mac without the developer tools: run  xcode-select --install  (a window opens and I click Install), wait for me.

3. If the claude command does not work in a terminal, install Claude Code for this user only (no administrator rights needed):
   - Windows, in PowerShell:  irm https://claude.ai/install.ps1 | iex
   - Mac or Linux:  curl -fsSL https://claude.ai/install.sh | bash

4. Install the plugin now, before the long setup (it takes seconds):
   claude plugin marketplace add SirOxygenFish/reel-studio
   claude plugin install reel-studio@siroxygenfish
   If it is already installed, run  claude plugin update reel-studio@siroxygenfish  instead. If this chat restarts after this step, just continue with step 5.

5. Find the installed copy: the newest folder ~/.claude/plugins/cache/siroxygenfish/reel-studio/<version>. Use its bin/reel-tool (on Windows in PowerShell: bin\reel-tool.cmd) by its full path for the next steps. Run  reel-tool setup  in the background: it downloads 5-8 GB and takes 10 to 30 minutes. Every few minutes tell me in one line how far it is. When it has finished, run  reel-tool doctor  and fix what it reports (administrator steps: show them to me as above).

6. Videos folder: the folder this chat was started in (your current working directory) is my videos folder. Show me its full path. Then run
   reel-tool autostart on --folder "<that folder>"
   so the phone upload page starts by itself every time I log in. Autostart: [yes]  (if I changed this to no, skip the command and tell me that  reel-tool phone-link --start  starts the page by hand). Then run  reel-tool shortcut on  so I get a desktop icon that starts the page and shows the phone link.

7. Run  reel-tool phone-link --start --open . In your reply, show me the phone link and the QR code from its output (in a code block), and tell me: scan it with the iPhone camera, open the page in Safari, tap Share, then Add to Home Screen.

8. Tell me:
   - After setup I can lower Effort to Medium (the model menu under the message box) to save usage.
   - Any question later, including Tailscale for using the phone away from home: ask in this same chat.

9. Then write this cheat sheet, exactly:
   Every day:
   1. iPhone: Reel Studio icon, choose the clips, Send.
   2. Claude app: Code, my computer's session (this same chat).
   3. Write: make a Reel (add anything special you want).
   4. Wait for Claude to say it is done.
   5. Upload page: To gallery. The Reel is in Photos.

10. End your last message with exactly this line:
   Finished. Now send /reload-plugins in this chat.
   (/reload-plugins turns Reel Studio on in this same chat.) Later, if I ask for a Reel and you cannot see the reel-studio skills, tell me to quit the Claude app completely and open this same chat again; until then, read the skills in the installed copy and use reel-tool by its full path.

Touch nothing else.
```
