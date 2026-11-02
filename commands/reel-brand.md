---
description: Create or change a brand profile: colours, logo, wordmark, fonts, language, subtitle style. Generates a theme with contrast checks and a palette sheet.
argument-hint: "[brand name or a change to make]"
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *), Read, Write, AskUserQuestion
---

You run a short brand wizard. Several profiles can exist (one per account). Request: $ARGUMENTS

Run `reel-tool brand list` first. Then gather, asking as little as possible, in the user's language (at most 2 rounds of questions; offer good defaults; skip what they already said):
- **Name** of the brand and the Instagram handle.
- **Main colour** (a hex code, or a word such as "forest green" that you turn into hex). Optionally a second colour and one accent. No accent given: the tool picks a complement.
- **Light or dark** scenes. Default light.
- **Fonts:** Montserrat is the default. Offer Plus Jakarta Sans, Inter, Poppins, Manrope, Oswald, or their own .ttf file.
- **Wordmark** text or a logo file (path), for faceless Reels. Optional.
- **Spoken language(s)** and the **phone model** they film with, optional: they let a clip find its brand by itself.
- **Subtitle style:** the default is white heavy text with a black outline and the spoken word in lemon yellow. Change only if they ask. Colours to avoid, if any.

Then run:
`reel-tool brand new --name "..." --primary "#..." [--secondary "#..."] [--accent "#..."] [--mode light|dark] [--font "..."] [--body-font "..."] [--font-file path] [--wordmark "..."] [--logo path] [--handle "@..."] [--language en] [--devices "iPhone 15"] [--avoid "purple"] [--sub-color "#..."] [--sub-active "#..."] [--sub-font "..."] [--title-color "#..."] [--default]`

It prints a WCAG contrast table (normal text 4.5:1, large text and graphics 3:1) and writes `palette.png`, and it nudges colours until they pass. Read the palette image and judge it: is the accent clearly different from the main colour, does it look like the brand? If not, run again with a better accent. Exit code 1 means a pair still fails or an avoided hue is present: fix the input colours and re-run.

Report in plain words: the colours (hex and role), why the accent was chosen, and the path of `palette.png`. `reel-tool brand use <slug>` switches the default.
