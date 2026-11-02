# Third-party components

## Bundled in this plugin

| Component | Licence | Where | Source | Licence text |
|---|---|---|---|---|
| Phosphor Icons 2.1.1 (npm @phosphor-icons/core) | MIT | `motion/assets/icons/ph*.json.gz` | https://phosphoricons.com | `motion/assets/icons/LICENSE.phosphor` |
| Tabler Icons 3.49 (npm @tabler/icons) | MIT | `motion/assets/icons/tb*.json.gz` | https://tabler.io/icons | `motion/assets/icons/LICENSE.tabler` |
| Noto Emoji images by Google, via the Iconify "noto" set (without flags and skin-tone variants) | Apache 2.0 | `motion/assets/icons/noto.json.gz` | https://github.com/googlefonts/noto-emoji | `motion/assets/icons/LICENSE.noto` |
| Open Peeps by Pablo Stanley | CC0 1.0 (public domain) | `motion/assets/peeps/peeps.json` | https://www.openpeeps.com | `motion/assets/peeps/LICENSE.peeps` |

The icon bundles are the original SVG data packed into gzipped JSON by `motion/tools/build_icons.mjs`; the peeps were extracted
from the npm package @opeepsfun/open-peeps 1.0.6 by `motion/tools/build_assets.mjs`. Each licence was checked at its source on
2026-11-02. The plugin icon, the motion engine, the scene library and every other file are original work under this
repository's MIT licence (see `LICENSE`).

## Downloaded by /reel-setup, into your data folder

| Component | Licence | Downloaded from |
|---|---|---|
| ffmpeg 9.0.2 essentials build (Gyan), Windows | GPL v3 | github.com/GyanD/codexffmpeg |
| ffmpeg 8.1 static build (BtbN), Linux | GPL v3 | github.com/BtbN/FFmpeg-Builds |
| ffmpeg 9.0.2 static build (Martin Riedl), macOS | GPL v3 | ffmpeg.martin-riedl.de |
| Node.js 24 | MIT | nodejs.org |
| chrome-headless-shell 156 (Chrome for Testing) | BSD-style Chromium licence | storage.googleapis.com/chrome-for-testing-public |
| uv and CPython 3.11 | MIT or Apache 2.0; PSF | github.com/astral-sh |
| faster-whisper, CTranslate2 | MIT | PyPI |
| Whisper large-v3 model, converted by Systran | MIT | huggingface.co/Systran |
| NVIDIA CUDA runtime wheels (only on NVIDIA machines) | NVIDIA proprietary, redistributable | PyPI |
| DeepFilterNet 0.5.6 and DeepFilterNet3 model | MIT or Apache 2.0 | PyPI, github.com/Rikorose/DeepFilterNet |
| PyTorch, torchaudio (CPU) | BSD-3-Clause | download.pytorch.org |
| RNNoise model bd.rnnn (fallback denoiser) | BSD-3-Clause, per the model repository | github.com/richardpl/arnndn-models |
| YuNet face detector | MIT | github.com/opencv/opencv_zoo |
| OpenCV, NumPy, SciPy, Pillow, resvg_py, huggingface_hub | Apache 2.0, BSD, HPND, MPL 2.0, Apache 2.0 | PyPI |
| Montserrat, Plus Jakarta Sans and any font you pick in /reel-brand (@fontsource) | SIL Open Font License 1.1 | registry.npmjs.org |
| Montserrat Black TTF and Noto Sans Symbols 2 (subtitles on Linux and macOS) | SIL Open Font License 1.1 | github.com/JulietaUla/Montserrat, github.com/google/fonts |

Each direct download is pinned by SHA-256 in `scripts/pins.json`.

## System fonts

On Windows, subtitles default to Segoe UI Black and symbols use Segoe UI Symbol, fonts that come with Windows; they are used
from the system and not redistributed. On Linux and macOS the downloaded Montserrat Black and Noto Sans Symbols 2 are used.

## Generated content

Sound effects and phone rings are synthesised in code; no recorded sound or music is bundled or downloaded. Bespoke scenes
written for your Reels stay in your data folder.

## MIT licence text

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
