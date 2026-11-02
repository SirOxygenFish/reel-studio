"""reel-tool recut <job> [--drop A-B ...] [--in K T] [--out K T] [--tail T] [--delete K] [--move K POS] [--fix "IDX=word" ...] [--fix "OLD=NEW" ...]

Edit the cut without ever touching subtitles by hand. Times of --drop are REEL seconds (as in transcript.txt); --in/--out set
piece K's source in/out point (see `reel-tool recut <job>` with no options for the table of pieces). Everything derived
(words.json, cuts.json, transcript.txt, the stutter audio) is rebuilt, and old render products are invalidated.
"""
import json, re, sys
from pathlib import Path

import common as C
from autocut import derive, out_time_map


def drop_range(cut, a, b):
    """remove Reel time [a, b): the pieces it touches are shortened or split"""
    pieces, new = cut["pieces"], []
    offs, _ = out_time_map(pieces)
    for p, off in zip(pieces, offs):
        L = p["b"] - p["a"]; pa, pb = off, off + L
        if b <= pa or a >= pb:
            new.append(p); continue
        keep = []
        if a > pa + 0.02:
            keep.append((p["a"], p["a"] + (a - pa)))
        if b < pb - 0.02:
            keep.append((p["a"] + (b - pa), p["b"]))
        for j, (x, y) in enumerate(keep):
            mine = [w for w in p["words"] if x <= (w[0] + w[1]) / 2 <= y]
            new.append(dict(p, a=round(x, 3), b=round(y, 3), words=mine, joint=p.get("joint") if j == 0 else "jump"))
    cut["pieces"] = new


def main(argv):
    job = C.job_dir(argv[0]); argv = argv[1:]
    cut = C.load_json(job / "cut.json") or C.fail("no cut.json: run reel-tool analyze first")
    changed = False; i = 0; fixes = []
    while i < len(argv):
        k = argv[i]
        if k == "--drop":
            a, b = map(float, argv[i + 1].split("-")); drop_range(cut, a, b); changed = True; i += 2
        elif k in ("--in", "--out"):
            n, t = int(argv[i + 1]), float(argv[i + 2]); cut["pieces"][n]["a" if k == "--in" else "b"] = t
            p = cut["pieces"][n]; p["words"] = [w for w in p["words"] if p["a"] <= (w[0] + w[1]) / 2 <= p["b"]]; changed = True; i += 3
        elif k == "--tail":
            cut["pieces"][-1]["b"] = cut["pieces"][-1]["b"] + float(argv[i + 1]); changed = True; i += 2
        elif k == "--move":
            n, to = int(argv[i + 1]), int(argv[i + 2]); cut["pieces"].insert(to, cut["pieces"].pop(n)); changed = True; i += 3
        elif k == "--delete":
            del cut["pieces"][int(argv[i + 1])]; changed = True; i += 2
        elif k == "--fix":
            fixes.append(argv[i + 1]); i += 2
        else:
            C.fail("unknown option " + k)
    if fixes:
        allw = [w for p in cut["pieces"] for w in p["words"]]
        for f in fixes:
            old, new = f.split("=", 1)
            if old.isdigit():
                allw[int(old)][2] = new
            else:
                n = 0
                for w in allw:
                    if w[2] == old or re.sub(r"[.,;:?!]+$", "", w[2]).lower() == old.lower():
                        tail = re.search(r"[.,;:?!]+$", w[2]); w[2] = new + (tail.group() if tail and not re.search(r"[.,;:?!]$", new) else ""); n += 1
                print(f"fixed {n} x {old} -> {new}")
        changed = True
    if changed:
        total, _ = derive(job, cut)
        for f in ("gate.json", "final.mp4.gate"):
            (job / f).unlink(missing_ok=True)
        print(f"cut updated: {len(cut['pieces'])} pieces, {total:.2f} s. Run reel-tool stutter and subs again.")
    offs, total = out_time_map(cut["pieces"])
    k = 0
    for i, (p, off) in enumerate(zip(cut["pieces"], offs)):
        txt = " ".join(f"[{k + j}]{w[2]}" if j == 0 else w[2] for j, w in enumerate(p["words"]))[:90]; k += len(p["words"])
        print(f"{i:3d} reel {off:6.2f}-{off + p['b'] - p['a']:6.2f}  {Path(p['file']).name} {p['a']:7.2f}-{p['b']:7.2f} {p.get('joint', ''):5s} {txt}")
    print(f"total {total:.2f} s")


if __name__ == "__main__":
    main(sys.argv[1:])
