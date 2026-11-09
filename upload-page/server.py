"""Phone upload page: phones send clips to the input folder, and watch, save or delete finished Reels in the output folder.

Standard library only. Uploads are streamed to disk, so multi-GB 4K clips are fine.
Secure by default: it answers only private-network, loopback and Tailscale addresses, every request needs the private key that is
part of the printed link, nothing can be overwritten, names are sanitised, only video and photo types are accepted, and only exact
file names from the output folder can be downloaded. Delete, restore and "played" are POST only, JSON only, and only from this
page itself. Do not forward this port to the internet.

Finished videos:
  * posters (a frame at ~1 s) and lengths are cached in <output>/.reelpage/thumbs (a hidden folder);
  * videos stream with HTTP Range (206), so iPhone Safari can play and seek inline;
  * a "New" badge stays until a video is first played (<output>/.reelpage/played.json);
  * the delete button MOVES a video to <output>/_deleted/ (logged in deleted.json and log.txt), Undo / Restore moves it back;
  * after 30 days a deleted video goes to the Recycle Bin / Trash (checked at start and once a day). Never a permanent delete:
    if the Trash cannot take it, it stays in _deleted and is tried again the next day.
Run through: reel-tool upload-page
"""
import ctypes, hashlib, hmac, ipaddress, json, os, re, shutil, socket, subprocess, sys, threading, time, unicodedata, uuid
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
UPLOADS, READY, PORT, KEY = "", "", 5080, ""
KEEP_DAYS = 30                                            # then _deleted -> Recycle Bin / Trash

VIDEO_EXT = {".mov", ".mp4", ".m4v", ".3gp", ".3g2", ".avi", ".mkv", ".webm", ".hevc", ".mts", ".m2ts"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".dng"}
ALLOWED_EXT = VIDEO_EXT | IMAGE_EXT
MIME = {".mp4": "video/mp4", ".m4v": "video/x-m4v", ".mov": "video/quicktime", ".webm": "video/webm",
        ".mkv": "video/x-matroska", ".avi": "video/x-msvideo", ".3gp": "video/3gpp", ".3g2": "video/3gpp2",
        ".mts": "video/mp2t", ".m2ts": "video/mp2t", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".heic": "image/heic", ".heif": "image/heif", ".bmp": "image/bmp",
        ".tif": "image/tiff", ".tiff": "image/tiff"}
DOWNLOAD_MIME = {".shortcut": "application/octet-stream", ".mp4": "video/mp4", ".mov": "video/quicktime",
                 ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}   # /download and /v/ (SaveReel)
MAX_UPLOAD = 40 * 1024**3          # 40 GB per file
DISK_RESERVE = 2 * 1024**3         # always leave 2 GB free
CHUNK = 1024 * 1024
BATCH_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(_\d+)?$")
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
batch_lock = threading.Lock()
state_lock = threading.RLock()                            # _deleted index, played.json, moves
thumb_wake = threading.Event()
# Tailscale addresses: 100.64.0.0/10 is CGNAT space, not "private" for ipaddress; the IPv6 range is ULA
TAILSCALE_NETS = (ipaddress.ip_network("100.64.0.0/10"), ipaddress.ip_network("fd7a:115c:a1e0::/48"))
IS_WIN = os.name == "nt"


# folders inside the output folder (functions, because READY is set by serve() or by a test after import)
def deleted_dir():
    return os.path.join(READY, "_deleted")


def deleted_index():
    return os.path.join(deleted_dir(), "deleted.json")


def deleted_log():
    return os.path.join(deleted_dir(), "log.txt")


def cache_dir():
    return os.path.join(READY, ".reelpage")


def thumbs_dir():
    return os.path.join(cache_dir(), "thumbs")


def played_file():
    return os.path.join(cache_dir(), "played.json")


def log(msg):
    sys.stdout.write("%s  %s\n" % (time.strftime("%H:%M:%S"), msg))
    sys.stdout.flush()


def _common():
    """the plugin's shared helpers (ffmpeg from setup, Trash on macOS / Linux); None if this file runs on its own"""
    try:
        import common
        return common
    except ImportError:
        sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
        try:
            import common
            return common
        except Exception:
            return None
    except Exception:
        return None


def find_tool(name):
    c = _common()
    p = c.tool(name) if c else None
    return p if p and (os.path.isfile(p) or shutil.which(p)) else shutil.which(name)


FFMPEG, FFPROBE = None, None


# ---------------------------------------------------------------- Windows helpers
if IS_WIN:
    import msvcrt
    from ctypes import wintypes
    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _k32.CreateFileW.restype = wintypes.HANDLE
    _k32.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                                 wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    _k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _k32.SetFileAttributesW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD)
    _INVALID = ctypes.c_void_p(-1).value

    class _SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR),
                    ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", wintypes.LPVOID), ("lpszProgressTitle", wintypes.LPCWSTR)]
    _shell32 = ctypes.WinDLL("shell32")
    _shell32.SHFileOperationW.argtypes = (ctypes.POINTER(_SHFILEOPSTRUCTW),)


def open_shared(path):
    """Open for reading in a way that still lets delete move the file while a phone is streaming it."""
    if not IS_WIN:
        return open(path, "rb")                           # macOS / Linux can always rename an open file
    h = _k32.CreateFileW(path, 0x80000000, 0x1 | 0x2 | 0x4, None, 3, 0x80, None)   # GENERIC_READ, share R/W/DELETE
    if h is None or h == _INVALID:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(h, os.O_RDONLY | os.O_BINARY)
    except OSError:
        _k32.CloseHandle(h)
        raise
    return os.fdopen(fd, "rb")


def to_trash(path):
    """One file to the Recycle Bin / Trash (undoable). Never a permanent delete: on Windows FOF_WANTNUKEWARNING makes Windows
    ask instead of silently destroying a file it cannot recycle; elsewhere the plugin's Trash helper moves it (Finder Trash,
    gio trash or the freedesktop Trash folder)."""
    path = os.path.abspath(path)
    if IS_WIN:
        buf = ctypes.create_unicode_buffer(path + "\0")  # list of names, double-NUL terminated
        op = _SHFILEOPSTRUCTW()
        op.wFunc = 3                                      # FO_DELETE
        op.pFrom = ctypes.cast(buf, wintypes.LPCWSTR)
        op.fFlags = 0x0040 | 0x0010 | 0x0004 | 0x4000     # ALLOWUNDO | NOCONFIRMATION | SILENT | WANTNUKEWARNING
        rc = _shell32.SHFileOperationW(ctypes.byref(op))
        if rc or op.fAnyOperationsAborted or os.path.exists(path):
            raise OSError(f"Recycle Bin move failed (code {rc})")
        return
    c = _common()
    if not c or not c.trash(path):
        raise OSError("Trash move failed")


def hide(path):
    if IS_WIN and os.path.exists(path):
        _k32.SetFileAttributesW(path, 0x2)                # FILE_ATTRIBUTE_HIDDEN (the dot hides it elsewhere)


# ---------------------------------------------------------------- small helpers
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
    """Rename tmp -> folder/name, adding _2, _3 ... on a clash. Never overwrites (checked first on macOS / Linux)."""
    stem, ext = os.path.splitext(name)
    for i in range(1, 10000):
        cand = os.path.join(folder, name if i == 1 else f"{stem}_{i}{ext}")
        if not IS_WIN and os.path.lexists(cand):
            continue
        try:
            os.rename(tmp, cand)                          # on Windows os.rename never overwrites
            return os.path.basename(cand)
        except FileExistsError:
            continue
    raise OSError("no free file name")


def move_patiently(src, folder, name):
    """A file that ffmpeg or another program has open cannot be moved on Windows for a moment: retry for ~3 s."""
    for attempt in range(7):
        try:
            return place_without_overwrite(src, folder, name)
        except PermissionError:
            if attempt == 6:
                raise
            time.sleep(0.5)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def stamp(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def file_id(name):
    return hashlib.sha1(name.encode("utf-8")).hexdigest()[:12]


def media_key(name, st):
    """Changes whenever the file is replaced, so a re-rendered Reel gets a new poster."""
    return hashlib.sha1(f"{name}|{st.st_size}|{st.st_mtime_ns}".encode("utf-8")).hexdigest()[:16]


def title_of(name):
    return os.path.splitext(name)[0]


def ready_files():
    if not os.path.isdir(READY):
        return []
    out = []
    for n in os.listdir(READY):
        p = os.path.join(READY, n)
        ext = os.path.splitext(n)[1].lower()
        if ext in ALLOWED_EXT and os.path.isfile(p):
            st = os.stat(p)
            out.append({"name": n, "size": st.st_size, "mtime": st.st_mtime, "title": title_of(n),
                        "id": file_id(n), "ext": ext, "key": media_key(n, st),
                        "kind": "video" if ext in VIDEO_EXT else "image"})
    return sorted(out, key=lambda f: f["mtime"], reverse=True)


# ---------------------------------------------------------------- posters + lengths
def thumb_paths(key):
    return os.path.join(thumbs_dir(), key + ".jpg"), os.path.join(thumbs_dir(), key + ".json")


def run_quiet(cmd, timeout):
    flags = (0x08000000 | 0x00004000) if IS_WIN else 0    # CREATE_NO_WINDOW | BELOW_NORMAL_PRIORITY_CLASS
    return subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout, creationflags=flags)


def make_thumb(path, key, kind):
    jpg, meta_path = thumb_paths(key)
    meta = {"dur": None, "poster": False, "made": stamp(time.time())}
    if kind == "video" and FFPROBE:
        try:
            r = run_quiet([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], 60)
            meta["dur"] = round(float(r.stdout.decode().strip()), 2)
        except (ValueError, OSError, subprocess.SubprocessError):
            pass
    tmp = jpg + ".part.jpg"
    if FFMPEG:
        seeks = (["-ss", "1"], []) if kind == "video" else ([],)
        for ss in seeks:                                   # short clip: no frame at 1 s -> take the first one
            try:
                run_quiet([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *ss, "-i", path, "-frames:v", "1",
                           "-vf", "scale=540:-2:flags=lanczos", "-q:v", "4", tmp], 120)
            except (OSError, subprocess.SubprocessError):
                continue
            if os.path.isfile(tmp) and os.path.getsize(tmp) > 0:
                os.replace(tmp, jpg)
                meta["poster"] = True
                break
        if os.path.exists(tmp):
            os.remove(tmp)                                 # our own temp file only
    save_json(meta_path, meta)
    return meta


def thumb_meta(key):
    return load_json(thumb_paths(key)[1], None)


def scan_thumbs():
    os.makedirs(thumbs_dir(), exist_ok=True)
    hide(cache_dir())
    pending = [f for f in ready_files() if thumb_meta(f["key"]) is None]
    if not pending:
        return
    time.sleep(2)                                          # skip files that are still being copied in
    sizes = {f["name"]: f["size"] for f in ready_files()}
    made = 0
    for f in pending:
        if sizes.get(f["name"]) != f["size"]:
            thumb_wake.set()                               # look again on the next round
            continue
        meta = make_thumb(os.path.join(READY, f["name"]), f["key"], f["kind"])
        made += 1
        if not meta["poster"]:
            log(f"poster FAILED for {f['name']}")
    if made:
        log(f"posters: made {made}")


def thumb_worker():
    while True:
        try:
            scan_thumbs()
        except Exception as e:                             # keep the page running whatever happens
            log(f"poster worker error: {e!r}")
        thumb_wake.wait(60)                                # new Reels are noticed within a minute
        thumb_wake.clear()


# ---------------------------------------------------------------- played ("New" badge)
def played_state():
    with state_lock:
        state = load_json(played_file(), None)
        if state is None:                                  # first run: only Reels from the last 2 days count as new
            cutoff = time.time() - 2 * 86400
            state = {f["name"]: "before-badges" for f in ready_files() if f["kind"] == "video" and f["mtime"] < cutoff}
            save_json(played_file(), state)
            hide(cache_dir())
        return state


def mark_played(name):
    with state_lock:
        state = played_state()
        if name not in state:
            state[name] = stamp(time.time())
            save_json(played_file(), state)


# ---------------------------------------------------------------- deleted videos
def journal(line):
    with open(deleted_log(), "a", encoding="utf-8") as f:
        f.write(f"{stamp(time.time())}  {line}\n")


def sync_deleted(now=None):
    """Index of <output>/_deleted. Files put there by hand are picked up and their 30 days start now."""
    now = now or time.time()
    with state_lock:
        idx = load_json(deleted_index(), None) or {}
        items, logl = idx.get("items", []), idx.get("log", [])
        present = set()
        if os.path.isdir(deleted_dir()):
            present = {n for n in os.listdir(deleted_dir()) if os.path.splitext(n)[1].lower() in ALLOWED_EXT
                       and os.path.isfile(os.path.join(deleted_dir(), n))}
        changed = False
        kept = []
        for it in items:
            if it.get("file") in present:
                kept.append(it)
            else:
                logl.append({"action": "gone", "file": it.get("file"), "at": stamp(now)})
                changed = True
        known = {it["file"] for it in kept}
        for n in sorted(present - known):
            kept.append({"token": uuid.uuid4().hex, "file": n, "orig": n, "deleted_at": now,
                         "deleted": stamp(now), "by": "found in _deleted"})
            changed = True
        idx = {"items": kept, "log": logl}
        if changed:
            save_json(deleted_index(), idx)
        return idx


def delete_ready(fid, who):
    with state_lock:
        hit = next((f for f in ready_files() if f["id"] == fid), None)
        if not hit:
            return None
        src = os.path.join(READY, hit["name"])
        if not inside(src, READY):
            return None
        os.makedirs(deleted_dir(), exist_ok=True)
        idx = sync_deleted()
        final = move_patiently(src, deleted_dir(), hit["name"])   # MOVE, never delete
        now = time.time()
        item = {"token": uuid.uuid4().hex, "file": final, "orig": hit["name"], "deleted_at": now,
                "deleted": stamp(now), "by": who}
        idx["items"].append(item)
        idx["log"].append({"action": "deleted", "file": final, "orig": hit["name"], "at": stamp(now), "by": who})
        save_json(deleted_index(), idx)
        journal(f"deleted (moved to _deleted): {hit['name']}  [{who}]")
        log(f"deleted -> _deleted/{final}")
        return item


def restore_deleted(token, who):
    with state_lock:
        idx = sync_deleted()
        it = next((i for i in idx["items"] if i["token"] == token), None)
        if not it:
            return None
        src = os.path.join(deleted_dir(), it["file"])
        if not inside(src, deleted_dir()):
            return None
        final = move_patiently(src, READY, it["orig"])
        idx["items"] = [i for i in idx["items"] if i["token"] != token]
        idx["log"].append({"action": "restored", "file": final, "orig": it["orig"], "at": stamp(time.time()), "by": who})
        save_json(deleted_index(), idx)
        journal(f"restored to the output folder: {final}  [{who}]")
        log(f"restored -> {final}")
        thumb_wake.set()
        return final


def sweep_deleted(now=None):
    """Older than 30 days in _deleted -> Recycle Bin / Trash. The moving runs outside the lock."""
    now = now or time.time()
    with state_lock:
        idx = sync_deleted(now)
        due = [it for it in idx["items"] if now - float(it.get("deleted_at", now)) >= KEEP_DAYS * 86400]
    done, failed = [], []
    for it in due:
        path = os.path.join(deleted_dir(), it["file"])
        try:
            if not inside(path, deleted_dir()):
                raise OSError("outside _deleted")
            to_trash(path)
            done.append(it)
        except OSError as e:
            failed.append((it, str(e)))
    if done or failed:
        with state_lock:
            idx = sync_deleted(now)                            # recycled files simply vanish from the index...
            for it in done:
                idx["log"].append({"action": "trash", "file": it["file"], "orig": it["orig"], "at": stamp(time.time())})
                journal(f"after {KEEP_DAYS} days moved to the Recycle Bin / Trash: {it['file']}")
            for it, err in failed:
                idx["log"].append({"action": "trash-failed", "file": it["file"], "error": err, "at": stamp(time.time())})
                journal(f"could not move to the Recycle Bin / Trash, kept in _deleted: {it['file']} ({err})")
            idx["log"] = [e for e in idx["log"] if e.get("action") != "gone" or e.get("file") not in {d["file"] for d in done}]
            save_json(deleted_index(), idx)
    for it in done:
        log(f"{KEEP_DAYS} days: _deleted/{it['file']} -> Recycle Bin / Trash")
    return done, failed


def sweeper():
    while True:
        try:
            sweep_deleted()
        except Exception as e:
            log(f"30-day check error: {e!r}")
        time.sleep(24 * 3600)


def deleted_list():
    idx = sync_deleted()
    out = []
    for it in sorted(idx["items"], key=lambda i: -float(i.get("deleted_at", 0))):
        t = float(it.get("deleted_at", 0))
        out.append({"token": it["token"], "title": title_of(it["orig"]), "deleted_at": t,
                    "purge_at": t + KEEP_DAYS * 86400})
    return out


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ReelUpload"
    timeout = 300                                         # idle socket timeout, seconds
    head_only = False

    def log_message(self, fmt, *args):
        line = re.sub(r"([?&]k=)[^&\s]+", r"\1***", fmt % args)
        sys.stdout.write("%s  %s  %s\n" % (time.strftime("%H:%M:%S"), self.client_address[0], line)); sys.stdout.flush()

    def body(self, data):
        if not self.head_only:
            self.wfile.write(data)

    def send_json(self, code, obj, headers=()):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        self.body(body)

    def fail(self, code, msg, close=False, headers=()):
        if close:
            self.close_connection = True
        self.send_json(code, {"error": msg}, headers)

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

    def same_page(self):
        """Delete / restore / played must come from this page itself, not from another website in the same browser
        (on top of the private key, which another website does not know)."""
        host = (self.headers.get("Host") or "").strip().lower()
        if not host:
            return False
        origin = self.headers.get("Origin")
        if origin is not None and urlparse(origin).netloc.lower() != host:
            return False
        return (self.headers.get("Sec-Fetch-Site") or "same-origin") in ("same-origin", "none")

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

    def read_json(self):
        n = self.body_length()
        if n is None or n > 64 * 1024:
            self.fail(400, "bad request", close=True)
            return None
        raw = self.rfile.read(n) if n else b""
        if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
            self.fail(415, "bad request")
            return None
        try:
            obj = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(obj, dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            self.fail(400, "bad request")
            return None
        return obj

    def batch_dir(self, q):
        b = (q.get("batch") or [""])[0]
        if not BATCH_RE.match(b):
            return None
        d = os.path.join(UPLOADS, b)
        return d if os.path.isdir(d) and inside(d, UPLOADS) else None

    def by_id(self, fid):
        return next((f for f in ready_files() if f["id"] == fid), None)

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionError, socket.timeout):
            self.close_connection = True

    def do_HEAD(self):
        self.head_only = True
        try:
            self.do_GET()
        finally:
            self.head_only = False

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
            self.body(body)
        elif url.path == "/api/ready":
            self.api_ready()
        elif url.path == "/icon.png":                     # Home Screen icon (apple-touch-icon)
            f = os.path.join(os.path.dirname(HERE), ".claude-plugin", "icon.png")
            if not os.path.isfile(f):
                return self.fail(404, "file not found")
            self.send_file(f, "image/png", None)
        elif url.path == "/api/ping":                     # lets a second start see that this page already runs here
            self.send_json(200, {"app": "reel-studio-upload", "port": PORT})
        elif re.fullmatch(r"/howto/(en|ru|pl)\.mp4", url.path):  # the bundled iPhone tutorial, played on the page
            f = os.path.join(HERE, "tutorials", f"tutorial2-iphone.{url.path[7:9]}.mp4")
            if not os.path.isfile(f):
                f = os.path.join(HERE, "tutorials", "tutorial2-iphone.en.mp4")
            if not os.path.isfile(f):
                return self.fail(404, "file not found")
            self.send_file(f, "video/mp4", None)
        elif re.fullmatch(r"/shortcut/(en|ru|pl)/SaveReel\.shortcut", url.path):   # the signed iPhone Shortcut (one tap to add)
            f = os.path.join(HERE, "shortcut", url.path[10:12], "SaveReel.shortcut")
            if not os.path.isfile(f):
                return self.fail(404, "file not found")
            self.send_file(f, "application/octet-stream", 'attachment; filename="SaveReel.shortcut"')
        elif url.path == "/download":
            self.download((parse_qs(url.query).get("f") or [""])[0])
        elif re.fullmatch(r"/v/[0-9a-f]{12}\.[a-z0-9]{2,5}", url.path):   # short ASCII address for an iPhone Shortcut
            hit = self.by_id(url.path[3:15])
            self.download(hit["name"] if hit else "")
        elif re.fullmatch(r"/stream/[0-9a-f]{12}\.[a-z0-9]{2,5}", url.path):  # inline playback on the page, with Range
            self.stream(self.by_id(url.path[8:20]))
        elif re.fullmatch(r"/poster/[0-9a-f]{12}\.jpg", url.path):
            self.poster(self.by_id(url.path[8:20]))
        elif url.path in ("/api/delete", "/api/restore", "/api/played"):
            self.fail(405, "POST only", headers=(("Allow", "POST"),))
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
        if url.path in ("/api/delete", "/api/restore", "/api/played"):
            if not self.same_page():
                self.discard_body()
                return self.fail(403, "request not from this page")
            data = self.read_json()
            if data is None:
                return
            return {"/api/delete": self.api_delete, "/api/restore": self.api_restore,
                    "/api/played": self.api_played}[url.path](data)
        self.discard_body()
        self.fail(404, "not found")

    # ---- finished videos ----
    def api_ready(self):
        played = played_state()
        files, missing = [], False
        for f in ready_files():
            meta = thumb_meta(f["key"])
            missing |= meta is None
            files.append({k: f[k] for k in ("name", "size", "mtime", "title", "id", "ext", "kind")} | {
                "dur": (meta or {}).get("dur"),
                "poster": f"/poster/{f['id']}.jpg?v={f['key']}" if meta and meta.get("poster") else "",
                "new": f["kind"] == "video" and f["name"] not in played})
        if missing:
            thumb_wake.set()
        self.send_json(200, {"files": files, "deleted": deleted_list(), "keep_days": KEEP_DAYS})

    def api_delete(self, data):
        try:
            item = delete_ready(str(data.get("id", "")), self.client_address[0])
        except PermissionError:
            return self.fail(409, "the video is open on the computer, try again")
        except OSError as e:
            log(f"delete FAILED: {e!r}")
            return self.fail(500, "could not delete")
        if not item:
            return self.fail(404, "video not found")
        self.send_json(200, {"ok": True, "token": item["token"], "title": title_of(item["orig"])})

    def api_restore(self, data):
        try:
            final = restore_deleted(str(data.get("token", "")), self.client_address[0])
        except PermissionError:
            return self.fail(409, "the video is open on the computer, try again")
        except OSError as e:
            log(f"restore FAILED: {e!r}")
            return self.fail(500, "could not restore")
        if not final:
            return self.fail(404, "no longer in recently deleted")
        self.send_json(200, {"ok": True, "name": final, "title": title_of(final)})

    def api_played(self, data):
        hit = self.by_id(str(data.get("id", "")))
        if not hit:
            return self.fail(404, "video not found")
        mark_played(hit["name"])
        self.send_json(200, {"ok": True})

    def stream(self, hit):
        if not hit or not inside(os.path.join(READY, hit["name"]), READY):
            return self.fail(404, "file not found")
        self.send_file(os.path.join(READY, hit["name"]), MIME.get(hit["ext"], "application/octet-stream"),
                       f"inline; filename*=UTF-8''{quote(hit['name'])}")

    def poster(self, hit):
        meta = thumb_meta(hit["key"]) if hit else None
        if not meta or not meta.get("poster"):
            thumb_wake.set()
            return self.fail(404, "no poster yet")
        self.send_file(thumb_paths(hit["key"])[0], "image/jpeg", None, cache="private, max-age=604800")

    def download(self, want):
        files = {f["name"]: f for f in ready_files()}     # only exact names that exist in the output folder
        if want not in files:
            return self.fail(404, "file not found")
        path = os.path.join(READY, want)
        if not inside(path, READY):
            return self.fail(404, "file not found")
        ascii_name = re.sub(r"[^A-Za-z0-9._ -]", "_", want)
        self.send_file(path, DOWNLOAD_MIME.get(os.path.splitext(want)[1].lower(), "application/octet-stream"),
                       f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(want)}")

    def send_file(self, path, ctype, disposition, cache="no-cache"):
        """200 or 206 (one byte range: iPhone video players and resumed downloads need it), 416 for an impossible range"""
        try:
            f = open_shared(path)
        except OSError:
            return self.fail(404, "file not found")
        with f:
            st = os.fstat(f.fileno())
            size = st.st_size
            etag = f'"{size:x}-{st.st_mtime_ns:x}"'
            lastmod = formatdate(st.st_mtime, usegmt=True)
            start, end = 0, size - 1
            rng = re.match(r"^bytes=(\d*)-(\d*)$", self.headers.get("Range", "").strip())
            if_range = self.headers.get("If-Range")
            if if_range and if_range.strip() not in (etag, lastmod):
                rng = None                                   # file changed since the player's first request
            if rng and (rng.group(1) or rng.group(2)):
                if rng.group(1):
                    start = int(rng.group(1))
                    end = min(int(rng.group(2)), size - 1) if rng.group(2) else size - 1
                else:
                    start = max(0, size - int(rng.group(2)))
                    if not int(rng.group(2)):
                        start = size                         # "bytes=-0" can't be satisfied
                if start > end or start >= size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.send_header("Content-Length", "0")
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    return
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            else:
                self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(max(0, end - start + 1)))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("ETag", etag)
            self.send_header("Last-Modified", lastmod)
            self.send_header("Cache-Control", cache)
            self.send_header("X-Content-Type-Options", "nosniff")
            if disposition:
                self.send_header("Content-Disposition", disposition)
            self.end_headers()
            if self.head_only:
                return
            f.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = f.read(min(CHUNK, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    # ---- uploads ----
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
        stamp_ = time.strftime("%Y-%m-%d_%H-%M")
        with batch_lock:
            for i in range(1, 1000):
                name = stamp_ if i == 1 else f"{stamp_}_{i}"
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
    global UPLOADS, READY, PORT, KEY, FFMPEG, FFPROBE
    UPLOADS, READY, PORT, KEY = str(uploads), str(ready), int(port), key
    os.makedirs(UPLOADS, exist_ok=True); os.makedirs(READY, exist_ok=True)
    FFMPEG, FFPROBE = find_tool("ffmpeg"), find_tool("ffprobe")
    srv = Server(("0.0.0.0", PORT), Handler)
    threading.Thread(target=thumb_worker, name="posters", daemon=True).start()
    threading.Thread(target=sweeper, name="30-days", daemon=True).start()
    print("Upload page is running. Open on the phone:", flush=True)
    for ip in lan_ips():
        print(f"  http://{ip}:{PORT}/?k={KEY}", flush=True)
    print(f"Clips go to: {UPLOADS}\nFinished Reels come from: {READY}\n"
          f"Deleted Reels wait in: {deleted_dir()} (after {KEEP_DAYS} days they go to the Recycle Bin / Trash)\n"
          f"Local network and Tailscale only. Stop with Ctrl+C.", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
