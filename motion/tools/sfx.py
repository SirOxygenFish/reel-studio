"""Subtle synthesised sound effects with VARIETY (no downloads, no licences) - shared by the motion engine and the editing pipeline.
Usage: python sfx.py events.json voice.wav out.wav [--level -21] [--seed N]
events.json = [[t, kind], ...]  kind: whoosh | pop | tick | ding | swell   (aliases: click -> tick, rise -> swell)

Why: the same few sounds reused over and over are noticed. So:
- a bank of 6 distinct recipes per kind, and every hit is re-synthesised with random pitch (+-10 %), length (+-20 %) and
  timbre (filter colour / partials / noise mix), so no two hits are sample-identical;
- the same recipe is never used twice in a row and not again within 10 s (per kind);
- thinning: transitions (whoosh/swell) always play, but at most one sound per 1.2 s; accents (pop/tick) need >= 2.5 s
  since the last accent, dings >= 8 s since the last ding (so not every sticker gets a sound);
- level about -21 dB under the speech (+-1.5 dB per hit), mixed AFTER the voice chain; only the effects are turned down if
  they would push the peak over -1.8 dBFS. "swell" ends ON the event time (it rises into a reveal).
Deterministic for the same events + seed, so re-renders sound the same.
"""
import json, sys, hashlib
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 48000
RECENT_S, ACCENT_GAP, DING_GAP, MIN_GAP = 10.0, 2.5, 8.0, 1.2


def env_ad(n, a=0.01, curve=4.0):
    t = np.linspace(0, 1, n); att = max(1, int(a * SR)); e = np.exp(-curve * t)
    e[:att] *= np.linspace(0, 1, att); return e


def band(x, lo, hi):
    lo, hi = max(30, lo), min(SR / 2 - 200, hi)
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)


# ---- recipes: f(rng, p = pitch factor, L = length factor) -> mono float array ----
def w_sweep_up(r, p, L):
    n = int(0.30 * L * SR); x = r.standard_normal(n); out = np.zeros(n); k = 10; seg = n // k
    for i in range(k):
        lo = (250 + 380 * i) * p; out[i * seg:(i + 1) * seg] = band(x[i * seg:(i + 1) * seg], lo, lo * 2.3)
    return out * np.sin(np.linspace(0, np.pi, n)) ** 1.4
def w_sweep_down(r, p, L):
    return w_sweep_up(r, p * 1.1, L)[::-1] * 0.9
def w_airy(r, p, L):
    n = int(0.38 * L * SR); x = band(r.standard_normal(n), 2500 * p, 9000 * p); return x * np.sin(np.linspace(0, np.pi, n)) ** 2.2
def w_low(r, p, L):
    n = int(0.42 * L * SR); x = band(r.standard_normal(n), 140 * p, 900 * p); return x * np.sin(np.linspace(0, np.pi, n)) ** 1.2
def w_doppler(r, p, L):
    n = int(0.34 * L * SR); t = np.arange(n) / SR; f = 600 * p * (1 + 0.8 * np.tanh((t - t[-1] / 2) * 18))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25; x = band(r.standard_normal(n), 800 * p, 4000 * p)
    return (x + tone) * np.sin(np.linspace(0, np.pi, n)) ** 1.6
def w_flutter(r, p, L):
    n = int(0.32 * L * SR); x = band(r.standard_normal(n), 900 * p, 5000 * p)
    am = 0.6 + 0.4 * np.sin(2 * np.pi * (22 + 10 * r.random()) * np.arange(n) / SR); return x * am * np.sin(np.linspace(0, np.pi, n)) ** 1.5

def p_chirp_down(r, p, L):
    n = int(0.07 * L * SR); t = np.arange(n) / SR; f = (900 * np.exp(-t * 40) + 260) * p
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(n, 0.002, 5)
def p_bubble(r, p, L):
    n = int(0.09 * L * SR); t = np.arange(n) / SR; f = (380 + 900 * (t / t[-1]) ** 0.6) * p
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(n, 0.003, 4)
def p_cork(r, p, L):
    n = int(0.06 * L * SR); x = band(r.standard_normal(n), 600 * p, 2400 * p); return x * env_ad(n, 0.001, 9)
def p_wood(r, p, L):
    n = int(0.10 * L * SR); t = np.arange(n) / SR; f0 = 520 * p
    return (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 2.76 * t)) * env_ad(n, 0.001, 9)
def p_pluck(r, p, L):
    n = int(0.16 * L * SR); t = np.arange(n) / SR; f0 = 700 * p
    return sum(np.sin(2 * np.pi * f0 * h * t) / h for h in (1, 2, 3)) * env_ad(n, 0.001, 7)
def p_blip(r, p, L):
    n = int(0.05 * L * SR); t = np.arange(n) / SR; return np.sign(np.sin(2 * np.pi * 880 * p * t)) * 0.4 * env_ad(n, 0.001, 6)

def t_click(r, p, L):
    n = int(0.018 * L * SR); return band(r.standard_normal(n), 2500 * p, 8000 * p) * env_ad(n, 0.0005, 6)
def t_tick_hi(r, p, L):
    n = int(0.03 * L * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * 3100 * p * t) * env_ad(n, 0.0005, 8)
def t_tock(r, p, L):
    n = int(0.045 * L * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * 1250 * p * t) * env_ad(n, 0.0005, 7)
def t_snap(r, p, L):
    n = int(0.03 * L * SR); return band(r.standard_normal(n), 1200 * p, 3500 * p) * env_ad(n, 0.0005, 10)
def t_double(r, p, L):
    a = t_tick_hi(r, p, L); gap = np.zeros(int(0.045 * SR)); return np.concatenate([a, gap, t_tick_hi(r, p * 1.12, L) * 0.7])
def t_keys(r, p, L):
    n = int(0.04 * L * SR); return band(r.standard_normal(n), 1800 * p, 5200 * p) * env_ad(n, 0.0008, 5) * 0.8

def d_bell(r, p, L):
    n = int(0.6 * L * SR); t = np.arange(n) / SR; f = 1320 * p
    return (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) + 0.2 * np.sin(2 * np.pi * 3 * f * t)) * np.exp(-t * 7 / L)
def d_glass(r, p, L):
    n = int(0.7 * L * SR); t = np.arange(n) / SR; f = 1760 * p
    return (np.sin(2 * np.pi * f * t) + 0.6 * np.sin(2 * np.pi * f * 2.41 * t) + 0.3 * np.sin(2 * np.pi * f * 3.9 * t)) * np.exp(-t * 6 / L)
def d_chime2(r, p, L):
    a = d_bell(r, p * 0.89, L * 0.5); b = d_bell(r, p * 1.12, L * 0.6); off = int(0.09 * SR)
    out = np.zeros(max(len(a), off + len(b))); out[:len(a)] += a; out[off:off + len(b)] += b * 0.8; return out
def d_soft(r, p, L):
    n = int(0.5 * L * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * 988 * p * t) * np.exp(-t * 9 / L)
def d_marimba(r, p, L):
    n = int(0.45 * L * SR); t = np.arange(n) / SR; f = 784 * p
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 4 * t)) * np.exp(-t * 11 / L)
def d_sparkle(r, p, L):
    out = np.zeros(int(0.5 * L * SR))
    for k in range(4):
        s = d_glass(r, p * (1 + 0.12 * k), 0.35); i = int(k * 0.05 * SR); m = min(len(s), len(out) - i)
        if m > 0: out[i:i + m] += s[:m] * (0.8 ** k)
    return out

def s_noise(r, p, L):
    n = int(0.75 * L * SR); x = band(r.standard_normal(n), 400 * p, 6000 * p); return x * np.linspace(0, 1, n) ** 2.5
def s_tone(r, p, L):
    n = int(0.7 * L * SR); t = np.arange(n) / SR; f = 220 * p * (1 + 1.2 * (t / t[-1]) ** 2)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.linspace(0, 1, n) ** 2
def s_shimmer(r, p, L):
    n = int(0.8 * L * SR); t = np.arange(n) / SR
    tone = sum(np.sin(2 * np.pi * 660 * p * h * t) / h for h in (1, 1.5, 2))
    return (tone * 0.4 + band(r.standard_normal(n), 3000, 9000)) * np.linspace(0, 1, n) ** 3
def s_reverse(r, p, L):
    return d_bell(r, p * 0.8, L * 1.2)[::-1]
def s_vacuum(r, p, L):
    n = int(0.6 * L * SR); x = r.standard_normal(n); out = np.zeros(n); k = 8; seg = n // k
    for i in range(k):
        lo = (200 + 500 * i) * p; out[i * seg:(i + 1) * seg] = band(x[i * seg:(i + 1) * seg], lo, lo * 1.8)
    return out * np.linspace(0, 1, n) ** 2
def s_pad(r, p, L):
    n = int(0.9 * L * SR); t = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * 330 * p * k * t + r.random() * 6) for k in (1, 1.26, 1.5)) / 3 * np.linspace(0, 1, n) ** 2

BANK = {
    "whoosh": [w_sweep_up, w_sweep_down, w_airy, w_low, w_doppler, w_flutter],
    "pop":    [p_chirp_down, p_bubble, p_cork, p_wood, p_pluck, p_blip],
    "tick":   [t_click, t_tick_hi, t_tock, t_snap, t_double, t_keys],
    "ding":   [d_bell, d_glass, d_chime2, d_soft, d_marimba, d_sparkle],
    "swell":  [s_noise, s_tone, s_shimmer, s_reverse, s_vacuum, s_pad]}
ALIAS = {"click": "tick", "rise": "swell", "whip": "whoosh", "punch": "pop"}


def plan(events, seed):
    """thin the events and pick a recipe per hit: never the same recipe twice in a row, not again within 10 s (per kind)"""
    rng = np.random.default_rng(seed)
    evs = sorted(([float(a), ALIAS.get(b, b)] for a, b in events if ALIAS.get(b, b) in BANK), key=lambda e: e[0])
    chosen = []                                               # transitions first (they win), then accents fill the gaps
    for tr in (True, False):
        for t, kind in evs:
            if (kind in ("whoosh", "swell")) != tr or any(abs(t - c[0]) < MIN_GAP for c in chosen):
                continue
            if not tr:
                acc = [c[0] for c in chosen if c[1] in ("pop", "tick") and c[0] < t]
                dng = [c[0] for c in chosen if c[1] == "ding" and c[0] < t]
                if kind in ("pop", "tick") and acc and t - acc[-1] < ACCENT_GAP: continue
                if kind == "ding" and dng and t - dng[-1] < DING_GAP: continue
            chosen.append((t, kind)); chosen.sort()
    kept, used = [], {k: [] for k in BANK}                   # (time, recipe index)
    for t, kind in chosen:
        recent = {i for (tt, i) in used[kind] if t - tt < RECENT_S}
        prev = used[kind][-1][1] if used[kind] else None
        choices = [i for i in range(len(BANK[kind])) if i not in recent and i != prev] or \
                  [i for i in range(len(BANK[kind])) if i != prev]
        i = int(rng.choice(choices)); used[kind].append((t, i)); kept.append((t, kind, i))
    return kept


def main():
    ev = json.load(open(sys.argv[1])); src, out = sys.argv[2], sys.argv[3]
    level = float(sys.argv[sys.argv.index("--level") + 1]) if "--level" in sys.argv else -21.0
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else int(hashlib.md5(json.dumps(ev).encode()).hexdigest()[:8], 16)
    sr, v = wavfile.read(src); assert sr == SR, sr
    v = v.astype(np.float64) / (32768.0 if v.dtype == np.int16 else 1.0)
    mono = v if v.ndim == 1 else v.mean(1)
    w = int(0.4 * SR); rms = np.sqrt((mono[:len(mono) // w * w].reshape(-1, w) ** 2).mean(1))
    loud = rms[rms > np.percentile(rms, 40)]
    speech = float(np.median(loud)) if len(loud) else 0.0
    if speech < 1e-4:                                            # no voice at all (tutorials): level against a -20 dBFS speech reference
        speech = 10 ** (-20 / 20)
    track = np.zeros(len(mono)); rng = np.random.default_rng(seed + 1)
    hits = plan(ev, seed); names = []
    for t, kind, i in hits:
        p, L = rng.uniform(0.9, 1.1), rng.uniform(0.8, 1.2)
        s = BANK[kind][i](rng, p, L).astype(np.float64)
        s = s / np.sqrt(np.mean(s[np.abs(s) > 1e-4] ** 2) + 1e-12) * speech * 10 ** ((level + rng.uniform(-1.5, 1.5)) / 20)
        st = int((t - (len(s) / SR if kind == "swell" else 0)) * SR)          # a swell rises INTO the event
        a, b = max(0, st), min(len(track), st + len(s))
        if b > a:
            track[a:b] += s[a - st:b - st]
        names.append(f"{t:.1f}s {kind}:{BANK[kind][i].__name__}")
    lim = 10 ** (-1.8 / 20)
    for _ in range(8):                                           # turn down only the effects if they push peaks up
        mix = (v + track[:, None]) if v.ndim == 2 else v + track
        if np.max(np.abs(mix)) <= max(lim, np.max(np.abs(v))):
            break
        track *= 0.8
    peak = np.max(np.abs(mix))
    if peak > lim:
        mix *= lim / peak
    wavfile.write(out, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    print(f"sfx: {len(hits)} of {len(ev)} events kept, ~{level:.0f} dB under speech, recipes: " + ", ".join(names))


if __name__ == "__main__":
    main()
