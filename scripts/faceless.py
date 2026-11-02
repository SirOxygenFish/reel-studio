"""reel-tool faceless <job>: voice + full-screen motion graphics, no face.

Needs words.json and subs.ass (reel-tool subs), storyboard.json (written for this Reel), job.md complete.
The voice comes from the cut (raw) and goes through the chain once; with --voice file.wav an already cleaned voice is used as is.
"""
import os, subprocess, sys
from pathlib import Path

import common as C
import render, voice_chain


def main(argv):
    job = C.job_dir(argv[0]).resolve(); os.chdir(job)
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    J = C.job_sync(job); cut = C.load_json("cut.json") or C.fail("no cut.json")
    if not Path("storyboard.json").exists():
        C.fail("no storyboard.json")
    if "TODO" in Path("job.md").read_text(encoding="utf-8"):
        C.fail("job.md is not complete")
    B = C.brand(J.get("brand"))
    if opt("--voice"):
        import shutil
        shutil.copy(opt("--voice"), "voice.wav")
    else:
        infos = {x["file"]: x for x in J["info"]}; ps = []
        for k, p in enumerate(cut["pieces"]):
            ps.append(render.build_piece(job, k, p["file"], p["a"], p["b"], infos[p["file"]])[0])
        Path("_list.txt").write_text("".join(f"file 'pieces/{p.name}'\n" for p in ps), encoding="utf-8")
        r = C.ff("-f", "concat", "-safe", "0", "-i", "_list.txt", "-vn", "-c:a", "pcm_s16le", "_raw.wav")
        if r.returncode:
            C.fail(r.stderr[-400:])
        vr = voice_chain.run("_raw.wav", "voice.wav", "auto", preset=J.get("voice_preset"))
        C.save_json("voice_report.json", vr)
        Path("_raw.wav").unlink(missing_ok=True); Path("_list.txt").unlink(missing_ok=True)
    S = C.load_json("storyboard.json")
    S.update({"theme": S.get("theme") or B["theme"], "words": "words.json", "voice": "voice.wav", "subs": "subs.ass"})
    S.setdefault("sfx", True)
    import hybrid_paths
    S["extra_js"] = hybrid_paths.library_js(S.get("scenes", []))
    C.save_json("storyboard.json", S)
    fonts = C.sub_font(B["subs"])[1]
    ev = C.run_env(); ev["RS_SUB_FONTS"] = fonts
    r = subprocess.run([C.node(), str(C.MOTION / "engine" / "render.mjs"), "storyboard.json", "--out", "final.mp4", "--report", "report.json"], env=ev)
    if r.returncode:
        C.fail("engine render failed")
    Path("gate.json").unlink(missing_ok=True)
    print(f"final.mp4: {C.duration('final.mp4'):.2f} s. next: reel-tool gate {job.name}")


if __name__ == "__main__":
    main(sys.argv[1:])
