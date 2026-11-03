"""Upload page at login, and the desktop shortcut. User level only: no admin rights, nothing system-wide.

    reel-tool autostart on [--folder DIR] [--port N]   start the page at every login (and now)
    reel-tool autostart off                             stop starting it; the files it made go to the Recycle Bin / Trash
    reel-tool autostart status
    reel-tool shortcut on | off                         a desktop icon that starts the page and shows the phone link as a QR code

Windows: a Task Scheduler task "at log on" of this user (Startup-folder shortcut if the task can't be made).
macOS: a LaunchAgent in ~/Library/LaunchAgents.  Linux: a systemd --user service (XDG autostart entry if systemd --user is
not available). The page serves the videos folder (upload_page.folder in config.json, set by --folder, default Videos/Reels).
"""
import json, os, plistlib, shutil, subprocess, sys
from pathlib import Path

import common as C
import phone

NAME = "Reel Studio upload page"
LABEL = "com.siroxygenfish.reel-studio.upload"
UNIT = "reel-studio-upload.service"
SHORT = {"en": "Reel Studio phone link", "ru": "Reel Studio для телефона", "pl": "Reel Studio na telefon"}


def ps(script, **env):
    e = dict(os.environ, **{k: str(v) for k, v in env.items()})
    return subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, text=True, env=e, timeout=120)


def launch_cmd(*args):
    """[python, launch.py, *args, --log <data>/autostart/upload-page.log] with the windowless Python on Windows"""
    return [str(phone.venv_python(windowless=True)), str(phone.launcher()), *args, "--log", str(phone.LOG)]


# ---------- Windows ----------
def win_startup_lnk():
    r = ps("[Environment]::GetFolderPath('Startup')")
    return Path(r.stdout.strip()) / (NAME + ".lnk")


def win_lnk(path, cmd, icon=None, desc=""):
    script = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:RS_LNK); $s.TargetPath=$env:RS_EXE; $s.Arguments=$env:RS_ARGS;"
              "$s.WorkingDirectory=$env:RS_DIR; $s.Description=$env:RS_DESC; if ($env:RS_ICON) { $s.IconLocation=$env:RS_ICON }; $s.Save()")
    r = ps(script, RS_LNK=path, RS_EXE=cmd[0], RS_ARGS=subprocess.list2cmdline(cmd[1:]), RS_DIR=C.DATA, RS_DESC=desc, RS_ICON=icon or "")
    return r.returncode == 0 and Path(path).exists()


def win_on():
    cmd = launch_cmd("upload-page")
    script = r"""
$me = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$a = New-ScheduledTaskAction -Execute $env:RS_EXE -Argument $env:RS_ARGS -WorkingDirectory $env:RS_DIR
$t = New-ScheduledTaskTrigger -AtLogOn -User $me
$p = New-ScheduledTaskPrincipal -UserId $me -LogonType Interactive -RunLevel Limited
$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $env:RS_TASK -Action $a -Trigger $t -Principal $p -Settings $s -Description 'Starts the Reel Studio phone upload page at log on.' -Force | Out-Null
Start-ScheduledTask -TaskName $env:RS_TASK
"""
    r = ps(script, RS_EXE=cmd[0], RS_ARGS=subprocess.list2cmdline(cmd[1:]), RS_DIR=C.DATA, RS_TASK=NAME)
    if r.returncode == 0:
        return "task"
    print("Task Scheduler said no (" + (r.stderr.strip().splitlines() or ["?"])[-1][:160] + "); using the Startup folder instead")
    if not win_lnk(win_startup_lnk(), cmd, desc="Starts the Reel Studio phone upload page"):
        C.fail("could not make the Startup shortcut either")
    phone.start_background()
    return "startup"


def win_off():
    ps("if (Get-ScheduledTask -TaskName $env:RS_TASK -ErrorAction SilentlyContinue) {"
       " Stop-ScheduledTask -TaskName $env:RS_TASK -ErrorAction SilentlyContinue; Unregister-ScheduledTask -TaskName $env:RS_TASK -Confirm:$false }",
       RS_TASK=NAME)
    C.trash(win_startup_lnk())


def win_status():
    r = ps("$t = Get-ScheduledTask -TaskName $env:RS_TASK -ErrorAction SilentlyContinue; if ($t) { 'task ' + $t.State }", RS_TASK=NAME)
    if r.stdout.strip():
        return r.stdout.strip()
    return "startup folder" if win_startup_lnk().exists() else None


# ---------- macOS ----------
def mac_plist():
    return Path.home() / "Library" / "LaunchAgents" / (LABEL + ".plist")


def launchctl(*a):
    return subprocess.run(["launchctl", *a], capture_output=True, text=True)


def mac_on():
    p = mac_plist(); p.parent.mkdir(parents=True, exist_ok=True)
    plistlib.dump({"Label": LABEL, "ProgramArguments": launch_cmd("upload-page"), "WorkingDirectory": str(C.DATA),
                   "RunAtLoad": True, "KeepAlive": {"SuccessfulExit": False}, "ThrottleInterval": 60, "ProcessType": "Background"},
                  open(p, "wb"))
    dom = f"gui/{os.getuid()}"
    launchctl("bootout", f"{dom}/{LABEL}")
    r = launchctl("bootstrap", dom, str(p))
    if r.returncode:
        C.fail("launchctl bootstrap failed: " + (r.stderr or r.stdout).strip())
    return "launchagent"


def mac_off():
    launchctl("bootout", f"gui/{os.getuid()}/{LABEL}")
    C.trash(mac_plist())


def mac_status():
    r = launchctl("print", f"gui/{os.getuid()}/{LABEL}")
    if r.returncode == 0:
        st = next((l.split("=", 1)[1].strip() for l in r.stdout.splitlines() if l.strip().startswith("state =")), "loaded")
        return "launchagent " + st
    return "launchagent file only (not loaded)" if mac_plist().exists() else None


# ---------- Linux ----------
def unit_path():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "systemd" / "user" / UNIT


def xdg_entry():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "autostart" / "reel-studio-upload.desktop"


def has_user_systemd():
    return shutil.which("systemctl") is not None and subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True).returncode == 0


def sysd(*a):
    return subprocess.run(["systemctl", "--user", *a], capture_output=True, text=True)


def desktop_exec(cmd):
    return " ".join('"' + c.replace("\\", "\\\\").replace('"', '\\"') + '"' for c in cmd)


def linux_on():
    cmd = launch_cmd("upload-page")
    if has_user_systemd():
        u = unit_path(); u.parent.mkdir(parents=True, exist_ok=True)
        u.write_text(f"""[Unit]
Description={NAME}
After=network-online.target

[Service]
ExecStart={desktop_exec(cmd)}
WorkingDirectory={C.DATA}
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
""", encoding="utf-8")
        sysd("daemon-reload")
        r = sysd("enable", "--now", UNIT)
        if r.returncode == 0:
            return "systemd"
        print("systemd --user could not start it (" + r.stderr.strip()[:160] + "); using desktop autostart instead")
        C.trash(u); sysd("daemon-reload")
    e = xdg_entry(); e.parent.mkdir(parents=True, exist_ok=True)
    e.write_text(f"[Desktop Entry]\nType=Application\nName={NAME}\nExec={desktop_exec(cmd)}\nNoDisplay=true\nX-GNOME-Autostart-enabled=true\n",
                 encoding="utf-8")
    phone.start_background()
    return "xdg-autostart"


def linux_off():
    if unit_path().exists():
        sysd("disable", "--now", UNIT)
        C.trash(unit_path())
        sysd("daemon-reload")
    C.trash(xdg_entry())


def linux_status():
    if unit_path().exists():
        return "systemd " + (sysd("is-active", UNIT).stdout.strip() or "?") + ", " + (sysd("is-enabled", UNIT).stdout.strip() or "?")
    return "xdg-autostart" if xdg_entry().exists() else None


# ---------- shortcut ----------
def icon_file():
    """the plugin icon as .ico (Windows) / .png, kept in the data dir so it survives plugin updates"""
    from PIL import Image
    src = C.ROOT / ".claude-plugin" / "icon.png"
    png = phone.AUTO / "icon.png"; png.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, png)
    if C.IS_WIN:
        ico = phone.AUTO / "icon.ico"
        Image.open(src).save(ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        return ico
    return png


def shortcut_path():
    name = SHORT[C.ui_lang()]
    d = C.desktop_dir()
    return d / (name + (".lnk" if C.IS_WIN else ".app" if C.IS_MAC else ".desktop"))


def all_shortcut_paths():
    d = C.desktop_dir()
    return [d / (n + ext) for n in SHORT.values() for ext in (".lnk", ".app", ".desktop")]


def shortcut_on():
    cmd = launch_cmd("phone-link", "--start", "--open", "--no-qr")
    p = shortcut_path()
    if C.IS_WIN:
        if not win_lnk(p, cmd, icon=icon_file(), desc="Starts the Reel Studio upload page and shows the phone link"):
            C.fail("could not make the desktop shortcut")
    elif C.IS_MAC:
        app = p; (app / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True); (app / "Contents" / "Resources").mkdir(exist_ok=True)
        run = app / "Contents" / "MacOS" / "phone-link"
        run.write_text("#!/bin/bash\nexec " + " ".join("'" + c.replace("'", "'\\''") + "'" for c in cmd) + "\n", encoding="utf-8")
        run.chmod(0o755)
        info = {"CFBundleName": p.stem, "CFBundleDisplayName": p.stem, "CFBundleIdentifier": LABEL + ".link", "CFBundleExecutable": "phone-link",
                "CFBundlePackageType": "APPL", "CFBundleVersion": "1", "LSUIElement": True}
        icns = mac_icns(app / "Contents" / "Resources")
        if icns:
            info["CFBundleIconFile"] = icns
        plistlib.dump(info, open(app / "Contents" / "Info.plist", "wb"))
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"[Desktop Entry]\nType=Application\nName={p.stem}\nExec={desktop_exec(cmd)}\nIcon={icon_file()}\nTerminal=false\n",
                     encoding="utf-8")
        p.chmod(0o755)
        if shutil.which("gio"):
            subprocess.run(["gio", "set", str(p), "metadata::trusted", "true"], capture_output=True)
    print("desktop shortcut:", p)


def mac_icns(res):
    """icon.icns from the plugin icon with the built-in sips + iconutil; None if they are missing"""
    if not (shutil.which("sips") and shutil.which("iconutil")):
        return None
    src = icon_file(); iset = phone.AUTO / "icon.iconset"; iset.mkdir(parents=True, exist_ok=True)
    for s in (16, 32, 128, 256, 512):
        for k, n in ((1, f"icon_{s}x{s}.png"), (2, f"icon_{s}x{s}@2x.png")):
            subprocess.run(["sips", "-z", str(s * k), str(s * k), str(src), "--out", str(iset / n)], capture_output=True)
    r = subprocess.run(["iconutil", "-c", "icns", str(iset), "-o", str(res / "icon.icns")], capture_output=True)
    C.trash(iset)
    return "icon" if r.returncode == 0 else None


def shortcut_off():
    for p in all_shortcut_paths():
        if p.exists():
            C.trash(p); print("moved to the trash:", p)


# ---------- command ----------
def status():
    s = win_status() if C.IS_WIN else mac_status() if C.IS_MAC else linux_status()
    port, key = phone.settings()
    print("autostart:", s or "off")
    print("upload page:", {"ours": "running", "busy": f"port {port} is used by another program", "free": "not running"}[phone.state(port, key)],
          f"(port {port})")
    print("videos folder:", C.upload_folders()["input"])
    print("desktop shortcut:", next((str(p) for p in all_shortcut_paths() if p.exists()), "none"))
    return s


def main(argv):
    if not argv or argv[0] not in ("on", "off", "status"):
        C.fail("usage: reel-tool autostart on [--folder DIR] [--port N] | off | status")
    cmd = argv[0]
    if cmd == "status":
        status(); return
    if cmd == "off":
        win_off() if C.IS_WIN else mac_off() if C.IS_MAC else linux_off()
        port, key = phone.settings()
        print("autostart: off; the upload page is " + ("still running until logout" if phone.state(port, key) == "ours" else "stopped"))
        return
    cfg = C.load_json(C.CONFIG_FILE, {}) or {}
    up = cfg.setdefault("upload_page", {})
    if "--port" in argv:
        up["port"] = int(argv[argv.index("--port") + 1])
    if "--folder" in argv:
        up["folder"] = str(Path(argv[argv.index("--folder") + 1]).expanduser().resolve())
    up.setdefault("folder", str(C.videos_dir()))
    C.save_json(C.CONFIG_FILE, cfg)
    Path(up["folder"]).mkdir(parents=True, exist_ok=True)
    port, key = phone.settings()
    if phone.state(port, key) == "busy":
        C.fail(f"port {port} is used by another program. Pick a free one: reel-tool autostart on --port 5081")
    how = win_on() if C.IS_WIN else mac_on() if C.IS_MAC else linux_on()
    if how in ("startup", "xdg-autostart"):                  # these only act at the next login: start it now by hand
        ok = phone.state(port, key) == "ours" or phone.start_background(wait=15)
    else:
        ok = wait_ours(port, key)
    print(f"autostart: on ({how}); the page is {'running' if ok else 'NOT running yet, see ' + str(phone.LOG)}")
    print("videos folder:", up["folder"])


def wait_ours(port, key, secs=15):
    import time
    for _ in range(secs * 4):
        if phone.state(port, key) == "ours":
            return True
        time.sleep(0.25)
    return False


def shortcut_main(argv):
    if not argv or argv[0] not in ("on", "off"):
        C.fail("usage: reel-tool shortcut on | off")
    shortcut_on() if argv[0] == "on" else shortcut_off()


if __name__ == "__main__":
    main(sys.argv[1:])
