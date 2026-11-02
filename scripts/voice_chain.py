"""Voice clean-up chain for Reels. Runs on the VOICE ONLY (the concatenated speech of the cut), never twice on the same audio.
  1. highpass 80 Hz
  2. denoise / room-tail reduction: DeepFilterNet3 (attenuation limit 16 dB; 10 dB for mics that already gate or denoise)
     -> fallback arnndn (RNNoise model bd.rnnn, mix 0.8) -> fallback afftdn. A Reel never blocks on this step.
  3. EQ: -3 dB @ 300 Hz (mud), +4.5 dB @ 3.5 kHz (presence), +2.5 dB @ 9 kHz (air)
  4. compressor: +4 dB, threshold 0.08 (-22 dBFS), ratio 3, attack 5 ms, release 250 ms, knee 4
  5. split-band de-esser (5 kHz band, +6 dB over its speech baseline, 3:1, max -8 dB)
  6. optional --ring ring.wav (skits) mixed in here, ~5 dB under the voice, so the denoiser never sees it
  7. gain + alimiter (ceiling 0.66) tuned so that 8. two-pass loudnorm I=-14 TP=-1.5 runs in LINEAR mode
Usage:  reel-tool voice <in: wav/mp4> <out.wav> [--atten auto|16|10] [--preset phone|outdoor] [--ring ring.wav] [--denoise df|rnn|fft|none]
Prints which denoiser ran and the final loudness. Plain loudnorm alone raises room echo and noise: "from across the room".
"""
import json, os, re, subprocess, sys, tempfile, shutil
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt

import common as C

DF_MODEL = C.ENVD / "models" / "DeepFilterNet3"
RNN_MODEL = C.ENVD / "models" / "bd.rnnn"
EQ = "equalizer=f=300:t=q:w=1.0:g=-3,equalizer=f=3500:t=q:w=0.9:g=4.5,equalizer=f=9000:t=q:w=0.8:g=2.5"
COMP = "volume=4dB,acompressor=threshold=0.08:ratio=3:attack=5:release=250:knee=4:makeup=1"
LIMIT = 0.66
GATED_FLOOR_DB = -66.0        # room tone this low between words = the mic already gates or denoises: be gentle
# messenger-compressed phone clips: more room-tail cleanup, presence at 3 kHz, 7 kHz down so the codec's swirl is not lifted;
# outdoor: the same plus a higher highpass against wind rumble
PRESETS = {"phone": {"atten": 24, "hp": 80, "eq": "equalizer=f=250:t=q:w=1.2:g=-4,equalizer=f=500:t=q:w=1.4:g=-1.5,equalizer=f=3000:t=q:w=1.0:g=3.5,equalizer=f=7000:t=q:w=1.0:g=-1.5"},
           "outdoor": {"atten": 24, "hp": 150, "eq": "equalizer=f=300:t=q:w=1.2:g=-2,equalizer=f=3000:t=q:w=1.0:g=4,equalizer=f=6500:t=q:w=1.0:g=1.5"}}
DF_SNIPPET = r"""
import sys, types, numpy as np, torch
try:
    import torchaudio.backend.common
except Exception:                                  # torchaudio >= 2.1 removed this module, df.io still imports it
    b = types.ModuleType("torchaudio.backend"); c = types.ModuleType("torchaudio.backend.common"); c.AudioMetaData = object; b.common = c
    sys.modules["torchaudio.backend"] = b; sys.modules["torchaudio.backend.common"] = c
from scipy.io import wavfile
from df.enhance import init_df, enhance
model, state, _ = init_df(model_base_dir=sys.argv[3])
sr, x = wavfile.read(sys.argv[1]); assert sr == state.sr()
y = enhance(model, state, torch.from_numpy(x.astype(np.float32))[None], atten_lim_db=float(sys.argv[4]))
wavfile.write(sys.argv[2], sr, y[0].cpu().numpy().astype(np.float32))
"""


def ff(*a, **kw):
    return C.ff(*a, **kw)


def loud(path, extra=""):
    r = ff("-i", path, "-af", (extra + "," if extra else "") + "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-")
    return json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))


def room_floor(path):
    """level of the quiet 5 % of 20 ms frames, dBFS"""
    sr, x = wavfile.read(path); x = x.astype(np.float64)
    if abs(x).max() > 2:
        x = x / 32768
    n = int(sr * 0.02); f = x[:len(x) // n * n].reshape(-1, n)
    return float(np.percentile(10 * np.log10((f ** 2).mean(1) + 1e-12), 5))


def denoise(src, dst, mode, lim, tmp):
    if mode == "df":
        if DF_MODEL.is_dir():
            script = os.path.join(tmp, "df_run.py"); open(script, "w").write(DF_SNIPPET)
            try:
                r = subprocess.run([sys.executable, script, src, dst, str(DF_MODEL), str(lim)], capture_output=True, text=True, timeout=900)
                if r.returncode == 0 and os.path.exists(dst):
                    return f"DeepFilterNet3 (atten_lim {lim} dB)"
                print("DeepFilterNet failed, falling back:", r.stderr.strip().splitlines()[-1:] or r.returncode)
            except subprocess.TimeoutExpired:
                print("DeepFilterNet timed out, falling back")
        else:
            print("DeepFilterNet model missing - falling back (run /reel-setup)")
        mode = "rnn"
    if mode == "rnn":
        if RNN_MODEL.exists():
            m = str(RNN_MODEL).replace("\\", "/").replace(":", "\\:")
            if ff("-i", src, "-af", f"arnndn=m='{m}':mix=0.8", "-c:a", "pcm_f32le", dst).returncode == 0:
                return "arnndn (bd.rnnn, mix 0.8) - FALLBACK"
        mode = "fft"
    if mode == "fft":
        ff("-i", src, "-af", "afftdn=nr=10:nf=-50:tn=1", "-c:a", "pcm_f32le", dst, check=False)
        if os.path.exists(dst):
            return "afftdn (nr 10) - LAST FALLBACK"
    shutil.copy(src, dst)
    return "none"


def deess(src, dst, over=6.0, ratio=3.0, maxcut=8.0):
    sr, x = wavfile.read(src); x = x.astype(np.float64)
    hf = sosfiltfilt(butter(4, 5000, btype="high", fs=sr, output="sos"), x); lo = x - hf          # exact split
    w = int(0.005 * sr); env = np.sqrt(np.convolve(hf ** 2, np.ones(w) / w, mode="same")) + 1e-9
    edb = 20 * np.log10(env); act = edb > np.percentile(edb, 50)
    thr = np.percentile(edb[act], 75) + over
    red = np.clip((edb - thr) * (1 - 1 / ratio), 0, maxcut)
    a, r = np.exp(-1 / (0.001 * sr)), np.exp(-1 / (0.040 * sr)); g = np.empty_like(red); s = 0.0
    for i, v in enumerate(red):
        s = a * s + (1 - a) * v if v > s else r * s + (1 - r) * v; g[i] = s
    wavfile.write(dst, sr, (lo + hf * 10 ** (-g / 20)).astype(np.float32))


def run(src, out, atten="auto", ring=None, mode="df", preset=None):
    tmp = tempfile.mkdtemp(prefix="voice_")
    try:
        p = lambda n: os.path.join(tmp, n)
        P = PRESETS.get(preset or "", {})
        ff("-i", src, "-vn", "-ac", "1", "-ar", "48000", "-af", f"highpass=f={P.get('hp', 80)}:poles=2", "-c:a", "pcm_f32le", p("hp.wav"), check=False)
        floor = room_floor(p("hp.wav"))
        lim = P["atten"] if P and str(atten) == "auto" else (10 if floor < GATED_FLOOR_DB else 16) if str(atten) == "auto" else int(atten)
        used = denoise(p("hp.wav"), p("dn.wav"), mode, lim, tmp)
        ff("-i", p("dn.wav"), "-af", f"{P.get('eq', EQ)},{COMP}", "-c:a", "pcm_f32le", p("eq.wav"))
        deess(p("eq.wav"), p("ds.wav"))
        cur = p("ds.wav")
        if ring:                                          # skit pre-roll ring: ~5 dB under the finished voice
            vi = float(loud(cur)["input_i"])
            ff("-i", cur, "-i", ring, "-filter_complex",
               f"[1:a]aresample=48000,pan=mono|c0=0.5*c0+0.5*c1,volume={vi - 8.6 + 24:.1f}dB[r];[0:a][r]amix=inputs=2:duration=first:normalize=0",
               "-c:a", "pcm_f32le", p("mix.wav")); cur = p("mix.wav")
        gain = -14.0 + 1.6 - float(loud(cur)["input_i"])  # start so that ~1.6 dB is left for loudnorm
        for _ in range(6):
            ff("-i", cur, "-af", f"volume={gain:.2f}dB,alimiter=limit={LIMIT}:attack=4:release=60:level=false", "-c:a", "pcm_f32le", p("lim.wav"))
            j = loud(p("lim.wav")); need = -14.0 - float(j["input_i"])
            if float(j["input_tp"]) + need <= -1.5:       # loudnorm can stay linear
                break
            gain += need                                  # push more of the gain through the limiter
        af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
              f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true:print_format=json,aresample=48000")
        r = ff("-i", p("lim.wav"), "-af", af, "-c:a", "pcm_s16le", out)
        kind = re.search(r'"normalization_type" : "(\w+)"', r.stderr)
        fin = loud(out)
        print(f"voice_chain: room floor {floor:.1f} dBFS; denoise = {used}; limiter gain {gain:.1f} dB; loudnorm {kind.group(1) if kind else '?'}; "
              f"result {float(fin['input_i']):.1f} LUFS, TP {float(fin['input_tp']):.1f} dBTP -> {out}")
        return {"denoiser": used, "lufs": float(fin["input_i"]), "tp": float(fin["input_tp"]), "floor_db": round(floor, 1), "atten": lim, "preset": preset or "normal"}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(args):
    opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
    run(args[0], args[1], opt("--atten", "auto"), opt("--ring"), opt("--denoise", "df"), opt("--preset"))


if __name__ == "__main__":
    main(sys.argv[1:])
