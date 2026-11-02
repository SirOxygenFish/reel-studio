"""reel-tool: dispatcher. Every step of a Reel goes through here, so a job needs no ad-hoc scripts.

Job, in order:
  scan [files] [--note "request"]     find the clips, duplicates, notes; creates the job
  analyze <job> [--lang xx] [--skit]  transcribe, pick takes, cut pauses -> transcript.txt, decisions.md
  brief <job>                         writes job.md; complete every TODO
  pieces <job>                        build the cut pieces (needed before sheets)
  recut <job> [--drop A-B ...]        change the cut; no options = table of pieces
  stutter <job>                       both stutter passes, every flag voted
  wordcheck <job>                     re-hear the whole cut: no word may go missing
  stabilize <job>                     vidstab for hand-held clips, used only if shake drops 30 %+
  vote <job> A-B [A-B ...]            re-hear a doubtful stretch 6 ways (Reel seconds): what was really said?
  jump <job> | bestcut <job> K        gesture check at the joins
  skit-pauses <job> [--apply]         shorten long skit pauses at calm frames
  sheets <job>                        qf/eyes.jpg, qf/mouth.jpg to look at
  subs <job> --title "a|b" ...        subtitles and title
  scene-kit                           prints the scene API (for writing bespoke scenes)
  scene-list [word]                   stock + library scenes, with what each one is
  scene-show <type>                   the code of a library scene
  preview <job> <segment> [--at t,t]  stills of one animation segment -> _motion/preview/sheet.jpg
  render <job>                        final.mp4
  segsheet <job>                      qf/segs.jpg
  mark <job> eyes|mouth|visual "..."  record a visual review
  gate <job>                          all quality gates
  deliver <job> "Name"                copy to the output folder (only after a PASS)
Other:
  faceless <job>      voice + motion graphics render from storyboard.json
  ring <job>          ring.wav for a skit that opens with a phone call
  voice IN OUT        the voice chain alone
  emoji name | --find word
  icon --find word    Phosphor / Tabler icon names for scenes
  clean [job|--all]   remove render caches of finished jobs (automatic after deliver)
  brand ...           see brand.py
  doctor [--full]     check everything
  config [key value]  show or change the user config
  upload-page         phone upload page
  status [job]        where a job stands
"""
import json, runpy, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import common as C

MODS = {"scan": "scan", "analyze": "autocut", "brief": "brief", "recut": "recut", "stutter": "stutter_check", "subs": "make_subs", "render": "render",
        "gate": "gate", "deliver": "deliver", "voice": "voice_chain", "emoji": "emoji_png", "brand": "brand", "doctor": "doctor", "preview": "preview",
        "faceless": "faceless", "upload-page": "upload", "scene-list": "scenes", "scene-kit": "scenes", "pieces": "scenes", "status": "scenes", "config": "scenes", "scene-show": "scenes", "ring": "scenes", "vote": "vote", "wordcheck": "wordcheck", "clean": "clean", "icon": "scenes", "stabilize": "stabilize", "skit-pauses": "skit_pauses"}


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("help", "-h", "--help"):
        print(__doc__); return
    cmd, rest = a[0], a[1:]
    if cmd in ("jump", "bestcut", "sheets", "segsheet", "mark"):
        import checks
        checks.main(cmd, rest); return
    if cmd not in MODS:
        C.fail(f"unknown command {cmd}; reel-tool help lists them")
    mod = __import__(MODS[cmd])
    if MODS[cmd] == "scenes":
        mod.main(cmd, rest)
    else:
        mod.main(rest)


if __name__ == "__main__":
    main()
