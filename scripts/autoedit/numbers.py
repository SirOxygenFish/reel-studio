"""Numbers for the screen: spoken Polish number words become digits in the subtitles.

Whisper without a prompt writes what it hears as words («jeden przecinek czterdzieści
sześć procent»); the hand edit showed «1,46%». This module finds the runs of number
words, reads each run back with voice/tools/pl_normalize.py (the same reader the voice
side uses, so both agree on what a number is) and replaces the run with one word in
the display form the reference edit used:

    jeden przecinek czterdzieści sześć procent   -> 1,46%
    siedemdziesiąt trzy tysiące                  -> 73 | tysiące   (two words)
    pięć milionów maili                          -> 5 | milionów | maili
    sto prób                                     -> 100 | prób
    dwanaście tysięcy pięćset                    -> 12 500
    trzy próby, jednego dolara, pół miliona      -> unchanged (these read better as words)

Only a run that reads back to exactly ONE value is a number; anything else is shrunk
from the right until it does, so «sześćset siedemset» stays two numbers and a stray
«przecinek» or «i» at the end is never swallowed. Ordinals stay words, and so does a
cardinal that is the front of an ordinal («dwa tysiące dwudziestym szóstym»).

Pure: no files, no models. Only Polish is converted; Russian words pass unchanged.

The file name is the stdlib's «numbers». Inside the package that does not matter
(reel.numbers), but a process whose sys.path[0] is reel/ itself (`cd reel && python
-c ...`) would find this file for every `import numbers`, and numpy, fractions,
decimal and statistics would all break on it. The guard below hands the real stdlib
module over in that case. It stays here, not under another name, because the plan
and the other modules know this module as reel.numbers.
"""
from __future__ import annotations

import re

if __name__ == "numbers":
    # Imported as the top-level «numbers» (see the docstring): load the stdlib's own
    # numbers.py from the rest of sys.path and put it in sys.modules in our place; the
    # import system returns whatever sys.modules holds once this file has run.
    import importlib.machinery as _machinery
    import importlib.util as _util
    import os as _os
    import sys as _sys

    _here = _os.path.normcase(_os.path.dirname(_os.path.abspath(__file__)))
    _spec = _machinery.PathFinder.find_spec(
        "numbers", [p for p in _sys.path if _os.path.normcase(_os.path.abspath(p or ".")) != _here])
    if _spec is None or _spec.loader is None:
        raise ImportError("the standard library's numbers module was not found")
    _real = _util.module_from_spec(_spec)
    _sys.modules["numbers"] = _real
    _spec.loader.exec_module(_real)
else:
    from .words import _pl

NBSP = "\u00a0"
# Why a no-break space inside «12 500»: the chunker and the phrase lists split on plain
# spaces, so a number shown as one word must not contain one; libass draws it as a space.

_CARD_KINDS = ("z", "u", "t", "d", "h")          # pl_normalize._WORDS kinds of cardinals
_ORD_KINDS = ("ou", "ot", "od", "oh", "os")      # ... and of ordinals
_HALVES = ("pół", "półtora", "półtorej")
_PCT = frozenset(("procent", "procentów", "procenta", "procentach", "procentami", "procentom",
                  "procencie", "proc"))
# A small number joined to a number shown in digits by one of these is shown in digits
# too: «jeden albo dwa procent» -> «1 albo 2%», «od pięciu do dziesięciu tysięcy».
_LINKS = frozenset(("albo", "lub", "czy", "do"))

_LEAD = re.compile(r"^[^\w]*")
_TRAIL = re.compile(r"[^\w%]*$")
_DIGIT_WORD = re.compile(r"\d+(?:[.,]\d+)?")
_SPLIT_TAIL = re.compile(r"^[,\-–—]\d")           # Whisper's "1" + ",46%" / "1" + "-2"


# ----------------------------------------------------------------- tokens
def _parts(text) -> tuple[str, str, str]:
    """'„Sto,' -> ('„', 'sto', ','): leading punctuation, lowercased core, trailing punctuation."""
    t = str(text or "").strip()
    lead = _LEAD.match(t).group()
    rest = t[len(lead):]
    trail = _TRAIL.search(rest).group()
    core = rest[:len(rest) - len(trail)] if trail else rest
    return lead, core.lower(), trail


def _kind(core: str) -> str | None:
    """pl_normalize's kind of a lowercased core ("u", "s", "ou", ...), "half", or None."""
    if core in _HALVES:
        return "half"
    if not core.isalpha():
        return None
    got = _pl()._WORDS.get(core)
    return got[0] if got else None


def _singular_scales() -> frozenset:
    """«tysiąc», «miliona», ... : a scale noun that means 1000 / a million on its own.
    A plural one alone («tysiące ludzi», «miliony») means "thousands", not a number."""
    out = set()
    for _value, (sg, _pl_forms) in getattr(_pl(), "_SCALES", ()):
        out.update(sg.values())
    return frozenset(out)


def _value(core_tokens: list) -> list:
    try:
        return list(_pl().words_to_numbers(" ".join(core_tokens)))
    except Exception:  # noqa: BLE001 - a reader problem means "not a number", never a crash
        return []


# ----------------------------------------------------------------- spans
def number_spans(words: list, lang: str = "pl") -> list:
    """Runs of Polish number words: [(i0, i1, value, pct), ...], words[i0:i1] is the run.

    A run starts on a cardinal (or «pół/półtora/półtorej», or a singular scale noun),
    continues over cardinals, scale nouns, «przecinek» and «i» before «pół», and stops
    at any punctuation (the word carrying it may end the run). It must read back to one
    value, or it is shrunk from the right. A following «procent/procentów/procenta/
    proc.» belongs to the run and sets pct. Digits Whisper wrote are not runs.
    """
    if lang != "pl" or not words:
        return []
    parts = [_parts(w[2]) for w in words]
    kinds = [_kind(c) for _, c, _ in parts]
    singular = _singular_scales()
    n = len(words)

    def startable(k: int) -> bool:
        kd = kinds[k]
        return kd in _CARD_KINDS or kd == "half" or (kd == "s" and parts[k][1] in singular)

    def continues(k: int) -> bool:
        """May word k extend a run that reached word k-1?"""
        if parts[k - 1][2] or parts[k][0]:
            return False                      # punctuation between them ends the run
        kd, core = kinds[k], parts[k][1]
        if kd in _CARD_KINDS or kd in ("s", "half"):
            return True
        if core == "przecinek":
            return k + 1 < n and not parts[k][2] and kinds[k + 1] in _CARD_KINDS
        if core == "i":
            return k + 1 < n and not parts[k][2] and parts[k + 1][1] == "pół"
        return False

    out = []
    i = 0
    while i < n:
        if not startable(i):
            i += 1
            continue
        j = i
        while j + 1 < n and continues(j + 1):
            j += 1
        vals: list = []
        while j >= i:
            while j > i and parts[j][1] in ("przecinek", "i"):
                j -= 1
            vals = _value([p[1] for p in parts[i:j + 1]])
            if len(vals) == 1:
                break
            j -= 1
        if len(vals) != 1 or j < i:
            i += 1
            continue
        if j + 1 < n and kinds[j + 1] in _ORD_KINDS and not parts[j][2] and not parts[j + 1][0]:
            i = j + 2                         # the front of an ordinal: all of it stays words
            continue
        end, pct = j + 1, False
        if end < n and not parts[j][2] and not parts[end][0] and parts[end][1] in _PCT:
            end, pct = end + 1, True
        out.append((i, end, vals[0], pct))
        i = end
    return out


# ----------------------------------------------------------------- display
def _group(n: int) -> str:
    return f"{n:,}".replace(",", NBSP) if abs(n) >= 10000 else str(n)


def fmt_number(value) -> str:
    """1.46 -> "1,46", 2.5 -> "2,5", 100 -> "100", 2026 -> "2026", 12500 -> "12 500"."""
    v = float(value)
    if v.is_integer():
        return _group(int(v))
    s = repr(round(v, 9))
    if "e" in s or "." not in s:
        s = f"{v:.9f}".rstrip("0")
    ip, fp = s.split(".")
    sign = "-" if ip.startswith("-") else ""
    return sign + _group(abs(int(ip))) + "," + fp


def _in_cards(value, card_values) -> bool:
    for c in card_values or ():
        try:
            if abs(float(c) - float(value)) < 1e-9:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _kept_as_words(span_cores: list, span_kinds: list, value, pct: bool) -> bool:
    """Small numbers stay words («trzy próby», «jednego dolara», «pół roku», «tysiąc
    razy»): digits are for the numbers worth reading at a glance. So does «pół
    miliona» / «pół tysiąca»: Polish never writes «0,5 miliona»."""
    if pct:
        return False                          # a percentage is always a figure: «2%»
    if len(span_kinds) == 1 and span_kinds[0] in ("half", "s"):
        return True
    if len(span_kinds) == 2 and span_cores[0] == "pół" and span_kinds[1] == "s":
        return True
    v = float(value)
    return v.is_integer() and 0 <= v <= 9


def _merge_fragments(words: list, lang: str) -> list:
    """Whisper splits some numbers: "1" + ",46%" -> "1,46%", "1" + "–2" -> "1-2"; and
    in Polish a figure it wrote followed by «procent» is "46%"."""
    out: list = []
    for w in words:
        s, e, t = float(w[0]), float(w[1]), str(w[2]).strip()
        p = float(w[3]) if len(w) > 3 and isinstance(w[3], (int, float)) else 1.0
        prev = out[-1] if out else None
        if prev is not None and _SPLIT_TAIL.match(t) and re.search(r"\d$", prev[2]):
            tail = ("-" + t[1:]) if t[0] in "–—" else t
            out[-1] = [prev[0], e, prev[2] + tail, min(prev[3], p)]
            continue
        if prev is not None and lang == "pl":
            lead, core, trail = _parts(t)
            if core in _PCT and not lead and _DIGIT_WORD.fullmatch(prev[2]):
                out[-1] = [prev[0], e, prev[2] + "%" + trail, min(prev[3], p)]
                continue
        out.append([s, e, t, p])
    return out


def display_numbers(words: list, lang: str = "pl", card_values=()) -> list:
    """Words -> a new word list with each number run shown the way the reference edit did.

    Each run becomes ONE word [s of its first word, e of its last, display + the last
    word's trailing punctuation, min p]. A run ending on a scale noun with a front
    below 1000 keeps the noun as its own word («73» + «tysiące»), so the chunker can
    split them. Values 0-9, every «jeden/jedna/jedno» form, a lone «pół» or «tysiąc»
    and «pół miliona / pół tysiąca» stay words unless the value is in card_values
    (a card shows it, so the subtitle
    should match) or it is linked by «albo/lub/czy/do» to a number shown in digits.
    Words come back as [s, e, text, p]; lang other than "pl" only glues Whisper's split
    figures ("1" + ",46%").
    """
    ws = _merge_fragments(words or [], lang)
    spans = number_spans(ws, lang)
    if not spans:
        return ws
    parts = [_parts(w[2]) for w in ws]
    kinds = [_kind(c) for _, c, _ in parts]

    shown = []                                # per span: digits?
    for i0, i1, value, pct in spans:
        num_end = i1 - 1 if pct else i1
        digits = not _kept_as_words([p[1] for p in parts[i0:num_end]], kinds[i0:num_end], value, pct) \
            or _in_cards(value, card_values)
        shown.append(digits)

    def linked(a: tuple, b: tuple) -> bool:
        """Span a, one link word, then span b, with no punctuation in between."""
        k = a[1]
        return (b[0] == k + 1 and parts[k][1] in _LINKS and not parts[k][0] and not parts[k][2]
                and not parts[k - 1][2] and not parts[b[0]][0])

    changed = True
    while changed:
        changed = False
        for x in range(len(spans) - 1):
            a, b = spans[x], spans[x + 1]
            if shown[x] == shown[x + 1] or not linked(a, b):
                continue
            small = x if not shown[x] else x + 1
            sp = spans[small]
            if float(sp[2]).is_integer() and kinds[sp[0]] in _CARD_KINDS:
                shown[small] = True
                changed = True

    out: list = []
    k = 0
    for (i0, i1, value, pct), digits in zip(spans, shown):
        out.extend(list(w) for w in ws[k:i0])
        k = i1
        run = ws[i0:i1]
        if not digits:
            out.extend(list(w) for w in run)
            continue
        lead = parts[i0][0]
        trail = parts[i1 - 1][2]
        num_end = i1 - 1 if pct else i1
        # «73 tysiące», «5 milionów», «2,5 tysiąca»: the noun stays its own word. A front
        # below 1 (only «pół», shown in digits because a card asked for the value) would
        # read «0,5 miliona»: that one is written out in full, «500 000».
        if not pct and num_end - i0 >= 2 and kinds[num_end - 1] == "s":
            front = _value([p[1] for p in parts[i0:num_end - 1]])
            scale = _pl()._WORDS[parts[num_end - 1][1]][1]
            if len(front) == 1 and 1 <= float(front[0]) < 1000 \
                    and abs(float(front[0]) * scale - float(value)) < 1e-6 * max(1.0, float(value)):
                head = ws[i0:num_end - 1]
                out.append([head[0][0], head[-1][1], lead + fmt_number(front[0]),
                            min(w[3] for w in head)])
                out.append(list(ws[num_end - 1]))
                continue
        text = lead + fmt_number(value) + ("%" if pct else "") + trail
        out.append([run[0][0], run[-1][1], text, min(w[3] for w in run)])
    out.extend(list(w) for w in ws[k:])
    return out
