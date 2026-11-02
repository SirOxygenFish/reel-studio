---
name: reel-voice
description: The voice clean-up chain for Reels and how to use it. Read when a Reel's voice sounds distant, noisy or uneven, or when asked to clean up audio.
allowed-tools: Bash(reel-tool *), PowerShell(reel-tool *)
---

# Voice

Plain loudness normalisation raises room echo and noise: the speaker sounds "across the room". So every new Reel runs this chain, once, on the raw voice; `reel-tool render` does it for you.

1. Highpass 80 Hz.
2. DeepFilterNet3, attenuation limit 16 dB (10 dB when the room floor is under -66 dBFS: such a mic already gates or denoises and more would chew the voice). It falls back to RNNoise (`arnndn`), then `afftdn`; a Reel never blocks on it, but the gate fails on a fallback, so run `/reel-doctor`.
3. EQ: -3 dB at 300 Hz (mud), +4.5 dB at 3.5 kHz (presence), +2.5 dB at 9 kHz (air).
4. Compressor: +4 dB, threshold -22 dBFS, 3:1, 5 ms attack, 250 ms release.
5. De-esser: split-band at 5 kHz, 3:1 above +6 dB over the speech baseline, at most -8 dB.
6. Skits only: the ring tone mixes in here, after the denoiser, or the denoiser would remove it.
7. Limiter, then two-pass loudnorm to -14 LUFS, -1.5 dBTP, in linear mode.

Presets (the `- Voice:` line of job.md): `phone` for messenger-compressed copies (low bitrate, mono, no device tag; `brief` suggests it): DeepFilterNet 24 dB, EQ -4 dB at 250 Hz, -1.5 at 500, +3.5 at 3 kHz, -1.5 at 7 kHz so codec swirl is not lifted. `outdoor` for wind and street: the same plus highpass 150 Hz, EQ -2 at 300, +4 at 3 kHz, +1.5 at 6.5 kHz.

Rules:
- **Never twice.** A finished Reel already carries the chain: do not run it on delivered files. To make a faceless version of a finished Reel, pass its audio through as it is (`reel-tool faceless <job> --voice clean.wav`).
- Music, if asked for, goes on after the chain, on the finished voice.
- Sound effects are mixed after the chain, about 21 dB under the voice; only the effects are turned down if peaks get close.
- Override the limit per brand: `"voice": {"atten_db": 10}` in brand.json, or `reel-tool config voice '{"atten_db": 10}'`.
- Recording advice worth passing on when a voice sounds distant: clip the mic higher (15 cm from the mouth), switch off any noise reduction on the transmitter.
