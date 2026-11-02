"""reel-tool upload-page [--port N]: starts the phone upload page (LAN and Tailscale only, private key in the link)."""
import secrets, sys
from pathlib import Path

import common as C

sys.path.insert(0, str(C.ROOT / "upload-page"))


def main(argv):
    import server
    cfg = C.load_json(C.CONFIG_FILE, {}) or {}
    up = cfg.setdefault("upload_page", {})
    if not up.get("key"):
        up["key"] = secrets.token_urlsafe(16); C.save_json(C.CONFIG_FILE, cfg)
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else int(up.get("port", 5080))
    F = C.folders()
    server.serve(F["input"], F["output"], port, up["key"])


if __name__ == "__main__":
    main(sys.argv[1:])
