#!/usr/bin/env bash
# First stage of setup: a private uv + Python 3.11 + venv in the data dir, then setup_env.py does the rest. Idempotent.
# Windows (Git Bash), Linux x86-64 and macOS on Apple Silicon. Nothing is installed system-wide and sudo is never used.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENVD="$REEL_STUDIO_DATA/env"
mkdir -p "$ENVD"
UV_VER=0.13.6
case "$(uname -s)-$(uname -m)" in
  MINGW*|MSYS*|CYGWIN*)
    UV_ASSET=uv-x86_64-pc-windows-msvc.zip; UV_SHA=a2a8820d5eea32f08ef467ef3b7f66883a9b076d5737a2fc2fbb5f458d1bb50f
    UV="$ENVD/uv/uv.exe"; VPY="$ENVD/venv/Scripts/python.exe" ;;
  Linux-x86_64)
    UV_ASSET=uv-x86_64-unknown-linux-gnu.tar.gz; UV_SHA=f29c3e94ffabd7e6f3ba521dba169a9b7ec12100bf3257087f0f24f6123f3645
    UV="$ENVD/uv/uv"; VPY="$ENVD/venv/bin/python" ;;
  Darwin-arm64)
    UV_ASSET=uv-aarch64-apple-darwin.tar.gz; UV_SHA=60fbd5c8a1ed681845eea28d9d622fcde03c51e91a43465b64a1e17db1ed3472
    UV="$ENVD/uv/uv"; VPY="$ENVD/venv/bin/python" ;;
  *)
    echo "Reel Studio runs on Windows x64, Linux x86-64 and macOS on Apple Silicon. This machine is $(uname -s) $(uname -m)."; exit 2 ;;
esac
for t in curl tar; do
  command -v "$t" >/dev/null || { echo "Missing: $t. Install it, e.g. on Ubuntu/Zorin: sudo apt install $t"; exit 2; }
done
sha_ok() {   # file sha
  if command -v sha256sum >/dev/null; then echo "$2  $1" | sha256sum -c --quiet -; else echo "$2  $1" | shasum -a 256 -c --quiet -; fi
}
if [ ! -x "$UV" ]; then
  echo "[bootstrap] downloading uv $UV_VER (private Python manager)"
  mkdir -p "$ENVD/uv"
  curl -fsSL --retry 3 -o "$ENVD/uv/$UV_ASSET" "https://github.com/astral-sh/uv/releases/download/$UV_VER/$UV_ASSET"
  sha_ok "$ENVD/uv/$UV_ASSET" "$UV_SHA"
  case "$UV_ASSET" in
    *.zip) (cd "$ENVD/uv" && unzip -oq "$UV_ASSET") ;;
    *) tar -xzf "$ENVD/uv/$UV_ASSET" -C "$ENVD/uv" --strip-components=1 ;;
  esac
  rm -f "$ENVD/uv/$UV_ASSET"
fi
export UV_PYTHON_INSTALL_DIR="$ENVD/python" UV_CACHE_DIR="$ENVD/uv-cache"
if [ ! -x "$VPY" ]; then
  echo "[bootstrap] creating Python 3.11 environment"
  "$UV" venv --python 3.11 --python-preference only-managed "$ENVD/venv"
fi
exec "$VPY" "$ROOT/scripts/setup_env.py" "$@"
