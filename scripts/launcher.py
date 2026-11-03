"""Reel Studio launcher. A copy lives in <data>/autostart/launch.py; the upload page autostart and the desktop shortcut call it
with the private venv's Python:   launch.py <reel-tool command> [args] [--log FILE]
It finds the newest installed copy of the plugin (so it keeps working after updates), points reel-tool at this data dir and
runs the command in-process. --log sends all output to FILE (needed when started without a console, e.g. pythonw).
"""
import glob, json, os, re, runpy, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent


def version_key(root):
    """the plugin's own version (plugin.json), so the newest copy wins wherever it lives"""
    try:
        v = json.load(open(root / ".claude-plugin" / "plugin.json", encoding="utf-8")).get("version", "0")
    except (OSError, ValueError):
        v = root.name
    return [int(x) for x in re.findall(r"\d+", v)] or [0]


def plugin_root():
    rec = {}
    try:
        rec = json.load(open(HERE / "root.json", encoding="utf-8"))
    except (OSError, ValueError):
        pass
    cfg = Path(rec.get("config_dir") or os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    found = [Path(p).parents[1] for p in glob.glob(str(cfg / "plugins" / "cache" / "*" / "reel-studio" / "*" / "scripts" / "cli.py"))]
    cands = [r for r in found + ([Path(rec["root"])] if rec.get("root") else []) if (r / "scripts" / "cli.py").exists()]
    if cands:
        return max(cands, key=version_key)                      # stable sort: on a tie the plugin cache copy wins
    raise SystemExit("Reel Studio is not installed any more: run /reel-setup in Claude Code")


def main():
    args = sys.argv[1:]
    if "--log" in args:
        i = args.index("--log"); log = Path(args[i + 1]); del args[i:i + 2]
        log.parent.mkdir(parents=True, exist_ok=True)
        if log.exists() and log.stat().st_size > 5 * 1024 * 1024:  # keep the log small: start a new one past 5 MB
            os.replace(log, log.with_suffix(".old.log"))
        sys.stdout = sys.stderr = open(log, "a", encoding="utf-8", buffering=1)
    os.environ["REEL_STUDIO_DATA"] = str(DATA)
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.chdir(DATA)
    cli = plugin_root() / "scripts" / "cli.py"
    sys.argv = [str(cli)] + args
    sys.path.insert(0, str(cli.parent))
    runpy.run_path(str(cli), run_name="__main__")


if __name__ == "__main__":
    main()
