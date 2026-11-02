"""Thresholds of the automatic edit (tuned on hand-edited reference Reels). Times in seconds."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common as C

SPEECH_DIR = C.DATA / "cache" / "speech"

EDIT: dict = {
    "talk_speech_ratio": 0.30,       # a clip is a talking clip above this share of speech (Silero)
    "talk_speech_min": 2.0,          # and at least this much speech
    "talk_min_words": 5,             # confirmed after pass 1
    "talk_min_p": 0.45,              # mean word probability
    # speech map (RMS dB per 0.1 s): speech = clamp(p90 - 12, -38, -28), pause = speech - 10
    "map_hop": 0.1,
    "map_p90_drop": 12.0,
    "map_speech_lo": -38.0,
    "map_speech_hi": -28.0,
    "map_pause_gap": 10.0,
    # utterance windows
    "vad_threshold": 0.45,
    "vad_min_silence": 0.30,
    "window_merge_gap": 0.45,
    "window_max": 20.0,
    "window_min": 0.6,
    "window_context": 1.0,
    # Whisper red flags
    "long_word": 1.0,                # a word this long over continuous speech = skipped words
    "long_word_speech": 0.6,         # share of speech frames beyond 0.6 s that makes it suspicious
    "long_retries": 2,
    "max_words_per_sec": 5.5,
    "echo_max": 0.25,                # phantom echo: shorter than this and repeats the previous word
    "echo_gap": 0.05,                # ...and starts at most this long after it
    # sentence units and groups
    "restart_gap": 0.6,              # a pause this long before a capital letter starts a new unit
    "align_min": 0.45,               # unit vs script sentence
    "prefix_min": 0.8,
    "pseudo_min": 0.6,               # unit vs earlier unit, no script
    "contain_min": 0.85,
    "script_f1": 0.5,                # a stored script matches what was said
    "false_start_words": 3,
    # scoring
    "tie": 0.03,                     # within this, the later take wins
    "ask_conf": 0.60,                # below this a decision may become a question
    "ask_min_seconds": 1.0,
    "max_questions": 3,
    "repeat_keep_gap": 0.6,          # identical sentences closer than this are a rhetorical repeat
    "repeat_ask_gap": 2.0,
    # pieces
    "merge_gap": 1.5,
    "pad_before": 0.10,
    "pad_after": 0.25,
    "pad_after_max": 0.50,
    "pause_cut": 0.9,                # pauses longer than this inside a piece are cut (tighten.py then goes further)
    "pause_keep_after": 0.25,
    "pause_keep_before": 0.15,
    "breath_max": 0.35,
    "piece_min": 0.6,
    "title_secs": 7.0,
}
