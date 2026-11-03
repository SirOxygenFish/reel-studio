"""Second stage of /reel-setup, run from the private venv. Idempotent: finished stages are skipped, a failed one is retried next time.
Everything goes into <data>/env; nothing is installed system-wide.   reel-tool setup [--only stage] [--check]

Heavy or third-party things are downloaded here, never bundled: Python packages, ffmpeg, Node, chrome-headless-shell, the
DeepFilterNet model, the RNNoise model, YuNet, the fonts and the Whisper model. Every direct download is pinned by SHA-256 (the
Linux ffmpeg build is checked against the digest GitHub publishes for it). Windows x64, Linux x86-64, macOS Apple Silicon.
"""
import hashlib, io, json, os, platform, shutil, subprocess, sys, tarfile, time, urllib.request, zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C

ENV = C.ENVD; STATE = ENV / "setup_state.json"
PINS = json.load(open(C.ROOT / "scripts" / "pins.json", encoding="utf-8"))
OS = "windows" if C.IS_WIN else "mac" if sys.platform == "darwin" else "linux"
UV = ENV / "uv" / ("uv.exe" if C.IS_WIN else "uv")
PY_PKGS = ["numpy<3", "scipy", "pillow", "opencv-python-headless>=4.8", "faster-whisper==1.2.1", "resvg_py==0.5.0", "huggingface_hub", "segno==1.6.1"]
DF_PKGS = ["torch", "torchaudio", "loguru", "appdirs", "packaging", "requests", "sympy"]
DF_NODEPS = ["deepfilternet==0.5.6", "deepfilterlib==0.5.6"]       # their numpy<2 pin is stale; numpy 2 works
GPU_PKGS = ["nvidia-cublas-cu12", "nvidia-cudnn-cu12==9.*"]


def state():
    return C.load_json(STATE, {}) or {}


def done(k):
    s = state(); s[k] = time.strftime("%Y-%m-%d %H:%M"); C.save_json(STATE, s)


def say(*a):
    print(*a, flush=True)


def fetch(url, sha=None):
    """download with progress lines every 25 %; verifies the pin"""
    say("  downloading", url.split("/")[-1])
    req = urllib.request.Request(url, headers={"User-Agent": "reel-studio-setup"})
    h = hashlib.sha256(); buf = io.BytesIO(); got = 0; mark = 25
    with urllib.request.urlopen(req, timeout=120) as r:
        total = int(r.headers.get("Content-Length") or 0)
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            buf.write(b); h.update(b); got += len(b)
            if total and got * 100 / total >= mark:
                say(f"    {mark} % of {total / 1048576:.0f} MB"); mark += 25
    if sha and h.hexdigest() != sha:
        raise SystemExit(f"checksum mismatch for {url}\n  got {h.hexdigest()}\n  want {sha}")
    return buf.getvalue()


def pip(*pkgs, index=None):
    env = dict(os.environ, VIRTUAL_ENV=str(ENV / "venv"), UV_CACHE_DIR=str(ENV / "uv-cache"))
    cmd = [str(UV), "pip", "install", "--python", sys.executable] + (["--index-url", index, "--extra-index-url", "https://pypi.org/simple", "--index-strategy", "unsafe-best-match"] if index else []) + list(pkgs)
    subprocess.run(cmd, check=True, env=env)


def stage_python():
    say("Python packages (speech, vision, images)")
    pip(*PY_PKGS)


def has_nvidia():
    return bool(shutil.which("nvidia-smi")) and subprocess.run(["nvidia-smi", "-L"], capture_output=True).returncode == 0


def stage_gpu():
    if has_nvidia():
        say("NVIDIA GPU found: installing the speed-up libraries for Whisper")
        pip(*GPU_PKGS)
    else:
        say("no NVIDIA GPU: Whisper will run on the CPU (slower, same quality)")


def stage_denoiser():
    say("Voice clean-up (DeepFilterNet, CPU build)")
    pip(*DF_PKGS, index=None if OS == "mac" else "https://download.pytorch.org/whl/cpu")
    pip("--no-deps", *DF_NODEPS)
    d = ENV / "models"; d.mkdir(parents=True, exist_ok=True)
    m = PINS["deepfilter_model"]
    z = fetch(m["url"], m["sha256"])
    with zipfile.ZipFile(io.BytesIO(z)) as f:
        f.extractall(d)
    m = PINS["rnnoise_model"]
    (d / "bd.rnnn").write_bytes(fetch(m["url"], m["sha256"]))


def stage_yunet():
    say("Face detector (YuNet)")
    m = PINS["yunet"]; d = ENV / "models"; d.mkdir(parents=True, exist_ok=True)
    (d / "face_detection_yunet_2023mar.onnx").write_bytes(fetch(m["url"], m["sha256"]))


def extract(data, dst, strip=1, name=""):
    """zip or tar archive into dst, dropping `strip` leading folders; file modes are kept, so binaries stay executable"""
    dst.mkdir(parents=True, exist_ok=True)
    if name.endswith(".zip") or data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for info in z.infolist():
                parts = info.filename.split("/")[strip:]
                if not parts or not parts[-1] or ".." in parts:
                    continue
                p = dst.joinpath(*parts); p.parent.mkdir(parents=True, exist_ok=True)
                mode = (info.external_attr >> 16) & 0o7777
                if (info.external_attr >> 16) & 0o170000 == 0o120000:      # a symlink inside the archive (macOS frameworks)
                    if p.exists() or p.is_symlink():
                        p.unlink()
                    os.symlink(z.read(info).decode(), p); continue
                p.write_bytes(z.read(info))
                if mode and not C.IS_WIN:
                    os.chmod(p, mode)
    else:
        with tarfile.open(fileobj=io.BytesIO(data)) as t:
            for m in t.getmembers():
                parts = m.name.split("/")[strip:]
                if not parts or ".." in parts:
                    continue
                m.name = "/".join(parts)
                t.extract(m, dst, filter="tar" if hasattr(tarfile, "data_filter") else None)


def github_asset(repo, tag, asset):
    """an asset of a GitHub release with the sha256 GitHub publishes for it"""
    rel = json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
                                                                  headers={"User-Agent": "reel-studio-setup"}), timeout=60))
    a = next(x for x in rel["assets"] if x["name"] == asset)
    return a["browser_download_url"], (a.get("digest") or "").replace("sha256:", "") or None


def chmod_x(*paths):
    for p in paths:
        if p.exists() and not C.IS_WIN:
            os.chmod(p, 0o755)


def stage_ffmpeg():
    say("ffmpeg")
    m = PINS["ffmpeg"][OS]; d = ENV / "ffmpeg"
    if "github" in m:
        url, sha = github_asset(**m["github"])
        if not sha:
            raise SystemExit("GitHub gave no checksum for " + url)
        extract(fetch(url, sha), d, 1, url)
    elif "files" in m:                                      # single binaries in zips (macOS build)
        for f in m["files"]:
            extract(fetch(f["url"], f["sha256"]), d / "bin", 0, f["url"])
    else:
        extract(fetch(m["url"], m["sha256"]), d, 1, m["url"])
    chmod_x(d / "bin" / "ffmpeg", d / "bin" / "ffprobe")


def stage_node():
    say("Node.js (private copy, runs the motion engine)")
    m = PINS["node"][OS]; d = ENV / "node"
    extract(fetch(m["url"], m["sha256"]), d, 1, m["url"])
    chmod_x(d / "bin" / "node")


def stage_chrome():
    say("chrome-headless-shell (renders the animation frames)")
    m = PINS["chrome"][OS]; d = ENV / "chrome" / ("chs-" + m["version"]); d.mkdir(parents=True, exist_ok=True)
    extract(fetch(m["url"], m["sha256"]), d, 0, m["url"])
    for exe in d.glob("*/chrome-headless-shell"):
        chmod_x(exe)


def fontsource(pkg, ver=None):
    """one @fontsource package straight from the npm registry (woff2 + css), into env/fonts/node_modules"""
    say("  font", pkg)
    meta = json.load(urllib.request.urlopen(f"https://registry.npmjs.org/@fontsource/{pkg}/{ver or 'latest'}", timeout=60))
    data = fetch(meta["dist"]["tarball"])
    dst = ENV / "fonts" / "node_modules" / "@fontsource" / pkg; dst.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as t:
        for m in t.getmembers():
            n = m.name.split("/", 1)[-1]
            if not m.isfile() or ".." in n:
                continue
            if not (n.endswith(".css") or n == "package.json" or n == "LICENSE" or (n.startswith("files/") and n.endswith(".woff2"))):
                continue
            if n.startswith("files/") and not any(w in n for w in ("-600-normal", "-700-normal", "-800-normal", "-900-normal")):
                continue
            if n.endswith(".css") and not any(n == f"{w}.css" for w in ("600", "700", "800", "900")):
                continue
            p = dst / n; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(t.extractfile(m).read())


def stage_fonts():
    say("Fonts (Open Font License)")
    for pkg, ver in PINS["fonts"].items():
        fontsource(pkg, ver)
    if not C.IS_WIN:                                       # subtitles need a heavy TTF (Windows has Segoe UI Black) and a symbols font
        d = ENV / "fonts" / "ttf"; d.mkdir(parents=True, exist_ok=True)
        for f in PINS["subtitle_fonts"]:
            (d / f["name"]).write_bytes(fetch(f["url"], f["sha256"]))


def stage_whisper():
    model = C.config().get("whisper_model", "large-v3")
    say(f"Speech model Whisper {model} (about 3 GB, once)")
    from huggingface_hub import snapshot_download
    snapshot_download(f"Systran/faster-whisper-{model}", allow_patterns=["config.json", "preprocessor_config.json", "model.bin", "tokenizer.json", "vocabulary.*"])


def stage_config():
    cfg = C.load_json(C.CONFIG_FILE, None)
    if cfg is None:
        C.save_json(C.CONFIG_FILE, {"version": 1})
    C.BRANDS.mkdir(parents=True, exist_ok=True); C.USER_LIB.mkdir(parents=True, exist_ok=True)


STAGES = [("config", stage_config), ("python", stage_python), ("gpu", stage_gpu), ("yunet", stage_yunet), ("ffmpeg", stage_ffmpeg), ("node", stage_node),
          ("chrome", stage_chrome), ("fonts", stage_fonts), ("denoiser", stage_denoiser), ("whisper", stage_whisper)]


def main():
    argv = sys.argv[1:]; only = argv[argv.index("--only") + 1] if "--only" in argv else None
    ENV.mkdir(parents=True, exist_ok=True); s = state()
    if "whisper" in s and not C.whisper_ready():            # older installs kept the model in ~/.cache: fetch it into the data dir
        s.pop("whisper")
    if "python" in s:                                         # a package added in a later version (segno: the phone QR code)
        try:
            import segno  # noqa: F401
        except ImportError:
            s.pop("python")
    todo = [(k, f) for k, f in STAGES if (only == k if only else k not in s)]
    if "--check" in argv:
        print(json.dumps({"done": [k for k, _ in STAGES if k in s], "todo": [k for k, _ in STAGES if k not in s]})); return
    if not todo:
        say("everything is installed. Run /reel-doctor to verify."); return
    say(f"Reel Studio setup: {len(todo)} of {len(STAGES)} stages to do, into {ENV}")
    for i, (k, f) in enumerate(todo, 1):
        say(f"[{i}/{len(todo)}] {k}")
        t0 = time.time(); f(); done(k); say(f"  done in {time.time() - t0:.0f} s")
    # drop uv's download cache: the installed files are hard links or copies and stay; this clears leftovers from earlier versions
    subprocess.run([str(UV), "cache", "clean"], env=dict(os.environ, UV_CACHE_DIR=str(ENV / "uv-cache")), capture_output=True)
    say("setup finished. Next: /reel-doctor, then /reel-brand.")


if __name__ == "__main__":
    main()
