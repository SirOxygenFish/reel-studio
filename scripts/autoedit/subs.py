"""Subtitles: the hand edit's chunker, sizes and animated ASS file, as functions.

This is a line-by-line port of a hand-tuned reference script (make_ass.py v3), because its
look was approved by real viewers: short lines (1-3 words, up to 5 once small words are
moved), a line does not end on a small connecting word, a lone flashing word is glued to
the next line, the spoken word turns yellow and bumps to 110 %, each new line pops in
from 80 %.

Changes from the reference, all deliberate:
* a lone word ending a sentence (. ? ! …) is never glued to the next line;
* a small word moves to the next line only while that line stays at 4 words or
  fewer (the reference could stack them into a 6-word line when no phrases came);
* no two lines are ever on screen together, even on odd Whisper timings;
* timestamps are computed in whole centiseconds (the reference could print 0:00:60.00);
* word and title text lose { } and backslashes (ASS override syntax), and the title
  loses dashes (nothing we show has an en or em dash);
* the title's font size shrinks so every line fits (the reference fitted by hand).

Pure: no Flask, no ffmpeg. PIL is only used to measure text.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

import common as C

from . import config
from .numbers import display_numbers
from .words import clean_words, strip_dashes

# ----------------------------------------------------------------- word lists
# The reference SMALL set, verbatim: a line may not end on one of these.
SMALL_GOLD = frozenset({
    "i", "a", "w", "z", "na", "do", "o", "że", "to", "nie", "jak", "od", "po", "za", "się", "mu", "mi",
    "ten", "te", "bo", "ale", "co", "czy", "swój", "swoje", "swojego", "jest", "jeśli", "żeby", "który",
    "która", "czego", "tego", "ja", "ty", "może", "ile", "zanim", "by", "twoja", "twój", "nas", "mój",
    "moja", "mojego", "osób", "razy", "być", "bardziej", "jedyna", "tym", "brak", "taka"})
# ... plus the common prepositions and conjunctions that reel did not happen to use.
# Words a subtitle line must never END on when a model groups the words: prepositions,
# conjunctions and «nie» / «не», which belong with the word after them. Narrower than
# SMALL (which also holds pronouns and verbs the reference edit happened to move).
DANGLING = frozenset({
    "i", "a", "w", "we", "z", "ze", "na", "do", "o", "od", "po", "za", "ku", "przez", "dla", "bez",
    "pod", "nad", "przy", "u", "że", "bo", "ale", "albo", "lub", "czy", "oraz", "ani", "jeśli",
    "gdy", "kiedy", "aby", "żeby", "więc", "czyli", "niż", "nie",
    "и", "а", "но", "в", "во", "на", "с", "со", "к", "ко", "о", "об", "за", "по", "из", "от",
    "до", "для", "у", "что", "чтобы", "или", "не", "ни", "если", "когда"})

SMALL_PL = SMALL_GOLD | frozenset({
    "ze", "we", "ku", "przez", "dla", "bez", "pod", "nad", "przy", "u", "oraz", "lub", "ani", "czyli",
    "gdy", "kiedy", "gdzie", "aby", "więc"})
# The Russian reel's list (reference/make_ass.py) without «тратит» and «настоящий», which
# were words of that one video, not connecting words.
SMALL_EN = frozenset({
    "a", "an", "the", "and", "or", "but", "so", "of", "to", "in", "on", "at", "by", "for", "from", "with", "as", "is", "are",
    "was", "were", "be", "it", "its", "that", "this", "these", "those", "if", "than", "not", "no", "i", "you", "we", "they",
    "he", "she", "my", "your", "our", "their", "his", "her", "do", "does", "did", "can", "will", "would", "have", "has"})
SMALL_DE = frozenset({
    "der", "die", "das", "ein", "eine", "und", "oder", "aber", "in", "im", "an", "am", "auf", "mit", "für", "von", "zu", "zum",
    "zur", "ist", "sind", "nicht", "ich", "du", "wir", "sie", "es", "dass", "wenn", "als", "wie"})
SMALL_ES = frozenset({
    "el", "la", "los", "las", "un", "una", "y", "o", "pero", "de", "del", "a", "al", "en", "con", "por", "para", "que", "si",
    "no", "es", "son", "se", "te", "me", "lo", "le", "mi", "tu", "su", "como"})
SMALL_FR = frozenset({
    "le", "la", "les", "un", "une", "des", "et", "ou", "mais", "de", "du", "à", "au", "en", "dans", "sur", "avec", "pour", "que",
    "qui", "si", "ne", "pas", "est", "sont", "je", "tu", "il", "elle", "on", "nous", "vous", "ce", "se"})
SMALL_IT = frozenset({
    "il", "lo", "la", "i", "gli", "le", "un", "una", "e", "o", "ma", "di", "a", "da", "in", "con", "su", "per", "che", "se", "non",
    "è", "sono", "mi", "ti", "si", "ci"})
SMALL_PT = frozenset({
    "o", "a", "os", "as", "um", "uma", "e", "ou", "mas", "de", "do", "da", "em", "no", "na", "com", "por", "para", "que", "se",
    "não", "é", "são", "me", "te", "seu", "sua"})
SMALL_UK = frozenset({
    "і", "й", "та", "а", "але", "в", "у", "на", "з", "із", "до", "від", "для", "що", "щоб", "не", "ні", "це", "я", "ти", "ми", "ви",
    "як", "якщо", "коли", "по", "за", "про"})
SMALL_RU = frozenset({
    "у", "в", "во", "на", "и", "с", "со", "к", "ко", "о", "об", "а", "не", "за", "по", "из", "от", "до",
    "для", "что", "как", "то", "ты", "я", "мы", "он", "их", "им", "это", "кто", "ради", "чтобы", "более",
    "если", "когда", "которых", "которому", "твоей", "твоим", "твоими", "своих", "своим", "всё", "все",
    "твой", "под"})

# ----------------------------------------------------------------- reference constants
# These are the reference's own numbers; they shape the look, so they live here with
# the algorithm rather than in config.EDIT (nothing about them is tuned per reel).
BREAK_CHARS = 14        # a line is closed once its raw text is longer than this
MAX_WORDS = 3
SPLIT_CHARS = 18        # a non-phrase line longer than this loses its last word
SMALL_MOVE_CHARS = 20   # a SMALL word moves to the next line only if that stays this short
SMALL_MOVE_WORDS = 4    # ... and this few words (ours, not the reference's; see chunk())
LONE_CHARS = 24         # a lone word is glued to the next line only if this stays short
LONE_GAP = 0.45         # ... or when it would flash for less than this (start to start)
HOLD_GAP = 0.6          # a line stays up until the next one when the gap is shorter
HOLD_AFTER = 0.35       # ... otherwise it stays this long after its last word
LINE_GAP = 0.05         # a line ends this long before the next one starts
LEAD_IN = 0.05          # the first word of a line shows this early

MAXS, AVAIL = 112, 880  # subtitle font size cap and usable width (1080 - 2 x 100); configure() may change MAXS
TWO_LINES_BELOW = 96    # below this size a line is split in two, balanced
TITLE_SIZE, TITLE_MIN, TITLE_AVAIL = 128, 72, 980
YEL, WHT = "&H0076F1FF&", "&H00FFFFFF&"
STYLE = dict(C.DEFAULT_SUBS)
SMALL_BY_LANG = {"ru": SMALL_RU, "be": SMALL_RU, "uk": SMALL_UK, "pl": SMALL_PL, "en": SMALL_EN, "de": SMALL_DE, "es": SMALL_ES,
                 "fr": SMALL_FR, "it": SMALL_IT, "pt": SMALL_PT}


def configure(subs: dict) -> None:
    """the brand's subtitle style (colours, sizes, font); the defaults are the house look"""
    global MAXS, TITLE_SIZE, YEL, WHT
    STYLE.update(subs or {})
    MAXS, TITLE_SIZE = int(STYLE["max_size"]), int(STYLE["title_size"])
    YEL, WHT = C.ass_color(STYLE["active_color"]), C.ass_color(STYLE["color"])
    _font_file.cache_clear(); _ft.cache_clear()

_BREAK = re.compile(r"[.,!?:;]$")
_SENTENCE_END = re.compile(r"[.?!…]$")
_UNSAFE = re.compile(r"[{}\\]")


def clean(t: str) -> str:
    """Only . , ; : come off the end: ? and ! stay visible, they carry the tone."""
    return re.sub(r"[.,;:]+$", "", t)


def _safe(t) -> str:
    """Word text that cannot break the ASS line: no override braces, no backslash, no
    line breaks. The no-break space inside «12 500» is kept (it is not collapsed)."""
    return re.sub(r"[\r\n\t\v\f ]+", " ", _UNSAFE.sub("", str(t or ""))).strip(" \u00a0")


# ----------------------------------------------------------------- chunker
def _phrase_tokens(phrases) -> list:
    """Phrases as token lists. They are split on plain spaces only, because a number
    shown as one word keeps its no-break space («12 500»)."""
    out = []
    for p in phrases or ():
        toks = [clean(t).lower() for t in str(p).split(" ") if t.strip()]
        if toks:
            out.append(toks)
    return out


def chunk(words: list, phrases=(), small=SMALL_PL) -> list:
    """Words [[s, e, text, ...], ...] -> lines (lists of the words).

    The reference algorithm, step by step:
    1. a phrase hit is its own line;
    2. otherwise a line closes at punctuation, at 3 words or past 14 raw characters;
    3. a non-phrase line over 18 characters loses its last word to a line of its own;
    4. a line tries not to end on a SMALL word: the word moves to the next line when
       that line stays <= 20 characters and <= 4 words;
    5. a lone word is glued to the next line when it is SMALL or would flash for under
       0.45 s (<= 24 characters, the next line not a phrase), but never a word that
       ends a sentence.

    So a line has 1-3 words from the rules, up to 5 after steps 4 and 5 (the reference
    reel's own longest line, «Może mi się nie uda.», came out that way), and a phrase
    has whatever the phrase has. Two changes from the reference, both recorded in the
    test and neither changing a reference line: the sentence-end guard in step 5, and the
    4-word limit in step 4. Without that limit a rules-only line could pile up SMALL
    words to 6 («A może być i 100 prób.»); now it stops at «A może» + «być i 100 prób.».
    """
    words = [[w[0], w[1], str(w[2])] + list(w[3:]) for w in words or []]
    ph = _phrase_tokens(phrases)

    def key(c: list) -> list:
        return [clean(x[2]).lower() for x in c]

    def is_ph(c: list) -> bool:
        return key(c) in ph

    chunks: list = []
    cur: list = []
    i = 0
    while i < len(words):
        hit = next((p for p in ph if key(words[i:i + len(p)]) == p), None)
        if hit:
            if cur:
                chunks.append(cur)
                cur = []
            chunks.append(words[i:i + len(hit)])
            i += len(hit)
            continue
        w = words[i]
        i += 1
        cur.append(w)
        if _BREAK.search(w[2]) or len(cur) == MAX_WORDS or len(" ".join(x[2] for x in cur)) > BREAK_CHARS:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)

    fixed = []
    for c in chunks:
        if len(c) > 1 and not is_ph(c) and len(" ".join(x[2] for x in c)) > SPLIT_CHARS:
            fixed += [c[:-1], c[-1:]]
        else:
            fixed.append(c)
    chunks = fixed

    # don't end a line on a preposition / short connecting word
    changed = True
    while changed:
        changed = False
        for k in range(len(chunks) - 1):
            c = chunks[k]
            if len(c) > 1 and not is_ph(c) and c[-1][2].lower() in small \
                    and len(chunks[k + 1]) < SMALL_MOVE_WORDS \
                    and len(" ".join(x[2] for x in c[-1:] + chunks[k + 1])) <= SMALL_MOVE_CHARS:
                chunks[k + 1].insert(0, c.pop())
                changed = True

    # a lone short/flashing word is glued to the next line
    out: list = []
    for c in chunks:
        p = out[-1] if out else None
        if p and len(p) == 1 and not is_ph(c) and not _SENTENCE_END.search(p[0][2].rstrip()) \
                and (clean(p[0][2]).lower() in small or c[0][0] - p[0][0] < LONE_GAP) \
                and len(" ".join(clean(x[2]) for x in p + c)) <= LONE_CHARS:
            p += c
        else:
            out.append(c)
    return out


# ----------------------------------------------------------------- sizes
@lru_cache(maxsize=1)
def _font_file() -> tuple[str, str]:
    """(path, family name) of the subtitle font"""
    name, path = C.sub_font(STYLE)
    return path, name


@lru_cache(maxsize=1)
def _ft():
    return ImageFont.truetype(_font_file()[0], 100)


def font_name() -> str:
    return _font_file()[1]


def wpx(t: str, size: float) -> float:
    """Rendered width in px at an ASS font size (libass size = ascent + descent)."""
    return _ft().getlength(t) / 100 * size / 1.34


def layout(texts: list) -> tuple:
    """(font size, line-break index or None): as big as fits, else two balanced lines."""
    full = wpx(" ".join(texts), MAXS)
    if full <= 0:
        return MAXS, None
    size = min(MAXS, AVAIL * MAXS / full)
    if size >= TWO_LINES_BELOW or len(texts) < 2:
        return size, None
    w, k = min((max(wpx(" ".join(texts[:k]), MAXS), wpx(" ".join(texts[k:]), MAXS)), k)
               for k in range(1, len(texts)))
    return min(MAXS, AVAIL * MAXS / w), k


def title_layout(lines: list) -> int | None:
    """The Title style's font size: 128 when every line fits 980 px, else the largest
    whole size that fits, down to 72. None when even 72 is too wide (the caller should
    shorten the title; ass_document then draws it at 72). A string is split at \\N or
    newlines, the way ass_document reads a title."""
    if isinstance(lines, str):
        lines = _title_lines(lines)
    widest = max((wpx(str(t), TITLE_SIZE) for t in lines or () if str(t).strip()), default=0.0)
    if widest <= TITLE_AVAIL:
        return TITLE_SIZE
    size = int(TITLE_AVAIL * TITLE_SIZE / widest)
    return size if size >= TITLE_MIN else None


# ----------------------------------------------------------------- ASS
def ts(t: float) -> str:
    """h:mm:ss.cc from whole centiseconds, so 59.996 is 0:01:00.00, never 0:00:60.00.
    Rounded exactly like the reference's f"{t:.2f}" everywhere else."""
    try:
        t = max(float(t), 0.0)
    except (TypeError, ValueError):
        t = 0.0
    if t != t or t == float("inf"):
        t = 0.0
    cs = int(format(t, ".2f").replace(".", ""))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def _title_lines(title) -> list:
    if not title:
        return []
    if isinstance(title, (list, tuple)):
        raw = [str(x) for x in title]
    else:
        raw = re.split(r"\\N|\n", str(title))
    return [x for x in (_safe(strip_dashes(r)) for r in raw) if x]


def _header(lang: str) -> str:
    enc = 204 if lang in ("ru", "uk", "be") else 238 if lang in ("pl", "cs", "sk", "hu", "ro", "hr", "sl") else 1
    name = font_name()
    st = STYLE; c = C.ass_color
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,{name},{TITLE_SIZE},{c(st["title_color"])},{c(st["title_color"])},{c(st["title_outline_color"])},&H90000000,0,0,0,0,100,100,0,0,1,{st["title_outline"]},{st["title_shadow"]},8,50,50,{st["title_margin_v"]},{enc}
Style: Sub,{name},{MAXS},{c(st["color"])},{c(st["color"])},{c(st["outline_color"])},&H90000000,0,0,0,0,100,100,0,0,1,{st["outline"]},{st["shadow"]},2,60,60,{st["margin_v"]},{enc}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _starts(chunks: list) -> list:
    """Each word's start, made non-decreasing over the whole reel. Whisper now and then
    starts a word a little before the one it follows; drawn as is, that word's line
    would come up while the previous one is still on screen."""
    out, run = [], float("-inf")
    for c in chunks:
        row = []
        for w in c:
            run = max(run, float(w[0]))
            row.append(run)
        out.append(row)
    return out


def events(chunks: list, total: float, keywords=(), roles=()) -> list:
    """One Dialogue per word: the line with that word yellow, bumped to 110 %.
    keywords: words underlined on screen. roles: [[t0, t1], ...] spans of the second voice (skits), its lines get their own colour.

    Timing is the reference's, with one guarantee added: every event of a line ends
    by the line's end (cend), and cend is at or before the next line's first event,
    so two lines are never on screen together, even when a word starts less than
    0.05 s before the next line (the reference let the earlier word run over). On
    ordinary timings (every reference line) the clamps change nothing."""
    ev = []
    starts = _starts(chunks)
    for ci, c in enumerate(chunks):
        st = starts[ci]
        nxt = starts[ci + 1][0] if ci + 1 < len(chunks) else float(total)
        last_end = max(float(c[-1][1]), st[-1])
        cend = min(nxt if nxt - last_end < HOLD_GAP else last_end + HOLD_AFTER, nxt - LINE_GAP)
        # word k shows from bounds[k] to bounds[k + 1]; the first one LEAD_IN early
        bounds = [min(t - LEAD_IN if k == 0 else t, cend) for k, t in enumerate(st)] + [cend]
        texts = [clean(x[2]) for x in c]
        size, brk = layout(texts)
        base = C.ass_color(STYLE["second_voice_color"]) if any(a - 0.05 <= c[0][0] < b for a, b in roles) else WHT
        kw = {str(x).lower() for x in keywords}
        for wi, w in enumerate(c):
            s, e = bounds[wi], bounds[wi + 1]
            body = "" if base == WHT else "{\\c%s}" % base
            for k, t in enumerate(texts):
                if k:
                    body += r"\N" if k == brk else " "
                if t.lower() in kw:
                    t = r"{\u1}" + t + r"{\u0}"
                if k != wi:
                    body += t
                elif wi == 0:
                    body += "{\\c%s}%s{\\c%s}" % (YEL, t, base)   # line pops in, first word yellow
                else:
                    body += "{\\c%s\\t(0,90,\\fscx110\\fscy110)}%s{\\c%s\\fscx100\\fscy100}" % (YEL, t, base)
            pop = r"\fscx80\fscy80\t(0,100,\fscx100\fscy100)" if wi == 0 else ""
            ev.append(f"Dialogue: 1,{ts(s)},{ts(e)},Sub,,0,0,0,,{{\\fs{size:.0f}{pop}}}{body}")
    return ev


def ass_document(words: list, total: float, title=None, lang: str = "pl", phrases=(),
                 title_secs: float | None = None, small=None, keywords=(), roles=()) -> str:
    """The whole .ass file for the reel.

    words: reel-time words ready for the chunker (subtitle_words output). total: the
    reel's length. title: a string with \\N or newlines between lines, or a list of
    lines; None or empty means no title. phrases: word groups that must stay one line.
    title_secs defaults to config.EDIT["title_secs"]; small defaults to the language's
    list.
    """
    if small is None:
        small = SMALL_BY_LANG.get(lang, frozenset())
    secs = config.EDIT.get("title_secs", 7.0) if title_secs is None else float(title_secs)
    ws = []
    for w in words or []:
        t = _safe(w[2])
        if re.search(r"[\w%]", t):
            ws.append([float(w[0]), float(w[1]), t] + list(w[3:4]))
    head = _header(lang)
    lines = _title_lines(title)
    if lines:
        size = title_layout(lines) or TITLE_MIN
        fs = "" if size == TITLE_SIZE else f"\\fs{size}"
        text = r"{\fad(250,500)\fscx70\fscy70\t(0,300,\fscx100\fscy100)" + fs + "}" + r"\N".join(lines)
        head += f"Dialogue: 2,{ts(0)},{ts(min(secs, float(total)))},Title,,0,0,0,,{text}\n"
    return head + "\n".join(events(chunk(ws, phrases, small), float(total), keywords, roles)) + "\n"


def write_ass(path, text: str) -> None:
    """utf-8 with a BOM (libass and every player read it; the reference did the same)."""
    with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write(text)


# ----------------------------------------------------------------- LLM groups
def _split(t: str) -> list:
    return [x for x in str(t).split() if x]


def validate_groups(sentence_words: list, groups) -> list | None:
    """Accept an LLM's regrouping of ONE sentence only if it changed nothing but the
    grouping: the groups' tokens (clean(), lowercased) must equal the sentence's tokens
    exactly, in order. Each group holds whole words, at most 3 (4 when the line is at
    most 18 characters) and at most 22 characters. Returns the multi-word groups, in
    the sentence's own spelling, for chunk(phrases=...); None means use the rules only.

    sentence_words must be subtitle_words() output (one model.sentences() sentence of
    it), and the LLM must have been shown that same text: the comparison is exact, so
    «sto prób» against a sentence showing «100 prób» is rejected (and a phrase checked
    against raw words would pass here but never match in chunk()).
    """
    texts = [str(w[2]) if isinstance(w, (list, tuple)) else str(w) for w in sentence_words or []]
    wtoks: list = []                       # (token, index of the word it came from)
    for k, t in enumerate(texts):
        for part in _split(clean(t).lower()):
            wtoks.append((part, k))
    if not wtoks or not isinstance(groups, (list, tuple)) or not groups:
        return None
    gtoks: list = []
    bounds = []
    for g in groups:
        if isinstance(g, (list, tuple)):
            g = " ".join(str(x) for x in g)
        if not isinstance(g, str):
            return None
        toks = [x for x in (clean(y).lower() for y in _split(g)) if x]
        if not toks:
            return None
        bounds.append((len(gtoks), len(gtoks) + len(toks)))
        gtoks += toks
    if gtoks != [t for t, _ in wtoks]:
        return None
    phrases = []
    for a, b in bounds:
        if a > 0 and wtoks[a][1] == wtoks[a - 1][1]:
            return None                    # a group may not start inside a word
        idx = list(range(wtoks[a][1], wtoks[b - 1][1] + 1))
        if len(idx) < 2:
            continue
        shown = " ".join(clean(texts[k]) for k in idx)
        if len(idx) > 4 or (len(idx) == 4 and len(shown) > 18) or len(shown) > 22:
            return None
        if clean(texts[idx[-1]]).lower() in DANGLING and not _SENTENCE_END.search(texts[idx[-1]]):
            # «przestać za», «być i», «nic nie»: the model broke its own rule; forced
            # as a phrase, the line would end on a word that belongs to the next one,
            # so this spot is left to the rules (their SMALL move fixes exactly this)
            continue
        phrases.append(" ".join(clean(texts[k]).lower() for k in idx))
    return phrases


# ----------------------------------------------------------------- words in
def _clean(words: list, lang: str, echo: float) -> list:
    """words.clean_words, except that a dropped phantom echo hands its sentence end
    (. ? ! …) to the word it repeated. Whisper's echo often carries the only full stop
    of the sentence («46%.» after «czterdzieści sześć procent», «tak.» after «Tak»);
    lost with the echo, the next sentence would be glued onto the same line and
    model.sentences() would see one sentence where there were two."""
    split = clean_words(words, lang, echo_max=float("-inf"))   # quotes and 'siebie:"A' only
    kept = clean_words(split, lang, echo_max=echo)              # ... then the echoes go
    out: list = []
    j = 0
    for w in split:
        if j < len(kept) and kept[j][2] == w[2] and kept[j][0] == w[0]:
            out.append(list(kept[j]))
            j += 1
            continue
        end = re.search(r"[.?!…]+$", str(w[2]))
        if out and end and not _SENTENCE_END.search(out[-1][2]):
            out[-1][2] = clean(out[-1][2]) + end.group()        # «tak,» + «tak.» -> «tak.»
    return out


def subtitle_words(words_tl: list, lang: str = "pl", card_values=(),
                   echo_max: float | None = None) -> list:
    """Reel-time Whisper words -> words ready for chunk(): phantom echoes and quote
    marks off (clean_words, an echo's full stop kept), numbers as digits
    (display_numbers), no dashes.

    These are the words everything text-shaped downstream must use, in this order:
    subtitle_words -> model.sentences -> the LLM's line groups -> validate_groups ->
    chunk / ass_document. The LLM must see these display words («100 prób»), not the
    raw ones («sto prób»): chunk() matches phrases against these texts, and a group
    written over the raw words never matches and is silently ignored."""
    # echo_max=float("-inf") for a voice-over take: its words are the exact text he typed,
    # so «bardzo, bardzo» or «nie, nie, nie» is really said twice
    echo = config.EDIT.get("echo_max", 0.25) if echo_max is None else echo_max
    ws = _clean(words_tl, lang, echo)
    # once more after the digits: a phantom «46%» Whisper added after «czterdzieści sześć
    # procent» only repeats the word before it once both are digits
    ws = _clean(display_numbers(ws, lang, card_values), lang, echo)
    out = []
    for w in ws:
        t = re.sub(r"(?<=\d)[–—](?=\d)", "-", str(w[2]))    # «1–2» is a range: keep a hyphen
        t = strip_dashes(t)
        if t:
            out.append([w[0], w[1], t, w[3] if len(w) > 3 else 1.0])
    return out
