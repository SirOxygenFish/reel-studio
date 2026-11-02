"""Retakes, false starts and pauses: which of his attempts at each sentence the reel
keeps, and exactly where each kept piece of a clip starts and ends.

He films himself saying the text, usually several times per clip: a clean take, an
aborted «Bo jedyna…», a restart, a long pause while he remembers the next line. A hand
editor keeps the LAST complete clean take of every sentence, in the order of the text,
and cuts the pauses. This module does the same from what speech.py measured
(ClipSpeech dicts): no model and no audio decoding, so every decision is testable and
every threshold lives in config.EDIT.

    build_units    utterances -> sentence units (one attempt at one sentence each)
    build_groups   units -> groups (all attempts at one sentence). ONE aligner: against
                   the script's sentences, or, without a script, against the sentences
                   heard so far (so a later redo returns to where it was first said)
    score          per attempt: complete / fluency / asr / script -> default + confidence
    questions      the few genuinely hard choices, in Russian, for the speaker
    choose         his answers applied -> the chosen attempts, in text order
    to_pieces      chosen attempts -> clip pieces in source seconds: pads, pause cuts,
                   joints; each becomes a talk segment
    analyze        all of the above plus a readable log of what was dropped and why

Units, groups and the selection are plain JSON-able dicts, so a draft waiting for his
answers can be stored and resumed with choose() + to_pieces(). build_groups may split
or join units (a Whisper sentence that holds two script sentences, or one sentence
Whisper broke at a pause); the new units are appended to the list it was given and the
old ones marked "gone".

Pure: no Flask, no Whisper, no files.
"""
from __future__ import annotations

import itertools
import math
import re
from collections import Counter

import numpy as np

from . import audio as A
from . import config
from . import words as W

# ----------------------------------------------------------------- constants
# Token alignment (Smith-Waterman): two tokens match when W.tok_sim >= _TOK_MATCH, so
# «statycznie» meets «statystycznie» and «sto» meets «100».
_TOK_MATCH = 0.8
_SHORT_TOKEN = 4                       # tokens this short must match exactly (or by value)
_SHORT_SENTENCE = 3                    # sentences this short are retakes only nearby
_SW_MATCH, _SW_MISS, _SW_GAP = 2, -1, -1
# Coverage walks over a few words he inserted and took back («pięć milionów listów, nie,
# maili» against «pięć milionów maili»): with the full gap cost the match would stop there.
_SW_COVER_GAP = -0.5
# An unfinished unit Whisper could hardly read is mumbling from an aborted attempt
# («Jeśli tym idziesz, więc czytasz…» where he said «I siedem…»: mean p 0.53, one word at
# 0.12, in a clip whose words are 0.97 on the median). All of these must hold: a real
# sentence trailing off in a noisy spot keeps its words, the question is Whisper's doubt.
# (Candidates for config.EDIT.)
_GARBLE_P = 0.7                        # mean word p under this
_GARBLE_DROP = 0.25                    # ...and this far under the clip's median word p
_GARBLE_MIN_P = 0.35                   # ...with a word Whisper was this unsure about
_GARBLE_SECS = 2.0                     # ...and no longer than an aborted start
# A unit that ends without . ? ! still ends its sentence when he stops this long after it.
_END_GAP = 0.35
# Two attempts this similar say the same words; script sentences this similar are copies
# of an intentional repeat.
_SAME_WORDING = 0.85
_COPY_SIM = 0.85
# A unit is placed on a script sentence only when at least this share of its tokens
# matched there (an ad-lib sharing «sto prób» with a sentence is not a take of it).
_PRECISION = 0.5
# Confidence floors (see score()).
_CONF_FRAGMENT, _CONF_SCRIPT, _CONF_SAME = 0.9, 0.8, 0.75
_CONF_REPEAT_KEEP, _CONF_REPEAT_ASK, _CONF_REPEAT_CLIPS, _CONF_COPIES = 0.7, 0.5, 0.85, 0.85
_SCRIPT_GAP = 0.10                     # this much closer to the script = a clear winner
_CONTINUITY_Q = 0.05                   # a take next to its neighbours may cost this much q
_CONTINUITY_CONF = 0.9                 # ...and only decisions below this confidence move
_W_SCRIPT = (0.35, 0.25, 0.10, 0.30)   # q weights: complete, fluency, asr, script
_W_PLAIN = (0.45, 0.35, 0.20)          # q weights without a script sentence
_COMPLETE_COV, _PARTIAL_COV = 0.85, 0.6   # coverage for complete 1 / 0.5
_ASR_LO, _ASR_SPAN = 0.5, 0.45         # asr = (mean p - lo) / span, clamped to 0..1
_PEN = {"fillers": 0.25, "restarts": 0.35, "long": 0.30, "abandoned": 0.10}
# Words an attempt says beyond another attempt at the same sentence, inside the part they
# share: a little per word (a rephrase, which may be the better wording), a restart's
# worth when a correction word among them shows he took something back («listów, nie,
# maili», «na swój, znaczy na nasz»). The correction word counts next to a comma, the way
# Whisper writes a correction, so a plain «nie» of the sentence is not one.
_PEN_EXTRA, _PEN_EXTRA_MAX, _PEN_CORRECTION = 0.05, 0.2, 0.35
_CORRECTION = {
    "pl": {"nie", "znaczy", "czyli", "właściwie", "raczej", "przepraszam", "sorry", "sory",
           "wróć"},
    "ru": {"нет", "точнее", "вернее", "значит", "извините", "простите", "прости"},
    "uk": {"ні", "точніше", "вірніше", "тобто", "вибачте", "пробачте"},
    "en": {"no", "sorry", "actually", "rather", "mean", "wait", "correction"},
    "de": {"nein", "sorry", "entschuldigung", "also", "besser", "gemeint"},
    "es": {"no", "perdón", "digo", "mejor", "espera"},
    "fr": {"non", "pardon", "désolé", "enfin", "plutôt"},
    "it": {"no", "scusa", "scusate", "anzi", "cioè"},
    "pt": {"não", "desculpa", "desculpe", "aliás", "melhor"},
}
# «yyy» with no word: a speech stretch this long inside a word gap this long (edges off,
# since Whisper's word ends are loose)
_FILL_GAP, _FILL_RUN, _FILL_EDGE = 0.3, 0.15, 0.08
# Piece edges. A Silero start this close to Whisper's is where the word really starts
# (Whisper glues a word to the silence before it); it moves forward only over quiet.
_REGION_BACK, _REGION_AHEAD, _REGION_QUIET = 0.2, 0.6, 0.25
# Pass-1 Whisper can glue up to a second of silence to a word («Ostatnio» 0.80 s): a word
# whose first this-long is quiet starts at its first loud frame instead.
_LEAD_QUIET = 0.25
_MIN_WORD = 0.05                       # a word Whisper gave no length gets this on screen
_EDGE_DB = 8.0                        # loud = floor + this (word ends, tails)...
_EDGE_BELOW_PAUSE = 12.0               # ...and at least the pause level - this
_QUIET_DB = 10.0                       # "quiet" = below floor + this when there is no pause level
_TAIL_EXTRA = 0.04                     # past the last loud frame of the last word
_BREATH_DB = 6.0                       # a breath = floor + this, touching the next word...
_BREATH_BELOW_PAUSE = 8.0              # ...and at least the pause level - this
_SNAP, _SNAP_GAIN = 0.05, 1.0          # snap a cut to a quieter frame this close, if this much quieter
_OTHER_PAD = 0.05                      # never closer than this to speech not in the piece
_MIN_CUT = 0.1                         # a pause cut shorter than this is not worth a jump
_PLAY_PAD = (0.10, 0.25)               # around a take played in a question
_QUOTE_MAX = 90
_FALSE_START_LOOKAHEAD = 8             # a false start is redone within this many units

_ASK_TEXT = {
    "take": "Two good takes of the same line. Which one stays?",
    "repeat": "The line was said twice in a row. Keep both?",
}
_AUTO = {"id": "auto", "label": "You decide"}
_WHY = {
    "meta": "spoken note to self",
    "false_start": "false start",
    "filler": "filler, no words",
    "fragment": "broken-off line",
    "take": "extra take",
    "broken": "broken take",
    "repeat": "repeated line",
}

# A unit ending on a connecting word was cut off («…czego chcemy, to»). The first set
# ends a sentence only as a question («A?», «No i?»); the second can end one outright
# («Nie wiem jak.», «Jestem za.», «Która?», «Ну и что.»), so it counts only when Whisper
# put no full stop after it.
_CONNECT = {
    "pl": {"i", "a", "że", "bo", "w", "we", "z", "ze", "na", "do", "o", "od", "dla",
           "przez", "przy", "u", "oraz", "lub", "ani", "żeby", "aby"},
    "ru": {"и", "а", "но", "в", "во", "на", "с", "со", "к", "ко", "о", "об", "из", "от",
           "до", "для", "чтобы"},
    "uk": {"і", "й", "та", "а", "але", "в", "у", "на", "з", "із", "до", "від", "для", "щоб"},
    "en": {"and", "the", "a", "an", "of", "to", "with", "for", "from", "in", "on", "at", "by", "because"},
    "de": {"und", "der", "die", "das", "ein", "eine", "mit", "für", "von", "zu", "im", "am", "weil"},
    "es": {"y", "el", "la", "los", "las", "un", "una", "de", "con", "para", "en", "por", "porque"},
    "fr": {"et", "le", "la", "les", "un", "une", "de", "du", "avec", "pour", "dans", "sur", "parce"},
    "it": {"e", "il", "lo", "la", "i", "gli", "le", "un", "una", "di", "con", "per", "in", "su", "perché"},
    "pt": {"e", "o", "a", "os", "as", "um", "uma", "de", "com", "para", "em", "por", "porque"},
}
_CONNECT_OPEN = {
    "pl": {"to", "ale", "po", "czy", "albo", "jak", "jeśli", "jeżeli", "gdy", "kiedy", "niż",
           "za", "który", "która", "które", "którzy", "których", "którą", "którym",
           "której"},
    "ru": {"что", "это", "как", "когда", "если", "или", "чем", "по", "за", "который",
           "которая", "которое", "которые", "которых", "которой", "которую"},
    "uk": {"що", "це", "як", "коли", "якщо", "або", "чим", "по", "за", "який", "яка", "яке", "які"},
    "en": {"that", "which", "who", "if", "when", "or", "but", "than", "so", "as", "about", "like"},
    "de": {"dass", "wenn", "oder", "aber", "als", "wie", "welche", "welcher"},
    "es": {"que", "si", "cuando", "o", "pero", "como", "cual"},
    "fr": {"que", "qui", "si", "quand", "ou", "mais", "comme"},
    "it": {"che", "se", "quando", "o", "ma", "come"},
    "pt": {"que", "se", "quando", "ou", "mas", "como"},
}
_META = (("jeszcze", "raz"), ("od", "nowa"), ("przepraszam",), ("sorry",), ("sory",),
         ("stop",), ("еще", "раз"), ("заново",), ("стоп",), ("блин",),
         ("one", "more", "time"), ("start", "over"), ("take", "two"), ("scratch", "that"), ("let", "me", "redo"),
         ("let", "me", "start"), ("noch", "mal"), ("nochmal",), ("otra", "vez"), ("de", "nuevo"), ("ще", "раз"))
# What goes with a retake request and says nothing itself: «Nie, jeszcze raz.», «Dobra,
# stop.», «Ну, блин, ещё раз.» are requests whatever follows; «Spróbuj jeszcze raz.» has a
# word of its own and is a request only when he then starts something again.
_META_WITH = {
    "pl": {"nie", "dobra", "dobrze", "okej", "ok", "okay", "no", "tak", "to", "jeszcze",
           "raz", "od", "nowa", "początku", "sorki", "sorry", "sory", "przepraszam", "stop",
           "kurczę", "kurde", "ej", "oj", "boże", "jezu"},
    "ru": {"нет", "ну", "так", "давай", "ладно", "еще", "раз", "все", "короче", "окей",
           "ой", "блин", "стоп", "заново", "сначала", "извините", "простите", "это"},
    "uk": {"ні", "ну", "так", "давай", "добре", "ще", "раз", "все", "стоп", "вибачте", "це"},
    "en": {"no", "okay", "ok", "so", "yeah", "yes", "right", "um", "uh", "sorry", "stop", "again", "one", "more", "time",
           "let", "me", "start", "over", "oh", "god", "damn", "that", "scratch", "take", "two", "wait"},
    "de": {"nein", "okay", "ok", "also", "ja", "noch", "mal", "nochmal", "sorry", "stop"},
    "es": {"no", "vale", "ok", "bueno", "otra", "vez", "de", "nuevo", "perdón", "para"},
}

_CLOSE = "\"'»”“)\\]"
_END = re.compile(r"[.!?…]+[" + _CLOSE + r"]*$")
_TRAIL = re.compile(r"(?:…|\.\.\.?|[-\u2013\u2014])[" + _CLOSE + r"]*$")   # «to-», «to…»
_SPLIT_CHARS = re.compile(r"[:\"„”“«»/]+")
_FILLER = re.compile(r"^(?:y+|e+|e+m+|e+r+m*|e+h+m*|m{2,}|h+m+|m+h+m+|u+m+|u+h+|a+h+|"
                     r"э+|э+м+|м{2,}|х+м+|м+г+м+)$")
_SCRIPT_SPLIT = re.compile(r"([.!?…]+[" + _CLOSE + r"]*)(?=\s|$)")


def _E() -> dict:
    """Read at call time, so a test or a bench can override one threshold."""
    return config.EDIT


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if x < lo else hi if x > hi else x


def _num(x, default: float | None = None) -> float | None:
    """A finite number, else `default` (ClipSpeech comes from a cache file: never trust it
    to crash-proof the edit)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return default
    x = float(x)
    return x if math.isfinite(x) else default


def _arr(x) -> np.ndarray:
    try:
        a = np.asarray(x if x is not None else [], dtype=np.float64).ravel()
    except (TypeError, ValueError):
        return np.zeros(0)
    return np.where(np.isfinite(a), a, -100.0) if a.size else a


_NUMS = re.compile(r"(\d+)")


def _natural(name: str) -> list:
    """File name with its numbers read as numbers: IMG_998 before a test clip."""
    return [int(p) if p.isdigit() else p.lower() for p in _NUMS.split(str(name))]


def _clip_order(clips: dict) -> list:
    """(name, ClipSpeech) in the order he recorded them. That order decides which take is
    the later one and where a redo goes, so it must not depend on how the caller built the
    dict: by "recorded" (seconds, when every clip has one), else by file name with numbers
    read as numbers, the way a phone names its recordings (a test clip before a test clip)."""
    items = [(n, cs) for n, cs in (clips or {}).items() if isinstance(cs, dict)]
    if items and all(_num(cs.get("recorded")) is not None for _, cs in items):
        return sorted(items, key=lambda x: (_num(x[1]["recorded"]), _natural(x[0])))
    return sorted(items, key=lambda x: _natural(x[0]))


# ----------------------------------------------------------------- tokens
_SIM: dict = {}


def _eq(a: str, b: str) -> bool:
    """Tokens match (cached: the aligner asks about the same pairs many times). Short
    words must be the same word or the same number: «tak» is not «taka»."""
    if a == b:
        return True
    key = (a, b) if a < b else (b, a)
    v = _SIM.get(key)
    if v is None:
        if len(_SIM) > 300_000:
            _SIM.clear()
        need = 1.0 - 1e-9 if min(len(a), len(b)) <= _SHORT_TOKEN else _TOK_MATCH
        v = _SIM[key] = W.tok_sim(a, b) >= need
    return v


def _is_filler(text: str) -> bool:
    t = W.norm_token(text)
    return bool(t) and bool(_FILLER.match(t))


def _word_tokens(text: str, lang: str) -> list:
    """One Whisper word -> comparison tokens: quotes split off, digits read as Polish words
    («1,46%» -> jeden przecinek czterdzieści sześć procent) so they meet the script."""
    t = _SPLIT_CHARS.sub(" ", str(text or ""))
    if lang != "ru" and re.search(r"\d", t):
        try:
            t = W._pl().normalize(t)
        except Exception:  # noqa: BLE001 - the number reader is a help, never a blocker
            pass
    return [x for x in W.tokens(t) if not _FILLER.match(x)]


def _text_tokens(text: str, lang: str) -> list:
    out = []
    for w in str(text or "").split():
        out += _word_tokens(w, lang)
    return out


def _capital(text: str) -> bool:
    m = re.search(r"[^\W\d_]", str(text or ""))
    return bool(m) and m.group(0).isupper()


def _restarts(toks: list) -> int:
    """Immediate repeats of 2 to 4 tokens («bo jedyna bo jedyna rzecz»): he restarted."""
    n, i = 0, 0
    while i < len(toks):
        hit = 0
        for size in (4, 3, 2):
            if i + 2 * size <= len(toks) and toks[i:i + size] == toks[i + size:i + 2 * size]:
                hit = size
                break
        if hit:
            n += 1
            i += hit
        else:
            i += 1
    return n


# ----------------------------------------------------------------- alignment
def _sw(a: list, b: list, gap: float = _SW_GAP) -> dict:
    """Smith-Waterman local alignment of two token lists (match +2, mismatch -1, gap -1).

    Returns score, matched pairs and the aligned ranges: a[ua:ub] against b[ra:rb]."""
    n, m = len(a), len(b)
    empty = {"score": 0, "m": 0, "ua": 0, "ub": 0, "ra": 0, "rb": 0, "pairs": []}
    if not n or not m:
        return empty
    H = [[0] * (m + 1) for _ in range(n + 1)]
    best, bi, bj = 0, 0, 0
    for i in range(1, n + 1):
        ai, row, up = a[i - 1], H[i], H[i - 1]
        for j in range(1, m + 1):
            v = up[j - 1] + (_SW_MATCH if _eq(ai, b[j - 1]) else _SW_MISS)
            if up[j] + gap > v:
                v = up[j] + gap
            if row[j - 1] + gap > v:
                v = row[j - 1] + gap
            if v < 0:
                v = 0
            row[j] = v
            if v > best:
                best, bi, bj = v, i, j
    if best <= 0:
        return empty
    pairs, i, j = [], bi, bj
    while i > 0 and j > 0 and H[i][j] > 0:
        h, eq = H[i][j], _eq(a[i - 1], b[j - 1])
        if h == H[i - 1][j - 1] + (_SW_MATCH if eq else _SW_MISS):
            if eq:
                pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif h == H[i - 1][j] + gap:
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    if not pairs:
        return empty
    return {"score": best, "m": len(pairs), "ua": pairs[0][0], "ub": pairs[-1][0] + 1,
            "ra": pairs[0][1], "rb": pairs[-1][1] + 1, "pairs": pairs}


def _lcs(a: list, b: list) -> tuple:
    """Fuzzy longest common subsequence: (length, matched index pairs)."""
    n, m = len(a), len(b)
    if not n or not m:
        return 0, []
    L = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        ai, row, nxt = a[i], L[i], L[i + 1]
        for j in range(m):
            nxt[j + 1] = row[j] + 1 if _eq(ai, b[j]) else max(row[j + 1], nxt[j])
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        if _eq(a[i - 1], b[j - 1]) and L[i][j] == L[i - 1][j - 1] + 1:
            pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif L[i - 1][j] >= L[i][j - 1]:
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return L[n][m], pairs


def _f1(a: list, b: list) -> float:
    if not a or not b:
        return 0.0
    return 2.0 * _lcs(a, b)[0] / (len(a) + len(b))


def _prefix(a: list, b: list) -> float:
    """How much of A is the start of B (A shorter than B)."""
    if not a or len(a) > len(b):
        return 0.0
    return sum(1 for x, y in zip(a, b) if _eq(x, y)) / len(a)


def _align_all(T: list, refs: list, expected: int | None = None) -> list:
    """T's local alignment with every reference, best first: (score, region F1, nearness
    to where the text should be next)."""
    out = []
    for k, R in enumerate(refs):
        if not R:
            continue
        sw = _sw(T, R)
        if not sw["m"]:
            continue
        region = T[sw["ua"]:sw["ub"]]
        sw.update(k=k, f1=2.0 * _lcs(region, R)[0] / (len(region) + len(R)),
                  prec=sw["m"] / len(T))
        out.append(sw)
    near = (lambda r: -abs(r["k"] - expected)) if expected is not None else (lambda r: 0)
    out.sort(key=lambda r: (r["score"], round(r["f1"], 6), near(r)), reverse=True)
    return out


# ----------------------------------------------------------------- units
def _w(w) -> list | None:
    """A word as [s, e, text, p], or None when it is not one. A missing or non-finite p
    reads as 1.0 (no doubt we can measure); a zero-length word stays (it was said)."""
    try:
        s, e, t = float(w[0]), float(w[1]), str(w[2]).strip()
    except (TypeError, ValueError, IndexError, KeyError):
        return None
    if not t or not math.isfinite(s) or not math.isfinite(e) or e < s:
        return None
    p = _num(w[3], 1.0) if len(w) > 3 else 1.0
    return [round(s, 3), round(e, 3), t, round(_clamp(p), 3)]


def _utt_start(u: dict) -> float:
    s = _num(u.get("s"))
    if s is not None:
        return s
    ws = [w for w in (_w(x) for x in u.get("words") or []) if w]
    return min(w[0] for w in ws) if ws else 0.0


def _utterances(cs: dict) -> list:
    """The clip's utterances in time order; the plain word list when there are none."""
    utts = [u for u in cs.get("utterances") or []
            if isinstance(u, dict) and isinstance(u.get("words"), list) and u["words"]]
    if utts:
        return sorted(utts, key=_utt_start)
    ws = cs.get("words") or cs.get("pass1") or []
    return [{"words": ws, "unresolved_long": []}] if isinstance(ws, list) and ws else []


def _clip_words(cs: dict) -> list:
    out = []
    for u in _utterances(cs):
        out += [w for w in (_w(x) for x in u.get("words") or []) if w]
    out.sort(key=lambda w: w[0])
    return out


def _gap_speech(fdb: np.ndarray, a: float, b: float, level: float) -> int:
    """Speech with no word between two words («yyy» Whisper did not write): the number
    of runs of frames above speech level at least _FILL_RUN long."""
    if fdb.size == 0 or b - a < _FILL_GAP:
        return 0
    i0 = max(0, int(np.ceil((a + _FILL_EDGE) / A.HOP)))
    i1 = min(fdb.size, int((b - _FILL_EDGE - A.WIN) / A.HOP) + 1)
    if i1 <= i0:
        return 0
    loud = fdb[i0:i1] > level
    runs, cur = 0, 0
    for x in loud:
        cur = cur + 1 if x else 0
        if cur * A.HOP >= _FILL_RUN and cur * A.HOP - A.HOP < _FILL_RUN:
            runs += 1
    return runs


def _sentence_parts(ws: list, gap: float):
    """Split at . ? ! … and before a capital after a pause of at least `gap`."""
    cur = []
    for w in ws:
        if cur and w[0] - cur[-1][1] >= gap and _capital(w[2]):
            yield cur
            cur = []
        cur.append(w)
        if _END.search(w[2]) or _TRAIL.search(w[2]):
            yield cur
            cur = []
    if cur:
        yield cur


def _find_metas(toks: list):
    """Every retake marker in a word list: (word index, words in it, phrase)."""
    for i in range(len(toks)):
        for ph in _META:
            if tuple(toks[i:i + len(ph)]) == ph:
                yield i, len(ph), " ".join(ph)
                break


def _plain(words: list, lang: str) -> list:
    """Comparison tokens of some words, fillers out."""
    out = []
    for w in words:
        if not _is_filler(w[2]):
            out += _word_tokens(w[2], lang)
    return out


def _has_content(toks: list, lang: str) -> bool:
    """Something besides the «nie», «dobra», «jeszcze» that go with a retake request."""
    comp = _META_WITH.get(lang, _META_WITH["en"])
    return any(t not in comp for t in toks)


def _restart_at(X, Y, phrase: str, lang: str) -> int | None:
    """Where in Y the words X (said after Y) start Y again, as a token index of Y, or
    None: at 0 when X has Y's first two words («Bo jedyna…», then «Bo jedyna rzecz…»; a
    one-word Y needs that word), near Y's end when X picks up two of the words where Y
    broke off («…która nas, sorry, która nas dzieli»). An X that says the marker again is
    the same sentence twice («Spróbuj jeszcze raz. Spróbuj jeszcze raz.»), not a retake."""
    if not X or not Y:
        return None
    ph = phrase.split()
    if any(X[i:i + len(ph)] == ph for i in range(len(X))):
        return None
    comp = _META_WITH.get(lang, _META_WITH["en"])
    X = list(itertools.dropwhile(lambda t: t in comp, X))
    lead = len(Y) - len(list(itertools.dropwhile(lambda t: t in comp, Y)))
    Y = Y[lead:]
    if not X or not Y:
        return None
    if len(Y) == 1:
        return 0 if _eq(X[0], Y[0]) else None
    if len(X) < 2:
        return None
    for i in [0] + list(range(max(1, len(Y) - 3), len(Y) - 1)):
        if _eq(X[0], Y[i]) and _eq(X[1], Y[i + 1]):
            return lead + i if i else 0
    return None


def _redoes(X, Y, phrase: str, lang: str) -> bool:
    return _restart_at(X, Y, phrase, lang) is not None


def _word_at(words: list, lang: str, tok: int) -> int:
    """The index of the word that holds comparison token `tok` of _plain(words)."""
    n = 0
    for wi, w in enumerate(words):
        if _is_filler(w[2]):
            continue
        n += len(_word_tokens(w[2], lang))
        if n > tok:
            return wi
    return len(words)


def _meta_parts(words: list, lang: str = "pl", prev=None, nxt=None) -> list:
    """(words, meta phrase or "") parts. A marker («jeszcze raz», «od nowa», «stop»,
    «przepraszam»…) asks for a retake when it stands alone («Nie, jeszcze raz.») or when he
    really starts again around it: the words after it restart the words before it («…która,
    od nowa, bo jedyna rzecz…»); a marker at the head is followed by a restart of what he
    said just before (`prev`: «Przepraszam, bo jedyna…» after «Bo jedyna rzecz, która…»);
    a marker at the tail is followed by a restart of its sentence (`nxt`: «…która, stop.»
    then «Bo jedyna rzecz…»). Otherwise it is his text and stays whole: «Spróbuj jeszcze
    raz.», «Czasem trzeba sobie powiedzieć stop.», «Nie bój się zacząć od nowa, to
    normalne.». When he picks up where he broke off («Bo jedyna rzecz, która nas, sorry,
    która nas dzieli…»), the words he says again go out with the marker, so the sentence
    reads once. `prev` / `nxt` are the tokens of the sentences said around this one."""
    norm = [W.norm_token(w[2]) for w in words]
    for p, n_ph, phrase in _find_metas(norm):
        bw, mw, aw = words[:p], words[p:p + n_ph], words[p + n_ph:]
        B, X = _plain(bw, lang), _plain(aw, lang)
        b_has, a_has = _has_content(B, lang), _has_content(X, lang)
        if not b_has and not a_has:
            return [(words, phrase)]
        if b_has and a_has:
            at = _restart_at(X, B, phrase, lang)
            if at is not None:
                cut = _word_at(bw, lang, at) if at else len(bw)
                if cut <= 0:
                    cut = len(bw)
                return (_meta_parts(bw[:cut], lang, prev, X) + [(bw[cut:] + mw, phrase)]
                        + _meta_parts(aw, lang, B, nxt))
        elif a_has:
            if _redoes(X, prev, phrase, lang):
                return [(bw + mw, phrase)] + _meta_parts(aw, lang, prev, nxt)
        elif _redoes(nxt, B, phrase, lang) or _redoes(nxt, prev, phrase, lang):
            return _meta_parts(bw, lang, prev, nxt) + [(mw + aw, phrase)]
    return [(words, "")]


def _fill_unit(u: dict, words: list, fill_w: list, fill_g: list, longs: list) -> dict:
    """Everything a unit derives from its words (shared by new, split and joined units)."""
    lang = u.get("lang", "pl")
    toks, tw = [], []
    for wi, w in enumerate(words):
        if fill_w[wi]:
            continue
        for t in _word_tokens(w[2], lang):
            toks.append(t)
            tw.append(wi)
    s, e = words[0][0], words[-1][1]
    last = words[-1][2]
    terminal = bool(_END.search(last)) and not _TRAIL.search(last)
    asked = terminal and bool(re.search(r"[?!]", last))
    tok = W.norm_token(last)
    trail = bool(_TRAIL.search(last)) or \
        (tok in _CONNECT.get(lang, _CONNECT["en"]) and not asked) or \
        (not terminal and tok in _CONNECT_OPEN.get(lang, _CONNECT_OPEN["en"]))
    u.update({
        "s": round(s, 3), "e": round(e, 3), "words": words,
        "text": " ".join(w[2] for w in words), "tokens": toks, "tok_w": tw,
        "trail": trail, "terminal": terminal,
        "fillers": int(sum(fill_w) + sum(fill_g)), "fill_w": fill_w, "fill_g": fill_g,
        "restarts": _restarts(toks),
        "unresolved_long": [x for x in longs if x[1] > s and x[0] < e],
        "asr": round(float(np.mean([w[3] for w in words])), 3) if words else 0.0,
    })
    return u


def _longs(utt: dict) -> list:
    out = []
    for x in utt.get("unresolved_long") or []:
        try:
            s, e = float(x[0]), float(x[1])
        except (TypeError, ValueError, IndexError, KeyError):
            continue
        if math.isfinite(s) and math.isfinite(e):
            out.append([round(s, 3), round(e, 3), str(x[2]) if len(x) > 2 else ""])
    return out


def build_units(clips: dict) -> list:
    """Every clip's utterances -> sentence units, in time order: clips in the order he
    recorded them (see _clip_order), utterances and words by time inside each.

    Unit: {id, file, clip, utt, utt_end, lang, s, e, words, text, tokens, tok_w, trail,
    terminal, meta, meta_phrase, fillers, restarts, unresolved_long, asr, gap_after, src,
    drop}. `clip` is the clip's place in that order. `tokens` are the comparison tokens
    (fillers out, digits as words) and `tok_w` the word each token came from."""
    E = _E()
    # every sentence of every clip first: a retake marker is judged by what he says around it
    parts, sound = [], {}
    for ci, (name, cs) in enumerate(_clip_order(clips)):
        lang = str(cs.get("lang") or "pl")
        sound[ci] = (_arr(cs.get("fdb")), _num(cs.get("speech_db"), -32.0))
        for ui, utt in enumerate(_utterances(cs)):
            ws = sorted((w for w in (_w(x) for x in utt.get("words") or []) if w),
                        key=lambda w: w[0])
            longs = _longs(utt)
            for pi, part in enumerate(_sentence_parts(ws, E["restart_gap"])):
                parts.append({"ci": ci, "file": name, "ui": ui, "pi": pi, "lang": lang,
                              "words": part, "longs": longs})
    toks = [_plain(p["words"], p["lang"]) for p in parts]
    units, per_clip = [], {}
    for k, part in enumerate(parts):
        ci, lang = part["ci"], part["lang"]
        prev = toks[k - 1] if k and parts[k - 1]["ci"] >= ci - 1 else None
        nxt = toks[k + 1] if k + 1 < len(parts) and parts[k + 1]["ci"] <= ci + 1 else None
        fdb, level = sound[ci]
        for sub, phrase in _meta_parts(part["words"], lang, prev, nxt):
            if not sub:
                continue
            fill_w = [1 if _is_filler(w[2]) else 0 for w in sub]
            fill_g = [_gap_speech(fdb, a[1], b[0], level) for a, b in zip(sub, sub[1:])]
            u = {"id": "", "file": part["file"], "clip": ci, "utt": part["ui"],
                 "utt_end": part["ui"], "lang": lang, "meta": bool(phrase),
                 "meta_phrase": phrase, "gap_after": 99.0,
                 "src": f"{ci}.{part['ui']}.{part['pi']}", "drop": ""}
            u = _fill_unit(u, sub, fill_w, fill_g, part["longs"])
            units.append(u)
            per_clip.setdefault(ci, []).append(u)
    for mine in per_clip.values():
        for a, b in zip(mine, mine[1:]):
            a["gap_after"] = round(b["s"] - a["e"], 3)
    for i, u in enumerate(units, 1):
        u["id"] = f"u{i}"
    first = {}
    for u in units:                      # meta split-offs share the id of the first part
        u["src"] = first.setdefault(u["src"], u["id"])
    return units


def _tkey(u: dict) -> tuple:
    return (u["clip"], u["s"], u["e"])


def _derive(u: dict, i: int, j: int, uid: str) -> dict:
    """Words i..j of unit u as a unit of its own."""
    nu = {k: u[k] for k in ("file", "clip", "utt", "utt_end", "lang", "meta", "meta_phrase",
                           "src", "gap_after")}
    nu.update(id=uid, drop="")
    return _fill_unit(nu, u["words"][i:j], u["fill_w"][i:j], u["fill_g"][i:j - 1],
                      u["unresolved_long"])


def _split_unit(u: dict, tok_idx: int, units: list) -> tuple:
    """Cut unit u before token tok_idx (at a word boundary); the halves join `units`."""
    tw = u["tok_w"]
    if not 0 < tok_idx < len(tw):
        return None, None
    wi = tw[tok_idx]
    if tw[tok_idx - 1] == wi:            # never inside a word read as several tokens
        wi += 1
    n = len(u["words"])
    if not 0 < wi < n:
        return None, None
    a, b = _derive(u, 0, wi, u["id"] + "a"), _derive(u, wi, n, u["id"] + "b")
    if not a["tokens"] or not b["tokens"]:
        return None, None
    a["gap_after"] = round(b["s"] - a["e"], 3)
    a["split_end"] = True               # it ends where a sentence ends, comma or not
    b["split_end"] = u.get("split_end", False)
    u["gone"] = "split"
    units += [a, b]
    return a, b


def _join_units(p: dict, c: dict, units: list) -> dict:
    """Two consecutive units that are one attempt (Whisper broke it at a pause)."""
    nu = {k: p[k] for k in ("file", "clip", "utt", "lang", "src")}
    nu.update(id=f"{p['id']}+{c['id']}", utt_end=c["utt_end"], meta=False, meta_phrase="",
              gap_after=c["gap_after"], drop="", parts=[p["id"], c["id"]],
              split_end=c.get("split_end", False))
    _fill_unit(nu, p["words"] + c["words"], p["fill_w"] + c["fill_w"],
               p["fill_g"] + [0] + c["fill_g"], p["unresolved_long"] + c["unresolved_long"])
    p["gone"] = c["gone"] = "merged"
    units.append(nu)
    return nu


def _leaves(units: list) -> list:
    """The smallest units that exist (no split parents, no joined wholes)."""
    return [u for u in units if u.get("gone") != "split" and not u.get("parts")]


def _members(u: dict, by_id: dict) -> set:
    if u.get("parts"):
        out = set()
        for p in u["parts"]:
            if p in by_id:
                out |= _members(by_id[p], by_id)
        return out
    return {u["id"]}


def _adjacent(a: dict, b: dict, leaves: list, by_id: dict, skip=("filler",)) -> bool:
    """b follows a in the same clip with nothing said between them (a «yyy» aside, or
    what `skip` names)."""
    if a["file"] != b["file"] or b["s"] < a["e"] - 0.01:
        return False
    mine = _members(a, by_id) | _members(b, by_id)
    for x in leaves:
        if x["file"] != a["file"] or x["id"] in mine or x.get("drop") in skip:
            continue
        if x["s"] >= a["e"] - 0.01 and x["e"] <= b["s"] + 0.01:
            return False
    return True


# ----------------------------------------------------------------- script
def _script_sentences(script: str, lang: str) -> list:
    """[{text, tokens}]: the script cleaned like the voice pipeline cleans it, split at
    . ! ? … (closing quotes stay with their sentence), digits read as words."""
    raw = str(script or "")
    ru = lang == "ru" or W.is_cyrillic(raw)
    text = raw
    if not ru:
        try:
            text = W._st().clean_for_speech(raw) or raw
        except Exception:  # noqa: BLE001 - an unreadable script is used as written
            text = raw
    out = []
    for para in text.splitlines():
        parts = _SCRIPT_SPLIT.split(para)
        for j in range(0, len(parts), 2):
            sent = (parts[j] + (parts[j + 1] if j + 1 < len(parts) else "")).strip()
            if not sent:
                continue
            said = sent
            if not ru and re.search(r"\d", sent):
                try:
                    said = W._pl().normalize(sent)
                except Exception:  # noqa: BLE001
                    said = sent
            toks = _text_tokens(said, lang)
            if toks:
                out.append({"text": _balance_quotes(W.strip_dashes(sent)), "tokens": toks})
    return out


def _balance_quotes(t: str) -> str:
    """«"Może ja jestem za słaby.» keeps no half of a quote the split cut in two."""
    t = t.strip()
    if t.count('"') % 2:
        t = t.strip('"').strip()
    if t.count("„") != t.count("”"):
        t = t.strip("„”").strip()
    if t.count("«") != t.count("»"):
        t = t.strip("«»").strip()
    return t


def _copy_roots(refs: list) -> list:
    """Each sentence's first identical (or near: «I robimy…» / «Robimy…») copy."""
    roots = list(range(len(refs)))
    for k in range(len(refs)):
        for j in range(k):
            if roots[j] == j and len(refs[k]) >= 2 and W.seq_sim(refs[j], refs[k]) >= _COPY_SIM:
                roots[k] = j
                break
    return roots


def _placeable(T: list, al: dict, refs: list, E: dict) -> bool:
    """Enough of T belongs to the aligned sentence: most of its tokens matched locally,
    or the whole of T reads as a paraphrase of it («a może być i sto prób» for «A czasem
    jeszcze sto prób», where the local match is only «sto prób»)."""
    return al["prec"] >= _PRECISION or _f1(T, refs[al["k"]]) >= E["align_min"]


def _place_script(u: dict, refs: list, E: dict, expected) -> tuple | None:
    """("join", alignment) | ("split", token index, alignment or None) | None (decided in
    the second pass)."""
    T = u["tokens"]
    al = _align_all(T, refs, expected)
    if not al:
        return None
    b = al[0]
    if b["f1"] < E["align_min"]:
        return None
    n = len(T)
    join = b if _placeable(T, b, refs, E) else None
    for cut, rest in ((b["ub"], T[b["ub"]:]), (b["ua"], T[:b["ua"]])):
        if len(rest) < 2 or not 0 < cut < n:
            continue
        r = _align_all(rest, refs, b["k"])
        ok = bool(r) and r[0]["f1"] >= E["align_min"] and _placeable(rest, r[0], refs, E)
        if not ok:                         # a restart: the leftover opens some sentence
            ok = any(_prefix(rest, R) >= E["prefix_min"] for R in refs)
        if ok:
            return ("split", cut, join)
    if join is not None:
        return ("join", join)
    # the matching part is buried in other words: set it apart and look again
    head, tail = b["ua"], n - b["ub"]
    cut = b["ua"] if head >= tail else b["ub"]
    return ("split", cut, None) if 0 < cut < n else None


def _groups_script(units: list, live: list, sents: list, E: dict) -> list:
    refs = [s["tokens"] for s in sents]
    roots = _copy_roots(refs)
    placed = {}                                        # uid -> (k, ra, rb, how)
    order = list(live)
    i, prev_k = 0, None
    while i < len(order):
        u = order[i]
        res = _place_script(u, refs, E, None if prev_k is None else prev_k + 1)
        if res and res[0] == "split":
            a, b = _split_unit(u, res[1], units)
            if a is not None:
                order[i:i + 1] = [a, b]
                continue
            res = ("join", res[2]) if res[2] is not None else None
        if res:
            al = res[1]
            placed[u["id"]] = (al["k"], al["ra"], al["rb"], "full")
            prev_k = al["k"]
        i += 1

    # second pass, in time order: continuations, prefix fragments, false starts, ad-libs
    by_id = {u["id"]: u for u in units}
    leaves = _leaves(units)
    first_k = [placed.get(u["id"], (None,))[0] for u in order]
    adlibs = []
    for idx, u in enumerate(order):
        if u["id"] in placed:
            continue
        T = u["tokens"]
        prev = order[idx - 1] if idx else None
        if prev is not None and prev["id"] in placed and _adjacent(prev, u, leaves, by_id):
            k, ra, rb, _ = placed[prev["id"]]
            R = refs[k]
            for st in (rb, rb - 1, rb + 1):
                if 0 <= st < len(R) and _prefix(T, R[st:]) >= E["prefix_min"]:
                    placed[u["id"]] = (k, st, min(len(R), st + len(T)), "cont")
                    break
            if u["id"] in placed:
                continue
        k_prev = next((placed[order[j]["id"]][0] for j in range(idx - 1, -1, -1)
                       if order[j]["id"] in placed), None)
        k_next = next((first_k[j] for j in range(idx + 1, len(order)) if first_k[j] is not None),
                      None)
        allowed = [k for k in ([k_next] + ([k_prev, k_prev + 1, k_prev + 2] if k_prev is not None
                                           else [0, 1])) if k is not None and 0 <= k < len(refs)]
        if len(T) >= 2 or u["trail"] or not u["terminal"]:
            for k in allowed:
                if _prefix(T, refs[k]) >= E["prefix_min"]:
                    placed[u["id"]] = (k, 0, len(T), "prefix")
                    break
            if u["id"] in placed:
                continue
        if _false_start(u, order[idx + 1:], E):
            u["drop"] = "false_start"
            continue
        adlibs.append(u)

    groups = []
    for k, s in enumerate(sents):
        groups.append({"id": "", "kind": "script", "text": s["text"], "tokens": s["tokens"],
                       "script_idx": k, "candidates": [], "_key": (k, 0, 0.0)})
    spans = {}
    for u in order:
        if u["id"] in placed:
            k, ra, rb, _ = placed[u["id"]]
            groups[roots[k]]["candidates"].append(u["id"])
            spans[u["id"]] = (ra, rb)
    members = {}
    for k, r in enumerate(roots):
        members.setdefault(r, []).append(k)
    for r, ks in members.items():
        if len(ks) > 1:
            for k in ks:
                groups[k]["copies"] = ks
    for g in groups:
        g["candidates"] = _chain(g["candidates"], g["tokens"], units, spans)

    # ad-libs: grouped among themselves, placed after the sentence said just before them
    for ag in _groups_pseudo(units, adlibs, E):
        now = {x["id"]: x for x in units}
        first = min((now[c] for c in ag["candidates"]), key=_tkey)
        n0 = next((n for n, x in enumerate(order) if _tkey(x) >= _tkey(first)), len(order))
        k_before = next((placed[order[j]["id"]][0] for j in range(n0 - 1, -1, -1)
                         if order[j]["id"] in placed), -1)
        ag["_key"] = (k_before, 1, float(n0))
        ag["kind"] = "adlib"
        groups.append(ag)
    keep = []
    for g in groups:
        if g["candidates"] or (g.get("copies") and groups[g["copies"][0]]["candidates"]):
            keep.append(g)
    keep.sort(key=lambda g: g["_key"])
    return keep


def _false_start(u: dict, later: list, E: dict) -> bool:
    """A few words that open something he says right after: «Może…» before «Może nie…»."""
    nw = sum(1 for w in u["words"] if not _is_filler(w[2]))
    if nw > E["false_start_words"] or not u["tokens"]:
        return False
    for v in later[:_FALSE_START_LOOKAHEAD]:
        if v["clip"] - u["clip"] > 1:
            break
        if len(v["tokens"]) > len(u["tokens"]) and _prefix(u["tokens"], v["tokens"]) >= E["prefix_min"]:
            return True
    return False


def _chain(cand_ids: list, R: list, units: list, spans: dict | None = None) -> list:
    """Candidates that continue each other in one clip become one attempt: «Ale to znaczy,»
    then «że nie musisz…» is one take Whisper cut at a pause, not two; «Bo jedyna rzecz,»
    «która nas, sorry,» «która nas dzieli…» too (the retake request between them is cut
    out of the piece)."""
    by_id = {u["id"]: u for u in units}
    leaves = _leaves(units)
    spans = spans or {}
    out = []
    for c in sorted((by_id[x] for x in cand_ids if x in by_id), key=_tkey):
        if out:
            p = out[-1]
            near = p["file"] == c["file"] and _adjacent(p, c, leaves, by_id)
            # across a retake request only a clean continuation («Bo,» «stop.» «Bo
            # jedyna…» is a restart, not one attempt)
            meta = not near and p["file"] == c["file"] and \
                _adjacent(p, c, leaves, by_id, ("filler", "meta"))
            if near or meta:
                sp = spans.get(p["id"]) or _span(p, R)
                sc = spans.get(c["id"]) or _span(c, R)
                if sp and sc and sc[0] >= sp[1] - (0 if meta else 1) and sc[1] > sp[1]:
                    nu = _join_units(p, c, units)
                    spans[nu["id"]] = (sp[0], sc[1])
                    by_id[nu["id"]] = nu
                    leaves = _leaves(units)
                    out[-1] = nu
                    continue
        out.append(c)
    return [u["id"] for u in out]


def _span(u: dict, R: list):
    sw = _sw(u["tokens"], R)
    return (sw["ra"], sw["rb"]) if sw["m"] else None


# ----------------------------------------------------------------- no script
def _ends(u: dict) -> bool:
    """The attempt reaches the end of its sentence: . ? !, a split we made at a sentence
    boundary, or a pause after it."""
    return bool(u["terminal"] or u.get("split_end") or u["gap_after"] >= _END_GAP)


def _rep_key(u: dict) -> tuple:
    """The attempt that best shows the whole sentence: finished (a full stop beats a
    pause after a comma), then the longest."""
    return (0 if u["trail"] else 1,
            2 if (u["terminal"] or u.get("split_end")) else 1 if _ends(u) else 0,
            len(u["tokens"]))


def _set_rep(g: dict, by_id: dict) -> None:
    cands = [by_id[c] for c in g["candidates"] if c in by_id]
    rep = max(cands, key=_rep_key)
    g["rep"], g["tokens"], g["text"] = rep["id"], rep["tokens"], W.strip_dashes(rep["text"])


def _groups_pseudo(units: list, live: list, E: dict) -> list:
    """Units in time order against the sentences heard so far. A unit that matches one
    (similar, a prefix, or one containing the other) is another take of it; otherwise it
    is a new sentence at the end. Groups keep the order of first appearance, so a redo
    returns to where the original was."""
    groups: list = []
    order = list(live)
    by_id = {u["id"]: u for u in units}
    where: dict = {}                              # unit id -> its group
    i = 0
    while i < len(order):
        u = order[i]
        T = u["tokens"]
        cut = _span_cut(T, groups) if len(groups) >= 2 and len(T) >= 4 else None
        if cut is not None:
            a, b = _split_unit(u, cut, units)
            if a is not None:
                by_id.update({a["id"]: a, b["id"]: b})
                order[i:i + 1] = [a, b]
                continue
        prev = order[i - 1] if i and order[i - 1]["file"] == u["file"] else None
        nxt = order[i + 1] if i + 1 < len(order) and order[i + 1]["file"] == u["file"] else None
        g = _best_group(u, groups, E, by_id, where.get(prev["id"]) if prev else None, nxt)
        if g is not None:
            cut = _extra_cut(T, g, by_id, E)
            if cut is not None:
                a, b = _split_unit(u, cut, units)
                if a is not None:
                    by_id.update({a["id"]: a, b["id"]: b})
                    order[i:i + 1] = [a, b]
                    continue
            prev_id = g["candidates"][-1] if g["candidates"] else None
            g["candidates"].append(u["id"])
            if prev_id is not None and by_id[prev_id]["file"] == u["file"]:
                g["candidates"] = _chain(g["candidates"], g["tokens"], units)
                by_id = {x["id"]: x for x in units}
            _set_rep(g, by_id)
        else:
            g = {"id": "", "kind": "pseudo", "text": "", "tokens": [], "script_idx": None,
                 "candidates": [u["id"]]}
            _set_rep(g, by_id)
            groups.append(g)
        where[u["id"]] = g
        for c in g["candidates"]:
            where[c] = g
        i += 1
    for n, g in enumerate(groups):
        g["_key"] = (n, 0, 0.0)
    return groups


_NEAR_SECONDS = 15.0                   # one long clip: a short phrase said again later is a new line, not a retake


def _near(u: dict, g: dict, by_id: dict) -> bool:
    """Some attempt at g was made just before u: in the clip before it, or close by in the same
    clip. «It's protein.» at 6 s and «It's protein, so it helps...» at 29 s are two lines."""
    for c in g["candidates"]:
        x = by_id.get(c)
        if x is None:
            continue
        d = u["clip"] - x["clip"]
        if d == 1:
            return True
        if d == 0 and u.get("words") and x.get("words") and u["words"][0][0] - x["words"][-1][1] <= _NEAR_SECONDS:
            return True
    return False


def _match(u: dict, g: dict, E: dict) -> tuple:
    """(similar, partial, rank) of unit u against sentence g: `similar` is a retake by
    itself; `partial` (a short sentence, a prefix, one inside the other) needs support."""
    T, R = u["tokens"], g["tokens"]
    if not R or not T:
        return False, False, None
    lcs = _lcs(T, R)[0]
    f1 = 2.0 * lcs / (len(T) + len(R))
    pre = _prefix(T, R) if (len(T) >= 2 or u["trail"] or not u["terminal"]) else 0.0
    pre2 = _prefix(R, T) if len(R) >= 2 else 0.0
    con = lcs / len(T) if (len(T) >= 4 or (len(T) >= 3 and not u["terminal"])) else 0.0
    con2 = lcs / len(R) if len(R) >= 3 else 0.0
    similar = f1 >= E["pseudo_min"] and min(len(T), len(R)) > _SHORT_SENTENCE
    partial = (f1 >= E["pseudo_min"] or pre >= E["prefix_min"] or pre2 >= E["prefix_min"]
               or con >= E["contain_min"] or con2 >= E["contain_min"])
    return similar, partial, (round(f1, 6), max(pre, pre2, con, con2))


def _best_group(u: dict, groups: list, E: dict, by_id: dict, prev_g=None, nxt=None):
    """The sentence u is another attempt at, or None. A long sentence said again is a
    retake wherever it comes. A short one, or a mere prefix / part of one, counts only
    next to where it was said, or when its neighbours in the clip are attempts at the
    sentences around it (the whole passage said again): a late «To jest tak.» is its own
    sentence, not a false start of «To jest tak, że wysyłasz sto…» from two clips back."""
    best, best_key = None, None
    for n, g in enumerate(groups):
        similar, partial, key = _match(u, g, E)
        if not (similar or partial):
            continue
        if not similar and not _near(u, g, by_id):
            ctx = prev_g is not None and n and groups[n - 1] is prev_g
            if not ctx and nxt is not None and n + 1 < len(groups) and len(nxt["tokens"]) > _SHORT_SENTENCE:
                ctx = any(_match(nxt, groups[n + 1], E)[:2])
            if not ctx:
                continue
        key = key + (n,)
        if best_key is None or key > best_key:
            best, best_key = g, key
    return best


def _span_cut(T: list, groups: list):
    """Where a unit that says two known sentences in one breath changes sentence."""
    P, owner = [], []
    for n, g in enumerate(groups):
        P += g["tokens"]
        owner += [n] * len(g["tokens"])
    sw = _sw(T, P)
    if sw["m"] < 4:
        return None
    count = Counter(owner[j] for _, j in sw["pairs"])
    involved = sorted(n for n, c in count.items()
                      if c >= 2 and c >= 0.5 * len(groups[n]["tokens"]))
    if len(involved) < 2:
        return None
    first = involved[0]
    last_t = max(i for i, j in sw["pairs"] if owner[j] == first)
    cut = last_t + 1
    return cut if 0 < cut < len(T) else None


def _extra_cut(T: list, g: dict, by_id: dict, E: dict):
    """A take of a known, finished sentence with more words around it: the extra words
    (3 or more after it, or a restart of it before it) are a unit of their own. Against
    a sentence heard only unfinished («Między tobą a tym, czego nie…», «…czego chcemy,»)
    the longer unit is simply the whole take."""
    rep = by_id.get(g.get("rep"))
    if rep is None or rep["trail"] or not (rep["terminal"] or rep.get("split_end")):
        return None
    R = g["tokens"]
    sw = _sw(T, R, _SW_COVER_GAP)       # «…milionów listów, nie, maili.» is not two sentences
    if not sw["m"] or sw["m"] < 0.8 * len(R):
        return None
    if len(T) - sw["ub"] >= 3:
        return sw["ub"]
    head = T[:sw["ua"]]
    if len(head) >= 3 or (len(head) >= 2 and _prefix(head, R) >= E["prefix_min"]):
        return sw["ua"]
    return None


# ----------------------------------------------------------------- groups
def build_groups(units: list, script: str | None = None, lang: str = "pl") -> list:
    """Units -> groups, one per sentence, in the order of the text.

    Group: {id, kind ("script" | "adlib" | "pseudo"), text, tokens, candidates: [unit ids],
    script_idx, order, copies?}. Meta units and «yyy»-only units are marked dropped here;
    false starts too. May split or join units: see the module docstring."""
    E = _E()
    sents = _script_sentences(script, lang) if script and str(script).strip() else []
    if sents:
        _unmeta(units, sents, E)
    live = []
    for u in sorted((u for u in units if not u.get("gone")), key=_tkey):
        if u.get("drop"):
            continue
        if u["meta"]:
            u["drop"] = "meta"
        elif not u["tokens"]:
            u["drop"] = "filler"
        else:
            live.append(u)
    if sents:
        groups = _groups_script(units, live, sents, E)
    else:
        groups = _groups_pseudo(units, live, E)
    groups = _drop_strays(groups, units, E)
    for n, g in enumerate(groups):
        g["id"] = f"g{n + 1}"
        g["order"] = n
        g.pop("_key", None)
    ids = [g for g in groups]
    for g in ids:                       # copies point at group ids, not sentence indexes
        if g.get("copies") and isinstance(g["copies"][0], int):
            g["copies"] = [x["id"] for x in ids if x.get("script_idx") in g["copies"]]
    return groups


def _drop_strays(groups: list, units: list, E: dict) -> list:
    """Sentences heard once that are debris of an aborted attempt, not content: an
    unfinished one Whisper could hardly read, or a few words wedged between two attempts
    at the same other sentence («…czego chcemy,» «To jedność.» «Bo jedyna…»)."""
    by_id = {u["id"]: u for u in units}
    owner = {c: n for n, g in enumerate(groups) for c in g["candidates"]}
    seq = sorted((by_id[c] for c in owner if c in by_id), key=_tkey)
    pos = {u["id"]: i for i, u in enumerate(seq)}
    heard: dict = {}
    for u in _leaves(units):
        heard.setdefault(u["clip"], []).extend(w[3] for w in u["words"])
    median = {k: float(np.median(v)) for k, v in heard.items() if v}

    def garbled(u: dict) -> bool:
        """Whisper's guess at mumbling: unsure of the whole, very unsure of a word, much
        less sure than of the rest of the clip, short and unfinished."""
        return (u["trail"] and u["asr"] < _GARBLE_P and u["e"] - u["s"] <= _GARBLE_SECS
                and u["asr"] <= median.get(u["clip"], 1.0) - _GARBLE_DROP
                and min((w[3] for w in u["words"]), default=1.0) < _GARBLE_MIN_P)

    def stray(u: dict, n: int) -> bool:
        if garbled(u):
            return True
        nw = sum(1 for w in u["words"] if not _is_filler(w[2]))
        i = pos[u["id"]]
        if nw > E["false_start_words"] or not 0 < i < len(seq) - 1:
            return False
        a, b = seq[i - 1], seq[i + 1]
        return a["file"] == u["file"] == b["file"] and owner[a["id"]] == owner[b["id"]] != n

    keep = []
    for n, g in enumerate(groups):
        cands = [by_id[c] for c in g["candidates"] if c in pos]
        if g.get("kind") == "script" or not cands or not all(stray(u, n) for u in cands):
            keep.append(g)
            continue
        for u in cands:
            u["drop"] = "false_start"
    return keep


def _unmeta(units: list, sents: list, E: dict) -> None:
    """«Stop!» or «Spróbuj jeszcze raz.» is a line of the script, not a request for a
    retake: a meta unit (joined back with the rest of its sentence when it was split off)
    that the script says is kept."""
    by_src: dict = {}
    for u in units:
        if not u.get("gone"):
            by_src.setdefault(u["src"], []).append(u)
    refs = [s["tokens"] for s in sents]
    for src, parts in by_src.items():
        metas = [u for u in parts if u["meta"]]
        if not metas:
            continue
        phrase_toks = W.tokens(metas[0]["meta_phrase"])
        with_phrase = [R for R in refs if any(R[i:i + len(phrase_toks)] == phrase_toks
                                              for i in range(len(R)))]
        if not with_phrase:
            continue
        parts.sort(key=_tkey)
        whole = [t for u in parts for t in _text_tokens(u["text"], u["lang"])]
        if max(_f1(whole, R) for R in with_phrase) < (E["align_min"] if len(parts) > 1 else 0.8):
            continue
        if len(parts) == 1:
            parts[0]["meta"] = False
            continue
        a = parts[0]
        for b in parts[1:]:
            a = _join_units(a, b, units)
        a["meta"], a["meta_phrase"] = False, ""


# ----------------------------------------------------------------- scoring
def _abandoned(c: dict, cands: list, gid: str, timeline: list) -> int:
    """He started this sentence again right after this attempt (same or next utterance,
    or the first one of the next clip), with nothing else said in between."""
    later = [x for x in cands if _tkey(x) > _tkey(c)]
    if not later:
        return 0
    n = min(later, key=_tkey)
    if n["clip"] == c["clip"]:
        if n["utt"] - c["utt_end"] > 1:
            return 0
    elif not (n["clip"] == c["clip"] + 1 and n["utt"] == 0):
        return 0
    for u, g in timeline:
        if g != gid and _tkey(c) < _tkey(u) < _tkey(n):
            return 0
    return 1


def _coverage(T: list, R: list, use_script: bool) -> tuple:
    """(coverage 0..1, LCS length): how much of the sentence this attempt says. The
    extent comes from the local alignment, so a stray match far away («tak» at the end of
    «To jest tak, że… tak») does not stretch a three-word fragment over the sentence; its
    gaps are cheap enough to walk over a few words the reference has and this attempt
    has not (a reference take with «listów, nie,» in it: the clean take still reaches
    «maili» and its end). Against the script the share of its words counts too
    (paraphrase costs a little)."""
    if not T or not R:
        return 0.0, 0
    lcs = _lcs(T, R)[0]
    sw = _sw(T, R, _SW_COVER_GAP)
    ext = max((sw["rb"] - sw["ra"]) / len(R) if sw["m"] else 0.0, lcs / len(R))
    return (0.5 * lcs / len(R) + 0.5 * ext if use_script else ext), lcs


def _extra(c: dict, cands: list, E: dict) -> tuple:
    """(penalty, words): what attempt c says beyond another attempt at the same sentence,
    inside the part both say. «…pięć milionów listów, nie, maili» against «…pięć milionów
    maili» has two words more, and «nie,» among them means he took «listów» back: that
    costs as much as a restart. Words only one of them has at the edges are not counted
    (an unfinished take is judged by coverage), nor are words in place of other words (a
    different wording). The worst comparison counts."""
    T = c["tokens"]
    corr = _CORRECTION.get(c.get("lang", "pl"), _CORRECTION["en"])
    ws, tw = c["words"], c["tok_w"]
    worst = (0.0, 0)
    for o in cands:
        O = o["tokens"]
        if o is c or not O or not T:
            continue
        n, pairs = _lcs(T, O)
        if len(pairs) < 2 or 2.0 * n / (len(T) + len(O)) < E["pseudo_min"]:
            continue
        extra = (pairs[-1][0] - pairs[0][0]) - (pairs[-1][1] - pairs[0][1])
        if extra <= 0:
            continue
        hit = {i for i, _ in pairs}
        took = False
        for i in range(pairs[0][0], pairs[-1][0] + 1):
            if i in hit or T[i] not in corr:
                continue
            wi = tw[i]
            if ws[wi][2].rstrip().endswith(",") or (wi and ws[wi - 1][2].rstrip().endswith(",")):
                took = True
        pen = _PEN_CORRECTION if took else min(_PEN_EXTRA_MAX, _PEN_EXTRA * extra)
        worst = max(worst, (pen, extra))
    return worst


def _is_fragment_of(r: dict, d: dict, E: dict) -> bool:
    return len(r["tokens"]) < len(d["tokens"]) and _prefix(r["tokens"], d["tokens"]) >= E["prefix_min"]


def score(groups: list, units: list, script=None) -> None:
    """Score every candidate and pick each group's default (fills the groups in place).

    Per candidate: complete 1 / 0.5 / 0, fluency, asr, script similarity, q. Per group:
    "scores", "default" (list of unit ids, usually one; [] = nothing kept), "conf",
    "seconds", and "ask" when the choice is worth a question. With a script, groups of a
    repeated sentence share their takes («copies»); without one, identical sentences side
    by side follow the repeat rules."""
    E = _E()
    by_id = {u["id"]: u for u in units}
    leaves = _leaves(units)
    timeline = sorted(((by_id[c], g["id"]) for g in groups for c in g["candidates"]
                       if c in by_id), key=lambda x: _tkey(x[0]))
    gmap = {g["id"]: g for g in groups}
    for g in groups:                    # scoring again starts from what build_groups made
        for k in ("ask", "repeat", "dropped", "continuity"):
            g.pop(k, None)
        if g.get("copies") and g["copies"][0] != g["id"]:
            g["candidates"] = []
    for g in groups:
        cands = sorted((by_id[c] for c in g["candidates"] if c in by_id), key=_tkey)
        g["candidates"] = [c["id"] for c in cands]
        use_script = g.get("kind") == "script"
        R = g.get("tokens") or []
        sc = {}
        for c in cands:
            T = c["tokens"]
            cov, lcs = _coverage(T, R, use_script)
            if len(cands) == 1 and not use_script:
                cov = 1.0
            complete = 1.0 if (cov >= _COMPLETE_COV and not c["trail"] and _ends(c)) else \
                0.5 if cov >= _PARTIAL_COV else 0.0
            ab = _abandoned(c, cands, g["id"], timeline)
            pen_extra, extra = _extra(c, cands, E)
            pen = (_PEN["fillers"] * c["fillers"] + _PEN["restarts"] * c["restarts"]
                   + _PEN["long"] * len(c["unresolved_long"]) + _PEN["abandoned"] * ab
                   + pen_extra)
            fluency = 1.0 - min(1.0, pen)
            asr = _clamp((c["asr"] - _ASR_LO) / _ASR_SPAN)
            ssim = 2.0 * lcs / (len(T) + len(R)) if (use_script and T and R) else 0.0
            if use_script:
                q = (_W_SCRIPT[0] * complete + _W_SCRIPT[1] * fluency + _W_SCRIPT[2] * asr
                     + _W_SCRIPT[3] * ssim)
            else:
                q = _W_PLAIN[0] * complete + _W_PLAIN[1] * fluency + _W_PLAIN[2] * asr
            sc[c["id"]] = {"complete": complete, "coverage": round(cov, 3),
                           "fluency": round(fluency, 3), "asr": round(asr, 3),
                           "script": round(ssim, 3), "q": round(q, 4), "abandoned": ab,
                           "extra": extra}
        g["scores"] = sc
        _pick(g, cands, sc, use_script, E)
    for g in groups:
        if g.get("copies") and g["copies"][0] == g["id"]:
            _share_copies(g, [gmap[x] for x in g["copies"] if x in gmap], by_id, leaves)
    for g in groups:
        if g.get("kind") != "script" and len(g.get("default") or []) == 1:
            _repeat_rule(g, by_id, leaves, E)
    _continuity(groups, by_id, leaves)
    for g in groups:
        d = [by_id[x] for x in g.get("default") or [] if x in by_id]
        g["seconds"] = round(sum(u["e"] - u["s"] for u in d), 3)
        if not g.get("ask"):
            _take_question(g, by_id, E)


def _pick(g: dict, cands: list, sc: dict, use_script: bool, E: dict) -> None:
    """Best q; ties within EDIT["tie"] go to the later take (his last clean one)."""
    if not cands:
        g["default"], g["conf"] = [], 1.0
        return
    qmax = max(sc[c["id"]]["q"] for c in cands)
    tied = [c for c in cands if sc[c["id"]]["q"] >= qmax - E["tie"] - 1e-9]
    d = tied[-1]
    others = [c for c in cands if c is not d]
    conf = 1.0
    if others:
        r = max(others, key=lambda c: (sc[c["id"]]["q"], _tkey(c)))
        sd, sr = sc[d["id"]], sc[r["id"]]
        conf = _clamp(0.5 + 2.5 * (sd["q"] - sr["q"]))
        if sr["complete"] < sd["complete"] or _is_fragment_of(r, d, E):
            conf = max(conf, _CONF_FRAGMENT)
        elif W.seq_sim(r["tokens"], d["tokens"]) >= _SAME_WORDING:
            conf = max(conf, _CONF_SAME)
        if use_script and sd["script"] - sr["script"] >= _SCRIPT_GAP - 1e-9:
            conf = max(conf, _CONF_SCRIPT)
    g["default"], g["conf"] = [d["id"]], round(conf, 3)
    # a lone few-word trail («I…», «Bo jedyna…») never finished anywhere is a false start;
    # not when it says the whole script sentence (the script ends it there)
    nw = sum(1 for w in d["words"] if not _is_filler(w[2]))
    whole = use_script and sc[d["id"]]["coverage"] >= _COMPLETE_COV
    if d["trail"] and sc[d["id"]]["complete"] < 1 and nw <= E["false_start_words"] and not whole:
        g["default"], g["conf"], g["dropped"] = [], _CONF_FRAGMENT, "fragment"


def _share_copies(root: dict, members: list, by_id: dict, leaves: list) -> None:
    """A sentence the script says N times keeps up to N complete takes, in time order
    (the earliest extras go); fewer spoken copies are fine. Copies that follow each other
    in the script are said back to back, so only a run of takes side by side fills them
    (three recordings that each say it once keep the last one, not two). All takes stay
    candidates of the first copy; each later copy gets the one it keeps."""
    sc = root["scores"]
    pool = sorted((by_id[c] for c in root["candidates"] if c in by_id), key=_tkey)
    done = [c for c in pool if sc[c["id"]]["complete"] >= 1]
    if len(done) < 2:
        return
    idx = [m.get("script_idx") for m in members]
    together = all(isinstance(a, int) and isinstance(b, int) and b == a + 1
                   for a, b in zip(idx, idx[1:]))
    if together:
        runs = [[done[0]]]
        for c in done[1:]:
            if _adjacent(runs[-1][-1], c, leaves, by_id):
                runs[-1].append(c)
            else:
                runs.append([c])
        keep = runs[-1][-len(members):]
    else:
        keep = done[-len(members):]
    for i, m in enumerate(members):
        m["conf"] = _CONF_COPIES
        m["default"] = [keep[i]["id"]] if i < len(keep) else []
        if m is not root:
            m["candidates"] = list(m["default"])
            m["scores"] = {x: sc[x] for x in m["default"]}


def _repeat_rule(g: dict, by_id: dict, leaves: list, E: dict) -> None:
    """Without a script, the same sentence twice side by side: close together it is a
    rhetorical repeat (keep both), a second or two apart it is unclear (ask, default one),
    across clips it is a retake (the later one)."""
    sc = g["scores"]
    cands = [by_id[c] for c in g["candidates"]]
    d = by_id[g["default"][0]]
    i = cands.index(d)
    for nb in ([cands[i - 1]] if i > 0 else []) + ([cands[i + 1]] if i + 1 < len(cands) else []):
        if sc[nb["id"]]["complete"] < 1 or sc[d["id"]]["complete"] < 1:
            continue
        if nb["tokens"] != d["tokens"]:        # a retake varies; a rhetorical repeat does not
            continue
        first, second = sorted((nb, d), key=_tkey)
        if first["file"] == second["file"]:
            if not _adjacent(first, second, leaves, by_id):
                continue
            gap = second["s"] - first["e"]
            if gap < E["repeat_keep_gap"]:
                g["default"], g["conf"], g["repeat"] = [first["id"], second["id"]], \
                    _CONF_REPEAT_KEEP, "keep"
            elif gap <= E["repeat_ask_gap"]:
                g["default"], g["conf"], g["repeat"] = [second["id"]], _CONF_REPEAT_ASK, "ask"
                secs = first["e"] - first["s"]
                if secs < E["ask_min_seconds"]:        # «Nie.» twice: not worth a question
                    return
                g["ask"] = {
                    "kind": "repeat", "default": "b",
                    "impact": round((1 - _CONF_REPEAT_ASK) * secs, 4),
                    "options": [
                        {"id": "a", "label": "Оба раза", "keep": [first["id"], second["id"]],
                         "play": _play(first, second)},
                        {"id": "b", "label": "Один раз", "keep": [second["id"]],
                         "play": _play(second)},
                    ]}
            else:
                continue
        elif second["clip"] == first["clip"] + 1:
            g["default"], g["conf"], g["repeat"] = [second["id"]], \
                max(g["conf"], _CONF_REPEAT_CLIPS), "clips"
        else:
            continue
        return


def _continuity(groups: list, by_id: dict, leaves: list) -> None:
    """An uncertain choice goes to the take that sits next to its neighbours' takes when
    that costs little: fewer cuts, the same breath. Never back to an older recording of a
    sentence he said again later in another utterance or clip: that redo was on purpose
    (clip 1 «A B C», clip 2 only «B»: the reel keeps clip 2's «B»)."""
    ordered = sorted((g for g in groups if g.get("default")), key=lambda g: g["order"])
    for idx, g in enumerate(ordered):
        if g.get("conf", 1) >= _CONTINUITY_CONF or len(g["default"]) != 1 or g.get("repeat") \
                or g.get("copies") or len(g["candidates"]) < 2:
            continue
        before = max((by_id[x] for x in ordered[idx - 1]["default"]), key=_tkey) if idx else None
        after = min((by_id[x] for x in ordered[idx + 1]["default"]), key=_tkey) \
            if idx + 1 < len(ordered) else None

        def adj(c):
            n = 0
            if before is not None and _adjacent(before, c, leaves, by_id):
                n += 1
            if after is not None and _adjacent(c, after, leaves, by_id):
                n += 1
            return n

        sc = g["scores"]
        d = by_id[g["default"][0]]
        cur = adj(d)
        best = None
        for cid in g["candidates"]:
            c = by_id[cid]
            if c is d or sc[cid]["q"] < sc[d["id"]]["q"] - _CONTINUITY_Q \
                    or sc[cid]["complete"] < sc[d["id"]]["complete"]:
                continue
            if _tkey(c) < _tkey(d) and (c["file"] != d["file"] or c["utt_end"] < d["utt"]):
                continue
            a = adj(c)
            if a > cur and (best is None or (a, sc[cid]["q"]) > best[0]):
                best = ((a, sc[cid]["q"]), c)
        if best is not None:
            g["default"] = [best[1]["id"]]
            g["continuity"] = True


def _play(a: dict, b: dict | None = None) -> dict:
    b = b or a
    return {"file": a["file"], "t0": round(max(0.0, a["s"] - _PLAY_PAD[0]), 2),
            "t1": round(b["e"] + _PLAY_PAD[1], 2)}


def _take_question(g: dict, by_id: dict, E: dict) -> None:
    if len(g.get("default") or []) != 1 or len(g["candidates"]) < 2 or g.get("repeat"):
        return
    if g.get("conf", 1) >= E["ask_conf"] or g["seconds"] < E["ask_min_seconds"]:
        return
    sc = g["scores"]
    d = by_id[g["default"][0]]
    others = [by_id[c] for c in g["candidates"] if c != d["id"] and sc[c]["complete"] >= 0.5]
    if not others:
        return
    r = max(others, key=lambda c: (sc[c["id"]]["q"], _tkey(c)))
    first, second = sorted((d, r), key=_tkey)
    g["ask"] = {
        "kind": "take", "default": "a" if d is first else "b",
        "impact": round((1 - g["conf"]) * g["seconds"], 4),
        "options": [
            {"id": "a", "label": "Первый", "keep": [first["id"]], "play": _play(first)},
            {"id": "b", "label": "Второй", "keep": [second["id"]], "play": _play(second)},
        ]}


# ----------------------------------------------------------------- questions
def _qid(g: dict) -> str:
    return "q" + str(g["id"]).lstrip("g")


def _quote(text: str) -> str:
    t = W.strip_dashes(re.sub(r"\s+", " ", str(text or "")).strip())
    t = t.replace("„", "").replace("”", "").replace('"', "")
    if len(t) > _QUOTE_MAX:
        t = t[:_QUOTE_MAX].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return f"„{t}”"


def questions(groups: list, extra=()) -> list:
    """The hardest choices, at most EDIT["max_questions"], ranked by (1-conf)*seconds.

    Question: {id, kind, text, quote, group, default, options: [{id, label, play}, ...,
    {id: "auto", label: «Решите сами»}]}. `extra` are questions the orchestrator built
    (the «which sound» conflict); they may carry "impact" and rank first without it."""
    E = _E()
    items = []
    for g in groups:
        a = g.get("ask")
        if not a:
            continue
        opts = [{"id": o["id"], "label": o["label"], "play": o["play"]} for o in a["options"]]
        items.append((a["impact"], {
            "id": _qid(g), "kind": a["kind"], "text": _ASK_TEXT[a["kind"]],
            "quote": _quote(g.get("text")), "group": g["id"], "default": a["default"],
            "options": opts + [dict(_AUTO)]}))
    for x in extra or ():
        if not isinstance(x, dict) or not x.get("id"):
            continue
        q = {k: v for k, v in x.items() if k != "impact"}
        opts = list(q.get("options") or [])
        if not any(isinstance(o, dict) and o.get("id") == "auto" for o in opts):
            opts.append(dict(_AUTO))
        q["options"] = opts
        try:
            impact = float(x.get("impact", 1e9))
        except (TypeError, ValueError):
            impact = 1e9
        items.append((impact, q))
    items.sort(key=lambda t: -t[0])
    return [q for _, q in items[:int(E["max_questions"])]]


def choose(groups: list, answers: dict | None = None) -> list:
    """The chosen attempts in text order: [{group, order, units: [unit ids], text}].
    answers = {question id: option id}; "auto" or no answer keeps the default."""
    answers = answers or {}
    sel = []
    for g in sorted(groups, key=lambda g: g.get("order", 0)):
        keep = list(g.get("default") or [])
        a = g.get("ask")
        if a:
            pick = answers.get(_qid(g))
            for o in a["options"]:
                if pick == o["id"]:
                    keep = list(o["keep"])
        if keep:
            sel.append({"group": g["id"], "order": g.get("order", 0), "units": keep,
                        "text": g.get("text", "")})
    return sel


# ----------------------------------------------------------------- pieces
def _i(fdb: np.ndarray, t: float) -> int:
    return min(max(int(round((t - A.WIN / 2) / A.HOP)), 0), fdb.size - 1)


def _last_loud(fdb: np.ndarray, a: float, b: float, thr: float) -> float:
    """End of the last frame above thr with its centre in [a, b]; b when none is."""
    if fdb.size == 0 or b <= a:
        return b
    i, j = _i(fdb, a), _i(fdb, b)
    for k in range(j, i - 1, -1):
        if fdb[k] > thr:
            return min(b, k * A.HOP + A.WIN)
    return b


def _first_loud(fdb: np.ndarray, a: float, b: float, thr: float) -> float:
    """Start of the first frame above thr with its centre in [a, b]; a when none is."""
    if fdb.size == 0 or b <= a:
        return a
    i, j = _i(fdb, a), _i(fdb, b)
    for k in range(i, j + 1):
        if fdb[k] > thr:
            return max(a, k * A.HOP)
    return a


def _snap(fdb: np.ndarray, t: float) -> float:
    """The quietest frame within ±_SNAP, when it is clearly quieter than where we are."""
    if fdb.size == 0:
        return t
    q = A.quietest(fdb, t, _SNAP)
    return q if fdb[_i(fdb, q)] < fdb[_i(fdb, t)] - _SNAP_GAIN else t


class _Clip:
    """What the edges need from one ClipSpeech."""

    def __init__(self, cs: dict):
        self.fdb = _arr(cs.get("fdb"))
        fl = _num(cs.get("floor_db"))
        self.floor = fl if fl is not None else A.noise_floor(self.fdb)
        regions = []
        for r in cs.get("regions") or []:
            if isinstance(r, (list, tuple)) and len(r) >= 2:
                a, b = _num(r[0]), _num(r[1])
                if a is not None and b is not None:
                    regions.append((a, b))
        self.regions = sorted(regions)
        self.words = _clip_words(cs)
        dur = _num(cs.get("dur"))
        if dur is not None and dur > 0:
            self.dur = dur
        elif self.fdb.size:
            self.dur = self.fdb.size * A.HOP + A.WIN
        else:                               # nothing measured: the words are all we know
            self.dur = max((w[1] for w in self.words), default=0.0) + _E()["pad_after_max"]
        pause = _num(cs.get("pause_db"))
        # noise_floor is the quietest tenth of the clip, often well under the room tone
        # between words (-71 against -58 on the reference clips), so "quiet" and "loud" are
        # also measured against the clip's pause level from the speech map
        self.quiet = pause if pause is not None else self.floor + _QUIET_DB
        self.thr = max(self.floor + _EDGE_DB, self.quiet - _EDGE_BELOW_PAUSE)
        self.breath = max(self.floor + _BREATH_DB, self.quiet - _BREATH_BELOW_PAUSE)

    def heard(self, w: list) -> list:
        """Word w without the silence Whisper glued before it (pass-1 words can carry a
        second of it): it starts at its first loud frame when the first _LEAD_QUIET of it
        is quiet. The pause before it is then measured right, and its subtitle starts
        when he says it."""
        if self.fdb.size and w[1] > w[0]:
            fl = _first_loud(self.fdb, w[0], w[1], self.thr)
            if fl - w[0] >= _LEAD_QUIET and fl < w[1]:
                return [round(fl, 3), w[1], w[2], w[3]]
        return w

    def sound_start(self, w: list, lower: float = 0.0) -> float:
        """Where word w is first heard: Whisper's start, past silence Whisper glued to the
        word, moved to a Silero start close by, then walked back to the «s»
        (reel.audio.onset), never before `lower`. A later Silero start is taken only over
        quiet and only when it begins inside the word or the word's own place is quiet
        (Whisper misplaced it): a short «I» Silero missed before a hesitation is kept."""
        w = self.heard(w)
        t, fdb = w[0], self.fdb
        for rs, _ in self.regions:
            if rs < t - _REGION_BACK:
                continue
            if rs > t + _REGION_AHEAD:
                break
            if rs <= t:
                t = rs
            elif A.loud_share(fdb, t, rs, self.quiet) < _REGION_QUIET and (
                    rs < w[1] or A.loud_share(fdb, w[0], w[1], self.quiet) < _REGION_QUIET):
                t = rs
            break
        t = max(t, lower)
        if self.fdb.size:
            t = A.onset(self.fdb, t, max(w[1], t + 0.1), self.floor)
        return max(t, lower)

    def sound_end(self, w: list, limit: float) -> float:
        """Where word w stops being heard (Whisper's end is often late, sometimes early)."""
        if self.fdb.size == 0:
            return w[1]
        if self.fdb[_i(self.fdb, w[1])] > self.thr:
            return min(A.loud_run_edge(self.fdb, w[1], self.thr, +1), limit, w[1] + 0.3)
        end = _last_loud(self.fdb, w[0], w[1], self.thr)
        return end if end < w[1] else w[1]


def _can_merge(run: dict, u: dict, geo: _Clip, E: dict) -> bool:
    last = run["units"][-1]
    if last["file"] != u["file"] or u["s"] < last["e"] - 0.01 or u["s"] - last["e"] > E["merge_gap"]:
        return False
    keys = {_wkey(w) for x in run["units"] + [u] for w in x["words"]}
    return not any(last["e"] - 0.01 < (w[0] + w[1]) / 2 < u["s"] + 0.01 and _wkey(w) not in keys
                   for w in geo.words)


def _wkey(w: list) -> tuple:
    return (w[0], w[1], w[2])


def _fit_words(mine: list, a: float, b: float) -> list:
    """Words clipped to the piece [a, b]; a word Whisper gave no length (s == e) gets
    _MIN_WORD on screen, taken from the room around it, so its subtitle still shows."""
    out = [[max(w[0], a), min(w[1], b), w[2], w[3]] for w in mine]
    for i, w in enumerate(out):
        if w[1] - w[0] >= _MIN_WORD:
            continue
        nx = out[i + 1][0] if i + 1 < len(out) else b
        w[1] = max(w[1], min(w[0] + _MIN_WORD, nx, b))
        if w[1] - w[0] < _MIN_WORD:
            pv = out[i - 1][1] if i else a
            w[0] = min(w[0], max(w[1] - _MIN_WORD, pv, a))
    return [[round(w[0], 3), round(w[1], 3), w[2], w[3]] for w in out]


def _run_pieces(run: dict, geo: _Clip, E: dict) -> tuple:
    """One run of chosen words in one clip -> [(start, end, words)], pause notes.

    Fillers Whisper wrote («yyy», «eee») are not words of the piece: they get no subtitle,
    at an edge they are cut like any speech that is not ours, and between two words they
    count as part of the pause."""
    ws, seen = [], set()
    for u in run["units"]:
        flags = u.get("fill_w") or [0] * len(u["words"])
        for w, f in zip(u["words"], flags):
            if _wkey(w) not in seen:
                seen.add(_wkey(w))
                if not f:
                    ws.append(w)
    if not ws:
        return [], []
    spoken = {_wkey(w) for w in ws}
    others = [w for w in geo.words if _wkey(w) not in spoken]
    ws = sorted((geo.heard(w) for w in ws), key=lambda w: w[0])
    w0, wl = ws[0], ws[-1]
    fdb = geo.fdb

    # start: the real first sound minus the pad, never into speech that is not ours
    # (onset walks back through loud frames, which would be the previous word's)
    lo = 0.0
    before = [w for w in others if w[0] < w0[0]]
    if before:
        pw = before[-1]
        lo = min(_last_loud(fdb, pw[0], min(pw[1], w0[0]), geo.thr) + _OTHER_PAD, w0[0])
    on = geo.sound_start(w0, lower=lo)
    start = max(on - E["pad_before"], lo, 0.0)

    # end: a tail after the last word, up to the loud edge, never into the next speech
    le = wl[1]
    tail = le + E["pad_after"]
    if fdb.size:
        tail = max(tail, A.loud_run_edge(fdb, le, geo.thr, +1) + _TAIL_EXTRA)
    hi = geo.dur
    after = [w for w in others if w[0] > wl[0]]
    if after:
        nw = after[0]
        hi = min(hi, _first_loud(fdb, max(nw[0], le), max(nw[1], le), geo.thr) - _OTHER_PAD)
    end = min(tail, le + E["pad_after_max"], hi, geo.dur)
    end = max(end, min(le, geo.dur), start + 0.1)

    # pause cuts; speech between two of our words that is not ours (a retake request
    # inside a take we joined, a «yyy») goes out with the pause around it: a «yyy» only
    # when the whole stretch is long enough to cut, anything else always
    cuts = []
    for a, b in zip(ws, ws[1:]):
        ae = geo.sound_end(a, b[0])
        low, keep_after, must = ae, E["pause_keep_after"], False
        for f in others:
            if a[0] < f[0] and f[1] <= b[0] + 0.01:
                fs = _first_loud(fdb, f[0], f[1], geo.thr)
                low = max(low, min(_last_loud(fdb, f[0], f[1], geo.thr) + _OTHER_PAD, b[0]))
                keep_after = min(keep_after, max(_OTHER_PAD, fs - ae - _OTHER_PAD))
                must = must or not _is_filler(f[2])
        bs = geo.sound_start(b, lower=low)
        if bs - ae <= E["pause_cut"] and not must:
            continue
        ca = ae + keep_after
        head = E["pause_keep_before"]
        if fdb.size:
            b0 = A.loud_run_edge(fdb, bs - A.HOP * 1.5, geo.breath, -1)
            if b0 < bs - A.HOP * 2:
                head = min(E["breath_max"], max(head, bs - b0 + 0.03))
        cb = bs - head
        if low > ae:                        # never back into the speech we cut out
            cb = max(cb, low)
        ca, cb = _snap(fdb, ca), _snap(fdb, cb)
        if cb - ca >= _MIN_CUT:
            cuts.append((ca, cb, bs - ae, must))
    acc, cur = [], start
    for ca, cb, g, must in cuts:
        if ca > cur and (must or ca - cur >= E["piece_min"]):
            acc.append((ca, cb, g, must))
            cur = cb
    if acc and end - acc[-1][1] < E["piece_min"] and not acc[-1][3]:
        acc.pop()
    edges = [start] + [x for ca, cb, _, _ in acc for x in (ca, cb)] + [end]
    parts = []
    for a, b in zip(edges[0::2], edges[1::2]):
        mine = [w for w in ws if a <= (w[0] + w[1]) / 2 <= b]
        parts.append((round(a, 3), round(b, 3), _fit_words(mine, a, b)))
    # (a cut of speech that is not ours is logged by that unit's own line)
    notes = [(run["file"], ca, cb, g) for ca, cb, g, must in acc if not must]
    return parts, notes


def to_pieces(selection: list, clips: dict, units: list, notes: list | None = None) -> list:
    """Chosen attempts -> pieces of clips, in text order (the shared Piece schema).
    `notes`, when given a list, receives the pause cuts as (file, from, to, pause seconds)
    for decisions(), so a draft resumed with choose() + to_pieces() logs them too."""
    pieces, cut = _pieces(selection, clips, units)
    if notes is not None:
        notes.extend(cut)
    return pieces


def _pieces(selection: list, clips: dict, units: list) -> tuple:
    E = _E()
    by_id = {u["id"]: u for u in units}
    geos = {}
    runs = []
    for ent in selection or []:
        for u in sorted((by_id[x] for x in ent.get("units") or [] if x in by_id), key=_tkey):
            cs = (clips or {}).get(u["file"])
            if not isinstance(cs, dict):
                continue
            geo = geos.get(u["file"]) or geos.setdefault(u["file"], _Clip(cs))
            if runs and _can_merge(runs[-1], u, geo, E):
                runs[-1]["units"].append(u)
                if ent["group"] not in runs[-1]["groups"]:
                    runs[-1]["groups"].append(ent["group"])
            else:
                runs.append({"file": u["file"], "units": [u], "groups": [ent["group"]]})
    pieces, notes = [], []
    prev = None
    for run in runs:
        geo = geos[run["file"]]
        parts, cut = _run_pieces(run, geo, E)
        notes += cut
        for j, (a, b, ws) in enumerate(parts):
            if j:
                joint = "jump"
            elif prev is None or prev["file"] != run["file"]:
                joint = "clip"
            else:
                joint = "jump" if _time_next(prev, run, geo) else "take"
            pieces.append({"file": run["file"], "start": a, "end": b, "words": ws,
                           "text": " ".join(w[2] for w in ws), "joint": joint,
                           "groups": list(run["groups"]), "role": "talk", "audio": "clip"})
        prev = run
    return pieces, notes


def _time_next(prev: dict, run: dict, geo: _Clip) -> bool:
    """This run goes on from where the previous one stopped, with only a pause between."""
    pe = max(u["e"] for u in prev["units"])
    rs = min(u["s"] for u in run["units"])
    if rs < pe:
        return False
    return not any(pe + 0.01 < (w[0] + w[1]) / 2 < rs - 0.01 for w in geo.words)


# ----------------------------------------------------------------- script lookup
def _bag(text: str) -> set:
    t = str(text or "")
    if not W.is_cyrillic(t) and re.search(r"\d", t):
        try:
            t = W._pl().normalize(t)
        except Exception:  # noqa: BLE001
            pass
    return {x for x in W.tokens(_SPLIT_CHARS.sub(" ", t)) if sum(ch.isalpha() for ch in x) >= 4}


def match_script(heard_text: str, candidates) -> str | None:
    """Which stored text he was reading: the best candidate by content-word F1 (words of 4+
    letters), when it reaches EDIT["script_f1"]. The words are compared as sets: he says
    every sentence two or three times, and each retake must not count against the text
    (nor a sentence the script repeats in its favour)."""
    heard = _bag(heard_text)
    if not heard:
        return None
    best, best_f = None, 0.0
    for c in candidates or []:
        if not isinstance(c, str) or not c.strip():
            continue
        bag = _bag(c)
        if not bag:
            continue
        f = 2.0 * len(heard & bag) / (len(heard) + len(bag))
        if f > best_f:
            best, best_f = c, f
    return best if best is not None and best_f >= _E()["script_f1"] else None


# ----------------------------------------------------------------- all together
def _short(text: str, n: int = 50) -> str:
    t = W.strip_dashes(re.sub(r"\s+", " ", str(text or "")).strip())
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def _line(u: dict, why: str) -> str:
    return f"{u['file']} {u['s']:.1f}-{u['e']:.1f} с: {why} „{_short(u['text'])}”"


def decisions(units: list, groups: list, selection: list, notes=()) -> list:
    """What was left out and why, one Russian line each, for the job log."""
    by_id = {u["id"]: u for u in units}
    chosen = set()
    for ent in selection:
        for x in ent["units"]:
            if x in by_id:
                chosen |= _members(by_id[x], by_id)
    out = []
    for u in sorted((u for u in units if u.get("drop") and not u.get("gone")), key=_tkey):
        out.append((_tkey(u), _line(u, _WHY.get(u["drop"], "убрано"))))
    for g in groups:
        sc = g.get("scores") or {}
        for c in g["candidates"]:
            u = by_id.get(c)
            if u is None or _members(u, by_id) & chosen:
                continue
            if g.get("dropped"):
                why = _WHY["fragment"]
            elif g.get("repeat") in ("ask", "clips"):
                why = _WHY["repeat"]
            else:
                why = _WHY["broken"] if (sc.get(c) or {}).get("complete", 1) < 1 else _WHY["take"]
            out.append((_tkey(u), _line(u, why)))
    out.sort(key=lambda t: t[0])
    lines = [x for _, x in out]
    for f, a, b, g in notes:
        lines.append(f"{f} {a:.1f}-{b:.1f} с: вырезана пауза {g:.1f} с")
    return lines


def analyze(clips: dict, script: str | None = None, lang: str = "pl", answers: dict | None = None,
            extra_questions=()) -> dict:
    """The whole retake pass: {units, groups, pieces, questions, selection, decisions}
    (selection = choose()'s output, what a stored draft resumes from)."""
    units = build_units(clips)
    groups = build_groups(units, script, lang)
    score(groups, units, script)
    qs = questions(groups, extra_questions)
    sel = choose(groups, answers or {})
    pieces, notes = _pieces(sel, clips, units)
    return {"units": units, "groups": groups, "pieces": pieces, "questions": qs,
            "selection": sel, "decisions": decisions(units, groups, sel, notes)}
