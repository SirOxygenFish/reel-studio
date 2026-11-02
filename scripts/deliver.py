"""reel-tool deliver <job> ["Reel name"]: the only way a Reel reaches the output folder.

Refuses unless gate.json says PASS for exactly this final.mp4. Never overwrites: a file of the same name moves to _old/ first
(with " v1", " v2" ...). Updates the variety ledger of the brand, the inputs ledger (so a clip is recognised next time) and
the jobs ledger (so a re-shoot of the same script is recognised), and writes delivery.json for the final report.
"""
import datetime, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

import common as C


def safe_name(n):
    n = re.sub(r"[—–]", "-", n)
    n = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", n)
    return re.sub(r"\s{2,}", " ", n).strip(" .") or "Reel"


def main(argv):
    job = C.job_dir(argv[0]).resolve(); os.chdir(job)
    J = C.job_sync(job); G = C.load_json("gate.json") or C.fail("no gate.json: run reel-tool gate first")
    h = hashlib.sha256(Path("final.mp4").read_bytes()).hexdigest()
    if not G.get("pass"):
        C.fail("the gate has not passed; fix the failures: " + "; ".join(r["check"] for r in G["rows"] if not r["ok"]))
    if G.get("sha256") != h:
        C.fail("final.mp4 changed after the gate: run reel-tool gate again")
    name = safe_name(argv[1] if len(argv) > 1 else C.job_name(job, J))
    F = C.folders(); out = F["output"]; out.mkdir(parents=True, exist_ok=True)
    dst = out / (name + ".mp4")
    if dst.exists():
        old = out / "_old"; old.mkdir(exist_ok=True); n = 1
        while (old / f"{name} v{n}.mp4").exists():
            n += 1
        shutil.move(str(dst), str(old / f"{name} v{n}.mp4"))
        print(f"older version moved to _old/{name} v{n}.mp4")
    shutil.copy2("final.mp4", dst)
    B = C.brand(J.get("brand"))
    vf = "visuals_variety.json" if Path("visuals_variety.json").exists() else "visuals.json"
    if (C.load_json(vf, {}) or {}).get("hybrid", {}).get("segments"):
        subprocess.run([sys.executable, str(C.MOTION / "tools" / "variety.py"), "add", vf, "--name", name, "--account", B["slug"]]
                       + (["--replaces", "|".join(C.replaced_names(J))] if C.replaced_names(J) else []), env=C.run_env())
    if Path("scenes").is_dir():                              # this Reel's bespoke scenes join the user's library
        C.USER_LIB.mkdir(parents=True, exist_ok=True)
        for f in Path("scenes").glob("*.js"):
            shutil.copy2(f, C.USER_LIB / f.name)
    L = C.load_json(C.INPUTS_LEDGER, {"clips": {}}) or {"clips": {}}
    for x in J.get("info", []):
        if x.get("audio_md5"):
            L["clips"][x["audio_md5"]] = {"name": x["name"], "job": J["job"], "output": str(dst), "date": datetime.date.today().isoformat()}
    C.save_json(C.INPUTS_LEDGER, L)
    jl = C.load_json(C.JOBS_LEDGER, {"jobs": []}) or {"jobs": []}
    W = C.load_json("words.json", {"words": []})
    jl["jobs"] = [j for j in jl["jobs"] if j.get("job") != J["job"]]
    jl["jobs"].append({"job": J["job"], "name": name, "output": str(dst), "brand": B["slug"], "date": datetime.date.today().isoformat(),
                       "transcript": " ".join(w[2] for w in W["words"])})
    C.save_json(C.JOBS_LEDGER, jl)
    C.save_json("delivery.json", {"name": name, "file": str(dst), "seconds": G.get("duration"), "lufs": G.get("lufs"), "motion": G.get("motion"), "bespoke": G.get("bespoke")})
    print(f"delivered: {dst}\nlength {G.get('duration'):.1f} s, loudness {G.get('lufs')} LUFS")
    import clean                                            # older finished jobs give their render caches back
    clean.auto(quiet=False)


if __name__ == "__main__":
    main(sys.argv[1:])
