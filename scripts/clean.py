"""reel-tool clean [job ...] [--all] [--keep N] [--days D] [--dry-run]

Removes the render caches of finished jobs: pieces/, stab/, _motion clips, _build, the 16 kHz copies of the audio. They are
large (often 1-2 GB a job) and are rebuilt by the next render if needed. Never touched: the clips, final.mp4, job.json, job.md,
cut.json, visuals.json, scenes/, subtitles, reports, and anything in the output folder.

Without arguments: jobs delivered more than --days ago (default from config cache_days, 14), except the newest --keep (default
cache_keep, 5). `deliver` runs this automatically. `--all` = every job's caches (what /reel-doctor --clear-cache does).
"""
import shutil, sys, time
from pathlib import Path

import common as C

CACHE_DIRS = ("pieces", "stab", "_build")
CACHE_GLOBS = ("_motion/*.mkv", "_motion/_build", "kept16k.wav", "final16k.wav", "_fonts")


def size(p: Path) -> int:
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.exists() else 0


def clean_job(job: Path, dry=False) -> int:
    freed = 0
    for d in CACHE_DIRS:
        p = job / d
        if p.exists():
            freed += size(p)
            dry or shutil.rmtree(p, ignore_errors=True)
    for g in CACHE_GLOBS:
        for p in job.glob(g):
            freed += size(p)
            if not dry:
                shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    return freed


def auto(keep=None, days=None, dry=False, quiet=False) -> int:
    cfg = C.config(); keep = int(cfg.get("cache_keep", 5) if keep is None else keep); days = float(cfg.get("cache_days", 14) if days is None else days)
    work = C.folders(cfg)["work"]
    done = sorted((j.parent for j in work.glob("*/delivery.json")), key=lambda d: (d / "delivery.json").stat().st_mtime, reverse=True)
    freed = 0
    for d in done[keep:]:
        if time.time() - (d / "delivery.json").stat().st_mtime > days * 86400:
            freed += clean_job(d, dry)
    if not quiet:
        print(f"{'would free' if dry else 'freed'} {freed / 1048576:.0f} MB of render caches ({len(done)} delivered jobs, kept the newest {keep}, older than {days:g} days cleaned)")
    return freed


def main(argv):
    dry = "--dry-run" in argv
    opt = lambda k: argv[argv.index(k) + 1] if k in argv else None
    jobs = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--keep", "--days"))]
    if "--all" in argv:
        work = C.folders()["work"]; freed = sum(clean_job(j.parent, dry) for j in work.glob("*/job.json"))
        print(f"{'would free' if dry else 'freed'} {freed / 1048576:.0f} MB of render caches in {work}")
    elif jobs:
        for j in jobs:
            print(f"{j}: {'would free' if dry else 'freed'} {clean_job(C.job_dir(j), dry) / 1048576:.0f} MB")
    else:
        auto(opt("--keep"), opt("--days"), dry)


if __name__ == "__main__":
    main(sys.argv[1:])
