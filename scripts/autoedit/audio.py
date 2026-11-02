"""Audio measurements for the automatic edit, numpy only (the app's .venv has no scipy).

Ported from voice/tools/audio_tools.py, reworked to run on a stored array of frame
levels (`fdb`: dBFS per 10 ms frame), so reel.takes can place cuts from a clip's cached
analysis without decoding the audio again:

    fdb frame i covers [i*HOP, i*HOP + WIN) seconds; its centre is i*HOP + WIN/2.

Everything takes 16 kHz mono float32 (what faster_whisper decodes to).
"""
from __future__ import annotations

import numpy as np

SR = 16000
HOP = 0.010
WIN = 0.020


def load(path) -> np.ndarray:
    """Any audio/video file -> 16 kHz mono float32 (PyAV via faster_whisper)."""
    from faster_whisper.audio import decode_audio
    return np.asarray(decode_audio(str(path), sampling_rate=SR), dtype=np.float32)


def frame_db(wav, sr: int = SR, win: float = WIN, hop: float = HOP) -> np.ndarray:
    """RMS level per frame in dBFS, floor -120."""
    x = np.asarray(wav, dtype=np.float64).ravel()
    n, h = max(1, int(round(win * sr))), max(1, int(round(hop * sr)))
    if x.size == 0:
        return np.zeros(0)
    if x.size < n:
        power = np.array([np.mean(x * x)])
    else:
        cs = np.concatenate(([0.0], np.cumsum(x * x)))
        starts = np.arange(1 + (x.size - n) // h) * h
        power = (cs[starts + n] - cs[starts]) / n
    return 10.0 * np.log10(np.maximum(power, 1e-12))


def noise_floor(db) -> float:
    """The level of the quiet between words: min(10th percentile, -48 dB), ignoring
    frames of exact digital silence (a clip of nothing but zeros gives -120)."""
    db = np.asarray(db, dtype=np.float64).ravel()
    if db.size == 0:
        return -120.0
    live = db[db > -119.9]
    return float(min(np.percentile(live if live.size else db, 10), -48.0))


def speech_map(wav, sr: int = SR, hop: float = 0.1, p90_drop: float = 12.0,
               lo: float = -38.0, hi: float = -28.0, gap: float = 10.0) -> dict:
    """RMS dB per `hop` (the reference edit's speech map) with thresholds adapted to the clip:
    speech = clamp(p90 - p90_drop, lo, hi), pause = speech - gap. On the reference iPhone clips
    this lands on the hand-picked -32 / -42."""
    x = np.asarray(wav, dtype=np.float64).ravel()
    n = max(1, int(round(hop * sr)))
    if x.size == 0:
        return {"hop": hop, "db": [], "speech": hi, "pause": hi - gap}
    pad = (-x.size) % n
    frames = np.pad(x, (0, pad)).reshape(-1, n)
    db = 20.0 * np.log10(np.sqrt(np.mean(frames * frames, axis=1)) + 1e-9)
    live = db[db > -100]
    p90 = float(np.percentile(live, 90)) if live.size else -60.0
    speech = float(min(max(p90 - p90_drop, lo), hi))
    return {"hop": hop, "db": [round(float(v), 1) for v in db],
            "speech": round(speech, 1), "pause": round(speech - gap, 1)}


def vad_regions(wav, sr: int = SR, threshold: float = 0.45, min_silence: float = 0.30,
                min_speech: float = 0.06) -> list:
    """Silero speech regions [(start, end), ...] in seconds, no padding."""
    from faster_whisper.vad import VadOptions, get_speech_timestamps

    audio = np.asarray(wav, dtype=np.float32).ravel()
    if sr != SR:
        raise ValueError("vad_regions wants 16 kHz audio")
    if audio.size == 0:
        return []
    opts = VadOptions(threshold=threshold, neg_threshold=max(threshold - 0.15, 0.01),
                      min_speech_duration_ms=int(round(min_speech * 1000)),
                      min_silence_duration_ms=int(round(min_silence * 1000)),
                      speech_pad_ms=0)
    # silence after the clip closes speech that reaches the end where Silero hears it stop
    pad = np.zeros(int(round((min_silence + 0.1) * SR)) + 512, np.float32)
    dur = audio.size / SR
    out = []
    for ts in get_speech_timestamps(np.concatenate([audio, pad]), opts):
        s, e = min(ts["start"] / SR, dur), min(ts["end"] / SR, dur)
        if e - s > min_speech:
            out.append((round(s, 3), round(e, 3)))
    return out


def _idx(db, t: float, hop: float = HOP, win: float = WIN) -> int:
    """The frame centred nearest time t."""
    i = int(round((t - win / 2) / hop))
    return min(max(i, 0), len(db) - 1)


def db_at(db, t: float, hop: float = HOP, win: float = WIN) -> float:
    db = np.asarray(db)
    return float(db[_idx(db, t, hop, win)]) if db.size else -120.0


def loud_run_edge(db, t: float, thr: float, outward: int, hop: float = HOP,
                  win: float = WIN) -> float:
    """How far a run of frames above thr reaches outward from time t (-1 back from a
    speech start, +1 forward from a speech end). The run must touch t. Returns t when
    the frame at t is already quiet, else the outer window edge of the last loud frame."""
    db = np.asarray(db)
    if db.size == 0:
        return t
    i = _idx(db, t, hop, win)
    if db[i] <= thr:
        return t
    while 0 <= i + outward < db.size and db[i + outward] > thr:
        i += outward
    return i * hop if outward < 0 else i * hop + win


def onset(db, start: float, end: float | None = None, floor_db: float | None = None,
          onset_db: float = 12.0, below: float = 20.0, dip: float = 0.12,
          reach: float = 0.40, hop: float = HOP) -> float:
    """Where the first word's sound begins: `start` (Silero / Whisper), or earlier.

    Silero starts «Stop.» at the vowel; the «s» comes before it. From start, frames
    louder than both floor + onset_db and the speech's own level - below are followed
    back across quiet stretches up to `dip` long, at most `reach`."""
    db = np.asarray(db, dtype=np.float64)
    start = float(start)
    if not db.size:
        return start
    stop = start + 1.0 if end is None else min(float(end), start + 1.0)
    a = min(int(start / hop), db.size - 1)
    word = db[a:max(int(stop / hop), a + 1)]
    thr = max((noise_floor(db) if floor_db is None else floor_db) + onset_db,
              float(np.percentile(word, 90)) - below)
    found, quiet = start, 0.0
    k = min(int(start / hop), db.size) - 1
    while k >= 0 and k * hop >= start - reach:
        if db[k] > thr:
            found, quiet = k * hop, 0.0
        else:
            quiet += hop
            if quiet > dip:
                break
        k -= 1
    return min(found, start)


def quietest(db, t: float, radius: float = 0.05, hop: float = HOP, win: float = WIN) -> float:
    """The centre of the quietest frame within ±radius of t (where a cut clicks least)."""
    db = np.asarray(db)
    if db.size == 0:
        return t
    a = _idx(db, t - radius, hop, win)
    b = _idx(db, t + radius, hop, win)
    if b < a:
        return t
    i = a + int(np.argmin(db[a:b + 1]))
    return round(i * hop + win / 2, 3)


def loud_share(db, a: float, b: float, thr: float, hop: float = HOP, win: float = WIN) -> float:
    """Share of frames in [a, b] above thr (0..1)."""
    db = np.asarray(db)
    if db.size == 0 or b <= a:
        return 0.0
    i, j = _idx(db, a, hop, win), _idx(db, b, hop, win)
    seg = db[i:j + 1]
    return float(np.mean(seg > thr)) if seg.size else 0.0


def to_list(db, nd: int = 1) -> list:
    """A frame array for JSON (rounded)."""
    return [round(float(v), nd) for v in np.asarray(db).ravel()]
