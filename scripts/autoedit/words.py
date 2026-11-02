"""Words: comparing what he said, cleaning Whisper's output, numbers for the screen.

Tokens are compared lowercased with punctuation removed; number words and digits are
compared by value ("sto" == "100"). The Polish number speller/reader lives in
voice/tools/pl_normalize.py (standard library only) and is loaded by file path under
the same sys.modules key section4_api uses, so both share one copy.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import threading
from difflib import SequenceMatcher
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_lock = threading.Lock()


def _load(name: str):
    with _lock:
        mod = sys.modules.get(name)
        if mod is None:
            spec = importlib.util.spec_from_file_location(name, _TOOLS / f"{name}.py")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            try:
                spec.loader.exec_module(mod)
            except BaseException:
                sys.modules.pop(name, None)
                raise
        return mod


def _pl():
    """pl_normalize.py next to this file"""
    return _load("pl_normalize")


def _st():
    """speech_text.py next to this file"""
    return _load("speech_text")


# ----------------------------------------------------------------- tokens
_TOKEN = re.compile(r"[^\W_]+(?:[.,][0-9]+)*%?|[0-9]+(?:[ .,][0-9]{3})*(?:,[0-9]+)?%?", re.UNICODE)
_NON_WORD = re.compile(r"[^\w%]+", re.UNICODE)


def norm_token(t: str) -> str:
    """"Tak." -> "tak", "1,46%" -> "1,46%" (digits keep their comma), "„A" -> "a"."""
    t = str(t or "").strip().lower().replace("ё", "е")
    if re.search(r"\d", t):
        t = re.sub(r"[^\d,.%]", "", t).strip(".,")
        return t
    return _NON_WORD.sub("", t)


def tokens(text) -> list:
    """Normalised tokens of a string or of a word list ([[s, e, text, ...], ...])."""
    if isinstance(text, (list, tuple)):
        items = [w[2] if isinstance(w, (list, tuple)) else w for w in text]
        return [t for t in (norm_token(x) for x in items) if t]
    return [t for t in (norm_token(x) for x in str(text or "").split()) if t]


_VALUE_CACHE: dict = {}


def _value(tok: str):
    """A single token's numeric value ("sto" -> 100, "100" -> 100), else None."""
    if tok in _VALUE_CACHE:
        return _VALUE_CACHE[tok]
    v = None
    if re.fullmatch(r"\d+(?:,\d+)?", tok):
        v = float(tok.replace(",", "."))
    elif tok.isalpha():
        try:
            words = getattr(_pl(), "_WORDS", {})
            if tok in words:
                got = _pl().words_to_numbers(tok)
                v = float(got[0]) if len(got) == 1 else None
        except Exception:  # noqa: BLE001 - a number reader problem is never fatal here
            v = None
    _VALUE_CACHE[tok] = v
    return v


def tok_sim(a: str, b: str) -> float:
    """0..1 similarity of two normalised tokens; number words equal their digits."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    va, vb = _value(a.rstrip("%")), _value(b.rstrip("%"))
    if va is not None and vb is not None:
        return 1.0 if abs(va - vb) < 1e-9 else 0.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def seq_sim(a, b) -> float:
    """0..1 similarity of two token sequences (strings or word lists): exact tokens."""
    ta, tb = (a if isinstance(a, list) and (not a or isinstance(a[0], str)) else tokens(a)), \
             (b if isinstance(b, list) and (not b or isinstance(b[0], str)) else tokens(b))
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return SequenceMatcher(None, ta, tb, autojunk=False).ratio()


def _lcs_fuzzy(ta: list, tb: list, thr: float = 0.8) -> int:
    """Length of the longest common subsequence, tokens matching when tok_sim >= thr."""
    if not ta or not tb:
        return 0
    prev = [0] * (len(tb) + 1)
    for a in ta:
        cur = [0] * (len(tb) + 1)
        for j, b in enumerate(tb, 1):
            cur[j] = prev[j - 1] + 1 if tok_sim(a, b) >= thr else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1]


def prefix_match(a, b, thr: float = 0.8) -> float:
    """How much of A is the start of B (0..1): A's tokens against B's first len(A)."""
    ta, tb = (a if isinstance(a, list) and (not a or isinstance(a[0], str)) else tokens(a)), \
             (b if isinstance(b, list) and (not b or isinstance(b[0], str)) else tokens(b))
    if not ta or len(ta) > len(tb):
        return 0.0
    return sum(1 for x, y in zip(ta, tb) if tok_sim(x, y) >= thr) / len(ta)


def contains(a, b, thr: float = 0.8) -> float:
    """How much of A appears, in order, inside B (0..1)."""
    ta, tb = (a if isinstance(a, list) and (not a or isinstance(a[0], str)) else tokens(a)), \
             (b if isinstance(b, list) and (not b or isinstance(b[0], str)) else tokens(b))
    if not ta:
        return 0.0
    return _lcs_fuzzy(ta, tb, thr) / len(ta)


# ----------------------------------------------------------------- cleaning
_QUOTES = "\"„”“«»"


def clean_words(words: list, lang: str = "pl", echo_max: float = 0.25,
                echo_gap: float = 0.05) -> list:
    """Whisper words [[s, e, text, p?], ...] -> the same, cleaned like the reference edit:

    * a token like 'siebie:"A' is split into 'siebie' + 'A' (time shared evenly) and
      quote marks are dropped;
    * a phantom echo is dropped: shorter than echo_max and the same word as the one
      before it, or «procent» right after a word with %.
    """
    raw = []
    for w in words or []:
        s0, e0, t = float(w[0]), float(w[1]), str(w[2])
        p = float(w[3]) if len(w) > 3 else 1.0
        parts = [x for x in re.split(r'(?<=:)[' + _QUOTES + ']', t.strip()) if x]
        for k, part in enumerate(parts):
            d = (e0 - s0) / len(parts)
            text = re.sub("[" + _QUOTES + "]", "", part).strip()
            if len(parts) > 1:
                text = text.rstrip(":")
            if text:
                raw.append([s0 + k * d, s0 + (k + 1) * d, text, p])
    out = []
    for w in raw:
        # only right after the word it repeats: «nie.» … 2 s … «Nie musisz» is two words,
        # and after words_on_timeline two pieces' words sit side by side
        if out and w[1] - w[0] < echo_max and w[0] - out[-1][1] <= echo_gap:
            a, b = norm_token(w[2]), norm_token(out[-1][2])
            if (a and a == b) or (a in ("procent", "procentów", "procenta", "процентов")
                                  and "%" in out[-1][2]):
                continue
        out.append(w)
    return out


_DASH_SPACED = re.compile(r"\s+[–—]\s+")
_DASH_ANY = re.compile(r"[–—]")


def strip_dashes(text: str) -> str:
    """No en or em dashes in anything shown: " – " becomes ", ", a lone one goes."""
    t = _DASH_SPACED.sub(", ", str(text or ""))
    t = _DASH_ANY.sub(" ", t)
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r",\s*,", ",", t)
    return re.sub(r"[ \t]{2,}", " ", t).strip()


_CYR = re.compile(r"[А-Яа-яЁё]")


def is_cyrillic(text: str) -> bool:
    letters = re.findall(r"[^\W\d_]", str(text or ""))
    if not letters:
        return False
    return sum(1 for c in letters if _CYR.match(c)) / len(letters) > 0.5
