"""Shared paths and helpers for every Reel Studio tool.

Mutable state lives in the data dir (survives plugin updates):
    <data>/config.json                 user config (brands, default format, languages, folders, subtitle style)
    <data>/env/                        everything /reel-setup installs (venv, ffmpeg, node, chrome, models, fonts)
    <data>/brands/<slug>/              brand.json, theme.json, palette.png, usage_ledger.json
    <data>/library/                    bespoke scenes written for this user's Reels
    <data>/inputs_ledger.json          every input clip seen, with its audio hash and the job that used it
The data dir comes from REEL_STUDIO_DATA, then CLAUDE_PLUGIN_DATA, then a default under ~/.claude/plugins/data.
"""
import copy, glob, hashlib, json, os, platform, re, shutil, subprocess, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = Path(os.environ.get("RS_PROJECT") or os.getcwd())    # where the user works; steps may chdir into the job folder
MOTION = ROOT / "motion"
IS_WIN = platform.system() == "Windows"
IS_MAC = sys.platform == "darwin"
EXE = ".exe" if IS_WIN else ""

VIDEO_EXT = {".mov", ".mp4", ".m4v", ".mkv", ".webm", ".avi", ".3gp", ".mts", ".m2ts", ".hevc"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


def data_dir() -> Path:
    for k in ("REEL_STUDIO_DATA", "CLAUDE_PLUGIN_DATA"):
        v = os.environ.get(k, "").strip()
        if v:
            return Path(v)
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "plugins" / "data"
    ptr = base / ".reel-studio-data"
    if ptr.exists():
        return Path(ptr.read_text(encoding="utf-8").strip())
    hits = sorted(glob.glob(str(base / "reel-studio*")))
    return Path(hits[0]) if hits else base / "reel-studio-siroxygenfish"


DATA = data_dir()
ENVD = DATA / "env"
os.environ.setdefault("HF_HOME", str(ENVD / "hf"))      # the Whisper model lives in the data dir too, not in ~/.cache
CONFIG_FILE = DATA / "config.json"
BRANDS = DATA / "brands"
USER_LIB = DATA / "library"
INPUTS_LEDGER = DATA / "inputs_ledger.json"
JOBS_LEDGER = DATA / "jobs_ledger.json"

DEFAULT_CONFIG = {
    "version": 1,
    "language": "auto",                 # report language: auto = the language of the user's request
    "subtitle_language": "auto",        # auto = the language spoken in the clip
    "default_format": "hybrid",         # hybrid | face | faceless
    "default_brand": "default",
    "input_folder": None,               # None = the current project folder
    "output_folder": None,              # None = <project>/reels-done
    "work_folder": None,                # None = <project>/reels-work
    "whisper_model": "large-v3",
    "voice": {"atten_db": "auto"},      # DeepFilterNet limit: auto = 16 dB, 10 dB for gated/noise-suppressed mics
    "upload_page": {"port": 5080},      # + key (made on first start), folder (the videos folder for the phone page)
    "ui_lang": "auto",                  # en | ru | pl for the phone link page and shortcuts; auto = system language
    "cache_keep": 5,                    # render caches of the newest N finished jobs stay
    "cache_days": 14,                   # ...and of any job delivered in the last N days
}

# the house subtitle look: white heavy sans, black outline, active word lemon yellow
DEFAULT_SUBS = {
    "font": "auto",                     # auto = Segoe UI Black on Windows, else Montserrat Black from setup
    "font_file": None,
    "color": "#FFFFFF", "active_color": "#FFF176", "outline_color": "#000000", "outline": 7, "shadow": 4,
    "max_size": 112, "margin_v": 470, "max_words": 3,
    "title_color": "#FFF59D", "title_outline_color": "#141414", "title_size": 128, "title_outline": 8, "title_shadow": 5,
    "title_margin_v": 205, "second_voice_color": "#8FD3FF",
    "sticker_color": "#FFF176", "sticker_ink": "#1D1D1B",
}


def load_json(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except (OSError, ValueError):
        return copy.deepcopy(default)


def save_json(p, obj):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def merged(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = merged(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def config() -> dict:
    """user config over the defaults, then an optional reel-studio.json in the project over that"""
    cfg = merged(DEFAULT_CONFIG, load_json(CONFIG_FILE, {}))
    return merged(cfg, load_json(PROJECT / "reel-studio.json", {}))


def folders(cfg=None) -> dict:
    cfg = cfg or config()
    return {"input": Path(cfg["input_folder"] or PROJECT), "output": Path(cfg["output_folder"] or PROJECT / "reels-done"),
            "work": Path(cfg["work_folder"] or PROJECT / "reels-work")}


def upload_folders(cfg=None) -> dict:
    """the folders the phone page serves: the videos folder chosen at install (upload_page.folder), else the project's"""
    cfg = cfg or config(); f = (cfg.get("upload_page") or {}).get("folder")
    if not f:
        return folders(cfg)
    f = Path(f)
    return {"input": f, "output": Path(cfg["output_folder"] or f / "reels-done"), "work": Path(cfg["work_folder"] or f / "reels-work")}


def ui_lang() -> str:
    """en | ru | pl for texts the app shows by itself (phone link page, shortcuts): config ui_lang, else the system language"""
    v = (config().get("ui_lang") or "auto").lower()
    if v in ("en", "ru", "pl"):
        return v
    cand = [os.environ.get(k, "") for k in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")]
    try:
        if IS_WIN:
            import ctypes
            cand.insert(0, {0x19: "ru", 0x15: "pl"}.get(ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF, "en"))
        elif IS_MAC:
            r = subprocess.run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True, text=True, timeout=5)
            cand.insert(0, re.sub(r"[^a-zA-Z_-]", " ", r.stdout).split()[0] if r.stdout.strip() else "")
    except Exception:
        pass
    for c in cand:
        c = c.lower()
        if c.startswith(("ru", "russian")):
            return "ru"
        if c.startswith(("pl", "polish")):
            return "pl"
        if c:
            return "en"
    return "en"


def desktop_dir() -> Path:
    """the user's Desktop (OneDrive-redirected on Windows, localised on Linux, e.g. Pulpit)"""
    try:
        if IS_WIN:
            r = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"], capture_output=True, text=True, timeout=20)
            if r.stdout.strip():
                return Path(r.stdout.strip())
        elif not IS_MAC and shutil.which("xdg-user-dir"):
            r = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, timeout=5)
            if r.stdout.strip():
                return Path(r.stdout.strip())
    except Exception:
        pass
    return Path.home() / "Desktop"


def videos_dir() -> Path:
    """a sensible default videos folder: Videos\\Reels (Windows), Movies/Reels (macOS), <XDG videos>/Reels (Linux)"""
    if IS_MAC:
        return Path.home() / "Movies" / "Reels"
    base = Path.home() / "Videos"
    if not IS_WIN and shutil.which("xdg-user-dir"):
        try:
            r = subprocess.run(["xdg-user-dir", "VIDEOS"], capture_output=True, text=True, timeout=5)
            if r.stdout.strip() and Path(r.stdout.strip()) != Path.home():
                base = Path(r.stdout.strip())
        except Exception:
            pass
    return base / "Reels"


def trash(path) -> bool:
    """move a file or folder we made to the Recycle Bin / Trash instead of deleting it; False if it could not be moved"""
    p = Path(path)
    if not (p.exists() or p.is_symlink()):
        return True
    try:
        if IS_WIN:
            kind = "DeleteDirectory" if p.is_dir() else "DeleteFile"
            ps = ("Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::"
                  f"{kind}($env:RS_TRASH, 'OnlyErrorDialogs', 'SendToRecycleBin')")
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], env=dict(os.environ, RS_TRASH=str(p)), capture_output=True, timeout=60)
        elif IS_MAC:
            dst = Path.home() / ".Trash" / p.name
            n = 2
            while dst.exists():
                dst = Path.home() / ".Trash" / f"{p.stem} {n}{p.suffix}"; n += 1
            shutil.move(str(p), str(dst))
        elif shutil.which("gio") and subprocess.run(["gio", "trash", str(p)], capture_output=True, timeout=30).returncode == 0:
            pass
        else:                                                    # freedesktop trash by hand
            import time, urllib.parse
            tr = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "Trash"
            (tr / "files").mkdir(parents=True, exist_ok=True); (tr / "info").mkdir(parents=True, exist_ok=True)
            name, n = p.name, 2
            while (tr / "files" / name).exists():
                name = f"{p.stem}.{n}{p.suffix}"; n += 1
            (tr / "info" / (name + ".trashinfo")).write_text(
                f"[Trash Info]\nPath={urllib.parse.quote(str(p.resolve()))}\nDeletionDate={time.strftime('%Y-%m-%dT%H:%M:%S')}\n", encoding="utf-8")
            shutil.move(str(p), str(tr / "files" / name))
    except Exception:
        return False
    return not (p.exists() or p.is_symlink())


def brand_list() -> list:
    return sorted(p.parent.name for p in BRANDS.glob("*/brand.json"))


def brand(slug=None) -> dict:
    """brand profile: {slug, name, wordmark, handle, language, subs{...}, theme_file, ...}; bundled neutral look if none"""
    cfg = config(); slug = slug or cfg.get("default_brand") or "default"
    b = load_json(BRANDS / slug / "brand.json", None)
    if b is None:
        b = {"slug": "default", "name": "Default", "wordmark": "", "handle": "", "theme": "default"}
        slug = "default"
    b["slug"] = slug
    b["subs"] = merged(DEFAULT_SUBS, b.get("subs"))
    b["theme"] = slug if (BRANDS / slug / "theme.json").exists() else b.get("theme", "default")
    return b


def ledger_path(slug) -> Path:
    return BRANDS / slug / "usage_ledger.json"


def libraries() -> list:
    """bespoke scenes: the job's own (scenes/ in the job folder, the render's cwd), this user's, the seed library; _kit.js is in the last"""
    return [Path.cwd() / "scenes", USER_LIB, MOTION / "library"]


# ---------- tools ----------
def tool(name) -> str:
    """ffmpeg/ffprobe: the copy from setup, RS_* override, else PATH (old builds on PATH are rejected by doctor)"""
    v = os.environ.get("RS_" + name.upper())
    for c in (v, ENVD / "ffmpeg" / "bin" / (name + EXE)):
        if c and Path(c).exists():
            return str(c)
    return shutil.which(name) or name


FF, FP = tool("ffmpeg"), tool("ffprobe")


def whisper_ready(model=None) -> bool:
    """the Whisper model files are in the data dir (setup stage "whisper")"""
    model = model or config().get("whisper_model", "large-v3")
    snap = Path(os.environ["HF_HOME"]) / "hub" / f"models--Systran--faster-whisper-{model}" / "snapshots"
    return any(snap.glob("*/model.bin"))


def node() -> str:
    c = ENVD / "node" / ("node" + EXE)
    if not c.exists():
        c = ENVD / "node" / "bin" / "node"
    return str(c) if c.exists() else (shutil.which("node") or "node")


def run_env() -> dict:
    """environment for the engine and helpers"""
    e = dict(os.environ)
    e.update({"REEL_STUDIO_DATA": str(DATA), "RS_PROJECT": str(PROJECT), "RS_FFMPEG": FF, "RS_PYTHON": sys.executable, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    e["PYTHONPATH"] = str(ROOT / "scripts") + os.pathsep + e.get("PYTHONPATH", "")
    return e


def ff(*a, **kw):
    return subprocess.run([FF, "-hide_banner", "-nostdin", "-y", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def probe(path) -> dict:
    r = subprocess.run([FP, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {}


def duration(path) -> float:
    return float(probe(path).get("format", {}).get("duration") or 0)


# ---------- fonts ----------
def _sys_font(*names):
    if not IS_WIN:
        return None
    root = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    for n in names:
        if (root / n).exists():
            return str(root / n)
    return None


def sub_font(subs=None) -> tuple:
    """(family name for libass, ttf path): the brand's choice, else the heavy system sans, else the font from setup"""
    subs = subs or DEFAULT_SUBS
    if subs.get("font_file") and Path(subs["font_file"]).exists():
        return subs["font"], subs["font_file"]
    if subs.get("font") not in (None, "auto"):
        for f in sorted((ENVD / "fonts" / "ttf").glob("*.ttf")):
            if subs["font"].lower().replace(" ", "") in f.stem.lower().replace("-", ""):
                return subs["font"], str(f)
    win = _sys_font("seguibl.ttf")
    if win and subs.get("font") in (None, "auto", "Segoe UI Black"):
        return "Segoe UI Black", win
    hit = sorted((ENVD / "fonts" / "ttf").glob("Montserrat-Black.ttf"))
    if hit:
        return "Montserrat Black", str(hit[0])
    fb = _sys_font("arialbd.ttf")
    return ("Arial", fb) if fb else ("Sans", "")


def symbol_font() -> str:
    hit = sorted((ENVD / "fonts" / "ttf").glob("NotoSansSymbols2*.ttf"))
    return _sys_font("seguisym.ttf") or (str(hit[0]) if hit else sub_font()[1])


def ass_color(hexv, alpha="00") -> str:
    h = hexv.strip().lstrip("#")
    return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


def rgb(hexv) -> tuple:
    h = hexv.strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------- jobs ----------
def slugify(s, maxlen=48) -> str:
    n = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    n = re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")
    return n[:maxlen].strip("-") or "reel-" + hashlib.sha1(s.encode("utf-8")).hexdigest()[:6]


def job_dir(job) -> Path:
    p = Path(job)
    return p if p.is_absolute() else folders()["work"] / job


def delivered_name(job) -> str | None:
    """the name a finished job was delivered under (delivery.json; older jobs wrote report.json)"""
    for f in ("delivery.json", "report.json"):
        d = load_json(Path(job) / f, {}) or {}
        if d.get("name"):
            return d["name"]
        if d.get("file"):
            return Path(d["file"]).stem
    return None


def replaced_names(J) -> list:
    """a correction replaces the Reel its old job delivered: that Reel is not "an earlier Reel" for the variety rules"""
    old = J.get("extends")
    if not old:
        return []
    try:
        od = job_dir(old)
    except SystemExit:
        return []
    return sorted(n for n in {delivered_name(od), job_name(od)} if n)


def job_name(job, J=None) -> str:
    """the Reel's name: job.json, else the 'Output name' line of the brief"""
    J = J or load_json(Path(job) / "job.json", {}) or {}
    if J.get("name"):
        return J["name"]
    try:
        m = re.search(r"^- Output name:\s*(.+?)\s*$", (Path(job) / "job.md").read_text(encoding="utf-8"), re.M)
    except OSError:
        m = None
    return m.group(1).strip("\"«» ") if m and "TODO" not in m.group(1) else (J.get("job") or "reel")


def job_sync(job) -> dict:
    """the decisions in job.md win: brand and format from the brief go into job.json, so every later step uses them"""
    job = Path(job); J = load_json(job / "job.json", {}) or {}
    try:
        t = (job / "job.md").read_text(encoding="utf-8")
    except OSError:
        return J
    b = re.search(r"^- Brand:\s*`?([a-z0-9-]+)", t, re.M); f = re.search(r"^- Format:\s*`?(hybrid|face|faceless|skit)\b", t, re.M)
    ch = False
    if b and b.group(1) in brand_list() and J.get("brand") != b.group(1):
        J["brand"] = b.group(1); ch = True
    if f and J.get("format") != f.group(1):
        J["format"] = f.group(1); ch = True
    v = re.search(r"^- Voice:\s*`?(normal|phone|outdoor)\b", t, re.M)
    if v and J.get("voice_preset", "normal") != v.group(1):
        J["voice_preset"] = None if v.group(1) == "normal" else v.group(1); ch = True
    if ch:
        save_json(job / "job.json", J)
    return J


def uprint(*a):
    print(*a, flush=True)


def fail(msg, code=1):
    print("ERROR:", msg, file=sys.stderr, flush=True)
    sys.exit(code)
