# Reel Studio

A Claude Code plugin that turns raw talking-head clips into finished 1080x1920 Instagram Reels from a short request. Say "edit this", "монтируй" or "zrób z tego rolkę" and you get: retakes, false starts and pauses cut; a cleaned voice at -14 LUFS; word-timed subtitles; stickers and a calm camera; full-screen motion graphics drawn new for your script; and hard quality gates that a Reel must pass before it is delivered.

Install guides in other languages: [Русский](docs/INSTALL.ru.md) · [Polski](docs/INSTALL.pl.md)

## Requirements

- A Claude plan that includes Claude Code (Pro or Max), and the Claude Code CLI
- One of:
  - **Windows 10/11, x64**, with [Git for Windows](https://git-scm.com/download/win)
  - **Linux, x86-64**: Ubuntu 22.04 or 24.04, or a distribution built on them (Zorin OS, Linux Mint, Pop!_OS)
  - **macOS on Apple Silicon** (M1 or newer). Intel Macs are not supported
- `git`, `curl` and `tar` (see your system below)
- About 10 GB of free disk: 5-8 GB for the tools and models (more with an NVIDIA GPU), the rest for work
- Internet for the one-time setup

An NVIDIA GPU is optional (Windows and Linux). It makes the speech steps about 10 times faster; the result is the same. On a Mac, speech runs on the CPU, which adds a few minutes per Reel.

Your clips stay on your computer. Claude reads what it needs to do the job (transcripts and sample frames), as in any Claude Code session.

## Install

The `/plugin` command works only in the **terminal CLI** (`claude` in a terminal), not in the desktop app. The desktop app uses the plugin once it is installed. Run these two lines in a terminal:

```bash
claude plugin marketplace add SirOxygenFish/reel-studio
```

```bash
claude plugin install reel-studio@siroxygenfish
```

The same inside an interactive `claude` session: `/plugin marketplace add SirOxygenFish/reel-studio`, then `/plugin install reel-studio@siroxygenfish`. Add `--scope project` to the install to enable it in one project only.

Then start Claude Code (CLI or desktop app) and run:

```
/reel-setup
```

It installs private copies of Python, ffmpeg, Node, a headless browser, the voice model, the face detector, the fonts and the speech model into the plugin's data folder. It changes nothing system-wide, never asks for an administrator password, is safe to re-run, and takes 10-30 minutes the first time. When the first command asks for permission, "always allow `reel-tool`" saves many prompts.

Finally:

```
/reel-doctor
```

It checks every piece and, for anything missing, prints the exact command that fixes it.

### Windows

1. Install Git for Windows if you do not have it. In PowerShell:

   ```powershell
   winget install --id Git.Git -e
   ```

2. Restart the terminal, then run the two install lines and `/reel-setup` as above.

Paths with spaces and non-Latin letters (for example `C:\Users\Анна\Видео`) are fine.

### Linux (Ubuntu, Zorin OS, Mint)

1. Make sure `git`, `curl` and `tar` are there:

   ```bash
   sudo apt install -y git curl tar
   ```

2. Run the two install lines and `/reel-setup` as above.
3. Run `/reel-doctor`. The headless browser needs a few system libraries that a desktop usually has already. If any are missing, doctor prints one line to copy, for example:

   ```bash
   sudo apt install -y libnspr4 libnss3 libasound2t64
   ```

   These are the only steps that use `sudo`, and you run them yourself.

With an NVIDIA card, install the normal NVIDIA driver from your distribution; setup brings its own CUDA libraries.

### macOS (Apple Silicon)

1. If `git` is missing, macOS offers to install the Command Line Tools the first time you type `git` in Terminal. Accept, or run:

   ```bash
   xcode-select --install
   ```

2. Run the two install lines and `/reel-setup` as above.

Everything goes into the plugin's data folder in your home folder; nothing needs `sudo`.

## Quickstart

1. Optional: `/reel-brand` creates a brand profile (colours, fonts, wordmark, subtitle style) with contrast checks and a palette sheet. Without one, a neutral look is used. To try the looks first: `reel-tool brand example northwind` (light) or `reel-tool brand example sunrise` (dark). Several profiles are fine, one per account.
2. Put your clips in the project folder.
3. Say `/reel`, or simply "edit this", in any language.
4. The finished Reel lands in `reels-done/`. The work folder is `reels-work/<job>/`.

You do not need to write a brief. Reel Studio inspects the clips, finds the newest unused batch, skips duplicates and finished Reels, detects the language, the brand (by camera and language) and whether it is a skit or a correction of an earlier Reel, writes the full brief itself, and asks at most one or two questions, only when the answer changes the result.

Ask for something specific when you want it: "only my face, no animation", "no face, only animation", "use the Sunrise brand", "title: Stop discounting", "this was recorded over the phone" (a voice preset for weak audio).

## What you can say

| You say | You get |
|---|---|
| edit this / монтируй / zmontuj / make it nice / add anims | Hybrid: face plus full-screen animation |
| only face, no animation | Face edit with subtitles, stickers and a slow push-in |
| no face, only animation | Your voice over motion graphics |
| a clip with two roles | Skit: timing kept, emoji accents only, each voice its own subtitle colour |
| a new clip plus "this is a fix for the last Reel" | Correction: the finished cut stays, only the re-said lines change |

## Commands

| Command | What it does |
|---|---|
| `/reel` | The main entry point |
| `/reel-setup` | Installs everything; safe to repeat |
| `/reel-brand` | Brand wizard |
| `/reel-doctor` | Checks everything; `--full` also runs a test render; `--clear-cache` frees the render caches |
| `/reel-upload-page` | Phone upload page, local network and Tailscale only |

## Quality gates

A Reel is delivered only if it passes all of these: format; motion, and animation that keeps moving; no dead stretches; safe zones (nothing under the subtitles or Instagram's buttons); every circle really round on every frame; scene variety across your last Reels; no dropped stickers and a minimum hold for every text; only your own words on screen; no health or income claims in visuals; -14 LUFS; stutter passes on the cut and on the final; no word lost in the cut; no repeated phrases; eye contact and idle-mouth reviews; and a visual review.

## Phone uploads

`/reel-upload-page` starts a small page: open the printed link on your phone, on the same Wi-Fi or over [Tailscale](https://tailscale.com). Clips land in the input folder with an optional note; finished Reels can be downloaded from the same page. It refuses any address outside private networks and your tailnet, and the link carries a private key. Do not forward the port to the internet.

## Configuration

`reel-tool config` shows the settings; `reel-tool config output_folder "D:/Reels"` changes one. Keys: `default_format` (hybrid, face, faceless), `default_brand`, `input_folder`, `output_folder`, `work_folder`, `language`, `whisper_model`, `cache_days`, `cache_keep`. A `reel-studio.json` in a project overrides them for that project. Subtitle style lives in the brand profile.

Your data (brands, the variety ledger, your bespoke scenes, the list of clips already edited) and the installed tools live in the plugin's data folder (`~/.claude/plugins/data/reel-studio-siroxygenfish`) and survive updates. Uninstalling removes it unless you use `claude plugin uninstall --keep-data`.

## Good to know

- Your original files are never changed or deleted. A new version of a Reel moves the older one to `reels-done/_old/`.
- Each Reel takes about 15-40 minutes of Claude's work, because the animations are designed for your script. On a Pro plan, a long Reel can use a good part of a usage window.
- Render caches (often 1-2 GB a job) are removed automatically for jobs delivered more than 14 days ago; the newest 5 keep theirs.

## Licence

MIT, see [LICENSE](LICENSE). Third-party parts and their licences: [THIRD_PARTY.md](THIRD_PARTY.md). Heavy third-party tools are downloaded during setup, never bundled.
