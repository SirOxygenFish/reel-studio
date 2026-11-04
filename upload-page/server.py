"""Phone upload page: phones send clips to the input folder and download finished Reels from the output folder.

Standard library only. Uploads are streamed to disk, so multi-GB 4K clips are fine.
Secure by default: it answers only private-network, loopback and Tailscale addresses, every request needs the private key that is
part of the printed link, nothing can be overwritten, names are sanitised, only video and photo types are accepted, and only exact
file names from the output folder can be downloaded. Do not forward this port to the internet.
Run through: reel-tool upload-page
"""
import hashlib, hmac, ipaddress, json, os, re, shutil, socket, sys, threading, time, unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
UPLOADS, READY, PORT, KEY = "", "", 5080, ""

VIDEO_EXT = {".mov", ".mp4", ".m4v", ".3gp", ".3g2", ".avi", ".mkv", ".webm", ".hevc", ".mts", ".m2ts"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".dng"}
ALLOWED_EXT = VIDEO_EXT | IMAGE_EXT
MAX_UPLOAD = 40 * 1024**3          # 40 GB per file
DISK_RESERVE = 2 * 1024**3         # always leave 2 GB free
CHUNK = 1024 * 1024
BATCH_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(_\d+)?$")
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
batch_lock = threading.Lock()
# Tailscale addresses: 100.64.0.0/10 is CGNAT space, not "private" for ipaddress; the IPv6 range is ULA
TAILSCALE_NETS = (ipaddress.ip_network("100.64.0.0/10"), ipaddress.ip_network("fd7a:115c:a1e0::/48"))


def safe_name(raw):
    """Plain file name: no folders, no forbidden characters, allowed extension; None if not acceptable."""
    name = unicodedata.normalize("NFC", raw or "").replace("\\", "/").split("/")[-1]
    name = "".join(c for c in name if c.isprintable() and c not in '<>:"/\\|?*')
    name = name.strip().strip(".").strip()
    stem, ext = os.path.splitext(name)
    ext = ext.lower()
    if ext not in ALLOWED_EXT:
        return None
    stem = stem.strip(" .")[:100] or "file"
    if stem.lower() in RESERVED:
        stem = "_" + stem
    return stem + ext


def inside(path, root):
    path, root = os.path.realpath(path), os.path.realpath(root)
    return os.path.commonpath([path, root]) == root and path != root


def place_without_overwrite(tmp, folder, name):
    """Rename tmp -> folder/name, adding _2, _3 ... on a clash. os.rename never overwrites on Windows."""
    stem, ext = os.path.splitext(name)
    for i in range(1, 10000):
        cand = os.path.join(folder, name if i == 1 else f"{stem}_{i}{ext}")
        try:
            os.rename(tmp, cand)
            return os.path.basename(cand)
        except FileExistsError:
            continue
    raise OSError("no free file name")


def ready_files():
    if not os.path.isdir(READY):
        return []
    out = []
    for n in os.listdir(READY):
        p = os.path.join(READY, n)
        if os.path.isfile(p) and os.path.splitext(n)[1].lower() in ALLOWED_EXT:
            st = os.stat(p)
            out.append({"name": n, "size": st.st_size, "mtime": st.st_mtime, "title": os.path.splitext(n)[0],
                        "id": hashlib.sha1(n.encode("utf-8")).hexdigest()[:12], "ext": os.path.splitext(n)[1].lower()})
    return sorted(out, key=lambda f: f["mtime"], reverse=True)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ReelUpload"
    timeout = 300                                         # idle socket timeout, seconds

    def log_message(self, fmt, *args):
        line = re.sub(r"([?&]k=)[^&\s]+", r"\1***", fmt % args)
        sys.stdout.write("%s  %s  %s\n" % (time.strftime("%H:%M:%S"), self.client_address[0], line)); sys.stdout.flush()

    def send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def fail(self, code, msg, close=False):
        if close:
            self.close_connection = True
        self.send_json(code, {"error": msg})

    def client_allowed(self):
        try:
            ip = ipaddress.ip_address(self.client_address[0])
        except ValueError:
            return False
        if ip.version == 6 and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        return (ip.is_private or ip.is_loopback or ip.is_link_local
                or any(ip in net for net in TAILSCALE_NETS if net.version == ip.version))

    def key_ok(self, url):
        return hmac.compare_digest((parse_qs(url.query).get("k") or [""])[0], KEY)

    def body_length(self):
        try:
            n = int(self.headers.get("Content-Length", ""))
            return n if n >= 0 else None
        except ValueError:
            return None

    def discard_body(self):
        n = self.body_length() or 0
        if n > 64 * 1024:                                 # too big to drain: just drop the connection
            self.close_connection = True
            return
        while n > 0:
            got = self.rfile.read(min(CHUNK, n))
            if not got:
                break
            n -= len(got)

    def batch_dir(self, q):
        b = (q.get("batch") or [""])[0]
        if not BATCH_RE.match(b):
            return None
        d = os.path.join(UPLOADS, b)
        return d if os.path.isdir(d) and inside(d, UPLOADS) else None

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionError, socket.timeout):
            self.close_connection = True

    def do_GET(self):
        url = urlparse(self.path)
        if not self.client_allowed() or not self.key_ok(url):
            return self.fail(403, "not allowed", close=True)
        if url.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(body)
        elif url.path == "/api/ready":
            self.send_json(200, {"files": ready_files()})
        elif url.path == "/icon.png":                     # Home Screen icon (apple-touch-icon)
            f = os.path.join(os.path.dirname(HERE), ".claude-plugin", "icon.png")
            if not os.path.isfile(f):
                return self.fail(404, "file not found")
            self.send_file(f, "icon.png", attach=False)
        elif url.path == "/api/ping":                     # lets a second start see that this page already runs here
            self.send_json(200, {"app": "reel-studio-upload", "port": PORT})
        elif re.fullmatch(r"/howto/(en|ru|pl)\.mp4", url.path):  # the bundled iPhone tutorial, played on the page
            f = os.path.join(HERE, "tutorials", f"tutorial2-iphone.{url.path[7:9]}.mp4")
            if not os.path.isfile(f):
                f = os.path.join(HERE, "tutorials", "tutorial2-iphone.en.mp4")
            if not os.path.isfile(f):
                return self.fail(404, "file not found")
            self.send_file(f, os.path.basename(f), attach=False)
        elif re.fullmatch(r"/shortcut/(en|ru|pl)/SaveReel\.shortcut", url.path):   # the signed iPhone Shortcut (one tap to add)
            f = os.path.join(HERE, "shortcut", url.path[10:12], "SaveReel.shortcut")
            if not os.path.isfile(f):
                return self.fail(404, "file not found")
            self.send_file(f, "SaveReel.shortcut")
        elif url.path == "/download":
            self.download((parse_qs(url.query).get("f") or [""])[0])
        elif re.fullmatch(r"/v/[0-9a-f]{12}\.[a-z0-9]{2,5}", url.path):   # short ASCII address for an iPhone Shortcut
            vid = url.path[3:15]
            self.download(next((f["name"] for f in ready_files() if f["id"] == vid), ""))
        else:
            self.fail(404, "not found")

    def do_POST(self):
        url = urlparse(self.path)
        if not self.client_allowed() or not self.key_ok(url):
            return self.fail(403, "not allowed", close=True)
        if url.path == "/api/batch":
            return self.new_batch()
        if url.path == "/api/upload":
            return self.upload(parse_qs(url.query))
        self.discard_body()
        self.fail(404, "not found")

    def new_batch(self):
        n = self.body_length()
        if n is None or n > 64 * 1024:
            return self.fail(400, "bad request", close=True)
        raw = self.rfile.read(n) if n else b""
        try:
            note = str(json.loads(raw.decode("utf-8") or "{}").get("note", "")).strip()[:5000]
        except (ValueError, AttributeError):
            return self.fail(400, "bad request")
        os.makedirs(UPLOADS, exist_ok=True)
        stamp = time.strftime("%Y-%m-%d_%H-%M")
        with batch_lock:
            for i in range(1, 1000):
                name = stamp if i == 1 else f"{stamp}_{i}"
                try:
                    os.mkdir(os.path.join(UPLOADS, name))
                    break
                except FileExistsError:
                    continue
            else:
                return self.fail(500, "could not create a folder")
        if note:
            with open(os.path.join(UPLOADS, name, "note.txt"), "w", encoding="utf-8") as f:
                f.write(f"What to do with this video ({time.strftime('%Y-%m-%d %H:%M')}):\n{note}\n")
        self.send_json(201, {"batch": name})

    def upload(self, q):
        folder = self.batch_dir(q)
        name = safe_name((q.get("name") or [""])[0])
        n = self.body_length()
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if folder is None:
            self.discard_body(); return self.fail(400, "unknown upload")
        if name is None or (ctype and not ctype.startswith(("video/", "image/")) and ctype != "application/octet-stream"):
            self.discard_body(); return self.fail(415, "only video and photos")
        if n is None:
            return self.fail(411, "no file size", close=True)
        if n > MAX_UPLOAD or n > shutil.disk_usage(UPLOADS).free - DISK_RESERVE:
            return self.fail(413, "not enough space on the computer", close=True)
        tmp = os.path.join(folder, f".{os.getpid()}_{threading.get_ident()}_{time.time_ns()}.part")
        left = n
        try:
            with open(tmp, "xb") as out:
                while left > 0:
                    chunk = self.rfile.read(min(CHUNK, left))
                    if not chunk:
                        break
                    out.write(chunk)
                    left -= len(chunk)
            if left:
                raise ConnectionError("client stopped sending")
            final = place_without_overwrite(tmp, folder, name)
        except Exception as e:
            self.close_connection = True
            try:
                os.remove(tmp)
            except OSError:
                pass
            self.log_message("upload FAILED %s (%s)", name, e)
            if not isinstance(e, (ConnectionError, socket.timeout)):
                try:
                    self.fail(500, "could not save", close=True)
                except OSError:
                    pass
            return
        self.log_message("saved %s\\%s (%.1f MB)", os.path.basename(folder), final, n / 1024**2)
        self.send_json(201, {"saved": final, "size": n})

    def download(self, want):
        files = {f["name"]: f for f in ready_files()}     # only exact names that exist in the output folder
        if want not in files:
            return self.fail(404, "file not found")
        path = os.path.join(READY, want)
        if not inside(path, READY):
            return self.fail(404, "file not found")
        self.send_file(path, want)

    def send_file(self, path, want, attach=True):
        """one file with Range support (iPhone video players and resumed downloads need it)"""
        size = os.path.getsize(path)
        start, end = 0, size - 1
        rng = re.match(r"^bytes=(\d*)-(\d*)$", self.headers.get("Range", "").strip())
        if rng and (rng.group(1) or rng.group(2)):
            if rng.group(1):
                start = int(rng.group(1)); end = min(int(rng.group(2)), size - 1) if rng.group(2) else size - 1
            else:
                start = max(0, size - int(rng.group(2)))
            if start > end or start >= size:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        ext = os.path.splitext(want)[1].lower()
        ctype = {".shortcut": "application/octet-stream", ".mp4": "video/mp4", ".mov": "video/quicktime", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(ext, "application/octet-stream")
        ascii_name = re.sub(r"[^A-Za-z0-9._ -]", "_", want)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        if attach:
            self.send_header("Content-Disposition", f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(want)}")
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = f.read(min(CHUNK, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)


def lan_ips():
    out = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 9))                  # no packet is sent; picks the LAN interface
        out.append(s.getsockname()[0])
    except OSError:
        pass
    finally:
        s.close()
    ts = shutil.which("tailscale") or next((p for p in ("/Applications/Tailscale.app/Contents/MacOS/Tailscale",
                                                         r"C:\Program Files\Tailscale\tailscale.exe") if os.path.exists(p)), None)
    if ts:
        import subprocess
        try:
            r = subprocess.run([ts, "ip", "-4"], capture_output=True, text=True, timeout=5)
            out += [x for x in r.stdout.split() if x.count(".") == 3]
        except (OSError, subprocess.SubprocessError):
            pass
    return out or ["127.0.0.1"]


class Server(ThreadingHTTPServer):
    """never shares a port: on Windows SO_REUSEADDR would let a second server bind a port another program already uses"""
    allow_reuse_address = os.name != "nt"
    daemon_threads = True

    def server_bind(self):
        if os.name == "nt" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def serve(uploads, ready, port, key):
    global UPLOADS, READY, PORT, KEY
    UPLOADS, READY, PORT, KEY = str(uploads), str(ready), int(port), key
    os.makedirs(UPLOADS, exist_ok=True); os.makedirs(READY, exist_ok=True)
    srv = Server(("0.0.0.0", PORT), Handler)
    print("Upload page is running. Open on the phone:", flush=True)
    for ip in lan_ips():
        print(f"  http://{ip}:{PORT}/?k={KEY}", flush=True)
    print(f"Clips go to: {UPLOADS}\nFinished Reels come from: {READY}\nLocal network and Tailscale only. Stop with Ctrl+C.", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
