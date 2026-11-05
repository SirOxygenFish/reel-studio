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
2. **Watch Tutorial 1** (about 80 seconds, it shows every click below): [English](https://github.com/SirOxygenFish/reel-studio/raw/main/docs/tutorials/tutorial1-pc.en.mp4) · [Русский](https://github.com/SirOxygenFish/reel-studio/raw/main/docs/tutorials/tutorial1-pc.ru.mp4) · [Polski](https://github.com/SirOxygenFish/reel-studio/raw/main/docs/tutorials/tutorial1-pc.pl.mp4). The video opens or downloads; play it.
3. **Open Code.** At the top left, click the **</>** icon. The tab is called **Code** (this is Claude Code).
4. **Two switches.** Your name at the bottom left, then **Settings**, then **Claude Code**, then scroll to **Remote Control**:
   - **Connect new sessions to Remote Control**: turn **on**
   - **Let your phone and claude.ai start sessions here**: leave **off**
   - **Keep this computer awake for Remote Control**: turn **on**

   Do this before the next step.
5. **A new chat.** Click **New**. Under the message box:
   - the first menu: choose **This computer**
   - **Choose…**, then **Open folder…**: create a new folder anywhere you like (for example **Reels**) and choose it. This folder becomes your videos folder.
   - the model: choose **Opus 5.5**, then **Effort**, then **High**
   - **Accept edits**: change it to **Auto**
6. **Install.** Copy the whole text from [the install prompt](INSTALL_PROMPT.md), paste it into this chat and send it. When Claude asks for permission, click **Allow**. If it shows you a command that needs an administrator password, paste it where it says and tell Claude when it is done. The setup takes 10 to 30 minutes.
7. **Turn Reel Studio on in this chat.** When Claude says it has finished, type **/reload-plugins** in the same chat and send it. If Claude still does not know Reel Studio after that, quit the Claude app completely (also from the taskbar tray or the menu bar), open it again and open the same chat.
8. **Keep using this chat.** This is your Reel Studio chat from now on, also from the phone. Do not start a new one: this chat already knows your setup. After setup you can lower **Effort** to **Medium** to save usage. If anything is unclear later (Tailscale, errors, changes), just ask this same chat in plain words.

## 3. On the iPhone, once

1. **Open the upload page.** At the end of the install, the computer showed a QR code (the desktop icon **Reel Studio phone link** shows it again). Scan it with the iPhone camera and open the page in Safari. The phone must be on the same Wi-Fi as the computer.
2. **Add SaveReel.** It saves a finished Reel into Photos. On the page, tap **Install SaveReel**. Safari asks to open it in Shortcuts: tap **Open**, then **Add Shortcut**, then **Done**. The first time you tap **To gallery**, iPhone asks for access: tap **Always Allow**. If it does not work, see the last section of this page.
3. **Put the page on the Home Screen.** Still in Safari, tap **Share**, then **Add to Home Screen**, then **Add**.
4. **Watch Tutorial 2**: on the upload page, tap **How to**. It plays from your computer, in the page's language.
5. **Instagram at full quality.** In Instagram open your profile, the menu (three lines), type **quality** in the settings search and turn on **Upload at highest quality**; otherwise Instagram compresses your Reels more.

## 4. Optional: away from home

The upload page only answers at home, on your own Wi-Fi. To use it anywhere, you need the free **Tailscale** app on the computer and on the iPhone ([tailscale.com/download](https://tailscale.com/download)). Ask your Claude chat to walk you through it, for example: "help me set up Tailscale". When it works, the desktop icon **Reel Studio phone link** shows a second QR code for "away from home": add that one to the Home Screen too.

## 5. Every day

1. iPhone: **Reel Studio** icon, choose the clips, **Send**.
2. Claude app: **Code**, your computer's session (the same chat as always).
3. Write: **make a Reel** (add anything special you want).
4. Wait for Claude to say it is done.
5. Upload page: **To gallery**. The Reel is in Photos.

## Last resort: build SaveReel by hand

Only if **Install SaveReel** did not work.

1. Open **Shortcuts** and tap **+**.
2. Add the action **Get Contents of URL** (search for "URL") and set its address to **Shortcut Input**.
3. Add the action **Save to Photo Album** (search for "album").
4. Rename the shortcut to exactly **SaveReel**. The first time it runs, tap **Allow**.
