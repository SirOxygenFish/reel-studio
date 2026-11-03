"""reel-tool upload-page [--port N]: starts the phone upload page (LAN and Tailscale only, private key in the link).

If the page already runs (autostart, the desktop shortcut or another session) it only prints the links. A port held by another
program is never shared: it stops with the line that picks another port.
"""
import sys

import common as C
import phone


def main(argv):
    port, key = phone.settings()
    if "--port" in argv:
        port = int(argv[argv.index("--port") + 1])
    st = phone.state(port, key)
    if st == "ours":
        print("The upload page is already running. Open on the phone:")
        for _, url in phone.links(port, key):
            print("  " + url)
        return
    if st == "busy":
        C.fail(f"port {port} is used by another program. Pick a free one: reel-tool config upload_page.port 5081")
    import server
    F = C.upload_folders()
    server.serve(F["input"], F["output"], port, key)


if __name__ == "__main__":
    main(sys.argv[1:])
