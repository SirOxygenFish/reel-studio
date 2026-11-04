# Reel Studio: start here

Reel Studio turns the clips you film on your iPhone into finished Instagram Reels. You send the clips from the phone, write one word to Claude, and the finished Reel comes back to your Photos. The editing runs on your computer. This page is everything you do yourself, once, in this order.

Other languages: [Русский](START_HERE.ru.md) · [Polski](START_HERE.pl.md)

## 1. What you need

- A Claude **Pro or Max** plan.
- A computer with one of:
  - Windows 10 or 11 (64-bit)
  - a Mac with an Apple processor (M1 or newer). Intel Macs do not work.
  - Linux based on Ubuntu 22.04 or 24.04 (for example Zorin OS or Linux Mint)
- About **10 GB** of free disk space and internet for the first setup.
- An iPhone with the **Claude** app, signed in with the same account.

The computer does the work, so it has to be switched on with the Claude app open (minimised is fine) whenever you send clips.

## 2. On the computer, once

1. **Install the Claude desktop app** from [claude.ai/download](https://claude.ai/download) and sign in.
2. **Watch Tutorial 1** (40 seconds): [English](https://github.com/SirOxygenFish/reel-studio/raw/main/docs/tutorials/tutorial1-pc.en.mp4) · [Русский](https://github.com/SirOxygenFish/reel-studio/raw/main/docs/tutorials/tutorial1-pc.ru.mp4) · [Polski](https://github.com/SirOxygenFish/reel-studio/raw/main/docs/tutorials/tutorial1-pc.pl.mp4). The video opens or downloads; play it.
3. **Two switches.** In the app: your name at the bottom left, then **Settings**, then **Claude Code**, then scroll to **Remote Control**:
   - **Connect new sessions to Remote Control**: turn **on**
   - **Let your phone and claude.ai start sessions here**: leave **off**
   - **Keep this computer awake for Remote Control**: turn **on**
4. **Install.** Open the **Code** tab, start a **New session** (any folder), copy the whole text from [the install prompt](INSTALL_PROMPT.md) and send it. Claude asks for permission before it runs commands: allow them. If it shows you a command that needs an administrator password, paste it where it says and tell Claude when it is done. The setup takes 10 to 30 minutes.
5. **The videos folder.** When Claude says it is finished, close that session and start a **New session** in the videos folder it names (normally `Reels` in your Videos folder, or in Movies on a Mac). This is the session you will use every day from the phone. Leave it open.

## 3. On the iPhone, once

1. **Open the upload page.** At the end of the install, the computer showed a QR code (the desktop icon **Reel Studio phone link** shows it again). Scan it with the iPhone camera and open the page in Safari. The phone must be on the same Wi-Fi as the computer.
2. **Add SaveReel.** It saves a finished Reel into Photos. On the page, tap **Install SaveReel**, then **Add Shortcut** at the bottom. The first time it runs, tap **Allow**. If nothing opens, tap **Does not open? Download the file** under the button, then open the downloaded file. If even that fails, see the last section of this page.
3. **Put the page on the Home Screen.** Still in Safari, tap **Share**, then **Add to Home Screen**, then **Add**.
4. **Watch Tutorial 2**: on the upload page, tap **How to**. It plays from your computer, in the page's language.

## 4. Optional: away from home

The upload page only answers at home, on your own Wi-Fi. To use it anywhere, install the free **Tailscale** app on the computer and on the iPhone ([tailscale.com/download](https://tailscale.com/download)), sign in to both with the same account and switch it on. Then the desktop icon **Reel Studio phone link** shows a second QR code for "away from home": add that one to the Home Screen too.

## 5. Every day

1. iPhone: **Reel Studio** icon, choose the clips, **Send**.
2. Claude app: **Code**, your computer's session.
3. Write: **make a Reel** (add anything special you want).
4. Wait for Claude to say it is done.
5. Upload page: **To gallery**. The Reel is in Photos.

## Last resort: build SaveReel by hand

Only if **Install SaveReel** did not work.

1. Open **Shortcuts** and tap **+**.
2. Add the action **Get Contents of URL** (search for "URL") and set its address to **Shortcut Input**.
3. Add the action **Save to Photo Album** (search for "album").
4. Rename the shortcut to exactly **SaveReel**. The first time it runs, tap **Allow**.
