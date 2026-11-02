"""The text side of a take: what is read aloud, and how it is cut for XTTS.

This replaces synth.py's clean_for_speech / split_sentences / plan_chunks for
the v2 engine (synth.py itself stays as it is: it is live). On the speaker's
real takes the old text side lost the listener in three ways:

* Reels scripts put a blank line after every line. Each line became a
  paragraph with 0.8 s of silence on top of the model's own, so the take
  "stopped for prolonged periods". Such a script is recognised here, and a
  single blank line in it is only a sentence break (see _line_mode).
* A short last sentence («Bez mitów.») stayed a chunk of its own, and XTTS
  pads a tiny chunk with silence or babble. Short pieces now merge forward
  and backward, and a short paragraph joins its neighbour.
* Part labels («Hak:», «CTA:»), stage directions («(pauza)», «[B-roll]») and
  «---» lines were read aloud or turned into pauses nobody wrote.

Each chunk ends in . ! or ?, carries no quotes, dashes or brackets (a dash
becomes the comma a speaker makes there), and says what kind of boundary
follows it, so the engine chooses the pause and not the text.

Standard library only: the app's .venv imports it too.
"""
from __future__ import annotations

import math
import re
import sys
import unicodedata

MAX_CHARS = 180         # longer input makes XTTS drop words
MIN_CHARS = 60          # shorter input makes it pad and babble
MIN_CUT = 40            # no piece cut out of a long sentence is shorter
SHORT_PARAGRAPH = 40    # a paragraph under this joins a neighbour

_LOWER = "a-zà-öø-ÿąćęłńóśźż"
_LOWER_START = re.compile("[" + _LOWER + "]")
_ALNUM = re.compile(r"[^\W_]")
_LETTER = re.compile(r"[^\W\d_]")
_CYR = re.compile("[\u0400-\u04FF]")

# Part labels a script carries: «Hak:», «HOOK -», «[CTA]», «Scena 2:», «Хук:».
# The chat-side twin is S4_LABEL_RE in static/section4.js; the two lists are
# the same, keep them so. The server applies it again because it also gets
# text typed straight into «voice-over». «Krok 1:» and «Punkt 1:» are not labels: «punkt
# pierwszy: zapisuj» is how he talks, so they are read.
_LABEL_WORDS = (
    r"część\s+główna|wezwanie\s+do\s+działania|call\s+to\s+action"
    r"|hak|hook|haczyk|wstęp|wprowadzenie|rozwinięcie|zakończenie|puenta"
    r"|podsumowanie|cta|scenariusz|tekst|lektor|voice-?over|narracja|intro|outro"
    r"|(?:część|scena|ujęcie|slajd|kadr)\s*#?\s*(?:\d+|[ivx]+(?![^\W\d_]))"
    r"|хук|вступление|основная\s+часть|призыв(?:\s+к\s+действию)?|концовка"
    r"|сценарий|текст|(?:часть|сцена|слайд)\s*#?\s*\d+"
)
# a hyphen separates only when a space touches it: «CTA - napisz», not «CTA-owy»
_LABEL_SEP = r"(?:[:.–—]|(?<=\s)-|-(?=\s|$))"
LABEL_RE = re.compile(
    r"^\s*(?:"
    # «[CTA]» or «(Hak)»: the brackets alone mark it, a separator is optional
    r"[\[(]\s*(?:" + _LABEL_WORDS + r")(?:\s*#?\d+)?\s*[\])]\s*" + _LABEL_SEP + r"?"
    # «Hak:», «Ujęcie 1 (0-3 s):», or the label alone on its line
    r"|(?:" + _LABEL_WORDS + r")(?:\s*#?\d+)?(?:\s*\([^)]*\))?\s*(?:" + _LABEL_SEP + r"|$)"
    r")\s*",
    re.IGNORECASE)

# Latin-script stage directions nobody says aloud. A bracket that starts with
# one is not read, unless it reads as his own sentence (see _is_stage).
STAGE_SURE = (
    "pauza", "pause", "oddech", "wdech", "wydech", "szeptem", "do kamery",
    "zbliżenie", "cięcie", "b-roll", "broll", "tekst na ekranie", "przejście",
    "ujęcie",
    # not in the first list, but AI-written scripts use them
    "uśmiecha się", "śmieje się",
)
# Directions that are also words he says. A bracket that started with one was
# dropped whole: «Zapisz się (pewnie to znasz) i działaj» came out as «Zapisz
# się i działaj», with no warning anywhere. Such a bracket is a direction only
# when helper words alone stand around the word: «(spokojnie)», «(mówi
# spokojnie)», «(z uśmiechem)». «(pokazuje telefon)» is then read aloud, the
# safer mistake than dropping his words.
STAGE_ALSO_SAID = (
    "uśmiech", "śmiech", "muzyka", "cisza", "spokojnie", "poważnie", "radośnie",
    "ciepło", "pewnie", "głośniej", "ciszej", "wolniej", "szybciej", "napis", "kadr",
    "patrzy", "pokazuje", "wskazuje", "dźwięk",
)
STAGE_WORDS = STAGE_SURE + STAGE_ALSO_SAID
# Inflected forms a bracket uses: «(z uśmiechem)», «(krótka pauza)», «(muzyką w
# tle)». «napis» must not catch «napisz»: «(napisz do mnie)» is a call to action.
_STAGE_FORMS = {
    "pauza": r"pauz[aęyą]", "uśmiech": r"uśmiech(?:em|u|y)?",
    "śmiech": r"śmiech(?:em|u|y)?", "muzyka": r"muzyk[aąię]|muzyce",
    "cisza": r"cisz[aęyą]", "oddech": r"oddech(?:em|u|y)?",
    "wdech": r"wdech(?:em|u|y)?", "wydech": r"wydech(?:em|u|y)?",
    "zbliżenie": r"zbliżeni[ea]", "cięcie": r"cięci[ea]", "b-roll": r"b[-\s]?roll",
    "napis": r"napis(?:em|u|y)?", "przejście": r"przejści[ea]",
    "ujęcie": r"ujęci[ea]", "kadr": r"kadr(?:u|ze|y)?", "dźwięk": r"dźwięk(?:i|u|iem)?",
}


def _stage_terms(words) -> str:
    return "|".join(_STAGE_FORMS.get(w, re.escape(w).replace(r"\ ", r"\s+"))
                    for w in sorted(words, key=len, reverse=True))


_STAGE_TERM = _stage_terms(STAGE_WORDS)
_STAGE_SURE_START = re.compile(r"^\s*(?:" + _stage_terms(STAGE_SURE) + r")(?![^\W\d_])",
                               re.IGNORECASE)
_STAGE_ANY = re.compile(r"(?<![^\W\d_])(?:" + _STAGE_TERM + r")(?![^\W\d_])",
                        re.IGNORECASE)
# words that may sit around a stage word in a direction: «(mówi spokojnie)»
_STAGE_GLUE = frozenset("""
    i a z ze w we na do po przy nad pod przed przez za od o u dla bez
    bardzo trochę lekko lekki lekka lekkie krótka
    krótki krótko krótkie dłuższa dłuższy długa długi chwila chwilę mówi mów
    mówię powoli cicho głośno tonem głosem patrząc patrzę kamerę kamery kamera
    kamerą obiektyw tle tło s sek sekunda sekundy sekund
""".split())
# A whole line that only directs the camera: «B-roll: kawa», «Napis: START».
# Deliberately short: «Efekt: po miesiącu masz nawyk» is something he says.
_STAGE_LINE = re.compile(
    r"^\s*(?:b[-\s]?roll|napis|tekst\s+na\s+ekranie|przejście|ujęcie|kadr|zbliżenie"
    r"|cięcie|muzyka|tło|pauza|pause)(?:\s*:.*|\s*[.!]?\s*)$", re.IGNORECASE)

_EMOJI = re.compile("[" + "".join(f"{chr(a)}-{chr(b)}" for a, b in (
    (0x1F000, 0x1FAFF),   # pictographs, flags, skin tones
    (0x2600, 0x27BF),     # misc symbols, dingbats
    (0x2190, 0x21FF),     # arrows
    (0x2300, 0x23FF),     # ⏰ ⏳ ⏩
    (0x25A0, 0x25FF),     # ▶ ◀ ▪
    (0x2B00, 0x2BFF),
    (0xE0020, 0xE007F),   # tag letters in subdivision flags
)) + "\uFE0E\uFE0F\u200D\u20E3©®™" + "]")   # 20E3: keycap in 1️⃣
# «Krok 1 → krok 2»: an arrow is a pause (_ARROW), but _EMOJI takes the arrow
# blocks first and the take ran on, «Krok jeden krok dwa». So they become «->»
# before it, which the normalizer leaves alone. «⟶» is in neither block and
# reached XTTS, which says its [UNK] as noise.
_ARROW_SIGN = re.compile("\\s*[\u2190\u2192\u21D0\u21D2\u27F5\u27F6\u27F8\u27F9"
                         "\u27A1\u2794\u279C]\uFE0F?\\s*")
# «1️⃣ Zapisuj» is a list marker; mid-line «3️⃣ zasady» keeps its digit
_KEYCAP_LEAD = re.compile("^\\s*[0-9#*]\uFE0F?\u20E3\\s*")
# Zero-width and bidi marks, and the blanks U+2800 / U+3164: Instagram drops
# empty lines, so captions keep their spacing with those (E000/E001 are ours,
# see _HELD)
_INVISIBLE = re.compile("[\u200B-\u200F\u202A-\u202E\u2060-\u2064\uFEFF\u00AD\u2800"
                        "\u3164\u115F\u1160\uFFA0\u180E\uE000\uE001]")
# a line that is only one of those, or a lone «.», is a blank line, not «---»
_SPACER = re.compile(r"\s*\.?\s*")
_MD_LINK = re.compile(r"\[([^\[\]]*)\]\(\s*(?:https?://|www\.)[^)]*\)")
# the full stop after a link ends the sentence: «Wejdź na x.pl. Potem…» lost
# it, and «…na Potem napisz» ran on
_URL = re.compile(r"(?:https?://|(?<![\w.])www\.)\S*?(?=[.,;:!?…)\]»”\"']*(?:\s|$))")
_HASHTAG = re.compile(r"(?<!\w)#[^\W\d_]\w*")
_MENTION = re.compile(r"(?<!\w)@\w+(?:\.\w+)*")
# «<3», «<3!» are a heart; «<3 miesiące» is «less than three months»
_EMOTICON = re.compile(
    r"(?:(?<!\S)(?:[:;]-?[)(DPp]+|[xX]D+)(?!\S)|<3+(?!\d)(?!\s*[" + _LOWER + r"0-9]))")
# «<3 miesiące», «>50%»: the model has no sound for < and >. «> 5» with a space
# is a markdown quote, so «>» needs the digit right after it.
_LESS = re.compile(r"(?<![<>=-])<\s?(?=\d)")
_MORE = re.compile(r"(?<![<>=-])>(?=\d)")
# «(0–3 s)», «(3-10 sek.)», «(0:00–0:03)»: where the words fall in the video.
# A timecode stays under 4 minutes: «(18:00–20:00)» is a time he says.
_TC = r"(?:0?[0-3]:[0-5]\d|\d{1,3})"
_TIMING = re.compile(
    r"\s*" + _TC + r"\s*(?:s|sek\.?)?\s*[-–—]\s*" + _TC
    + r"\s*(?:s|sek\.?|sekund[ay]?)?\s*", re.IGNORECASE)
_HELD = re.compile("\uE000(\\d+)\uE001")
_SQUARE = re.compile(r"\[[^\[\]]*\]")
_PAREN = re.compile(r"\(([^()]*)\)")
# the punctuation after a run stays: it belongs to the Polish sentence around it
_CYR_RUN = re.compile("[\u0400-\u04FF]+(?:[\\s\\-.,:;!?…]*[\u0400-\u04FF]+)*")
# Nouns an ordinal agrees with at the start of a line: «1. krok» is «pierwszy
# krok», «3. miejsce» «trzecie miejsce». The genitive months keep a date's day
# («15. sierpnia jadę»: pl_normalize reads the day).
_ORD_NOUNS = (
    "krok kroku etap etapu etapie miejsce miejsca miejscu dzień dnia dniu tydzień "
    "tygodnia tygodniu miesiąc miesiąca miesiącu rok roku raz punkt punktu zasada "
    "zasady sposób sposobu błąd błędu powód powodu rzecz rada wskazówka lekcja "
    "lekcji część części rozdział rozdziału odcinek odcinka edycja edycji runda "
    "rundy poziom poziomu sezon sezonu klasa klasy liga ligi pytanie zadanie tura "
    "faza fazy seria serii kwartał kwartału semestr semestru piętro piętrze "
    "stopień stopnia wersja wersji cel mit nawyk problem trik sekret filar element "
    "godzina minuta sekunda wiek wieku urodziny rocznica "
    "stycznia lutego marca kwietnia maja czerwca lipca sierpnia września "
    "października listopada grudnia"
).split()
# Leading list and quote marks. «N.» at the start of a line is a list mark and
# goes: «1. Zapisuj», «1. zapisuj cele», «1. 10 minut ruchu». Kept before a
# lowercase word or a digit, it was read «pierwszy zapisuj cele» and «jeden.
# dziesięć minut», which neither synth_v1 nor the old chat cleaner did. Only
# before a noun from _ORD_NOUNS is it an ordinal, left for the normalizer. A
# digit must come after a space: «1.5 kg» is a number. «1)» and «a)» are
# lists always. The chat-side twin is s4CleanLine in static/section4.js.
_BULLET = re.compile(
    r"^\s*(?:#{1,6}\s+|>+\s*|[-=]>\s*|[-*+•·▪–—]+\s+|\d{1,2}\)\s*|[a-zA-Z]\)\s+"
    r"|\d{1,2}\.\s+(?=\d)|\d{1,2}\.\s*(?=[^" + _LOWER + r"0-9\s])"
    r"|\d{1,2}\.\s*(?=[" + _LOWER + r"])(?!(?:" + "|".join(_ORD_NOUNS)
    + r")(?![^\W\d_]))|\d{1,2}\.\s*$)")

# Polish abbreviations whose dot must not end a sentence: «ok. 500 zł», «np.
# Kowalski» used to become two chunks with a full stop's fall in pitch between.
# «itd.»/«itp.» are left out: before a capital they do end the sentence.
# «ok.» only before a number: «Jest ok. Teraz zaczynamy.» is two sentences.
_ABBREV = re.compile(
    r"(?<![\w.])(np|tzn|tj|m\.in|tzw|ul|godz|nr|str|tel|prof|dr|mgr|inż|ds|ws"
    r"|wg|zob|św|ang|ok(?=\.\s+\d))\.(?=\s)", re.IGNORECASE)
_DOT_MARK = "\u2024"    # one dot leader: a stand-in the splitter ignores
# A sentence ends at . ! ? … (also before a closing quote), but not before a
# lowercase word: «3. miejsce», «tys. zł» and «I wtedy… cisza» go on.
_SENT_SPLIT = re.compile(
    r"(?:(?<=[.!?…])|(?<=[.!?…][\"'”»«)]))\s+(?=\S)(?![" + _LOWER + r"])")

_QUOTES = re.compile("[\"„”“«»‹›‚‛‟]")
# an apostrophe inside a word stays («McDonald's»), one used as a quote goes
_APOS = re.compile(r"['’‘`](?![^\W\d_])|(?<![^\W\d_])['’‘`]")
_DASH = re.compile(r"\s*[–—―‒]+\s*")
# «A -> B»: the arrow is a pause, and the model has no token for > or <
_ARROW = re.compile(r"\s*(?:-+>|=+>|<-+|<=+|[→⇒←⇐⟵⟶⟸⟹➡➔➜]\uFE0F?)\s*")
_HYPHEN_DASH = re.compile(r"(?:(?<=\s)|^)-+(?=\s|$)|(?<=[^\W\d_])-{2,}(?=[^\W\d_])")

# A long sentence cut at a space must not end on a word that leans on the next
# one («…i» / «tak dalej», «pięć» / «tysięcy», «nie» / «wiem»), and it reads
# best when the second half opens with a conjunction.
_NO_END = frozenset("""
    w we z ze o u i a na do od po za przy dla bez pod nad przed przez między ku
    że żeby aby by oraz lub albo czy ale bo więc gdy kiedy jeśli jeżeli nie jak
    co który która które którego której których którzy którym którą to ten ta
    tę tym tego tej tych mój moja moje mojego twój twoja twoje twojego swój
    swoja swoje swojego jego jej ich pół półtora
""".split())
_NUMBER_WORD = re.compile(
    r"^(?:jed(?:en|na|no|nego|nej)|dw(?:a|ie|óch|u|oma)|trz(?:y|ech)|czter(?:y|ech)"
    r"|pięć|sześć|siedem|osiem|dziewięć|dziesięć|pięciu|sześciu|siedmiu|ośmiu"
    r"|dziewięciu|dziesięciu|\w+nast(?:e|u|ych)|\w+naście|\w+dzieścia|\w+dzieści"
    r"|\w+dziestu|\w+dziesiąt|\w+dziesięciu|\w*set|\w*stu|sto|dwieście"
    r"|tysi[ąę]c\w*|milion\w*|miliard\w*)$")
_NO_START = frozenset("się by bym byś byśmy byście".split())
_CONJ = frozenset("""
    ale bo że żeby aby a i oraz lub albo czy gdy kiedy jeśli jeżeli który która
    które którego której których którzy którym którą więc dlatego ponieważ
    gdyż choć chociaż zanim niż aż jak gdzie dopóki skoro
""".split())
_CONJ_BONUS = 25        # characters of imbalance a conjunction is worth


# Text pasted from a Mac or a PDF can carry «ą» as «a» plus a combining
# ogonek: XTTS has no token for the mark ([UNK] is noise), and «Część 1:»
# would not look like a label. The Unicode hyphen and the modifier
# apostrophe become the plain ones the model knows.
_LOOKALIKE = str.maketrans({"\u2010": "-", "\u2011": "-", "\u02BC": "'",
                            "\u2032": "'", "\u2033": '"'})


def _nfc(t: str) -> str:
    return unicodedata.normalize("NFC", t).translate(_LOOKALIKE)


def _tidy(t: str) -> str:
    """Spaces and commas after something was removed: «Tak ,  , dalej» → «Tak, dalej»."""
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"(?<=\() | (?=\))", "", t)
    t = re.sub(r" (?=[.,!?…:;])", "", t)
    t = re.sub(r",(?: ?,)+", ",", t)
    t = re.sub(r",(?=[.!?…:;])", "", t)
    t = re.sub(r"(?<=[.!?…:;]),", "", t)
    t = re.sub(r"^[\s,.;:!?…]+", "", t)
    return t.strip()


def _is_stage(inner: str) -> bool:
    """True for a bracket that directs rather than speaks: «(pauza)», «(z uśmiechem)»."""
    s = inner.strip()
    if not _ALNUM.search(s) or _CYR.search(s):
        return True             # «(...)», and Russian hints like «(спокойно)»
    if _TIMING.fullmatch(s) and re.search(r"[:a-z]", s, re.IGNORECASE):
        return True             # «(0–3 s)»; a bare «(3-4)» may be said
    if not _STAGE_ANY.search(s):
        return False
    # a stage word among a few helpers only: «(krótka pauza)», «(mówi spokojnie)»,
    # but not «(pewnie to znasz)»
    rest = [w for w in re.findall(r"[^\W_]+", _STAGE_ANY.sub(" ", s))
            if w.lower() not in _STAGE_GLUE and not w.isdigit()]
    if not rest:
        return True
    # «(B-roll: ja przy biurku z laptopem)», «(ujęcie z drona)»: a word nobody
    # says, then what to show. Without the colon of such a note, a sentence of
    # its own («(Oddech to podstawa.)») or a longer clause («(przejście na
    # swoje było najlepszą decyzją)») is his to say.
    m = _STAGE_SURE_START.match(s)
    if not m:
        return False
    if s[m.end():].lstrip().startswith(":"):
        return True
    return len(rest) <= 3 and not re.search(r"[.!?…]$", s)


def _drop_stage_brackets(t: str) -> str:
    """Remove every (...) that directs, inner ones first.

    A kept inner bracket is held aside, so the one around it is judged too:
    «(pauza (2 s))» was read «pauza, 2 s».
    """
    held: list[str] = []

    def one(m: re.Match) -> str:
        inner = m.group(1)
        bare = _HELD.sub(" ", inner)
        if _is_stage(bare) and (_ALNUM.search(bare) or not _HELD.search(inner)):
            return " "
        held.append(m.group(0))
        return f"\uE000{len(held) - 1}\uE001"

    while True:
        new = _PAREN.sub(one, t)
        if new == t:
            break
        t = new
    while _HELD.search(t):
        t = _HELD.sub(lambda m: held[int(m.group(1))], t)
    return t


# Russian letters as a Pole would write the sound, for words the chat model
# spelled half in Cyrillic
_CYR_SOUNDS = {
    "а": "a", "б": "b", "в": "w", "г": "g", "д": "d", "е": "e", "ё": "jo",
    "ж": "ż", "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "ch", "ц": "c", "ч": "cz", "ш": "sz", "щ": "szcz", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "ju", "я": "ja", "і": "i", "ї": "ji",
    "є": "je", "ґ": "g",
}
_CYR_LATIN = str.maketrans({**_CYR_SOUNDS, **{k.upper(): v.capitalize()
                                             for k, v in _CYR_SOUNDS.items()}})


def _fix_mixed(t: str) -> str:
    """A word written half in Latin, half in Cyrillic is a Polish word.

    The chat model, talking Russian around a Polish script, sometimes slips
    Cyrillic letters into a Polish word («model oкупалności»). Dropped as
    Russian, that left «o ności» to read; spelled in Latin it can be said.
    """
    def one(m: re.Match) -> str:
        w = m.group(0)
        if _CYR.search(w) and _LETTER.search(_CYR.sub("", w)):
            return w.translate(_CYR_LATIN)
        return w
    return re.sub(r"[^\W_]+", one, t)


def _drop_russian(t: str) -> str:
    """A Russian note left in a Polish script would be read with Polish sounds.

    Judged per sentence: one that is mostly Cyrillic is a note and goes whole,
    with the file names or numbers inside it («Всего около 10 минут» left
    «10» behind); in a Polish sentence only the Cyrillic words go.
    """
    kept = []
    for part in re.split(r"(?<=[.!?…])\s+", t):
        cyr = len(_CYR.findall(part))
        if cyr and cyr >= len(re.findall(r"[^\W\d_]", part)) - cyr:
            continue
        kept.append(_CYR_RUN.sub(" ", part) if cyr else part)
    return " ".join(kept)


def empty_reason(text: str) -> str:
    """Why plan_chunks left nothing of text: "russian", or "" for anything else.

    A Russian sentence is dropped whole (_drop_russian), so the chat's Russian
    explanation pasted in place of the Polish script came to nothing, and the
    page said the text held only hashtags, links or emoji. "russian" when
    Cyrillic letters stood outside hashtags, mentions and links. Only
    meaningful for a text plan_chunks returns [] for.
    """
    for raw in str(text or "").splitlines():
        t = _URL.sub("", _MD_LINK.sub(r"\1", raw))
        if _CYR.search(_MENTION.sub("", _HASHTAG.sub("", t))):
            return "russian"
    return ""


def clean_line(line: str) -> str:
    """One raw line → what is read aloud; "" when nothing speakable is left.

    Chat replies arrive as markdown and captions end in hashtags; XTTS tries
    to pronounce all of it. Removing one thing can uncover another at the
    start of the line («Спокойно. Hak: Tak.» showed «Hak:» only once the
    Russian was gone), so the line is cleaned until nothing changes.
    """
    t = str(line or "")
    for _ in range(4):
        new = _clean_once(t)
        if new == t:
            break
        t = new
    return t


def _clean_once(t: str) -> str:
    t = _nfc(_INVISIBLE.sub("", t)).replace("\t", " ")
    if _CYR.search(t):
        t = _fix_mixed(t)
    t = _MD_LINK.sub(r"\1", t)                 # «[napisz](https://…)» keeps its words
    t = _URL.sub("", t)
    t = _HASHTAG.sub("", t)
    t = _KEYCAP_LEAD.sub("", t)
    t = _ARROW_SIGN.sub(" -> ", t)
    t = _EMOJI.sub("", t)
    t = t.replace("‼", "!").replace("⁉", "?")
    t = _EMOTICON.sub("", t)
    # before the underscore strip, or "@moje_konto" is read "małpa mojekonto"
    t = _MENTION.sub("", t)
    # «[B-roll: kawa]», «[CTA]», «[пауза 0.8]»: square brackets are never spoken
    while True:
        new = _SQUARE.sub(" ", t)
        if new == t:
            break
        t = new
    t = _drop_stage_brackets(t)
    t = _LESS.sub(" mniej niż ", t)
    t = _MORE.sub(" ponad ", t)
    t = t.replace("~~", "")
    # «~5 min» is «około pięciu minut» for the normalizer; other tildes are markdown
    t = re.sub(r"~(?!\s?\d)", "", t)
    t = re.sub(r"(?<=\d) ?\* ?(?=\d)", " x ", t)   # «2*3» is not «23»
    t = re.sub(r"[*_`]+", "", t)
    for _ in range(3):                         # «- **Hak:** 1. Zapisuj…»
        new = LABEL_RE.sub("", _BULLET.sub("", t), count=1)
        if new == t:
            break
        t = new
    if _STAGE_LINE.match(t):
        return ""
    if _CYR.search(t):
        t = _drop_russian(t)
    t = re.sub(r"[#\[\]{}]", " ", t)
    t = _tidy(t)
    return t if _ALNUM.search(t) else ""


def _is_separator(raw: str) -> bool:
    """«---», «—», «...», «***», «•»: a line drawn between parts, so a break.

    A line that held only a hashtag, an emoji or a link is not one: it is
    dropped, not turned into a pause he did not write.
    """
    if _SPACER.fullmatch(_INVISIBLE.sub("", raw)):
        return False            # a blank line, or the «.» spacer of a caption
    t = _MENTION.sub("", _EMOJI.sub("", _HASHTAG.sub("", _URL.sub("", raw))))
    t = _EMOTICON.sub("", _INVISIBLE.sub("", t))
    return bool(t.strip()) and not _ALNUM.search(t)


_CLOSERS = "\"'”»«)"


def _closed(line: str) -> str:
    # A line without closing punctuation ends with a pause, not running on.
    # «„Tak.”» is closed already: a second dot left «Tak..» once the quotes went.
    end = line.rstrip(_CLOSERS) or line
    return line if end[-1] in ".!?…:;," else line + "."


# a list item: the line before it ends where it ends, whatever case follows
_ITEM = re.compile(r"\s*(?:[-*+•·▪–—]+\s|\d{1,2}[.)]|[a-zA-Z]\)\s)")


def _is_item(raw: str) -> bool:
    return bool(_ITEM.match(raw) or _EMOJI.match(raw.lstrip()))   # «✅ zapisuj»


def _join_lines(lines: list[str], items: list[bool]) -> str:
    """A paragraph's lines as one text, each closed as it is meant to be read.

    A line that runs on into a lowercase line is one sentence wrapped: a
    full stop there read «wieczorem do. domu» and «będę miał. więcej czasu»
    with a sentence's fall in the middle. A long line (a wrapped paragraph)
    or one ending on «do», «i», «że» or a number runs straight on; a short
    one («trzydzieści dni» / «tyle dajesz») gets the comma of a phrase.
    """
    out = []
    for i, line in enumerate(lines):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        end = line.rstrip(_CLOSERS) or line
        if (nxt and not items[i + 1] and _LOWER_START.match(nxt)
                and end[-1] not in ".!?…:;,"):
            word = line.split()[-1].lower().strip(_CLOSERS)
            runs_on = (len(line) >= 50 or word in _NO_END or word[-1:].isdigit()
                       or bool(_NUMBER_WORD.match(word)))
            out.append(line if runs_on else line + ",")
        else:
            out.append(_closed(line))
    return " ".join(out)


def _scan(text: str) -> list[dict]:
    """Cleaned lines grouped into paragraphs.

    Each paragraph records the longest run of blank lines before it ("blank"),
    whether a separator line stood there ("hard"), and whether it ends like a
    heading or «…:», leading into the next one ("opens"). A line that cleaned
    to nothing (a hashtag, «(pauza)», a bare «CTA») is skipped and breaks
    the blank run it sits in, so «A / blank / #tag / blank / B» is one blank.
    """
    paras: list[dict] = []
    cur = None
    run = pending = 0
    hard = False
    for raw in str(text or "").splitlines():
        if _SPACER.fullmatch(_INVISIBLE.sub("", raw)):
            run += 1
            pending = max(pending, run)
            continue
        run = 0
        line = clean_line(raw)
        if not line:
            if _is_separator(raw):
                hard = True
            continue
        if cur is not None and (pending or hard):
            paras.append(cur)
            cur = None
        if cur is None:
            cur = {"lines": [], "items": [], "blank": pending, "hard": hard}
        cur["lines"].append(line)
        cur["items"].append(_is_item(raw))
        pending, hard = 0, False
    if cur is not None:
        paras.append(cur)
    for p in paras:
        p["text"] = _join_lines(p["lines"], p["items"])
        # «Trzy rzeczy:» or a title with no full stop leads into what follows
        last = p["lines"][-1].rstrip(_CLOSERS) or p["lines"][-1]
        p["opens"] = last[-1] not in ".!?…;,"
    return paras


def clean_for_speech(text: str) -> str:
    """Drop what should not be read aloud; paragraphs come back one per line.

    Backward compatible with synth.py: lines inside a paragraph are joined with
    spaces, each ending in .!?…:;, (a "." is added otherwise, except where a
    sentence wrapped onto a lowercase line goes on: see _join_lines). A
    separator line such as «---» also ends a paragraph; a line that held only
    a hashtag, an emoji, a link, a label or a stage direction is dropped
    without a break.
    """
    return "\n".join(p["text"] for p in _scan(text))


def ends_sentence(chunk: str) -> bool:
    """False when the splitter cut a long sentence at a comma or a space."""
    return bool(re.search(r"[.!?…][\"'”»«)]?$", str(chunk).rstrip()))


def _sentences(text: str) -> list[str]:
    """Sentences, with abbreviation dots still masked by _DOT_MARK."""
    text = _ABBREV.sub(lambda m: m.group(1) + _DOT_MARK, str(text or "").strip())
    return [p.strip() for p in _SENT_SPLIT.split(text) if p.strip()]


def _slen(p: str) -> int:
    """Length once spoken: tts_text adds a "." to a piece without one."""
    return len(p) + (0 if re.search(r"[.!?…,:;]$", p) else 1)


def _held_dot(word: str) -> bool:
    """«3.», «tys.», «zł.»: a dot still inside a sentence belongs to its word.

    The splitter leaves a dot only before a lowercase word, so it is an
    ordinal or an abbreviation; cut there, «zająłem 3.» fell like a sentence
    end and «miejsce…» opened the next chunk.
    """
    w = word.rstrip(".")
    return word.endswith(".") and (any(ch.isdigit() for ch in w) or len(w) <= 4)


def _can_break(p: str, s: int) -> bool:
    end = p.find(" ", s + 1)
    prev = p[p.rfind(" ", 0, s) + 1:s]
    nxt = p[s + 1:end if end >= 0 else len(p)]
    if not prev or not nxt:
        return False
    # «5 | zł», «5 | 000», «np. | Kowalski»
    if prev[-1].isdigit() or prev.endswith(_DOT_MARK) or _held_dot(prev):
        return False
    word = prev.lower().strip(",;:")
    if word in _NO_END or _NUMBER_WORD.match(word):
        return False
    return nxt.lower().strip(",.;:!?") not in _NO_START


def _best_cut(p: str, max_chars: int) -> int:
    """Where to cut a sentence longer than max_chars (the head is p[:cut]).

    A clause mark first (a comma, not the one in «49,99»), else a space. Aim
    at an even split, and never leave a piece under MIN_CUT on either side
    when that can be helped: a 15-character tail alone is a chunk XTTS
    babbles on.
    """
    ideal = len(p) / math.ceil(_slen(p) / max_chars)
    punct = [m.end() for m in re.finditer(r"[,;:.!?…](?=\s)", p)
             if not _held_dot(p[p.rfind(" ", 0, m.start()) + 1:m.end()])]
    spaces = [m.start() for m in re.finditer(" ", p) if _can_break(p, m.start())]

    def fits(c: int, room: int, tail: int) -> bool:
        return (MIN_CUT <= len(p[:c].rstrip()) <= room
                and len(p[c:].strip(" ,")) >= tail)

    for cands, room, tail, spaced in ((punct, max_chars, MIN_CUT, False),
                                      (punct, max_chars, 20, False),
                                      (spaces, max_chars - 1, MIN_CUT, True)):
        ok = [c for c in cands if fits(c, room, tail)]
        if ok:
            def cost(c: int) -> float:
                bonus = 0
                if spaced and p[c + 1:].split(" ", 1)[0].lower() in _CONJ:
                    bonus = _CONJ_BONUS
                return abs(c - ideal) - bonus
            return min(ok, key=cost)
    # nothing leaves a real tail: keep the head as long as possible
    ok = ([c for c in punct if MIN_CUT <= c <= max_chars]
          or [s for s in spaces if MIN_CUT <= s <= max_chars - 1]
          or [m.start() for m in re.finditer(" ", p) if 0 < m.start() <= max_chars - 1])
    return max(ok) if ok else max_chars - 1


def split_sentences(text: str, max_chars: int = MAX_CHARS,
                    min_chars: int = MIN_CHARS) -> list[tuple[str, bool]]:
    """Split into chunks XTTS handles well: not too long, and not too short.

    Returns [(piece, cut), ...]; cut is True when the piece ends where a long
    sentence was cut at a comma or a space, not at a sentence end.

    Long input makes XTTS drop words; short input makes it keep talking after
    the sentence ends. A lone "Cześć, tu Piotr." babbled in half of test runs,
    so a short piece merges into the next one, and a short piece left over
    (the last one: «…o czymś ważnym. Bez mitów.») into the one before it.
    """
    pieces: list[list] = []
    for p in _sentences(text):
        while _slen(p) > max_chars:
            cut = max(1, _best_cut(p, max_chars))
            head, p = p[:cut].rstrip(), p[cut:].strip(" ,")
            if head:
                pieces.append([head, True])
        if p:
            pieces.append([p, False])

    def fits(a: str, b: str) -> bool:
        return len(a) + 1 + _slen(b) <= max_chars

    merged: list[list] = []
    for p, cut in pieces:
        if merged and len(merged[-1][0]) < min_chars and fits(merged[-1][0], p):
            merged[-1] = [merged[-1][0] + " " + p, cut]
        else:
            merged.append([p, cut])
    out: list[list] = []
    for p, cut in merged:
        if out and len(p) < min_chars and fits(out[-1][0], p):
            out[-1] = [out[-1][0] + " " + p, cut]
        else:
            out.append([p, cut])
    return [(p.replace(_DOT_MARK, "."), cut) for p, cut in out]


def _marks(t: str) -> str:
    """Quotes, dashes and brackets as a speaker says them.

    Until nothing changes: a bracket gone can bring two marks together
    («Tak? (…) !» became «Tak?!» after one pass).
    """
    for _ in range(3):
        new = _marks_once(t)
        if new == t:
            break
        t = new
    return t


def _marks_once(t: str) -> str:
    t = _nfc(t)
    t = re.sub(r"\.{3,}", "…", t)
    t = re.sub(r"…+", "…", t)
    t = re.sub(r"[!?]*\?[!?]*", "?", t)        # «?!» and «!?» are asked, not shouted
    t = re.sub(r"!{2,}", "!", t)
    t = _QUOTES.sub(" ", t)                     # a space: «tak„nie”» is two words
    t = _APOS.sub(" ", t)
    # symbols the normalizer spells when it runs: XTTS has no token for
    # ~ + < > and says its [UNK] as noise
    t = _ARROW.sub(", ", t)
    t = re.sub(r"~\s?(?=\d)", " około ", t)
    t = re.sub(r"\s*\+\s*", " plus ", t)
    t = re.sub(r"[~<>^\\¨¶]", " ", t)
    t = re.sub(r"(?<=[.!?…])(?:\s*\.)+", "", t)   # «„Tak.”.» without its quotes
    t = _DASH.sub(", ", t)
    t = _HYPHEN_DASH.sub(",", t)
    # «Zrób to (np. w pracy) dziś» is said «Zrób to, np. w pracy, dziś»
    t = re.sub(r"[()\[\]{}•·▪|]", ",", t)
    t = re.sub(r",(?=[^\W\d_])", ", ", t)
    return _tidy(t)


def tts_text(chunk: str) -> str:
    """The exact string XTTS gets: no quotes or dashes, ending in . ! or ?.

    A trailing : ; , … or no punctuation becomes "."; «?!» stays «?».
    """
    t = _marks(str(chunk or "").replace(_DOT_MARK, "."))
    if not _ALNUM.search(t):
        return ""
    m = re.search(r"[\s.,:;!?…]+$", t)
    run = m.group(0) if m else ""
    end = "?" if "?" in run else "!" if "!" in run else "."
    return t[:len(t) - len(run)] + end


def _line_mode(paras: list[dict]) -> bool:
    """A script with a blank line after nearly every line.

    Reels scripts are written that way: at least 3 paragraphs, 60 % of them
    one sentence under 90 characters. There a blank line is only the end of
    a sentence; the old engine paused 0.8 s plus the model's own silence at
    every one.
    """
    if len(paras) < 3:
        return False
    single = sum(1 for p in paras
                 if len(p["text"]) < 90 and len(_sentences(p["text"])) == 1)
    return single >= 0.6 * len(paras)


def line_mode(text: str) -> bool:
    """Whether text is read in line mode (see _line_mode), judged as written.

    For the app: it asks this of the text as he typed it and passes the
    answer to synth.py (--line-mode on / off). Judged after the AI number
    pass, «W 2025 r. zarobiłem 64 500 zł…» written out grew from 65 to 169
    characters, the 90-character test failed, and the same script came back
    with the 0.50 s paragraph pause at its blank lines, depending only on
    whether Ollama was running.
    """
    return _line_mode(_scan(text))


def plan_chunks(text: str, normalize=None, line_mode: bool | None = None) -> list[dict]:
    """The chunk plan: [{"text", "after", "para"}, ...].

    "text" is what XTTS reads (already tts_text()-ed), "after" the kind of
    boundary after it ("clause", "sentence", "question", "paragraph", or
    "end" for the last chunk), "para" the paragraph index. normalize, when
    given, turns each paragraph's written numbers and abbreviations into
    words (pl_normalize.normalize) before it is cut. line_mode None judges
    line mode from text itself; True or False is the caller's, made on the
    text before it was rewritten (see line_mode()).
    """
    paras = _scan(text)
    if _line_mode(paras) if line_mode is None else line_mode:
        joined: list[dict] = []
        for p in paras:
            if joined and p["blank"] < 2 and not p["hard"]:
                joined[-1]["text"] += " " + p["text"]
                joined[-1]["opens"] = p["opens"]
            else:
                joined.append(dict(p))
        paras = joined

    groups: list[dict] = []
    for p in paras:
        t = p["text"]
        if normalize is not None:
            try:
                said = normalize(t)
                if not isinstance(said, str):
                    raise TypeError(f"returned {type(said).__name__}")
                t = said
            except Exception as exc:  # noqa: BLE001
                # a take read with the model's own number handling beats no take
                print(f"[speech_text] normalize failed ({exc!r}), paragraph "
                      "kept as written", file=sys.stderr, flush=True)
        t = _marks(t)
        pieces = [[s, cut] for s, cut in split_sentences(t) if _ALNUM.search(s)]
        if pieces:
            groups.append({"chunks": pieces, "opens": p["opens"]})

    def fits(a: str, b: str) -> bool:
        return len(a) + 1 + _slen(b) <= MAX_CHARS

    # A short paragraph alone is a tiny chunk: it joins the paragraph before
    # it, or the next one when there is none, or when it opens the next one
    # («Trzy rzeczy:», a title). A title merged backward ended the previous
    # part: «…Do zobaczenia. Jak zacząłem.»
    kept: list[list] = []
    for k, g in enumerate(groups):
        chunks = g["chunks"]
        if (len(groups) > 1 and len(chunks) == 1
                and len(tts_text(chunks[0][0])) < SHORT_PARAGRAPH):
            whole = chunks[0][0]
            nxt = groups[k + 1]["chunks"] if k + 1 < len(groups) else None
            to_prev = bool(kept) and fits(kept[-1][-1][0], whole)
            to_next = nxt is not None and fits(whole, nxt[0][0])
            if to_next and (g["opens"] or not to_prev):
                nxt[0] = [whole + " " + nxt[0][0], nxt[0][1]]
                continue
            if to_prev:
                kept[-1][-1] = [kept[-1][-1][0] + " " + whole, chunks[0][1]]
                continue
        kept.append(chunks)

    flat = []
    for chunks in kept:
        said = [(tts_text(c), cut) for c, cut in chunks]
        said = [(c, cut) for c, cut in said if c]
        if said:
            para = flat[-1][0] + 1 if flat else 0
            flat.extend((para, c, cut) for c, cut in said)

    plan = []
    for i, (para, chunk, cut) in enumerate(flat):
        if i == len(flat) - 1:
            after = "end"
        elif flat[i + 1][0] != para:
            after = "paragraph"
        elif cut:
            after = "clause"
        elif chunk.endswith("?"):
            after = "question"
        else:
            after = "sentence"
        plan.append({"text": chunk, "after": after, "para": para})
    return plan
