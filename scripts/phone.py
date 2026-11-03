"""The phone side of Reel Studio: the upload page's key, port and links, starting it in the background, and the phone link.

    reel-tool phone-link [--start] [--open] [--no-qr]
        prints the link to open on the phone (LAN, plus Tailscale when it runs) and a QR code; writes <data>/phone-link.html
        --start  start the upload page in the background first if it is not running
        --open   open phone-link.html in the browser (big QR code to scan with the iPhone camera)
"""
import html, json, os, secrets, socket, subprocess, sys, time, urllib.request
from pathlib import Path

import common as C

sys.path.insert(0, str(C.ROOT / "upload-page"))
AUTO = C.DATA / "autostart"                 # launcher, log and shortcut icon live here (stable across plugin updates)
LOG = AUTO / "upload-page.log"

TEXT = {
    "en": {"title": "Reel Studio: open on your phone", "lead": "Point the iPhone camera at the code and tap the link.",
           "home": "Then in Safari tap Share, then Add to Home Screen. From now on the page opens from its icon.",
           "away": "Away from home (Tailscale on, on both devices):", "home_net": "At home (same Wi-Fi):",
           "keep": "This link contains a private key. Do not share it."},
    "ru": {"title": "Reel Studio: откройте на телефоне", "lead": "Наведите камеру iPhone на код и нажмите на ссылку.",
           "home": "Потом в Safari нажмите «Поделиться» и «На экран „Домой“». Дальше страница открывается со значка.",
           "away": "Не дома (Tailscale включён на обоих устройствах):", "home_net": "Дома (та же сеть Wi-Fi):",
           "keep": "В ссылке есть личный ключ. Не пересылайте её никому."},
    "pl": {"title": "Reel Studio: otwórz na telefonie", "lead": "Skieruj aparat iPhone'a na kod i stuknij link.",
           "home": "Potem w Safari stuknij Udostępnij, a następnie Do ekranu początkowego. Odtąd strona otwiera się z ikony.",
           "away": "Poza domem (Tailscale włączony na obu urządzeniach):", "home_net": "W domu (ta sama sieć Wi-Fi):",
           "keep": "Link zawiera prywatny klucz. Nie wysyłaj go nikomu."},
}


def settings():
    """(port, key) of the upload page; the key is made on first use and kept in config.json"""
    cfg = C.load_json(C.CONFIG_FILE, {}) or {}
    up = cfg.setdefault("upload_page", {})
    if not up.get("key"):
        up["key"] = secrets.token_urlsafe(16); C.save_json(C.CONFIG_FILE, cfg)
    return int(up.get("port") or 5080), up["key"]


def state(port, key):
    """'ours' (this page answers with our key), 'busy' (something else holds the port) or 'free'"""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping?k={key}", timeout=2) as r:
            if json.loads(r.read().decode("utf-8")).get("app") == "reel-studio-upload":
                return "ours"
    except Exception:
        pass
    with socket.socket() as s:
        s.settimeout(1)
        return "busy" if s.connect_ex(("127.0.0.1", port)) == 0 else "free"


def links(port, key):
    """[(kind, url)]: the LAN address first, then Tailscale (100.64.0.0/10) when it runs"""
    import server
    out = []
    for ip in server.lan_ips():
        kind = "tailscale" if ip.startswith("100.") and 64 <= int(ip.split(".")[1]) <= 127 else "lan"
        out.append((kind, f"http://{ip}:{port}/?k={key}"))
    return sorted(out, key=lambda x: x[0] != "lan")


def launcher():
    """copy the launcher into the data dir (autostart and the desktop shortcut call it) and record this plugin copy"""
    AUTO.mkdir(parents=True, exist_ok=True)
    dst = AUTO / "launch.py"
    src = (C.ROOT / "scripts" / "launcher.py").read_text(encoding="utf-8")
    if not dst.exists() or dst.read_text(encoding="utf-8") != src:
        dst.write_text(src, encoding="utf-8")
    C.save_json(AUTO / "root.json", {"root": str(C.ROOT), "config_dir": os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")})
    return dst


def venv_python(windowless=False):
    py = Path(sys.executable)
    if C.IS_WIN and windowless and py.with_name("pythonw.exe").exists():
        return py.with_name("pythonw.exe")
    return py


def start_background(wait=10):
    """start the upload page detached from this process (it keeps running after the session ends); True once it answers"""
    port, key = settings()
    if state(port, key) == "ours":
        return True
    cmd = [str(venv_python(windowless=True)), str(launcher()), "upload-page", "--log", str(LOG)]
    kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "cwd": str(C.DATA)}
    if C.IS_WIN:
        kw["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000     # DETACHED_PROCESS | NEW_PROCESS_GROUP | NO_WINDOW
    else:
        kw["start_new_session"] = True
    subprocess.Popen(cmd, **kw)
    for _ in range(wait * 4):
        time.sleep(0.25)
        if state(port, key) == "ours":
            return True
    return False


def qr_svg(url, scale=10):
    import segno
    return segno.make(url, error="m").svg_inline(scale=scale, border=3, dark="#111111", light="#ffffff")


def write_page(ls):
    t = TEXT[C.ui_lang()]
    blocks = ""
    for kind, url in ls:
        head = t["away"] if kind == "tailscale" else t["home_net"]
        blocks += (f'<section><h2>{html.escape(head)}</h2><div class="qr">{qr_svg(url)}</div>'
                   f'<p class="url">{html.escape(url)}</p></section>')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(t['title'])}</title><style>
body{{margin:0;background:#f6f4ef;color:#1d1d1b;font:20px/1.5 -apple-system,"Segoe UI",Roboto,Arial,sans-serif}}
main{{max-width:860px;margin:0 auto;padding:32px 20px}} h1{{font-size:34px;margin:0 0 8px}} h2{{font-size:22px;margin:0 0 12px}}
section{{background:#fff;border:1px solid #e3dfd6;border-radius:18px;padding:22px;margin:20px 0;text-align:center}}
.qr svg{{width:min(360px,80vw);height:auto}} .url{{font:16px ui-monospace,Consolas,monospace;overflow-wrap:anywhere;color:#555}}
.note{{color:#8a6d00}}
</style></head><body><main><h1>{html.escape(t['title'])}</h1><p>{html.escape(t['lead'])}</p><p>{html.escape(t['home'])}</p>
{blocks}<p class="note">{html.escape(t['keep'])}</p></main></body></html>"""
    out = C.DATA / "phone-link.html"
    out.write_text(page, encoding="utf-8")
    return out


def open_file(p):
    if C.IS_WIN:
        os.startfile(str(p))                                    # noqa: the default browser
    else:
        subprocess.Popen(["open" if C.IS_MAC else "xdg-open", str(p)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main(argv):
    port, key = settings()
    st = state(port, key)
    if st != "ours" and "--start" in argv:
        if st == "busy":
            C.fail(f"port {port} is used by another program. Pick a free one: reel-tool config upload_page.port 5081")
        if not start_background():
            C.fail(f"the upload page did not start; see {LOG}")
        st = "ours"
    ls = links(port, key)
    page = write_page(ls)
    print("Upload page: " + ("running" if st == "ours" else "NOT running (reel-tool phone-link --start starts it)"))
    for kind, url in ls:
        print(f"{'Tailscale' if kind == 'tailscale' else 'Wi-Fi'}: {url}")
    if "--no-qr" not in argv:
        import segno
        print()
        segno.make(ls[0][1], error="m").terminal(compact=True)
    print(f"\nQR code page: {page}")
    if "--open" in argv:
        open_file(page)


if __name__ == "__main__":
    main(sys.argv[1:])
