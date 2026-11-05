"""reel-tool doctor [--full]: checks every dependency and says what to do. --full also renders a 2 s test scene, runs the voice
chain on a test tone and loads Whisper."""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

import common as C

R = []
OS = "windows" if C.IS_WIN else "mac" if sys.platform == "darwin" else "linux"
SETUP = "reel-tool setup        (or /reel-setup in Claude Code)"
# Ubuntu 22.04/24.04 and Zorin package for each shared library chrome-headless-shell needs (the t64 names are 24.04)
CHROME_DEBS = {"libnss3": "libnss3", "libnssutil3": "libnss3", "libsmime3": "libnss3", "libnspr4": "libnspr4", "libatk-1.0": "libatk1.0-0t64|libatk1.0-0",
               "libatk-bridge-2.0": "libatk-bridge2.0-0t64|libatk-bridge2.0-0", "libcups": "libcups2t64|libcups2", "libdrm": "libdrm2", "libxkbcommon": "libxkbcommon0",
               "libXcomposite": "libxcomposite1", "libXdamage": "libxdamage1", "libXfixes": "libxfixes3", "libXrandr": "libxrandr2", "libgbm": "libgbm1",
               "libpango-1.0": "libpango-1.0-0", "libcairo": "libcairo2", "libasound": "libasound2t64|libasound2", "libdbus-1": "libdbus-1-3", "libexpat": "libexpat1",
               "libxcb": "libxcb1", "libX11": "libx11-6", "libXext": "libxext6", "libglib-2.0": "libglib2.0-0t64|libglib2.0-0", "libgio-2.0": "libglib2.0-0t64|libglib2.0-0"}


def chrome_libs(exe):
    """Linux: shared libraries chrome-headless-shell cannot find -> the apt line that installs them"""
    if OS != "linux" or not shutil.which("ldd"):
        return []
    out = subprocess.run(["ldd", str(exe)], capture_output=True, text=True).stdout
    miss = [l.split()[0] for l in out.splitlines() if "not found" in l]
    pk = []
    newer = (Path("/etc/os-release").read_text() if Path("/etc/os-release").exists() else "").find('VERSION_ID="24') >= 0 or "t64" in subprocess.run(["apt-cache", "policy", "libasound2t64"], capture_output=True, text=True).stdout
    for m in miss:
        name = next((v for k, v in CHROME_DEBS.items() if m.startswith(k)), None)
        if name:
            name = name.split("|")[0 if newer else -1]
            if name not in pk:
                pk.append(name)
    return [miss, pk]


def row(name, ok, detail="", fix=""):
    R.append(ok); print(f"{'ok  ' if ok else 'FAIL'}  {name}: {detail}" + ("" if ok or not fix else f"\n      -> {fix}"), flush=True)


def main(argv):
    full = "--full" in argv
    if "--clear-cache" in argv:
        import clean
        clean.main(["--all"]); return
    print("data dir:", C.DATA, f"({OS})")
    if OS == "windows" and not shutil.which("bash"):
        row("Git for Windows", False, "bash not found", "winget install --id Git.Git -e   (then restart Claude Code)")
    st = C.load_json(C.ENVD / "setup_state.json", {}) or {}
    todo = [k for k in ("python", "ffmpeg", "node", "chrome", "fonts", "denoiser", "yunet", "whisper") if k not in st]
    row("setup stages", not todo, ", ".join(st) or "none", SETUP + (f"   (still to do: {', '.join(todo)})" if todo else ""))
    r = subprocess.run([C.FF, "-hide_banner", "-version"], capture_output=True, text=True)
    v = r.stdout.split("\n")[0] if r.returncode == 0 else "not found"
    fl = subprocess.run([C.FF, "-hide_banner", "-filters"], capture_output=True, text=True).stdout if r.returncode == 0 else ""
    miss = [f for f in ("ass", "zscale", "loudnorm", "acompressor", "arnndn", "ebur128", "afftdn", "tonemap") if not re.search(rf"\b{f}\b", fl)]
    row("ffmpeg", r.returncode == 0 and not miss, v[:60] + (f"; missing filters {miss}" if miss else ""), SETUP)
    r = subprocess.run([C.node(), "--version"], capture_output=True, text=True)
    ver = r.stdout.strip(); okn = r.returncode == 0 and int(ver.lstrip("v").split(".")[0]) >= 22
    row("Node.js", okn, ver or "not found", SETUP)
    ch = [p for p in (C.ENVD / "chrome").glob("chs-*/*/chrome-headless-shell*") if p.suffix in ("", ".exe")]
    row("chrome-headless-shell", bool(ch), ch[0].parent.parent.name if ch else "not found", SETUP)
    if ch and OS == "linux":
        cl = chrome_libs(ch[0])
        row("browser libraries", not cl or not cl[0], "all present" if not cl or not cl[0] else "missing " + ", ".join(cl[0][:6]),
            "sudo apt install -y " + " ".join(cl[1]) if cl and cl[1] else "install the libraries listed (ldd " + str(ch[0]) + ")")
    for mod in ("faster_whisper", "cv2", "scipy", "PIL", "resvg_py", "segno", "torch", "df"):
        r = subprocess.run([sys.executable, "-c", f"import {mod}" if mod != "df" else "import sys,types\nb=types.ModuleType('torchaudio.backend');c=types.ModuleType('torchaudio.backend.common');c.AudioMetaData=object;b.common=c\nsys.modules.setdefault('torchaudio.backend',b);sys.modules.setdefault('torchaudio.backend.common',c)\nimport df.enhance"],
                           capture_output=True, text=True, env=C.run_env())
        row("python " + mod, r.returncode == 0, "" if r.returncode == 0 else r.stderr.strip().splitlines()[-1][:120], SETUP)
    row("voice model", (C.ENVD / "models" / "DeepFilterNet3").is_dir() and (C.ENVD / "models" / "bd.rnnn").exists(), "", SETUP)
    row("speech model", C.whisper_ready(), C.config().get("whisper_model", "large-v3"), SETUP)
    row("face model", (C.ENVD / "models" / "face_detection_yunet_2023mar.onnx").exists(), "", SETUP)
    fonts = list((C.ENVD / "fonts" / "node_modules" / "@fontsource").glob("*"))
    row("fonts", len(fonts) >= 2, ", ".join(f.name for f in fonts), SETUP)
    row("subtitle font", bool(C.sub_font()[1]), C.sub_font()[0], SETUP + "   (fonts stage)")
    if OS != "windows" and not shutil.which("curl"):
        row("curl", False, "not found", "sudo apt install -y curl" if OS == "linux" else "xcode-select --install")
    gpu = shutil.which("nvidia-smi") and subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
    print("note  GPU:", gpu or "none: speech runs on the CPU, a 1 minute Reel takes about 5-10 minutes longer")
    usage = shutil.disk_usage(C.DATA if C.DATA.exists() else Path.home())
    row("disk space", usage.free > 6 * 1024 ** 3, f"{usage.free / 1024 ** 3:.0f} GB free", "free some space: a job needs about 3-5 GB while it renders (reel-tool clean --all frees the render caches)")
    q = C.quality()
    if q == "v2":
        he = C.hdr_engine_info()
        print("note  video quality v2: 4K lossless intermediate, BT.709, CRF 16 (about 1.3 GB of render cache per 30 s Reel, 2.3 GB from HDR"
              " originals, removed by the cache cleaner; finished Reels about 2x bigger than 1.0). HDR clips: " +
              ("GPU tonemap (libplacebo on Vulkan)" if he["engine"] == "placebo" else f"CPU tonemap (zscale; {he['why']})") +
              ". Old settings: --old-quality or reel-tool config quality v1")
    else:
        print("note  video quality v1 (the 1.0 settings: 1080 pieces, CRF 20). reel-tool config quality v2 for the 4K path")
    print("brands:", ", ".join(C.brand_list()) or "none (the neutral default look is used; /reel-brand makes one)")
    print("folders:", {k: str(v) for k, v in C.folders().items()})
    try:                                                         # the phone side: informational, never a failure
        import autostart, phone
        port, key = phone.settings()
        st = {"ours": "running", "busy": f"port {port} is used by another program (reel-tool config upload_page.port 5081)",
              "free": "not running"}[phone.state(port, key)]
        a = autostart.win_status() if C.IS_WIN else autostart.mac_status() if C.IS_MAC else autostart.linux_status()
        print(f"note  upload page: {st}; autostart {a or 'off (reel-tool autostart on)'}; videos folder {C.upload_folders()['input']}")
    except Exception as e:
        print("note  upload page: could not check (" + str(e)[:80] + ")")
    if full:
        full_test()
    print("\nALL GOOD" if all(R) else f"\n{R.count(False)} problem(s) above")
    sys.exit(0 if all(R) else 1)


def full_test():
    tmp = Path(tempfile.mkdtemp(prefix="reel_doctor_"))
    try:
        sb = tmp / "t.json"
        C.save_json(sb, {"theme": "default", "size": [1080, 1920], "t0": 0, "t1": 2.0, "words": str(tmp / "w.json"), "noMark": True,
                         "scenes": [{"type": "bigword", "lines": ["Reel", "Studio"], "hl": ["Studio"], "at": 0.1}]})
        C.save_json(tmp / "w.json", {"total": 2.0, "words": [[0.1, 0.6, "Reel"], [0.7, 1.4, "Studio."]]})
        r = subprocess.run([C.node(), str(C.MOTION / "engine" / "render.mjs"), str(sb), "--out", str(tmp / "o.mkv"), "--alpha", "--workers", "2", "--report", str(tmp / "r.json")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=C.run_env())
        ok = r.returncode == 0 and (tmp / "o.mkv").exists()
        row("engine test render", ok, (r.stdout.strip().splitlines() or [""])[-2 if ok else -1][:100], (r.stderr or r.stdout)[-300:])
        C.ff("-f", "lavfi", "-i", "sine=frequency=220:duration=4", "-ar", "48000", "-ac", "1", str(tmp / "a.wav"))
        import voice_chain
        vr = voice_chain.run(str(tmp / "a.wav"), str(tmp / "b.wav"))
        row("voice chain", "DeepFilterNet" in vr["denoiser"], vr["denoiser"], "the fallback ran: see the message above")
        sys.path.insert(0, str(Path(__file__).parent))
        from autoedit import speech
        with speech.WhisperSession(C.config().get("whisper_model", "large-v3")) as s:
            row("Whisper", True, f"{s.device}/{s.compute}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
