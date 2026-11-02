"""Written Polish to spoken Polish: numbers, dates, prices, abbreviations, acronyms.

XTTS has its own text cleaner and it gets Polish wrong: «m.in.» becomes
«panin» (its `\\bm\\.` rule means «pan»), «5 000 zł» «pięć zero zł», «z 5
osobami» «z pięć osobami», «12:30» «dwanaście:trzydzieści», «2x» «dwax». So
nothing with a digit, a symbol or an abbreviation may reach it: this module
writes all of it out in words first, the way a Pole says it aloud.

Two layers use it:

* the text AI rewrites the lines `needs_rewrite` flags, because only a reader
  of the whole sentence knows the case a number needs; `rewrite_prompt` asks
  for that and `accept_rewrite` checks the answer word by word, so a model
  that "improves" the text is refused line by line;
* `normalize` is the rule-based backup, and it also runs over the AI's
  accepted lines (it is idempotent), over what whisper heard and over the
  training transcripts, so every side compares the same words.

The rules guess the grammatical case from the neighbouring words only: after
od/do/bez/dla/około/wg/… the genitive, after dzięki/ku the dative, before a
noun in -ami/-mi the instrumental, before one in -ach the locative, after «z»
otherwise the genitive, and the nominative everywhere else. They cannot see a
verb's government («przyglądam się 5 osobom»), a preposition with two
meanings («po 2 tyg.»: after two weeks, or two weeks each) or a noun two
words away. The gender comes from short lists of feminine and
masculine-personal nouns and, for a lone 1, from the noun's ending. Those
misses are why the AI pass exists; the rules have to leave no digit behind
and to be right in the common cases.

Standard library only: it runs in the app's .venv, which has no num2words.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

CASES = ("nom", "gen", "dat", "acc", "ins", "loc")

_UNITS = {
    "nom": "zero jeden dwa trzy cztery pięć sześć siedem osiem dziewięć",
    "gen": "zera jednego dwóch trzech czterech pięciu sześciu siedmiu ośmiu dziewięciu",
    "dat": "zeru jednemu dwóm trzem czterem pięciu sześciu siedmiu ośmiu dziewięciu",
    "acc": "zero jeden dwa trzy cztery pięć sześć siedem osiem dziewięć",
    "ins": "zerem jednym dwoma trzema czterema pięcioma sześcioma siedmioma ośmioma dziewięcioma",
    "loc": "zerze jednym dwóch trzech czterech pięciu sześciu siedmiu ośmiu dziewięciu",
}
_UNITS = {c: s.split() for c, s in _UNITS.items()}

_ONE = {
    "f": dict(nom="jedna", gen="jednej", dat="jednej", acc="jedną", ins="jedną", loc="jednej"),
    "n": dict(nom="jedno", gen="jednego", dat="jednemu", acc="jedno", ins="jednym", loc="jednym"),
}
_TWO_F = dict(nom="dwie", acc="dwie", ins="dwiema")
# masculine-personal nominative: «dwaj ludzie», «trzej», «czterej»
_MP_NOM = {2: "dwaj", 3: "trzej", 4: "czterej"}
# collective numerals, said with «dzieci»: «dwoje dzieci», «z trojgiem dzieci»
_COLLECTIVE = {
    "nom": "dwoje troje czworo pięcioro sześcioro siedmioro ośmioro dziewięcioro",
    "gen": "dwojga trojga czworga pięciorga sześciorga siedmiorga ośmiorga dziewięciorga",
    "dat": "dwojgu trojgu czworgu pięciorgu sześciorgu siedmiorgu ośmiorgu dziewięciorgu",
    "acc": "dwoje troje czworo pięcioro sześcioro siedmioro ośmioro dziewięcioro",
    "ins": "dwojgiem trojgiem czworgiem pięciorgiem sześciorgiem siedmiorgiem ośmiorgiem "
           "dziewięciorgiem",
    "loc": "dwojgu trojgu czworgu pięciorgu sześciorgu siedmiorgu ośmiorgu dziewięciorgu",
}
_COLLECTIVE = {c: dict(zip(range(2, 10), s.split())) for c, s in _COLLECTIVE.items()}

_TEEN_NOM = ("dziesięć jedenaście dwanaście trzynaście czternaście piętnaście "
             "szesnaście siedemnaście osiemnaście dziewiętnaście").split()
_TEEN_OBL = ("dziesięciu jedenastu dwunastu trzynastu czternastu piętnastu "
             "szesnastu siedemnastu osiemnastu dziewiętnastu").split()
_TEEN_INS = ("dziesięcioma jedenastoma dwunastoma trzynastoma czternastoma "
             "piętnastoma szesnastoma siedemnastoma osiemnastoma dziewiętnastoma").split()

_TENS_NOM = [None, None] + ("dwadzieścia trzydzieści czterdzieści pięćdziesiąt "
                            "sześćdziesiąt siedemdziesiąt osiemdziesiąt dziewięćdziesiąt").split()
_TENS_OBL = [None, None] + ("dwudziestu trzydziestu czterdziestu pięćdziesięciu "
                            "sześćdziesięciu siedemdziesięciu osiemdziesięciu "
                            "dziewięćdziesięciu").split()
_TENS_INS = [None, None] + ("dwudziestoma trzydziestoma czterdziestoma pięćdziesięcioma "
                            "sześćdziesięcioma siedemdziesięcioma osiemdziesięcioma "
                            "dziewięćdziesięcioma").split()

_HUND_NOM = [None] + ("sto dwieście trzysta czterysta pięćset sześćset siedemset "
                      "osiemset dziewięćset").split()
_HUND_OBL = [None] + ("stu dwustu trzystu czterystu pięciuset sześciuset siedmiuset "
                      "ośmiuset dziewięciuset").split()
_HUND_INS = [None] + ("stoma dwustoma trzystoma czterystoma pięciuset sześciuset "
                      "siedmiuset ośmiuset dziewięciuset").split()


def _by_case(case, nom, obl, ins):
    if case in ("nom", "acc"):
        return nom
    return ins if case == "ins" else obl


# Nouns as (singular by case, plural by case), in the order of CASES.
def _decl(sg: str, pl: str) -> tuple[dict, dict]:
    return dict(zip(CASES, sg.split())), dict(zip(CASES, pl.split()))


_SCALES = (
    (10 ** 9, _decl("miliard miliarda miliardowi miliard miliardem miliardzie",
                    "miliardy miliardów miliardom miliardy miliardami miliardach")),
    (10 ** 6, _decl("milion miliona milionowi milion milionem milionie",
                    "miliony milionów milionom miliony milionami milionach")),
    (10 ** 3, _decl("tysiąc tysiąca tysiącowi tysiąc tysiącem tysiącu",
                    "tysiące tysięcy tysiącom tysiące tysiącami tysiącach")),
)


def _few(n: int) -> bool:
    """2-4 but not 12-14: «dwa złote», «dwadzieścia dwa złote», «dwanaście złotych»."""
    return n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14)


def _agree(n: int, case: str, noun: tuple[dict, dict]) -> str:
    """The noun form that follows the cardinal n in the given case."""
    sg, pl = noun
    if n == 1:
        return sg[case]
    if n >= 1000 and n % 1000 == 0:
        # the noun hangs on «tysiąc», not on the number: «pięcioma tysiącami złotych»
        return pl["gen"]
    if case in ("nom", "acc"):
        return pl["nom"] if _few(n) else pl["gen"]
    return pl[case]


def _unit(u: int, case: str, gender: str) -> str:
    if u == 1 and gender in _ONE:
        return _ONE[gender][case]
    if u == 2 and gender == "f" and case in _TWO_F:
        return _TWO_F[case]
    return _UNITS[case][u]


def _below_1000(n: int, case: str, gender: str) -> str:
    h, r = divmod(n, 100)
    words = []
    if h:
        words.append(_by_case(case, _HUND_NOM, _HUND_OBL, _HUND_INS)[h])
    if 10 <= r < 20:
        words.append(_by_case(case, _TEEN_NOM, _TEEN_OBL, _TEEN_INS)[r - 10])
    else:
        t, u = divmod(r, 10)
        if t:
            words.append(_by_case(case, _TENS_NOM, _TENS_OBL, _TENS_INS)[t])
        if u == 1 and (h or t):
            words.append("jeden")          # «dwadzieścia jeden», «dwudziestu jeden osób»
        elif u:
            words.append(_unit(u, case, gender))
    return " ".join(words)


def spell(n: int, case: str = "nom", gender: str = "m") -> str:
    """A cardinal in words: spell(5, "ins", "f") → «pięcioma», spell(2, "nom", "f") → «dwie».

    Genders "m", "f", "n" and "mp" (masculine-personal). For "mp" only the
    nominative and accusative differ: «dwaj/trzej/czterej», and «pięciu»,
    «dwudziestu dwóch», «stu» (the genitive forms); from a thousand up the
    counted noun is «tysiąc», so mp falls back to the masculine forms.
    """
    n = int(n)
    if case not in CASES:
        raise ValueError(f"unknown case {case!r}")
    if n < 0:
        return "minus " + spell(-n, case, gender)
    if n >= 10 ** 12:
        raise ValueError("numbers up to 999 999 999 999 only")
    if gender == "mp":
        if case in ("nom", "acc") and 0 < n < 1000:
            if n == 1:
                return "jeden" if case == "nom" else "jednego"
            if case == "nom" and n in _MP_NOM:
                return _MP_NOM[n]
            return spell(n, "gen", "m")
        gender = "m"
    if n == 0:
        return _UNITS[case][0]
    words = []
    for value, noun in _SCALES:
        k, n = divmod(n, value)
        if k == 1:
            words.append(noun[0][case])    # «tysiąc», never «jeden tysiąc»
        elif k:
            words.append(_below_1000(k, case, "m") + " " + _agree(k, case, noun))
    if n:
        words.append(_below_1000(n, case, gender))
    return " ".join(words)


# "pl" is the plural (not masculine-personal): «lata dziewięćdziesiąte», «w latach
# dziewięćdziesiątych», which «90-tych» and «w latach 90.» are read as
_ORD_END = {
    "hard": {"m": dict(nom="y", gen="ego", dat="emu", acc="y", ins="ym", loc="ym"),
             "n": dict(nom="e", gen="ego", dat="emu", acc="e", ins="ym", loc="ym"),
             "f": dict(nom="a", gen="ej", dat="ej", acc="ą", ins="ą", loc="ej"),
             "pl": dict(nom="e", gen="ych", dat="ym", acc="e", ins="ymi", loc="ych")},
    # drugi: «druga», «drugą», but «drugiego» keeps the i
    "velar": {"m": dict(nom="i", gen="iego", dat="iemu", acc="i", ins="im", loc="im"),
              "n": dict(nom="ie", gen="iego", dat="iemu", acc="ie", ins="im", loc="im"),
              "f": dict(nom="a", gen="iej", dat="iej", acc="ą", ins="ą", loc="iej"),
              "pl": dict(nom="ie", gen="ich", dat="im", acc="ie", ins="imi", loc="ich")},
    # trzeci: «trzecia», «trzecią»
    "soft": {"m": dict(nom="i", gen="iego", dat="iemu", acc="i", ins="im", loc="im"),
             "n": dict(nom="ie", gen="iego", dat="iemu", acc="ie", ins="im", loc="im"),
             "f": dict(nom="ia", gen="iej", dat="iej", acc="ią", ins="ią", loc="iej"),
             "pl": dict(nom="ie", gen="ich", dat="im", acc="ie", ins="imi", loc="ich")},
}
_ORD_UNITS = ("zerow pierwsz drug trzec czwart piąt szóst siódm ósm dziewiąt").split()
_ORD_TEENS = ("dziesiąt jedenast dwunast trzynast czternast piętnast szesnast "
              "siedemnast osiemnast dziewiętnast").split()
_ORD_TENS = [None, None] + ("dwudziest trzydziest czterdziest pięćdziesiąt sześćdziesiąt "
                            "siedemdziesiąt osiemdziesiąt dziewięćdziesiąt").split()
_ORD_HUND = [None] + ("setn dwusetn trzysetn czterysetn pięćsetn sześćsetn siedemsetn "
                      "osiemsetn dziewięćsetn").split()
_ORD_SCALE = {10 ** 3: "tysięczn", 10 ** 6: "milionow", 10 ** 9: "miliardow"}

# The first part of a one-word ordinal: «dwutysięczny», «pięciomilionowy».
_COMB = {1: "", 2: "dwu", 3: "trzy", 4: "cztero", 5: "pięcio", 6: "sześcio", 7: "siedmio",
         8: "ośmio", 9: "dziewięcio", 10: "dziesięcio", 11: "jedenasto", 12: "dwunasto",
         13: "trzynasto", 14: "czternasto", 15: "piętnasto", 16: "szesnasto",
         17: "siedemnasto", 18: "osiemnasto", 19: "dziewiętnasto", 20: "dwudziesto",
         30: "trzydziesto", 40: "czterdziesto", 50: "pięćdziesięcio", 60: "sześćdziesięcio",
         70: "siedemdziesięcio", 80: "osiemdziesięcio", 90: "dziewięćdziesięcio",
         100: "stu", 200: "dwustu", 300: "trzystu", 400: "czterystu", 500: "pięćset",
         600: "sześćset", 700: "siedemset", 800: "osiemset", 900: "dziewięćset"}


def _stem_kind(stem: str) -> str:
    if stem == "drug":
        return "velar"
    return "soft" if stem == "trzec" else "hard"


def _ord_word(stem: str, case: str, gender: str) -> str:
    return stem + _ORD_END[_stem_kind(stem)][gender][case]


def ordinal(n: int, case: str = "nom", gender: str = "m") -> str:
    """An ordinal: «pierwszy», «dwudziestego pierwszego», «dwa tysiące dwudziestym szóstym».

    Only the last two words are ordinal, as Poles say it: «tysiąc dziewięćset
    dziewięćdziesiąty dziewiąty», «sto pierwszy». A round hundred, thousand or
    million becomes one word («dwusetny», «dwutysięczny»); for a multiplier
    with no one-word form («dwadzieścia jeden tysięczny») the cardinal stays in
    front, which is understood but not textbook Polish. "mp" is treated as "m"
    (ordinals here are singular); "pl" gives the plural of the other genders
    («dziewięćdziesiąte», «dziewięćdziesiątych»), for decades.
    """
    n = int(n)
    if case not in CASES:
        raise ValueError(f"unknown case {case!r}")
    if n < 0 or n >= 10 ** 12:
        raise ValueError("ordinals from 0 to 999 999 999 999 only")
    gender = "m" if gender == "mp" else gender
    if n == 0:
        return _ord_word("zerow", case, gender)
    if n % 100:
        prefix, r = n - n % 100, n % 100
        if 10 <= r < 20:
            last = _ord_word(_ORD_TEENS[r - 10], case, gender)
        else:
            t, u = divmod(r, 10)
            parts = []
            if t:
                parts.append(_ord_word(_ORD_TENS[t], case, gender))
            if u:
                parts.append(_ord_word(_ORD_UNITS[u], case, gender))
            last = " ".join(parts)
    elif n % 1000:
        prefix = n - n % 1000
        last = _ord_word(_ORD_HUND[(n % 1000) // 100], case, gender)
    else:
        for scale in (10 ** 3, 10 ** 6, 10 ** 9):
            if n % (scale * 1000) or scale == 10 ** 9:
                break
        prefix = n - n % (scale * 1000) if scale < 10 ** 9 else 0
        k = (n % (scale * 1000)) // scale if scale < 10 ** 9 else n // scale
        word = _ord_word(_ORD_SCALE[scale], case, gender)
        last = _COMB[k] + word if k in _COMB else spell(k) + " " + word
    return (spell(prefix) + " " + last) if prefix else last


def _build_words() -> dict:
    """Every word form the speller can produce, mapped to (kind, value).

    Kinds: "z" zero, "u" 1-9, "t" 10-19, "d" tens, "h" hundreds, "s" a scale
    noun; the ordinal ones are "ou", "ot", "od", "oh" and "os" (a round
    thousand/million/billion, value already multiplied). Built from the same
    tables as spell() and ordinal(), so the two cannot drift apart.
    """
    w: dict[str, tuple[str, float]] = {}
    for case in CASES:
        w[_UNITS[case][0]] = ("z", 0)
        for u in range(1, 10):
            w[_UNITS[case][u]] = ("u", u)
        for g in ("f", "n"):
            w[_ONE[g][case]] = ("u", 1)
        for t in range(10):
            w[_by_case(case, _TEEN_NOM, _TEEN_OBL, _TEEN_INS)[t]] = ("t", 10 + t)
        for t in range(2, 10):
            w[_by_case(case, _TENS_NOM, _TENS_OBL, _TENS_INS)[t]] = ("d", 10 * t)
        for h in range(1, 10):
            w[_by_case(case, _HUND_NOM, _HUND_OBL, _HUND_INS)[h]] = ("h", 100 * h)
    for form in _TWO_F.values():
        w[form] = ("u", 2)
    for v, form in _MP_NOM.items():
        w[form] = ("u", v)
    for forms in _COLLECTIVE.values():
        for v, form in forms.items():
            w[form] = ("u", v)
    for value, (sg, pl) in _SCALES:
        for form in list(sg.values()) + list(pl.values()):
            w[form] = ("s", value)
    for g in ("m", "f", "n", "pl"):
        for case in CASES:
            for u, stem in enumerate(_ORD_UNITS):
                w[_ord_word(stem, case, g)] = ("ou", u)
            for t, stem in enumerate(_ORD_TEENS):
                w[_ord_word(stem, case, g)] = ("ot", 10 + t)
            for t in range(2, 10):
                w[_ord_word(_ORD_TENS[t], case, g)] = ("od", 10 * t)
            for h in range(1, 10):
                w[_ord_word(_ORD_HUND[h], case, g)] = ("oh", 100 * h)
            for scale, stem in _ORD_SCALE.items():
                for k, comb in _COMB.items():
                    w[comb + _ord_word(stem, case, g)] = ("os", k * scale)
    return w


_WORDS = _build_words()
_HALF = {"pół": 0.5, "półtora": 1.5, "półtorej": 1.5}
# which kind may follow which inside one number; "S" is "just after a scale noun"
_NEXT_CARD = {"S": "hdtu", "h": "dtu", "d": "u"}


def words_to_numbers(text: str) -> list:
    """Numbers spelled in Polish words, in order: «o osiemnastej trzydzieści» → [18, 30].

    Understands every form spell() and ordinal() produce, plus «pół»,
    «półtora/półtorej», «dwa i pół» (2.5) and «trzy przecinek siedemdziesiąt
    pięć» (3.75). A new number starts wherever the words cannot continue the
    current one: «sześćset siedemset» is [600, 700], «dwa do jednego» [2, 1],
    and a cardinal after an ordinal («osiemnastej trzydzieści») starts anew.
    Whole values come back as int, fractions as float.
    """
    toks = re.findall(r"[^\W\d_]+|[^\w\s]", str(text).lower())
    out: list = []
    st = {"have": False}

    def reset():
        st.update(have=False, total=0.0, group=0.0, last=None, ordinal=False,
                  scale=float("inf"))

    def flush():
        if st["have"]:
            v = round(st["total"] + st["group"], 9)
            out.append(int(v) if v == int(v) else v)
        reset()

    def start():
        flush()
        st["have"] = True

    reset()
    i = 0
    while i < len(toks):
        w = toks[i]
        nxt = toks[i + 1] if i + 1 < len(toks) else ""
        kind, val = _WORDS.get(w, (None, None))
        if w == "i" and nxt == "pół" and st["have"] and not st["ordinal"] \
                and st["last"] in ("u", "t", "d", "h"):
            st["group"] += 0.5                       # «dwa i pół», «dwa i pół tysiąca»
            i += 2
            continue
        if w in _HALF:
            start()
            st.update(group=_HALF[w], last="u")
        elif w == "przecinek" and st["have"] and not st["ordinal"] \
                and _WORDS.get(nxt, ("",))[0] in ("z", "u", "t", "d", "h"):
            # decimal digits: leading «zero»s, then one number below a thousand
            j, zeros = i + 1, ""
            while j < len(toks) and _WORDS.get(toks[j], ("",))[0] == "z":
                zeros += "0"
                j += 1
            frac, last = 0, "S"
            while j < len(toks):
                k2, v2 = _WORDS.get(toks[j], (None, None))
                if k2 is None or k2 not in _NEXT_CARD.get(last, ""):
                    break
                frac += int(v2)
                last = k2
                j += 1
            digits = zeros + (str(frac) if frac else "")
            if digits:
                st["group"] += float("0." + digits)
            st["last"] = "u"
            i = j
            continue
        elif kind in ("z", "u", "t", "d", "h"):
            if not (st["have"] and not st["ordinal"]
                    and kind in _NEXT_CARD.get(st["last"], "")):
                start()
            st["group"] += val
            st["last"] = kind
        elif kind == "s":
            if not (st["have"] and not st["ordinal"] and st["last"] != "S"
                    and val < st["scale"]):
                start()
                st["group"] = 1.0                    # «tysiąc» alone is 1000
            st["total"] += (st["group"] or 1.0) * val
            st.update(group=0.0, last="S", scale=val)
        elif kind in ("ou", "ot", "od", "oh"):
            fits = st["have"] and (
                (not st["ordinal"] and (st["last"] == "S" or
                                        (st["last"] == "h" and kind != "oh")))
                or (st["ordinal"] and st["last"] == "od" and kind == "ou"))
            if not fits:
                start()
            st["group"] += val
            st.update(last=kind, ordinal=True)
        elif kind == "os":
            base = val in _ORD_SCALE                 # «tysięczny» itself, a multiplier may precede
            if base and st["have"] and not st["ordinal"] \
                    and st["last"] in ("u", "t", "d", "h") and val < st["scale"]:
                st["total"] += st["group"] * val     # «dwadzieścia jeden tysięczny»
                st["group"] = 0.0
            elif st["have"] and not st["ordinal"] and st["last"] == "S" and val < st["scale"]:
                st["total"] += val
            else:
                start()
                st["total"] = float(val)
            st.update(last="os", ordinal=True)
        else:
            flush()
        i += 1
    flush()
    return out


_LEXICON_FILE = Path(__file__).resolve().with_name("pl_lexicon.json")
# the same entries as pl_lexicon.json, used when the file is missing or broken
_LEXICON_BUILTIN = {
    "AI": "ej aj", "CV": "ce fał", "PDF": "pe de ef", "SMS": "es em es", "DM": "di em",
    "B2B": "bi tu bi", "ZUS": "zus", "VAT": "wat", "PIT": "pit", "BLIK": "blik",
    "PESEL": "pesel", "NFZ": "en ef zet", "USA": "u es a", "UE": "u e", "OK": "okej",
    "IT": "aj ti", "PR": "pi ar", "SEO": "seo", "CTA": "ce te a", "FAQ": "ef a ku",
    "START": "start", "Reels": "rolki", "TikTok": "tik tok", "TikToka": "tik toka",
    "TikToku": "tik toku", "YouTube": "jutub", "YouTube'a": "jutuba",
    "YouTubie": "jutubie", "WhatsApp": "łotsap", "WhatsAppie": "łotsapie",
    "WhatsAppa": "łotsapa", "Instagram": "instagram", "Instagrama": "instagrama",
    "Instagramie": "instagramie", "Facebook": "fejsbuk", "Facebooka": "fejsbuka",
    "Facebooku": "fejsbuku", "online": "onlajn", "LIVE": "lajw", "Live": "lajw", "live": "lajw",
    "live'a": "lajwa", "live'ie": "lajwie", "PS": "postscriptum", "B2C": "bi tu si",
    "NIP": "nip", "VIP": "wip", "KRUS": "krus", "BIK": "bik", "CIT": "cit", "CEO": "si i oł",
}


def load_lexicon(path: Path | str | None = None) -> dict:
    """Written form → spoken form, from pl_lexicon.json; the built-in copy on any error."""
    try:
        data = json.loads(Path(path or _LEXICON_FILE).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data:
            raise ValueError("not a JSON object")
        return {str(k): str(v) for k, v in data.items() if str(k).strip() and str(v).strip()}
    except Exception:  # noqa: BLE001
        return dict(_LEXICON_BUILTIN)


LEXICON = load_lexicon()


def _lexicon_re(lex: dict) -> re.Pattern | None:
    keys = sorted(lex, key=len, reverse=True)
    if not keys:
        return None
    return re.compile(r"(?<![\w'’])(?:" + "|".join(re.escape(k) for k in keys) + r")(?![\w'’])")


_LEX_RE = _lexicon_re(LEXICON)

_UP = "A-ZĄĆĘŁŃÓŚŹŻ"
_LOW = "a-ząćęłńóśźż"
# «5 000», «5.000», «5 000» with a no-break space; a dot is a thousands mark
# only when exactly three digits and then a non-digit follow it
_INT = r"\d{1,3}(?:(?:[ \u00a0\u202f]|\.(?=\d{3}(?!\d)))\d{3})+(?!\d)|\d+"
_AMT = rf"(?<![\w,.])(?:{_INT})(?:[,.]\d+)?(?![\d])"
_AMT_PARSE = re.compile(r"(\d{1,3}(?:[ \u00a0\u202f.]\d{3})+|\d+)(?:[,.](\d+))?$")


def _amount(s: str) -> tuple[int, str]:
    """«5 000» → (5000, ""), «49,99» → (49, "99"), «2.5» → (2, "5")."""
    m = _AMT_PARSE.match(s.strip())
    return int(re.sub(r"\D", "", m.group(1))), (m.group(2) or "")


# Abbreviations whose dot is not a sentence end, as they are written.
_ABBR_WORDS = ("m.in. p.s. np. ok. tzn. tj. itd. itp. tzw. ul. godz. min. sek. prof. str. "
               "zob. ds. ws. tel. tys. proc. mies. tyg. szt. św. ew. dr. nr. wg. ps. r. w. vs.")
_ABBR_SET = set(_ABBR_WORDS.split()) | {"m. in.", "p. s."}
_ABBR_ANY = re.compile(
    r"(?<![\w.])(?i:m\.\s?in\.|p\.\s?s\.|np\.|ok\.|tzn\.|tj\.|itd\.|itp\.|tzw\.|ul\.|godz\.|"
    r"min\.|sek\.|prof\.|str\.|zob\.|ds\.|ws\.|tel\.|tys\.|proc\.|mies\.|tyg\.|szt\.|św\.|"
    r"ew\.|dr\.?|nr\.?|wg\.?|mln\.?|mld\.?|ps\.|vs\.?|c\.\s?d\.\s?n\.|cdn\.)(?!\w)")

_GEN_PREP = set("od do bez dla około ok u według wg podczas oprócz wśród spośród blisko "
                "koło sprzed zamiast powyżej poniżej spod znad obok wokół dookoła "
                "naprzeciw naprzeciwko".split())
_DAT_PREP = {"dzięki", "przeciw", "przeciwko", "ku"}
_NOT_LOC = {"strach", "zapach", "gmach", "dach", "piach", "ach", "gach"}

# Feminine nouns that often follow a number: «dwie godziny», «jedna osoba».
# Stems, so every case form matches; the ones that would also catch an
# adjective or a masculine noun («dobre», «kawałek», «poradnik») are listed
# whole in _FEM_EXACT, and _NOT_FEM keeps adjectives off the stems.
_FEM = tuple("godzin godzink minut sekund osob osób rzecz złotówk złotówek zasad reguł lekcj "
             "stron kobiet sesj metod wiadomoś książk książek rozmow chwil szans opcj cech "
             "decyzj zmian klientk strategi umiejętnoś histori platform aplikacj funkcj "
             "sytuacj rolk notatk strat tabel stref grup kampani odpowiedz możliwoś sztuk "
             "kalori dziewczyn butelk szklank łyżk wersj transakcj faktur umów umow prób "
             "córk córek siostr sióstr żon matk wnuczk prośb wypłat wskazówk wskazówek "
             "przyjaciółk przyjaciółek koleżank koleżanek babci babć podwyżk podwyżek ofert "
             "emerytur wizyt paczk paczek pożyczk pożyczek tabletk tabletek klientek "
             "partnerk partnerek".split())
# Whole families of feminine nouns: «wartość», «możliwości», «lekcja», «pasje»,
# «wizji». The -ość stem needs three letters so «gość» (a man) stays out.
_FEM_SUFFIX = re.compile(r"\w{3,}oś(?:ć|ci|cią|ciom|ciami|ciach)|\w{2,}[csz]j(?:a|e|i|ę|ą|om|ami|ach)")
_FEM_EXACT = set("noc nocy noce nocą nocami nocach nocom rada rady rad radę radą radzie "
                 "radami doba doby dób dobę dobą dobie kawa kawy kaw kawę kawą kawie "
                 "firma firmy firm firmę firmą firmie firmom firmami firmach porada porady "
                 "porad poradę poradą poradami praktyka praktyki praktyk praktykę".split())
# whole paradigms where a stem would also catch an adjective or a masculine
# noun: «rozmowy» and «umowy» end like «nowy» and were never feminine, so «2
# rozmowy» was «dwa rozmowy»; «mark» would catch «market» (final review, 2026-09-27)
_FEM_EXACT |= set(
    "rozmowa rozmowy rozmowę rozmową rozmowie rozmów rozmowom rozmowami rozmowach "
    "umowa umowy umowę umową umowie umów umowom umowami umowach "
    "marka marki markę marką marce marek markom markami markach "
    "praca prace pracy pracę pracą prac pracom pracami pracach "
    "droga drogi drogę drogą drodze dróg drogom drogami drogach "
    "sprawa sprawy sprawę sprawą sprawie spraw sprawom sprawami sprawach "
    "premia premie premii premię premią premiom premiami premiach "
    "nagroda nagrody nagrodę nagrodą nagrodzie nagród nagrodom nagrodami nagrodach "
    "szkoła szkoły szkołę szkołą szkole szkół szkołom szkołami szkołach "
    "rata raty ratę ratą racie rat ratom ratami ratach "
    "dieta diety dietę dietą diecie diet dietom dietami dietach "
    "część części częścią częściom częściami częściach".split())
_NOT_FEM = ("owy", "owe", "owa", "owych", "owym", "owymi", "owej", "ową", "nik", "niki", "ników",
            "nikiem", "nikach", "nikami", "niczy", "nicze", "nicza", "niczych")
# masculine-personal: «pięciu klientów», «dwóch ludzi»
_MP = set("ludzi mężczyzn facetów chłopaków klientów pracowników uczniów studentów przyjaciół "
          "partnerów liderów ekspertów lekarzy nauczycieli kolegów synów braci mentorów "
          "obserwujących znajomych specjalistów sprzedawców trenerów influencerów twórców "
          "członków polaków pracodawców przedsiębiorców inwestorów".split())


def _prev_word(before: str) -> str:
    """The word right before, lowercased; "" across a sentence end or a comma.

    «minus» is looked through: «od minus 5» needs the case «od» asks for.
    """
    m = re.search(r"([^\W\d_]+)(\.?)\s*$", before)
    if not m:
        return ""
    w = m.group(1).lower()
    if m.group(2) and w + "." not in _ABBR_SET:
        return ""                                # «Mam dom. 5 osób»: a new sentence
    if w == "minus" and not m.group(2):
        return _prev_word(before[:m.start()])
    return w


def _next_word(after: str) -> str:
    m = re.match(r"\s*([^\W\d_]+)", after)
    return m.group(1).lower() if m else ""


def _is_ins(w: str) -> bool:
    # «laty» is the old instrumental that survives in «przed pięcioma laty»
    return (len(w) > 3 and w.endswith("mi") and w not in {"sami", "tymi"}) or w == "laty"


def _is_loc(w: str) -> bool:
    return len(w) > 4 and w.endswith("ach") and w not in _NOT_LOC


# Genitive plurals that after 2-4 can only mean the genitive: «szukam 2 osób»
# was «dwie osób», «w wieku 52 lat» «pięćdziesiąt dwa lat», «2 córek» «dwie
# córek» (final review, 2026-09-27). Not «dni» or «rzeczy», which are also the
# nominative («dwa dni»). So is a feminine noun's -ek («partnerek», from
# «partnerka»); a masculine one is a singular («Krok 2 Wniosek» is a title).
_GEN_PL = set("osób lat kobiet firm godzin minut sekund córek sióstr książek lekcji groszy "
              "tygodni miesięcy stron zasad metod szans strat zmian sztuk sesji kalorii nocy "
              "prób rozmów umów wyświetleń polubień ćwiczeń marzeń pytań dziewczyn żon matek "
              "marek ofert szkół nagród dróg rat".split())
_NOT_GEN_EK = {"poniedziałek", "wtorek", "czwartek", "piątek", "człowiek", "kawałek", "początek"}
# «mamą 3 dzieci», «autorka 5 książek»: a noun that governs the genitive, taken
# as a cue only before the nouns a mother or an author has; «Mama 5 lat temu…»
# is the subject and a time
_GEN_HEAD = set("mama mamą matka matką tata tatą ojciec ojcem autor autorem autorka autorką "
                "właściciel właścicielem właścicielka właścicielką założyciel założycielem "
                "założycielka założycielką twórca twórcą babcia babcią dziadek dziadkiem".split())
_GEN_HEAD_NOUN = set("dzieci córek synów wnuków wnuczek wnucząt książek firm marek kursów "
                     "sklepów restauracji".split())


def _is_gen_pl(w: str) -> bool:
    return ((len(w) > 4 and w.endswith(("ów", "ych", "ich"))) or w in _GEN_PL
            or (len(w) > 4 and w.endswith("ek") and w not in _NOT_GEN_EK and _is_fem(w[:-2] + "ka")))


def _case_for(before: str, after: str = "", use_next: bool = True, n: int | None = None) -> str:
    p = _prev_word(before)
    if p in _GEN_PREP:
        return "gen"
    if p in _DAT_PREP:
        return "dat"
    if p == "wieku":
        return "gen"                                 # «w wieku 45 lat»: «czterdziestu pięciu lat»
    if use_next:
        nx = _next_word(after)
        if _is_ins(nx):
            return "ins"
        if _is_loc(nx):
            return "loc"
        # «z» takes the instrumental (checked above) or the genitive, never the
        # nominative: «z 3 miast», «z 10 osób», and at a phrase's end too: «Dzień
        # 1 z 30.» was «z trzydzieści». And «cztery» would need «kraje», so a
        # genitive plural after 2-4 means the genitive: «mam 2 innych».
        if p in ("z", "ze") or (nx and n is not None and _few(n) and _is_gen_pl(nx)):
            return "gen"
        if p in _GEN_HEAD and nx in _GEN_HEAD_NOUN:
            return "gen"
    return "nom"


_INS_PREP = {"z", "ze", "przed", "nad", "pod", "między"}
_LOC_PREP = {"o", "w", "we", "na", "przy", "po"}
# after these the counted noun is in the accusative, and a noun in -a there is a
# masculine animate one: «mam 1 syna» is «jednego», not «jedna»
_HAVE = set("mam masz ma mamy macie mają miałem miałam miał miała mieliśmy mieli znam "
            "poznałem poznałam zatrudniam zatrudniłem widzę widziałem szukam".split())
# neuter nouns in -ę, the only ones where «1 …ę» is not «jedną»
_NEUT_E = {"imię", "zwierzę", "ramię", "plemię", "szczenię", "kocię", "znamię", "brzemię"}


# «1 na 1», «1 z 5 osób», «1 na 10 klientów»: a preposition right after the 1.
# «na» was taken for a feminine noun in -a, «jedna na jeden» (final review,
# 2026-09-27). The counted noun comes after the second number, if at all.
_ONE_PREP = {"na", "z", "ze", "za", "dla", "do", "od", "spośród", "wśród"}
# masculine nouns in -a: «jeden kolega», «z jednym kolegą», not «jedna kolega»
_MASC_A = ("koleg", "mężczyzn", "specjalist", "artyst", "poet", "kierowc", "doradc", "twórc",
           "sprzedawc", "dentyst", "turyst", "sędzi", "znawc")
_MASC_A_EXACT = {"tata", "tatę", "tatą", "taty", "tacie"}


def _masc_a(w: str) -> bool:
    return w.startswith(_MASC_A) or w in _MASC_A_EXACT


def _one(before: str, after: str, case: str) -> str:
    """«1» before its noun, whose ending shows what the case heuristic cannot see.

    «z 1 osobą» → «jedną», «na 1 osobę» → «jedną», «z 1 klientem» → «jednym»,
    «po 1 dniu» → «jednym», «dla 1 klienta» → «jednego», «mam 1 syna» →
    «jednego»; in the genitive an -a noun is masculine («klienta», «dnia»),
    and -y/-i is feminine («marki»).
    """
    p, nx = _prev_word(before), _next_word(after)
    if nx in _ONE_PREP:
        m3 = re.match(r"\s*[^\W\d_]+\s+(\d[\d\s.,]*)?(.*)", after, re.S)
        g = "m"
        # «1 z 5 osób», «1 z moich klientek»: the whole it is one of; «1 na osobę»
        # or «1 z nich» say nothing about it
        if m3 and (m3.group(1) or nx in ("z", "ze", "spośród", "wśród")):
            rest = m3.group(2)
            g = "n" if _next_word(rest) in _CHILDREN else _gender_after(rest, 5)
        return spell(1, case, "m" if g == "mp" else g)
    if _masc_a(nx):
        if nx.endswith("ą"):
            return "jednym"                          # «z 1 kolegą»
        if nx.endswith(("ę", "i", "y")):
            return "jednego"                         # «mam 1 kolegę», «dla 1 kolegi»
        return spell(1, case, "m")                   # «przyszedł 1 kolega»
    fem = _is_fem(nx)
    if nx.endswith("ą") or (nx.endswith("ę") and nx not in _NEUT_E):
        return "jedną"
    # an adjective before the noun shows the form outright: «1 dobrego klienta»,
    # «dla 1 ważnej osoby», «z 1 dobrym klientem» (-ej/-ym only with a noun after,
    # «1 kolej» is a noun)
    m2 = re.match(r"\s*[^\W\d_]+\s+[^\W\d_]", after)
    if len(nx) > 4 and nx.endswith(("ego", "emu")):
        return "jednego" if nx.endswith("ego") else "jednemu"
    if len(nx) > 4 and m2 and nx.endswith(("ym", "im")):
        return "jednym"
    if len(nx) > 4 and m2 and nx.endswith("ej"):
        return "jednej"
    if (p in _INS_PREP and nx.endswith("em")) or nx == "razem":
        return "jednym"                              # «z 1 klientem», «za 1 razem»
    if p in _LOC_PREP and case in ("nom", "loc"):
        if len(nx) > 2 and nx.endswith("u") and not fem:
            return "jednym"                          # «po 1 dniu», «w 1 miesiącu»
        if fem and nx.endswith(("e", "i", "y")):
            return "jednej"                          # «na 1 stronie», «o 1 rzeczy»
    if case in ("nom", "acc"):
        # the verb may be further back in the clause: «mam 1 dziecko i 1 psa»
        clause = re.split(r"[.,;:!?…]", before)[-1].lower().split()
        if nx.endswith("a") and not fem and (p in _HAVE or _HAVE & set(clause)):
            return "jednego"
        return spell(1, case, _gender_after(after, 1))
    if case == "gen":
        return spell(1, case, "f" if fem or nx.endswith(("y", "i")) else "m")
    return spell(1, case, "f" if fem else "m")


def _is_fem(w: str) -> bool:
    return (w in _FEM_EXACT or (w.startswith(_FEM) and not w.endswith(_NOT_FEM))
            or bool(_FEM_SUFFIX.fullmatch(w)))


def _gender_for(word: str, n: int | None = None) -> str:
    if not word:
        return "m"
    if _is_fem(word):
        return "f"
    if word in _MP:
        return "mp"
    if n == 1:
        if _masc_a(word) or word in _ONE_PREP:
            return "m"
        if word.endswith("a"):
            return "f"
        if word.endswith(("o", "e", "ę", "um")):
            return "n"
    return "m"


_ADJ_END = ("ne", "re", "we", "te", "kie", "gie", "łe", "de", "ste", "nie", "ych", "ich",
            "ymi", "imi")


def _gender_after(after: str, n: int | None = None) -> str:
    """Gender of the counted noun, looking past one adjective: «2 proste zasady» → f.

    From two up, «proste» is the same before «zasady» and «pomysły», so the
    noun after it decides; for a lone 1 the adjective itself shows the gender.
    """
    m = re.match(r"\s*([^\W\d_]+)(?:\s+([^\W\d_]+))?", after)
    if not m:
        return "m"
    first, second = m.group(1).lower(), (m.group(2) or "").lower()
    g = _gender_for(first, n)
    if g == "m" and n != 1 and second and len(first) > 3 and first.endswith(_ADJ_END):
        g2 = _gender_for(second, n)
        if g2 in ("f", "mp"):
            return g2
    return g


def _sentence_start(before: str) -> bool:
    s = before.rstrip()
    if not s:
        return True
    if s[-1] in "!?…":
        return True
    if s[-1] == ".":
        tok = s.split()[-1].lower()
        return tok not in _ABBR_SET and not re.fullmatch(r"\d+\.", tok)
    return False


def _end_dot(after: str, trailing: bool = True) -> str:
    """The abbreviation's dot, kept when it also ends the sentence («itd.» at the end)."""
    if re.match(r"\s*[\"'”»)\]]*\s*$", after):
        return "."
    if trailing and re.match(rf"\s+[\"'„«(]?[{_UP}]", after):
        return "."
    return ""


def _apply(line: str, rx: re.Pattern, fn) -> str:
    """rx.sub with fn(m, before, after) → replacement or None (leave the match).

    A replacement that opens a sentence gets a capital letter, unless the
    written text began with a small letter («np.» stays «na przykład»).
    """
    def rep(m):
        before, after = m.string[:m.start()], m.string[m.end():]
        try:
            out = fn(m, before, after)
        except (ValueError, KeyError, IndexError):
            # «10 000 000 mln» is past the speller's range: leave it to the
            # later rules rather than fail a whole take over one odd token
            out = None
        if out is None:
            return m.group(0)
        if out and _sentence_start(before) and not m.group(0)[:1].islower():
            out = out[0].upper() + out[1:]
        return out
    return rx.sub(rep, line)


def _pad(before: str, after: str, words: str) -> str:
    """A symbol replaced by words, with a space on each side where a word touches it."""
    left = "" if (not before or before[-1].isspace() or before[-1] in "([„«\"'") else " "
    right = "" if (not after or after[0].isspace() or after[0] in ".,!?;:…)]\"”»") else " "
    return left + words + right


def _invariant(word: str) -> tuple[dict, dict]:
    return dict.fromkeys(CASES, word), dict.fromkeys(CASES, word)


_NOUNS = {
    "złoty": (_decl("złoty złotego złotemu złoty złotym złotym",
                    "złote złotych złotym złote złotymi złotych"), "m"),
    "grosz": (_decl("grosz grosza groszowi grosz groszem groszu",
                    "grosze groszy groszom grosze groszami groszach"), "m"),
    # accusative «dolar», to match «jeden»: «za jeden dolar» is how it is said
    "dolar": (_decl("dolar dolara dolarowi dolar dolarem dolarze",
                    "dolary dolarów dolarom dolary dolarami dolarach"), "m"),
    "cent": (_decl("cent centa centowi cent centem cencie",
                   "centy centów centom centy centami centach"), "m"),
    "euro": (_invariant("euro"), "n"),
    "procent": (_invariant("procent"), "m"),
    "kilometr": (_decl("kilometr kilometra kilometrowi kilometr kilometrem kilometrze",
                       "kilometry kilometrów kilometrom kilometry kilometrami kilometrach"), "m"),
    "metr": (_decl("metr metra metrowi metr metrem metrze",
                   "metry metrów metrom metry metrami metrach"), "m"),
    "centymetr": (_decl("centymetr centymetra centymetrowi centymetr centymetrem centymetrze",
                        "centymetry centymetrów centymetrom centymetry centymetrami "
                        "centymetrach"), "m"),
    "milimetr": (_decl("milimetr milimetra milimetrowi milimetr milimetrem milimetrze",
                       "milimetry milimetrów milimetrom milimetry milimetrami milimetrach"), "m"),
    "kilogram": (_decl("kilogram kilograma kilogramowi kilogram kilogramem kilogramie",
                       "kilogramy kilogramów kilogramom kilogramy kilogramami kilogramach"), "m"),
    "gram": (_decl("gram grama gramowi gram gramem gramie",
                   "gramy gramów gramom gramy gramami gramach"), "m"),
    "litr": (_decl("litr litra litrowi litr litrem litrze",
                   "litry litrów litrom litry litrami litrach"), "m"),
    "mililitr": (_decl("mililitr mililitra mililitrowi mililitr mililitrem mililitrze",
                       "mililitry mililitrów mililitrom mililitry mililitrami mililitrach"), "m"),
    "kilokaloria": (_decl("kilokaloria kilokalorii kilokalorii kilokalorię kilokalorią "
                          "kilokalorii", "kilokalorie kilokalorii kilokaloriom kilokalorie "
                          "kilokaloriami kilokaloriach"), "f"),
    "minuta": (_decl("minuta minuty minucie minutę minutą minucie",
                     "minuty minut minutom minuty minutami minutach"), "f"),
    "sekunda": (_decl("sekunda sekundy sekundzie sekundę sekundą sekundzie",
                      "sekundy sekund sekundom sekundy sekundami sekundach"), "f"),
    "godzina": (_decl("godzina godziny godzinie godzinę godziną godzinie",
                      "godziny godzin godzinom godziny godzinami godzinach"), "f"),
    "miesiąc": (_decl("miesiąc miesiąca miesiącowi miesiąc miesiącem miesiącu",
                      "miesiące miesięcy miesiącom miesiące miesiącami miesiącach"), "m"),
    "tydzień": (_decl("tydzień tygodnia tygodniowi tydzień tygodniem tygodniu",
                      "tygodnie tygodni tygodniom tygodnie tygodniami tygodniach"), "m"),
    "sztuka": (_decl("sztuka sztuki sztuce sztukę sztuką sztuce",
                     "sztuki sztuk sztukom sztuki sztukami sztukach"), "f"),
    "raz": (_decl("raz razu razowi raz razem razie",
                  "razy razy razom razy razami razach"), "m"),
    "stopień": (_decl("stopień stopnia stopniowi stopień stopniem stopniu",
                      "stopnie stopni stopniom stopnie stopniami stopniach"), "m"),
}
_UNIT_ABBR = {"km": "kilometr", "kg": "kilogram", "g": "gram", "m": "metr", "cm": "centymetr",
              "mm": "milimetr", "l": "litr", "ml": "mililitr", "kcal": "kilokaloria",
              "min": "minuta", "sek": "sekunda", "s": "sekunda", "h": "godzina",
              "godz": "godzina", "mies": "miesiąc", "tyg": "tydzień", "szt": "sztuka",
              "msc": "miesiąc"}
_SCALE_ABBR = {"tys": 10 ** 3, "k": 10 ** 3, "mln": 10 ** 6, "mld": 10 ** 9}
_SCALE_NOUN = {v: noun for v, noun in _SCALES}
_CURRENCY = {"zł": "złoty", "ZŁ": "złoty", "Zł": "złoty", "PLN": "złoty", "gr": "grosz", "€": "euro", "EUR": "euro",
             "$": "dolar", "USD": "dolar"}
_SUBUNIT = {"złoty": "grosz", "euro": "cent", "dolar": "cent"}
# «msc» is how «miesiąc» is often shortened: «5000 zł/msc» was «złotych msc»
_PER = {"mies": "miesięcznie", "miesiąc": "miesięcznie", "mc": "miesięcznie", "msc": "miesięcznie",
        "m-c": "miesięcznie", "rok": "rocznie", "r": "rocznie", "tyg": "tygodniowo",
        "h": "za godzinę", "godz": "za godzinę", "godzinę": "za godzinę",
        "os": "za osobę", "osobę": "za osobę", "szt": "za sztukę"}


def _half(n: int, gender: str) -> str:
    """n and a half: «pół», «półtora» («półtorej godziny»), «dwa i pół»."""
    if n == 0:
        return "pół"
    if n == 1:
        return "półtorej" if gender == "f" else "półtora"
    return spell(n, "nom", "m" if gender == "mp" else gender) + " i pół"


def _decimal(n: int, frac: str, gender: str = "m") -> str:
    """«2,5» → «dwa i pół», «3,75» → «trzy przecinek siedemdziesiąt pięć».

    A fraction is always said in the nominative: «od 2,5 kilometra» as «od
    dwóch i pół» is rare even in speech, and the AI pass knows better.
    """
    frac = frac.rstrip("0")
    if not frac:
        return spell(n, "nom", gender)
    if frac == "5":
        return _half(n, gender)
    lead = len(frac) - len(frac.lstrip("0"))
    return (spell(n) + " przecinek " + "zero " * lead + spell(int(frac))).strip()


def _say_number(n: int, frac: str, case: str, gender: str) -> str:
    if frac.rstrip("0"):
        return _decimal(n, frac, gender)
    return spell(n, case, gender)


def _quantity(n: int, frac: str, case: str, noun_key: str | None = None,
              scale: int = 1, money: bool = False) -> str:
    """A number with its unit, both in the right form.

    «5 min» → «pięć minut», «2 h» → «dwie godziny», «2,5 km» → «dwa i pół
    kilometra», «49,99 zł» → «czterdzieści dziewięć złotych dziewięćdziesiąt
    dziewięć groszy», «2,5 tys. zł» → «dwa i pół tysiąca złotych».
    """
    noun, gender = _NOUNS[noun_key] if noun_key else (None, "m")
    frac_s = frac.rstrip("0")
    if scale > 1:
        scale_noun = _SCALE_NOUN[scale]
        whole = n * scale + (int(frac_s) * scale // 10 ** len(frac_s) if frac_s else 0)
        exact = not frac_s or (int(frac_s) * scale) % 10 ** len(frac_s) == 0
        if frac_s == "5":
            head = _half(n, "m") + " " + scale_noun[0]["gen"]
        elif exact:
            head = spell(whole, case, "m")
        else:
            head = _decimal(n, frac, "m") + " " + scale_noun[0]["gen"]
        if noun is None:
            return head
        return head + " " + noun[1]["gen"]       # «tysięcy złotych», «miliona euro»
    if money and frac_s and len(frac) <= 2 and noun_key in _SUBUNIT:
        cents = int(frac.ljust(2, "0"))
        sub, sub_gender = _NOUNS[_SUBUNIT[noun_key]]
        parts = []
        if n:
            parts.append(spell(n, case, gender) + " " + _agree(n, case, noun))
        parts.append(spell(cents, case, sub_gender) + " " + _agree(cents, case, sub))
        return " ".join(parts)
    if frac_s:
        head = _decimal(n, frac, gender)
        return head + (" " + noun[0]["gen"] if noun else "")
    if noun is None:
        return spell(n, case, gender)
    return spell(n, case, gender) + " " + _agree(n, case, noun)


_MONTHS = ("stycznia lutego marca kwietnia maja czerwca lipca sierpnia września "
           "października listopada grudnia").split()
_GODZINA = dict(nom="godzina", gen="godziny", dat="godzinie", acc="godzinę", ins="godziną",
                loc="godzinie")
_LETTERS = dict(A="a", B="be", C="ce", D="de", E="e", F="ef", G="gie", H="ha", I="i", J="jot",
                K="ka", L="el", M="em", N="en", O="o", P="pe", Q="ku", R="er", S="es", T="te",
                U="u", V="fał", W="wu", X="iks", Y="igrek", Z="zet", Ą="ą", Ć="cie", Ę="ę",
                Ł="eł", Ń="eń", Ó="u", Ś="eś", Ź="ziet", Ż="żet")
# Common words written in capitals for emphasis: read as words, not spelled.
_CAPS_WORDS = set("to jest nie tak jak co na do za ale bez dla ten ta te tu tam ty ja my wy on "
                  "ona oni mam masz ma się już też czy kto gdy lub być był była może jeden dwa "
                  "sto raz dom czas dziś teraz stop top hit wow hej halo plan cel cele krok rok "
                  "dni noc moc kod link bio info fakt mit mity błąd rada test tego tym ich jej "
                  "go mu mi ci mnie nas was im jego twój moja mój nic zero szok nowe nowy nowa "
                  "tylko sale free new mega sam sama samo sami wiem keto eko fit hot vege musi "
                  "daj moje moi nasz nasza twoja twoje swoje".split())
_PL_LETTER = re.compile("[ĄĆĘŁŃÓŚŹŻ]")
_CAP_VOWEL = re.compile("[AEIOUYĄĘÓ]")


def _caps_word(t: str) -> bool:
    """A token in capitals read as a word, not spelled: five letters or more, a
    common word, or one with a Polish letter and a vowel. «CHCĘ» was spelled «ce
    ha ce ę» and «MEGA» «em e gie a» (final review, 2026-09-27); «ŁKS» has no
    vowel and is still spelled.
    """
    return (len(t) >= 5 or t.lower() in _CAPS_WORDS
            or bool(_PL_LETTER.search(t) and _CAP_VOWEL.search(t)))


_LIST_MARK = re.compile(rf"^(\s*)\d{{1,2}}\.\s+(?=[\"„«(]?[{_UP}])")
_LIST_PAREN = re.compile(r"^(\s*)\d{1,2}\)\s+")


def _r_list(line: str) -> str:
    # «1. Zapisuj…» is a list bullet, as synth's cleaner has always treated it
    return _LIST_PAREN.sub(r"\1", _LIST_MARK.sub(r"\1", line))


def _r_lexicon(line: str) -> str:
    if _LEX_RE is None:
        return line
    return _apply(line, _LEX_RE, lambda m, b, a: LEXICON.get(m.group(0)))


_TILDE = re.compile(r"[~≈]\s*(?=\d)")
_PLUS_AFTER = re.compile(rf"({_AMT})\+(?=\s+[{_LOW}])")
# a minus glued to a number: «-5 stopni», «o -20%»; not the hyphen of «3-4»,
# «600-700-800» or «e-5», nor a dash with a space after it
_MINUS = re.compile(r"(?<![\w.,])(?<!\d\s)[-−–](?=\d)")
_HASH_NUM = re.compile(r"#\s*(?=\d)")


def _r_approx(line: str) -> str:
    # «~5 km» → «około 5 km», «10 000+ osób» → «ponad 10 000 osób»; the number
    # rules then read the amount in the case «około»/«ponad» need. A minus left
    # for XTTS is not read at all, so «-5 stopni» came out as «pięć stopni».
    # «#1» is «numer 1», where XTTS would say «krzyżyk».
    line = _apply(line, _TILDE, lambda m, b, a: _pad(b, "x", "około"))
    line = _apply(line, _MINUS, lambda m, b, a: _pad(b, "x", "minus"))
    line = _apply(line, _HASH_NUM, lambda m, b, a: _pad(b, "x", "numer"))
    return _apply(line, _PLUS_AFTER, lambda m, b, a: "ponad " + m.group(1))


def _group_say(g: str) -> str:
    """A phone group digit for digit where it starts with zeros: «070» → «zero siedemdziesiąt»."""
    rest = g.lstrip("0")
    return ("zero " * (len(g) - len(rest)) + (spell(int(rest)) if rest else "")).strip()


_PHONE3 = re.compile(r"(?<![\w+])(?<!\d[\s-])(?:\+\s?(\d{2,3})[\s-]?)?(\d{3})[\s-](\d{3})[\s-]"
                     r"(\d{3})(?!\d|[\s-]\d)")
_PHONE_LAND = re.compile(r"(?<![\w+])(?<!\d[\s-])(?:\+\s?(\d{2})[\s-]?)?(\d{2})[\s-](\d{3})"
                         r"[\s-](\d{2})[\s-](\d{2})(?!\d|[\s-]\d)")
_PHONE_BARE = re.compile(r"(?<![\w+,.])(?:\+(\d{2,3})\s?)?(\d{9,12})(?![\d,.]\d|\d)")
_NOT_PHONE_AFTER = re.compile(r"\s*(?:zł|ZŁ|PLN|€|\$|%|tys|mln|mld|złotych|euro|dolarów|osób|ludzi)")


def _phone(code: str | None, groups: list[str]) -> str:
    head = ["plus " + spell(int(code))] if code else []
    return " ".join(head + [_group_say(g) for g in groups])


def _r_phone(line: str) -> str:
    def grouped(m, before, after):
        code, groups = m.group(1), [g for g in m.groups()[1:]]
        # «100 000 000 zł» is a price, not a phone number
        if not code and (_NOT_PHONE_AFTER.match(after) or groups[-1] == groups[-2] == "000"):
            return None
        return _phone(code, groups)

    def bare(m, before, after):
        s = m.group(2)
        # «1000000000 wyświetleń» is an amount: no phone number ends in six zeros
        if not m.group(1) and (_NOT_PHONE_AFTER.match(after) or s.endswith("000000")):
            return None
        return _phone(m.group(1), [s[i:i + 3] for i in range(0, len(s), 3)])

    for rx in (_PHONE3, _PHONE_LAND):
        line = _apply(line, rx, grouped)
    return _apply(line, _PHONE_BARE, bare)


_DATE_FULL = re.compile(r"(?<![\w.,])(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s*(r\.|roku(?!\w)))?(?!\d)")
_DATE_ISO = re.compile(r"(?<![\w.,-])(\d{4})-(\d{2})-(\d{2})(?![\d-])")
# «1. września» may carry an ordinal's dot: without it here the ordinal rule
# took the month for the noun it agrees with, «pierwsza września» (final review,
# 2026-09-27). «3. Maja» with a capital is a sentence end and a name.
_DATE_WORD = re.compile(r"(?<![\w.,])(\d{1,2})(\.?)\s+(" + "|".join(_MONTHS) + r")(?!\w)"
                        r"(?:\s+(\d{4})(?!\d)(?:\s*(r\.|roku(?!\w)))?)?", re.IGNORECASE)
_DATE_SHORT = re.compile(r"(?<![\w.,])(\d{1,2})\.(\d{2})(?!\d|\.\d)"
                         r"(?!\s*(?:zł|PLN|€|\$|%|km|kg|h|min|tys|mln|mld))")
# The first day of a range or a list before a month: «7-8 listopada» came out
# «siedmioósmego» (glued by the compound rule), «7 i 8 listopada» «siedem i
# ósmego», «od 7 do 8 listopada» «od siedmiu do ósmego» (final review,
# 2026-09-27). Every day is a genitive ordinal, and the dash is «od … do …».
_DAY_GEN = "|".join(sorted({ordinal(d, "gen") for d in range(1, 32)}, key=len, reverse=True))
_DAY_LINK = r"(?:\s*[-–—]\s*|\s*,\s*|\s+(?:i|oraz|lub|albo|do)\s+)"
_DATE_FIRST = re.compile(rf"(?<![\w.,])(\d{{1,2}})\.?(?P<link>{_DAY_LINK})(?=(?:{_DAY_GEN})"
                         rf"(?:{_DAY_LINK}(?:{_DAY_GEN}))*\s+(?:{'|'.join(_MONTHS)})(?!\w))",
                         re.IGNORECASE)
_DATE_CTX = {"dnia", "dniu", "dzień", "od", "do", "na", "w", "we", "z", "ze", "przed", "po",
             "poniedziałek", "wtorek", "środa", "środę", "czwartek", "piątek", "sobota",
             "sobotę", "niedziela", "niedzielę"}


def _date(d: int, mo: int, y, rok: str | None, after: str, month: str | None = None):
    if not (1 <= d <= 31 and 1 <= mo <= 12):
        return None
    out = ordinal(d, "gen") + " " + (month or _MONTHS[mo - 1])
    if y is not None:
        out += " " + ordinal(int(y), "gen") + " roku"
    if rok == "r.":
        out += _end_dot(after)
    return out


def _r_dates(line: str) -> str:
    line = _apply(line, _DATE_FULL, lambda m, b, a: _date(
        int(m.group(1)), int(m.group(2)), m.group(3), m.group(4), a))
    line = _apply(line, _DATE_ISO, lambda m, b, a: _date(
        int(m.group(3)), int(m.group(2)), m.group(1), None, a))
    line = _apply(line, _DATE_WORD, lambda m, b, a: None if m.group(2) and m.group(3)[:1].isupper()
                  else _date(int(m.group(1)), 1, m.group(4), m.group(5), a, month=m.group(3)))
    line = _apply(line, _DATE_SHORT, lambda m, b, a: _date(
        int(m.group(1)), int(m.group(2)), None, None, a) if _short_date(_prev_word(b)) else None)
    for _ in range(8):                   # «7, 8 i 9 listopada»: one day at a time, from the month back
        new = _apply(line, _DATE_FIRST, _first_day)
        if new == line:
            break
        line = new
    return line


def _first_day(m, before: str, after: str) -> str | None:
    d = int(m.group(1))
    if not 1 <= d <= 31:
        return None
    link, p = m.group("link").strip().lower(), _prev_word(before)
    day = ordinal(d, "gen")
    if link == "do":                     # «od 7 do 8 listopada»
        return day + " do " if p in ("od", "z", "ze") else None
    if link in ("-", "–", "—"):          # «7-8 listopada» → «od siódmego do ósmego listopada»
        return day + ", " if p in ("od", "do", "z", "ze") else "od " + day + " do "
    return day + (", " if link == "," else " " + link + " ")


def _short_date(prev: str) -> bool:
    """«12.10» is a date unless a word before it makes it a time («o 12.10»).

    Polish writes a decimal with a comma, so a dot between a day and a
    two-digit month is a date; with a date word only, «Spotkanie 12.10» was
    read «dwanaście przecinek jeden».
    """
    return prev in _DATE_CTX or prev not in _TIME_DOT_CTX


_YEAR_R = re.compile(r"(?<![\w.,])(\d{4})\s*(r\.|roku(?!\w))")
_YEAR_ROK = re.compile(r"(?<![\w.,])(\d{4})\s+rok(?!\w)")
_YEAR_BARE = re.compile(r"(?<![\w.,])((?:19|20)\d{2})(?!\d|[.,]\d)")
_YEAR_AFTER = re.compile(r"\s*(?:$|[.,!?;:…)\]\"”»]|(?:do|i|oraz|a|albo|lub|czy)(?!\w))")
_ROK = dict(nom="rok", gen="roku", dat="rokowi", acc="rok", ins="rokiem", loc="roku")
# «w maju 2026», «styczeń 2026 r.»: after a month the year is a genitive ordinal
_MONTH_ANY = _MONTHS + ("styczeń luty marzec kwiecień maj czerwiec lipiec sierpień wrzesień "
                        "październik listopad grudzień styczniu lutym marcu kwietniu maju "
                        "czerwcu lipcu sierpniu wrześniu październiku listopadzie "
                        "grudniu").split()
_YEAR_MONTH = re.compile(r"(?<![\w])(" + "|".join(_MONTH_ANY) + r")\s+((?:19|20)\d{2})(?!\d|[.,]\d)"
                         r"(?:\s*(r\.|roku(?!\w)))?", re.IGNORECASE)
# «w maju 2000 osób», «w maju 2000 zł», «od 2000 kcal», «w 2000 dni»: a counted
# noun or a unit after it makes the number an amount, not a year
_NOT_YEAR_AFTER = re.compile(
    r"\s*(?:[^\w\s.,!?;:…)\]\"”»]|(?:zł|ZŁ|Zł|PLN|EUR|USD|tys|mln|mld|k|km|kg|g|m|cm|mm|l|ml|"
    r"kcal|min|sek|s|h|godz|mies|tyg|szt|msc|osób|ludzi|razy|dni|lat|kobiet|firm|godzin|minut|"
    r"sekund|sztuk|stron|rzeczy|zasad|kalorii|lekcji|zdjęć|słów|groszy|euro|par|dzieci|braci|"
    r"przyjaciół|lekarzy|nauczycieli|[^\W\d_]*(?:ów|ych|ich|ek|ami|ach|eń|ań))(?!\w))")
# a year may open a story before its verb: «W 2020 straciłem pracę», «Od 2021
# pracuję zdalnie» were read as amounts, «od dwóch tysięcy dwudziestu jeden»
# (final review, 2026-09-27). Not after «z» or «około», where an amount is as likely.
_YEAR_VERB_PREP = {"w", "we", "po", "przed", "od", "do", "sprzed", "na", "przez"}
# «w latach 90.», «lata 80.», «od lat 70»: decades are plural ordinals
_DECADE = re.compile(r"(?<![\w])(lata|lat|latach|latami|latom)\s+([1-9]0)(\.?)(?!\d|[,.]\d|-)",
                     re.IGNORECASE)
_LATA_CASE = {"lata": "nom", "lat": "gen", "latach": "loc", "latami": "ins", "latom": "dat"}


def _year_case(before: str) -> str | None:
    p = _prev_word(before)
    if p in ("w", "we", "po"):
        return "loc"
    if p == "przed":
        return "ins"
    if p in ("od", "do", "z", "ze", "sprzed", "około", "ok"):
        return "gen"
    if p in ("na", "przez"):
        return "acc"                     # «plany na 2027 r.»: «na dwa tysiące dwudziesty siódmy rok»
    return None


def _r_years(line: str) -> str:
    def with_rok(m, before, after):
        case = _year_case(before) or "gen"
        return (ordinal(int(m.group(1)), case) + " " + _ROK[case]
                + (_end_dot(after) if m.group(2) == "r." else ""))

    def bare(m, before, after):
        p = _prev_word(before)
        if p in ("roku", "rok"):
            # «w roku 2026»: the noun is already there, the year agrees with it
            head = before.rstrip()[:-len(p)]
            case = "nom" if p == "rok" else ("loc" if _prev_word(head) in ("w", "we") else "gen")
        else:
            case = _year_case(before)
            if case is None:
                return None
            if not _YEAR_AFTER.match(after) and (
                    _prev_word(before) not in _YEAR_VERB_PREP or _NOT_YEAR_AFTER.match(after)
                    or not re.match(r"\s+[^\W\d_]", after)):
                return None
        return ordinal(int(m.group(1)), case)

    def month_year(m, before, after):
        rok = m.group(3)
        if not rok and _NOT_YEAR_AFTER.match(after):
            return None
        return (m.group(1) + " " + ordinal(int(m.group(2)), "gen")
                + (" roku" + (_end_dot(after) if rok == "r." else "") if rok else ""))

    def decade(m, before, after):
        # «przez lata 20 osób pracowało» counts people: after «lat»/«lata» a
        # decade needs its dot or the end of the phrase
        if not m.group(3) and _NOT_YEAR_AFTER.match(after):
            return None                              # «w ostatnich latach 20 osób odeszło»
        if (m.group(1).lower() in ("lat", "lata") and not m.group(3)
                and not re.match(r"\s*(?:$|[,;:!?…)\]\"”»]|(?:do|i|oraz|a|aż|to|ubiegłego|"
                                 r"zeszłego|poprzedniego|XX|XXI)(?!\w))", after)):
            return None
        word = ordinal(int(m.group(2)), _LATA_CASE[m.group(1).lower()], "pl")
        return m.group(1) + " " + word + (_end_dot(after) if m.group(3) else "")

    line = _apply(line, _DECADE, decade)
    line = _apply(line, _YEAR_MONTH, month_year)
    line = _apply(line, _YEAR_R, with_rok)
    line = _apply(line, _YEAR_ROK, lambda m, b, a: ordinal(int(m.group(1)), "nom") + " rok")
    return _apply(line, _YEAR_BARE, bare)


_ROMAN_OK = re.compile(r"M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})")
_ROMAN_VAL = dict(I=1, V=5, X=10, L=50, C=100, D=500, M=1000)


def _roman(s: str) -> int | None:
    if not s or not _ROMAN_OK.fullmatch(s):
        return None
    total = 0
    for a, b in zip(s, s[1:] + " "):
        v = _ROMAN_VAL[a]
        total += -v if b != " " and _ROMAN_VAL[b] > v else v
    return total or None


_CENT_AFTER = {"wiek": ("nom", "m"), "wieku": (None, "m"), "wiekiem": ("ins", "m"),
               "kwartał": ("nom", "m"), "kwartału": ("gen", "m"), "kwartale": ("loc", "m"),
               "kwartałem": ("ins", "m"), "edycja": ("nom", "f"), "edycji": ("gen", "f"),
               "edycję": ("acc", "f"), "edycją": ("ins", "f"), "tysiąclecie": ("nom", "n"),
               "tysiąclecia": ("gen", "n"), "tysiącleciu": ("loc", "n"),
               "tysiącleciem": ("ins", "n")}


def _ctx_nouns() -> dict:
    """Nouns a number after which is an ordinal («rozdział 2», «w klasie 3»): form → (case, gender)."""
    out: dict[str, tuple[str, str]] = {}
    for forms, gender in (("rozdział rozdziału rozdziałowi rozdział rozdziałem rozdziale", "m"),
                          ("część części części część częścią części", "f"),
                          ("tom tomu tomowi tom tomem tomie", "m"),
                          ("klasa klasy klasie klasę klasą klasie", "f"),
                          ("etap etapu etapowi etap etapem etapie", "m"),
                          ("edycja edycji edycji edycję edycją edycji", "f"),
                          ("sezon sezonu sezonowi sezon sezonem sezonie", "m"),
                          ("lekcja lekcji lekcji lekcję lekcją lekcji", "f"),
                          ("odcinek odcinka odcinkowi odcinek odcinkiem odcinku", "m")):
        for case, form in zip(CASES, forms.split()):
            out.setdefault(form, (case, gender))    # «części»: the genitive, same ending
    return out


_CTX_NOUNS = _ctx_nouns()

_ORD_COMB = {1: "pierwszo", 2: "drugo", 3: "trzecio", 4: "czwarto", 5: "piąto", 6: "szósto",
             7: "siódmo", 8: "ósmo", 9: "dziewiąto"}
_R = "[IVXLCDM]+"


def _comb_card(v: int) -> str:
    """The first part of a compound adjective: 30 → «trzydziesto» («trzydziestoletni»),
    100 → «stu» («stuprocentowy»), 21 → «dwudziestojedno»."""
    if v < 2:
        return ("zero", "jedno")[v]
    h, r = divmod(v, 100)
    out = _COMB[h * 100] if h else ""
    if r == 1:
        out += "jedno"
    elif r in _COMB:
        out += _COMB[r]
    elif r:
        out += _COMB[r - r % 10] + ("jedno" if r % 10 == 1 else _COMB[r % 10])
    return out


def _comb_century(v: int) -> str:
    """«XX-wieczny» → «dwudziesto», «XXI-wieczny» → «dwudziestopierwszo»."""
    return _COMB.get(v) or (_COMB[v - v % 10] + _ORD_COMB[v % 10])


def _suffix_form(n: int, tail: str, cardinal: bool = True) -> str | None:
    """A number with its written ending: «2-go» → «drugiego», «90-tych» →
    «dziewięćdziesiątych», «1-szy» → «pierwszy», «5-ciu» → «pięciu».

    The ending picks the one ordinal (or cardinal) form that ends with it;
    None when there is none («30-letni» is a compound) or more than one. A
    bare «-ch» is the cardinal: «2-ch» is how «dwóch» gets written.
    """
    def ending_with(forms):
        return {f for f in forms if f.endswith(tail) and len(f.rsplit(" ", 1)[-1]) > len(tail)}
    ords = ending_with({ordinal(n, c, g) for c in CASES for g in ("m", "f", "n", "pl")})
    cards = ending_with({spell(n, c, g) for c in CASES for g in ("m", "f", "n", "mp")}
                        if cardinal else set())
    hits = cards if cards and (not ords or len(tail) <= 2) else ords
    return hits.pop() if len(hits) == 1 else None


# «40-tce», «50-tka», «18-tka», «100-tkę», «40stce»: the noun Poles make of a
# number, most often an age. The compound rule made «czterdziestotce» of it, a
# word that does not exist, and the check refused the AI's right «czterdziestce»
# (final review, 2026-09-27). From 10 up it is the ordinal's stem and the
# ending without its t («czterdziest-ce», «set-ka»); 1-9 have stems of their own.
_MILESTONE_END = "ka|ki|ce|kę|ką|ek|kom|kami|kach"
_MILESTONE = re.compile(rf"(\d{{1,3}})(?:-((?:s?t)?(?:{_MILESTONE_END}))|(s?t(?:{_MILESTONE_END})))")
_UNIT_NOUN = {1: "jedyn", 2: "dwój", 3: "trój", 4: "czwór", 5: "piąt", 6: "szóst", 7: "siódem",
              8: "ósem", 9: "dziewiąt"}


def _milestone(token: str) -> str | None:
    """«40-tce» → «czterdziestce», «5-tka» → «piątka», «100-tkę» → «setkę»; None for other words."""
    m = _MILESTONE.fullmatch(token)
    if not m:
        return None
    v, end = int(m.group(1)), re.sub(r"^s?t", "", m.group(2) or m.group(3))
    if v in _UNIT_NOUN:
        stem = _UNIT_NOUN[v]
    elif 10 <= v < 20:
        stem = _ORD_TEENS[v - 10]
    elif v < 100 and v % 10 == 0 and v:
        stem = _ORD_TENS[v // 10]
    elif v == 100:
        stem = "set"
    else:
        return None                      # «21-ka»: no one word for it
    return stem + end


def _compound(token: str) -> tuple[str, int | None] | None:
    """How a number joined to a word by a hyphen is said, and the number it says.

    «30-letni» → («trzydziestoletni», None), a compound adjective;
    «2-go» → («drugiego», 2), «XX-tego» → («dwudziestego», 20), a number with
    its written ending; «XX-wieczny» → («dwudziestowieczny», None);
    «40-tce» → («czterdziestce», None), a number made a noun.
    """
    said = _milestone(token)
    if said:
        return said, None
    head, _, tail = token.partition("-")
    if not tail:
        return None
    if head.isdigit():
        v = int(head)
        said = _suffix_form(v, tail)
        if said:
            return said, v
        if tail in _WORDS:
            return None                  # «7-ósmego» is a range of days, never «siedmioósmego»
        return (_comb_card(v) + tail, None) if len(tail) >= 3 and v < 1000 else None
    v = _roman(head)
    if not v:
        return None
    said = _suffix_form(v, tail, cardinal=False)
    if said:
        return said, v
    return (_comb_century(v) + tail, None) if tail.startswith("wieczn") and v < 100 else None


def _compound_word(token: str) -> str | None:
    """«30-letni» → «trzydziestoletni», «XX-wieczny» → «dwudziestowieczny», «2-go» → «drugiego»."""
    c = _compound(token)
    return c[0] if c else None


_ROMAN_BEFORE = re.compile(rf"(?<![\w.])({_R})(?:\s*(w\.)(?!\w)|\s+("
                           + "|".join(_CENT_AFTER) + rf")(?!\w)|-(wieczn[{_LOW}]*))")
_ROMAN_AFTER = re.compile(r"(?<![\w])(" + "|".join(sorted(_CTX_NOUNS, key=len, reverse=True))
                          + rf")\s+(?:({_R})|(\d{{1,2}}))(?![\w]|[,.]\d)", re.IGNORECASE)
_ROMAN_NAME = re.compile(rf"(?<![\w])([{_UP}][{_LOW}]+)\s+([IVX]{{2,}})(?![\w])")
_ROMAN_NOUN = re.compile(rf"(?<![\w.])([IVX]{{2,}})(?=\s+[{_LOW}])")
# «I miejsce», «I etap», «I rata»: a Roman one before a noun that counts. It was
# read «i miejsce», never flagged for the AI, and the AI's «pierwsze miejsce»
# was refused (final review, 2026-09-27). A closed list: before any other word
# «I» is the conjunction.
_ROMAN_I_NOUNS = set(
    "miejsce miejsca miejscu miejscem etap etapu etapie etapem rata raty ratę racie ratą "
    "część części częścią stopień stopnia stopniu stopniem klasa klasy klasę klasie klasą "
    "edycja edycji edycję edycją runda rundy rundę rundzie rundą tura tury turę turze turą "
    "nagroda nagrody nagrodę nagrodzie nagrodą półrocze półrocza półroczu kwartał kwartału "
    "kwartale semestr semestru semestrze liga ligi ligę lidze".split())
_ROMAN_I = re.compile(r"(?<![\w.])I(?=\s+(?:" + "|".join(sorted(_ROMAN_I_NOUNS, key=len, reverse=True))
                      + r")(?!\w))")


def _ord_noun_form(before: str, noun: str) -> tuple[str, str]:
    """Case and gender of an ordinal from the noun after it and the preposition before it."""
    p = _prev_word(before)
    if p in ("w", "we", "na", "o", "przy", "po"):
        case = "loc"
    elif p in _GEN_PREP:
        case = "gen"
    elif p in ("z", "ze") and noun.endswith("ą"):
        case = "ins"
    else:
        case = "nom"
    # «zdobyłam 3. nagrodę», «II nagrodą»: the noun's ending shows the case the
    # verb gave it; -ę and -ą are feminine unless the noun is «kolega»-like
    if case == "nom" and ((noun.endswith("ę") and noun not in _NEUT_E) or noun.endswith("ą")):
        return ("acc" if noun.endswith("ę") else "ins"), ("m" if _masc_a(noun) else "f")
    if _is_fem(noun) or (case == "nom" and noun.endswith("a")):
        gender = "f"
    elif case == "nom" and noun.endswith(("e", "o", "um", "ę")):
        gender = "n"
    else:
        gender = "m"
    return case, gender


def _r_roman(line: str) -> str:
    def before_noun(m, before, after):
        v = _roman(m.group(1))
        if v is None or (len(m.group(1)) < 2 and not m.group(3)):
            return None
        p = _prev_word(before)
        if m.group(2):                                   # «XXI w.»
            case = "loc" if p in ("w", "we") else ("ins" if p == "przed" else "gen")
            return (ordinal(v, case) + " " + ("wiekiem" if case == "ins" else "wieku")
                    + _end_dot(after))
        if m.group(3):
            case, g = _CENT_AFTER[m.group(3).lower()]
            if case is None:
                case = "loc" if p in ("w", "we") else "gen"
            return ordinal(v, case, g) + " " + m.group(3)
        if v >= 100:
            return None
        return _comb_century(v) + m.group(4)             # «XX-wieczny» → «dwudziestowieczny»

    def after_noun(m, before, after):
        case, g = _CTX_NOUNS[m.group(1).lower()]
        if m.group(2):
            v = _roman(m.group(2))
            if v is None or (len(m.group(2)) == 1 and m.group(2) not in "IVX"):
                return None
        else:
            v = int(m.group(3))
        return m.group(1) + " " + ordinal(v, case, g)

    def name(m, before, after):
        # «Zająłem II miejsce»: a verb capitalized at the sentence start, not a
        # name; the noun rule below reads «drugie miejsce» (it was «drugi»)
        if _sentence_start(before) and re.match(rf"\s+[{_LOW}]", after):
            return None
        v = _roman(m.group(2))
        return None if v is None else m.group(1) + " " + ordinal(v)   # «Jan Paweł II»

    def noun(m, before, after):
        v = _roman(m.group(1))
        if v is None:
            return None
        case, g = _ord_noun_form(before, _next_word(after))
        return ordinal(v, case, g)                       # «II etap», «III edycja»

    line = _apply(line, _ROMAN_BEFORE, before_noun)
    line = _apply(line, _ROMAN_AFTER, after_noun)
    line = _apply(line, _ROMAN_NAME, name)
    line = _apply(line, _ROMAN_NOUN, noun)
    return _apply(line, _ROMAN_I, lambda m, b, a: ordinal(1, *_ord_noun_form(b, _next_word(a))))


_TIME_CASE = {"o": "loc", "po": "loc", "od": "gen", "do": "gen", "około": "gen", "ok": "gen",
              "przed": "ins", "między": "ins", "na": "acc", "godzinie": "loc",
              "godziny": "gen", "godzinę": "acc", "godziną": "ins", "godzina": "nom"}
_GODZ = re.compile(r"(?<![\w])(?i:godz)\.?\s*(\d{1,2})(?:[:.](\d{2}))?(?!\d|[.:,]\d)")
_TIME = re.compile(r"(?<![\w.,:])(\d{1,2}):(\d{2})(?!\d|:\d)")
_TIME_DOT = re.compile(r"(?<![\w.,])(\d{1,2})\.(\d{2})(?!\d|\.\d)")
_TIME_DOT_CTX = {"o", "od", "do", "po", "przed", "około", "godzinie", "godzina", "godziny"}
_SCORE = re.compile(r"(?<![\w.,:])(\d{1,3})((?::\d{1,3})+)(?!\d|:\d)")
# «1:30:00» is a duration; left to the other rules it came out «jeden:trzydzieści:zero»
_DURATION = re.compile(r"(?<![\w.,:])(\d{1,2}):(\d{2}):(\d{2})(?!\d|:\d)")
# «o 5 rano», «od 7 do 9 wieczorem»: an hour without minutes, known by the time of day
_DAYTIME = r"(?:rano|wieczorem|w\s+nocy|nad\s+ranem|po\s+południu|w\s+południe)(?!\w)"
_HOUR_WORD = re.compile(rf"(?<![\w.,:])(\d{{1,2}})(?=\s+{_DAYTIME}|\s+do\s+\d{{1,2}}\s+{_DAYTIME})")
_HOUR_PREP = {"o", "po", "od", "do", "około", "ok", "przed", "na", "między"}
# «20:00-21:00», «20.00-21.00», «godz. 9-17»: a span of time, «od dwudziestej do
# dwudziestej pierwszej». It came out «dwudziesta-dwudziesta pierwsza», the dot
# form lost the time («dwadzieścia, dwadzieścia jeden») and «w godz. 9-17» was
# «w godzina dziewiąta-siedemnaście» (final review, 2026-09-27). With dots and
# no «godz.», a minute part that is no month («.00», «.30») tells a time from a
# range of dates («12.05-15.05»).
_TIME_RANGE = re.compile(r"(?<![\w.,:])(?:(?P<g>(?i:godz)\.?)\s*)?(?P<h1>\d{1,2})(?:(?P<s1>[:.])"
                         r"(?P<m1>\d{2}))?\s*[-–—]\s*(?P<h2>\d{1,2})(?:(?P<s2>[:.])(?P<m2>\d{2}))?"
                         r"(?!\d|[.:,]\d)(?!\s*(?:zł|PLN|€|\$|%|km|kg|h|min|tys|mln|mld)(?!\w))")
# «pn.-pt.», «pon.–sob.»: a range of weekdays, left unread; its dot then opened a
# sentence in the middle of the line («Pracuję pn.-pt. Dziewiąta…»)
_WEEKDAY = {"pn": 0, "pon": 0, "wt": 1, "śr": 2, "czw": 3, "pt": 4, "sob": 5, "nd": 6, "niedz": 6}
_WEEKDAY_GEN = ("poniedziałku", "wtorku", "środy", "czwartku", "piątku", "soboty", "niedzieli")
_WEEKDAY_ALT = "|".join(sorted(_WEEKDAY, key=len, reverse=True))
_DAY_RANGE = re.compile(rf"(?<![\w.])(?i:({_WEEKDAY_ALT})\.?\s*[-–—]\s*({_WEEKDAY_ALT}))(\.?)(?!\w)")
# «Wstaję o 6.», «Live dziś o 20!»: a bare hour after «o», known by a word of the
# day's plan in the sentence; it was «o sześć». Never «po/przed N», which here
# is mostly an age («po 40»), nor «o N» without such a word («schudłam o 5»).
_HOUR_CUE = set("wstaję wstajesz wstaje wstajemy wstań budzę budzisz budzi budzik kładę "
                "kładziesz zasypiam zaczynam zaczynamy zaczyna startuję startujemy startuje "
                "start kończę kończymy kończy lajw spotkanie spotykamy widzimy webinar "
                "transmisja zapraszam dziś dzisiaj jutro codziennie pracuję pracujemy pracuje "
                "czynne czynny otwarte otwarty".split())
_PHRASE_END = r"(?=\s*(?:$|[.,!?;…)\]\"”»]))"
_HOUR_O = re.compile(r"(?<![\w.,:])(\d{1,2})(?!\d|[.,:]\d)(?:" + _PHRASE_END
                     + r"|(?=\s+(?:i|a|oraz|dziś|dzisiaj|jutro|codziennie)(?!\w)))")
_HOUR_SPAN = re.compile(r"(?<![\w.,:])(\d{1,2})\s+do\s+(\d{1,2})(?!\d|[.,:]\d)" + _PHRASE_END)


# «Dziś schudłam o 2.»: an amount by which something changed, whatever the day
_CHANGE = ("schud", "przytył", "wzr", "urosł", "spad", "zwiększ", "zmniejsz", "podniosł",
           "podniósł", "obniż", "więcej", "mniej", "taniej", "drożej", "dłużej", "krócej")


def _hour_cue(before: str, after: str) -> bool:
    clause = re.split(r"[.!?…]", before)[-1] + " " + re.split(r"[.!?…]", after)[0]
    words = set(re.findall(r"[^\W\d_]+", clause.lower()))
    return bool(words & _HOUR_CUE) and not any(w.startswith(_CHANGE) for w in words)


def _time_case(before: str) -> str:
    p = _prev_word(before)
    if p == "a" and re.search(r"(?i)(?<!\w)między(?!\w)", before):
        return "ins"                                     # «między 18:00 a 19:00»
    return _TIME_CASE.get(p, "nom")


def _clock(h: str, mm: str | None, case: str) -> str | None:
    h, mm = int(h), (mm or "")
    if h > 24 or (mm and int(mm) > 59):
        return None
    out = ordinal(h, case, "f") if h else "zero"           # «o 0:30» is «o zero trzydzieści»
    if mm and mm != "00":
        out += (" zero " + spell(int(mm[1]))) if mm[0] == "0" else (" " + spell(int(mm)))
    return out


def _r_times(line: str) -> str:
    def godz(m, before, after):
        case = _time_case(before)
        t = _clock(m.group(1), m.group(2), case)
        return None if t is None else _GODZINA[case] + " " + t

    def duration(m, before, after):
        h, mi, s = (int(x) for x in m.groups())
        if mi > 59 or s > 59:
            return None
        case = _case_for(before, use_next=False)
        parts = [_quantity(v, "", case, key) for v, key in
                 ((h, "godzina"), (mi, "minuta"), (s, "sekunda")) if v]
        return " ".join(parts) or "zero"

    def hour(m, before, after):
        p = _prev_word(before)
        if p not in _HOUR_PREP:
            return None
        return _clock(m.group(1), None, _time_case(before))

    def score(m, before, after):
        rest = m.group(2).split(":")[1:]
        return " do ".join([spell(int(m.group(1)))] + [spell(int(x), "gen") for x in rest])

    def trange(m, before, after):
        g = m.groupdict()
        if not g["g"]:
            if not (g["m1"] and g["m2"]):
                return None                      # «3-4»: a range of amounts
            if "." in (g["s1"], g["s2"]) and _prev_word(before) not in _TIME_DOT_CTX \
                    and all(1 <= int(x) <= 12 for x in (g["m1"], g["m2"])):
                return None                      # «12.05-15.05» is a range of dates
        if int(g["h1"]) == int(g["h2"]) == 0:
            return None                          # «(00:00-00:03)»: a timecode, not an hour
        t1, t2 = _clock(g["h1"], g["m1"], "gen"), _clock(g["h2"], g["m2"], "gen")
        if t1 is None or t2 is None:
            return None
        p = _prev_word(before)
        head = ("godzinach " if p in ("w", "we") else "godziny ") if g["g"] else ""
        return head + ("" if p == "od" and not head else "od ") + t1 + " do " + t2

    def days(m, before, after):
        a, b = _WEEKDAY[m.group(1).lower()], _WEEKDAY[m.group(2).lower()]
        said = _WEEKDAY_GEN[a] + " do " + _WEEKDAY_GEN[b]
        return (said if _prev_word(before) == "od" else "od " + said) + (
            _end_dot(after) if m.group(3) else "")

    def bare_o(m, before, after):
        if _prev_word(before) != "o" or not _hour_cue(before, after):
            return None
        return _clock(m.group(1), None, "loc")

    def span(m, before, after):
        if _prev_word(before) != "od" or not _hour_cue(before, after):
            return None                          # «od 9 do 17 lat» counts years
        t1, t2 = _clock(m.group(1), None, "gen"), _clock(m.group(2), None, "gen")
        return None if t1 is None or t2 is None else t1 + " do " + t2

    line = _apply(line, _DAY_RANGE, days)
    line = _apply(line, _TIME_RANGE, trange)
    line = _apply(line, _GODZ, godz)
    line = _apply(line, _DURATION, duration)
    line = _apply(line, _TIME, lambda m, b, a: _clock(m.group(1), m.group(2), _time_case(b)))
    line = _apply(line, _TIME_DOT, lambda m, b, a: _clock(m.group(1), m.group(2), _time_case(b))
                  if _prev_word(b) in _TIME_DOT_CTX else None)
    line = _apply(line, _HOUR_WORD, hour)
    line = _apply(line, _HOUR_O, bare_o)
    line = _apply(line, _HOUR_SPAN, span)
    # what is left with a colon is a score: «2:1» → «dwa do jednego»
    return _apply(line, _SCORE, score)


# the space after «°» belongs to it only before C/F: «20° w cieniu» was «stopniw cieniu»
_TEMP = re.compile(rf"(?:(?<![\w])([-−])(?=\d))?({_AMT})\s*°(?:\s*([CF])(?!\w))?")


def _r_temperature(line: str) -> str:
    def temp(m, before, after):
        n, frac = _amount(m.group(2))
        out = _quantity(n, frac, _case_for(before, use_next=False), "stopień")
        scale = {"C": " Celsjusza", "F": " Fahrenheita"}.get(m.group(3) or "", "")
        gap = " " if after[:1].isalpha() else ""
        return ("minus " if m.group(1) else "") + out + scale + gap
    return _apply(line, _TEMP, temp)


_SLASH_NUM = re.compile(rf"({_AMT})\s*/\s*(\d+)(?!\d|[,.]\d)")
_COMPOUND = re.compile(rf"(?<![\w,.])\d{{1,3}}-[{_LOW}]+(?!\w)|(?<![\w.])[IVXL]+-[{_LOW}]+(?!\w)"
                       rf"|(?<![\w,.])\d{{1,3}}s?t(?:{_MILESTONE_END})(?!\w)")


def _fraction(a: int, b: int, before: str) -> str:
    """«1/2» → «pół», «1/3» → «jedna trzecia», «2/3» → «dwie trzecie», in the case
    the word before asks for."""
    if (a, b) == (1, 2):
        return "pół"
    p = _prev_word(before)
    case = ("gen" if p in _GEN_PREP else "dat" if p in _DAT_PREP else
            "acc" if p in ("o", "na", "za", "przez") else "ins" if p in _INS_PREP else
            "loc" if p in ("w", "we", "przy", "po") else "nom")
    return spell(a, case, "f") + " " + ordinal(b, case, "f" if a == 1 else "pl")


def _r_slash_compound(line: str) -> str:
    def slash(m, before, after):
        n, frac = _amount(m.group(1))
        b = int(m.group(2))
        # «1/2 szklanki» is «pół szklanki», «1/3 klientek» «jedna trzecia
        # klientek»; it was «jeden na dwa szklanki» (final review, 2026-09-27).
        # Without a noun after it, or as «24/7», «80/20», it is a ratio.
        if not frac and 0 < n < b <= 4 and re.match(rf"\s+[{_LOW}]", after):
            return _fraction(n, b, before)
        return _say_number(n, frac, "nom", "m") + " na " + spell(b)

    line = _apply(line, _SLASH_NUM, slash)               # «24/7» → «dwadzieścia cztery na siedem»
    # «30-letni» → «trzydziestoletni», «2-go» → «drugiego», «lata 90-te» → «dziewięćdziesiąte»
    return _apply(line, _COMPOUND, lambda m, b, a: _compound_word(m.group(0)))


_UNIT_ALT = "km/h|" + "|".join(sorted(_UNIT_ABBR, key=len, reverse=True))
_PER_ALT = "|".join(sorted(_PER, key=len, reverse=True))


def _tail() -> str:
    """What may follow an amount: a scale, then a currency, a percent sign or a unit."""
    return (r"(?:\s*(?P<sc>tys|mln|mld)(?P<sdot>\.(?!\w))?(?!\w)|(?P<k>k)(?!\w))?"
            r"(?:\s*(?:(?P<cur>zł|ZŁ|Zł|PLN|gr|EUR|USD|€|\$)(?!\w)|(?P<pct>%|proc\.(?!\w))"
            rf"|(?P<u>{_UNIT_ALT})(?P<udot>\.(?!\w))?(?!\w)(?!\.\w)))?"
            rf"(?:\s*/\s*(?P<per>{_PER_ALT})(?P<pdot>\.(?!\w))?(?!\w))?")


_QTY = re.compile(rf"(?P<amt>{_AMT}){_tail()}")
_CUR_FIRST = re.compile(rf"(?P<cur>\$|€)\s?(?P<amt>{_AMT})"
                        r"(?:\s*(?P<sc>tys|mln|mld)(?P<sdot>\.(?!\w))?(?!\w)|(?P<k>k)(?!\w))?")
_RANGE = re.compile(rf"(?P<a>{_AMT})\s*[-–—]\s*(?P<amt>{_AMT}){_tail()}")


def _say_qty(g: dict, before: str, after: str, first: str | None = None,
             cur_first: bool = False) -> str | None:
    """One amount with what follows it; `first` is the other end of a range («3-4»).

    `cur_first` is «$1,5 mln.»: there the scale's dot is the last thing matched
    and may also be the full stop, which must not be lost.
    """
    n, frac = _amount(g["amt"])
    scale = _SCALE_ABBR.get(g.get("sc") or g.get("k") or "", 1)
    per = g.get("per")
    if not (scale > 1 or g.get("cur") or g.get("pct") or g.get("u")):
        if first is None:
            return None                                  # a bare number: the fallback reads it
        case = _case_for(before, after, n=n)
        gender = _gender_after(after, n)
        if gender == "mp" and case == "nom":
            case = "acc"                                 # «pięciu ludzi», «dwóch klientów»
        a_n, a_frac = _amount(first)
        return (_say_number(a_n, a_frac, case, gender) + ", "
                + _say_number(n, frac, case, gender))
    case = _case_for(before, use_next=False)
    dot = ""
    if g.get("cur"):
        noun_key = _CURRENCY[g["cur"]]
        out = _quantity(n, frac, case, noun_key, scale=scale, money=True)
        if cur_first and g.get("sdot"):
            dot = _end_dot(after)
    elif g.get("pct"):
        noun_key = "procent"
        out = _quantity(n, frac, case, noun_key, scale=scale)
        if g["pct"].endswith("."):
            dot = _end_dot(after)
    elif g.get("u"):
        noun_key = "kilometr" if g["u"] == "km/h" else _UNIT_ABBR[g["u"]]
        out = _quantity(n, frac, case, noun_key, scale=scale)
        if g["u"] == "km/h":
            out += " na godzinę"
        if g.get("udot"):
            dot = _end_dot(after)
    else:
        noun_key = None
        out = _quantity(n, frac, case, None, scale=scale)
        if g.get("sdot"):
            dot = _end_dot(after)
    if first is not None:
        a_n, a_frac = _amount(first)
        gender = _NOUNS[noun_key][1] if noun_key and scale == 1 else "m"
        out = _say_number(a_n, a_frac, case, gender) + ", " + out
    if per:
        if not g.get("cur"):
            return None
        out += " " + _PER[per]
        dot = _end_dot(after) if g.get("pdot") else ""
    return out + dot


def _r_quantities(line: str) -> str:
    line = _apply(line, _RANGE, lambda m, b, a: _say_qty(m.groupdict(), b, a, first=m.group("a")))
    line = _apply(line, _CUR_FIRST, lambda m, b, a: _say_qty(m.groupdict(), b, a, cur_first=True))
    return _apply(line, _QTY, lambda m, b, a: _say_qty(m.groupdict(), b, a))


_X_BOTH = re.compile(rf"(?P<a>{_AMT})\s*[x×]\s*(?P<b>\d+(?:,\d+)?)(?!\d|[,.]\d)")
_X_AFTER = re.compile(rf"(?P<a>{_AMT})\s*[x×](?!\w)")
_X_BEFORE = re.compile(rf"(?<![\w])[x×]\s*(?P<b>\d+(?:,\d+)?)(?!\d|[,.]\d)")


def _r_times_x(line: str) -> str:
    def both(m, before, after):
        (a, af), (b, bf) = _amount(m.group("a")), _amount(m.group("b"))
        return _say_number(a, af, "nom", "m") + " razy " + _say_number(b, bf, "nom", "m")

    def after_x(m, before, after):
        n, frac = _amount(m.group("a"))
        if frac.rstrip("0"):
            return _decimal(n, frac) + " raza"           # «półtora raza»
        return _quantity(n, "", "nom", "raz")            # «jeden raz», «dwa razy»

    def before_x(m, before, after):
        n, frac = _amount(m.group("b"))
        return "razy " + _say_number(n, frac, "nom", "m")

    line = _apply(line, _X_BOTH, both)
    line = _apply(line, _X_AFTER, after_x)
    return _apply(line, _X_BEFORE, before_x)


_ORD_DOT = re.compile(rf"(?<![\w.,])(\d{{1,4}})\.(?=\s+[{_LOW}])")


def _r_ordinal_dot(line: str) -> str:
    def ordn(m, before, after):
        case, g = _ord_noun_form(before, _next_word(after))
        return ordinal(int(m.group(1)), case, g)         # «3. miejsce» → «trzecie miejsce»
    return _apply(line, _ORD_DOT, ordn)


def _tzw(before: str, after: str) -> str:
    """«tzw.» agreeing with the word after it.

    It knew only the nominative: «o tak zwany pasywnym dochodzie», «tak zwane
    zasadę», «bez tak zwany etatu» (final review, 2026-09-27). An adjective's
    ending shows the form outright; a bare noun leans on the preposition.
    """
    nx, p = _next_word(after), _prev_word(before)
    if len(nx) > 3:
        for ends, said in (("ego", "zwanego"), ("emu", "zwanemu"), (("ymi", "imi"), "zwanymi"),
                           (("ych", "ich"), "zwanych"), (("ym", "im"), "zwanym"),
                           ("ej", "zwanej")):
            if nx.endswith(ends):
                return "tak " + said
    if nx.endswith("ą") or (nx.endswith("ę") and nx not in _NEUT_E):
        return "tak zwaną"                           # «poznaj tzw. zasadę»
    if nx.endswith(("ach", "ów")):
        return "tak zwanych"
    if nx.endswith("ami"):
        return "tak zwanymi"
    fem = _is_fem(nx)
    if p in _GEN_PREP:
        return "tak zwanej" if fem or nx.endswith(("i", "y")) else "tak zwanego"
    if p in _DAT_PREP:
        return "tak zwanej" if fem or nx.endswith(("e", "i", "y")) else "tak zwanemu"
    if p in ("o", "w", "we", "na", "przy", "po"):
        return "tak zwanej" if fem else "tak zwanym"  # «o tzw. dochodzie», «w tzw. strefie»
    if nx.endswith("a"):
        return "tak zwana"
    if nx.endswith(("e", "o", "um", "ę")):
        return "tak zwane"
    return "tak zwany"


def _ok(before: str, after: str) -> str:
    # «ok. 500 zł», «ok. pięciuset osób» is «około»; «Ok. Zaczynamy.» is «okej»
    if re.match(rf"\s*[~≈]?\s*(?:\d|[{_LOW}])", after):
        return "około"
    return "okej" + _end_dot(after)


def _ul(before: str, after: str) -> str:
    return "ulicy" if _prev_word(before) in {"na", "przy", "w", "z", "ze", "od", "do", "obok"} \
        else "ulica"


def _str(before: str, after: str) -> str:
    # «na str. 5» is «na stronie pięć», «ze str. 5» «ze strony»
    p = _prev_word(before)
    if p in ("na", "w", "we", "o", "przy", "po"):
        return "stronie"
    return "strony" if p in ("do", "od", "z", "ze", "bez", "dla", "u", "obok", "według", "wg")         else "strona"


# «kilka min.», «kilka tyg. temu», «po kilku mies.», «3x w tyg.»: after a
# quantifier or a preposition the abbreviation is the unit itself. It was read
# «kilka minimum», «kilka tygodniowo temu», «w tygodniowo» (final review,
# 2026-09-27): the adverb and «minimum» are only right after an amount.
_QUANT = set("kilka kilkanaście kilkadziesiąt kilkaset parę paręnaście kilku kilkunastu "
             "kilkudziesięciu kilkuset paru wiele wielu ile ilu kilkoma kilkunastoma paroma "
             "wieloma".split())


def _unit_after(before: str, key: str) -> str | None:
    """The unit in the form the word before it needs, or None when nothing asks for one.

    «kilka tyg.» → «tygodni», «po kilku mies.» → «miesiącach», «z kilkoma min.»
    → «minutami», «3x w tyg.» → «w tygodniu», «2 razy na mies.» → «na miesiąc».
    """
    sg, pl = _NOUNS[key][0]
    p = _prev_word(before)
    if p in _QUANT:
        if p.endswith("oma"):
            return pl["ins"]
        m = re.search(r"([^\W\d_]+)\s*$", before)
        pp = _prev_word(before[:m.start()]) if m else ""
        if pp in ("po", "w", "we", "o", "przy") and p.endswith("u"):
            return pl["loc"]
        return pl["gen"]
    if p in ("w", "we"):
        return pl["loc"] if key == "godzina" else sg["loc"]     # «w godzinach pracy»
    if p == "na":
        return sg["acc"]
    return None


def _min(before: str, after: str) -> str:
    # before a number it is «minimum» whatever comes before: «na min. 5 osób»
    unit = None if re.match(r"\s*\d", after) else _unit_after(before, "minuta")
    return (unit or "minimum") + _end_dot(after, trailing=bool(unit))


def _godz(before: str, after: str) -> str:
    unit = _unit_after(before, "godzina")
    if unit:
        return unit + _end_dot(after)
    p = _prev_word(before)
    word = "godzinie" if p in ("o", "po") else ("godziny" if p in ("od", "do", "około", "ok")
                                                else "godzina")
    return word + _end_dot(after)


# (pattern, spoken form or a function, whether its dot can also end a sentence)
_ABBR_RULES = [
    (r"m\.\s?in\.", "między innymi", False), (r"p\.\s?s\.|ps\.", "postscriptum", True),
    (r"np\.", "na przykład", False), (r"ok\.", _ok, None), (r"tzn\.", "to znaczy", False),
    (r"tj\.", "to jest", False), (r"itd\.", "i tak dalej", True),
    (r"itp\.", "i tym podobne", True), (r"tzw\.", _tzw, False), (r"ul\.", _ul, False),
    (r"godz\.", _godz, None), (r"min\.|min(?=\s*\d)", _min, None),
    (r"sek\.", lambda b, a: _unit_after(b, "sekunda") or "sekund", True),
    (r"dr\.?", "doktor", False), (r"prof\.", "profesor", False),
    (r"nr\.?", "numer", False), (r"str\.", _str, False), (r"zob\.", "zobacz", False),
    (r"wg\.?", "według", False), (r"ds\.", "do spraw", False), (r"ws\.", "w sprawie", False),
    (r"tel\.", "telefon", False), (r"proc\.", "procent", True),
    (r"mies\.", lambda b, a: _unit_after(b, "miesiąc") or "miesięcznie", True),
    (r"tyg\.", lambda b, a: _unit_after(b, "tydzień") or "tygodniowo", True),
    (r"tys\.?", "tysięcy", True), (r"mln\.?", "milionów", True), (r"mld\.?", "miliardów", True),
    (r"szt\.", "sztuk", True), (r"ew\.", "ewentualnie", False),
    (r"św\.", lambda b, a: "święta" if _next_word(a).endswith("a") else "święty", False),
    # «Etat vs biznes», «cdn.»: left unread, «C.d.n.» was «Ce.d.n.» (final review)
    (r"vs\.?", "kontra", False), (r"c\.\s?d\.\s?n\.|cdn\.", "ciąg dalszy nastąpi", True),
    (r"ok", lambda b, a: "około" if re.match(r"\s*\d", a) else "okej", False),
]
_ABBR_COMPILED = [(re.compile(rf"(?<![\w.])(?i:{p})(?![\w])"), say, trailing)
                  for p, say, trailing in _ABBR_RULES]


def _r_abbreviations(line: str) -> str:
    for rx, say, trailing in _ABBR_COMPILED:
        def rep(m, before, after, say=say, trailing=trailing):
            out = say(before, after) if callable(say) else say
            if trailing:
                out += _end_dot(after)
            elif trailing is False and m.group(0).endswith(".") and _end_dot(after, False):
                out += "."                               # «…, np.» at the very end
            return out
        line = _apply(line, rx, rep)
    return line


_NUM_LEFT = re.compile(_AMT)
# «z trzema dziećmi» is the usual form, so «dziećmi» keeps the plain cardinal
_CHILDREN = {"dzieci", "dzieciom", "dzieciach"}
_LABEL = {"numer", "numeru", "numerem", "numerze", "nr"}
_DIGITS = re.compile(r"\d+")


def _r_numbers(line: str) -> str:
    """Rule 17: any number still in digits, in the case its neighbours suggest."""
    def num(m, before, after):
        n, frac = _amount(m.group(0))
        if frac.rstrip("0"):
            return _decimal(n, frac, _gender_after(after))
        if n >= 10 ** 12:
            return None
        case = _case_for(before, after, n=n)
        nx = _next_word(after)
        # «5G», «4K»: the letter becomes a word of its own, spelled by the acronym rule
        gap = " " if after[:1].isalpha() else ""
        if nx in _CHILDREN and 2 <= n <= 9:
            return _COLLECTIVE[case][n] + gap
        if _prev_word(before) in _LABEL:
            return spell(n) + gap                        # «numer 1 zasada»: a label, not a count
        if n == 1:
            return _one(before, after, case) + gap
        gender = _gender_after(after, n)
        if gender == "mp" and case == "nom":
            case = "acc"                                 # «pięciu ludzi», «dwóch klientów»
        return spell(n, case, gender) + gap

    def digits(m, before, after):
        s = m.group(0)
        words = spell(int(s)) if len(s) <= 12 else " ".join(_UNITS["nom"][int(d)] for d in s)
        return _pad(before, after, words)                # «mp3» → «mp trzy»

    line = _apply(line, _NUM_LEFT, num)
    return _apply(line, _DIGITS, digits)


# A unit after a number written in words: «tysiąc zł», «kilka tysięcy zł», «pół
# miliona zł», «parę kg». No rule read it, the line was not even sent to the
# AI, and XTTS passes «zł» through as it is (final review, 2026-09-27). The
# genitive plural, unless the word before asks for another form. Only after a
# number word, a quantifier or «w» («w złotych»): «za km», «kosztuje km» are
# singular, and no rule can tell their case.
_FREE_UNIT = {"zł": "złoty", "ZŁ": "złoty", "Zł": "złoty", "PLN": "złoty", "km": "kilometr",
              "kg": "kilogram", "kcal": "kilokaloria", "cm": "centymetr", "mm": "milimetr",
              "ml": "mililitr"}
_FREE_UNIT_RE = re.compile(r"(?<=[^\W\d_])(\s+)(" + "|".join(_FREE_UNIT) + r")(?![\w/])")


def _free_unit_after(before: str) -> bool:
    w = (re.findall(r"[^\W\d_]+", before.lower()) or [""])[-1]
    return w in _WORDS or w in _QUANT or w in _HALF or w in ("w", "we")


def _r_free_units(line: str) -> str:
    def unit(m, before, after):
        if not _free_unit_after(before):
            return None
        sg, pl = _NOUNS[_FREE_UNIT[m.group(2)]][0]
        words = re.findall(r"[^\W\d_]+", before.lower())[-2:]
        w = words[-1] if words else ""
        if w == "jeden" and not (len(words) > 1 and words[-2] in _WORDS):
            form = sg["nom"]                             # «jeden złoty» («dwadzieścia jeden złotych»)
        elif w in ("dwa", "trzy", "cztery", "dwie", "oba", "obie"):
            form = pl["nom"]                             # «dwa złote», «dwadzieścia dwa złote»
        elif w in _HALF:
            form = sg["gen"]                             # «pół kilograma», «dwa i pół kilograma»
        elif w in ("w", "we"):
            form = pl["loc"]                             # «w złotych», «w kilogramach»
        else:
            form = pl["gen"]                             # «tysiąc złotych», «parę kilogramów»
        return m.group(1) + form
    return _apply(line, _FREE_UNIT_RE, unit)


_SYMBOLS = [(re.compile(r"\s*\+\s*"), "plus"), (re.compile(r"\s*=\s*"), "równa się"),
            (re.compile(r"\s*&\s*"), "i"), (re.compile(r"\s*%"), "procent"),
            (re.compile(r"\s*°"), "stopni"), (re.compile(r"\s*€"), "euro"),
            (re.compile(r"\s*\$"), "dolarów"), (re.compile(r"\s*[~≈]\s*"), ""),
            (re.compile(r"\s*/\s*"), "")]


def _r_symbols(line: str) -> str:
    for rx, word in _SYMBOLS:
        def rep(m, before, after, word=word):
            if not word:                                 # «on/ona» → «on ona»
                return "" if (not before or not after) else " "
            return _pad(before, after, word)
        line = _apply(line, rx, rep)
    return line


_CAPS = re.compile(rf"(?<![\w'’])[{_UP}]{{2,}}(?![\w'’])")
_CAP1 = re.compile(rf"(?<![\w'’.])([{_UP}])(?![\w'’])")


def _shouting(line: str) -> bool:
    """A line written in capitals: three capital tokens or more, two of them plainly words."""
    caps = _CAPS.findall(line)
    wordish = [c for c in caps if _caps_word(c)]
    return len(caps) >= 3 and len(wordish) >= 2


def _r_acronyms(line: str) -> str:
    """Rule 16: capitals. 2-4 letters are spelled («KPI» → «ka pe i»), 5 or more are a word.

    A line written in capitals for emphasis («NIE RÓB TEGO») is read as words:
    with three or more capital tokens, two of them plainly words, none is spelled.
    """
    shouting = _shouting(line)

    def acronym(m, before, after):
        t = m.group(0)
        if shouting or _caps_word(t):
            return t.lower()
        return " ".join(_LETTERS[c] for c in t)

    def letter(m, before, after):
        c = m.group(1)
        # Polish words: «W domu», «I powiem», and «— O czasie» after a dash or a
        # colon, which open a phrase just as a full stop does
        opens = _sentence_start(before) or before.rstrip()[-1:] in "—–-:„«(\"'"
        if c in "WZ" or (c in "AEIOUYÓĄĘ" and opens):
            return None
        return _LETTERS[c]                               # «punkt A i punkt B» → «a», «be»

    line = _apply(line, _CAPS, acronym)
    return _apply(line, _CAP1, letter)


# XTTS turns any `\bm\.` into «pan» and `\bp\.` into «pani», even right after
# another dot or glued to the next word («np.m.», «m.in.Okej» → «panin»), where
# the abbreviation rule does not look. Whatever is left is made safe here.
_MIN_ANY = re.compile(r"(?<!\w)(?i:m\.\s?in\.)")
_PS_ANY = re.compile(r"(?<!\w)(?i:p\.\s?s\.)")
_MP_DOT = re.compile(r"(?<!\w)([mMpP])\.")


def _r_pan(line: str) -> str:
    line = _apply(line, _MIN_ANY, lambda m, b, a: _pad(b, a, "między innymi"))
    line = _apply(line, _PS_ANY, lambda m, b, a: _pad(b, a, "postscriptum"))
    return _MP_DOT.sub(r"\1", line)


_RULES = (_r_list, _r_lexicon, _r_approx, _r_phone, _r_dates, _r_years, _r_roman, _r_times,
          _r_temperature, _r_slash_compound, _r_quantities, _r_times_x, _r_ordinal_dot,
          _r_abbreviations, _r_numbers, _r_free_units, _r_symbols, _r_acronyms, _r_pan)


def _normalize_line(line: str) -> str:
    if not line.strip():
        return line
    # A rule can leave work for an earlier one: the number rule parts «5nr» into
    # «pięć nr», and only then is «nr» a word the abbreviation rule sees. So the
    # chain runs until nothing changes, which is also what makes it idempotent.
    for _ in range(4):
        before = line
        for rule in _RULES:
            line = rule(line)
        if line == before:
            break
    return line


def normalize(text: str) -> str:
    """Written Polish → what is said aloud, line by line; lines and blank lines stay as they are.

    Idempotent: its output has nothing left for any rule to match.
    """
    if text is None:
        return ""                                # never the word «None» read aloud
    return "\n".join(_normalize_line(line) for line in str(text).split("\n"))


_SYMBOL_RE = re.compile(r"[%+=&~≈°$€]|(?<=\d)\s*(?:zł|ZŁ|Zł)(?!\w)")
# capital consonants without W and Z, which are Polish words («W domu»)
_CONSONANT = re.compile(r"(?<![\w'’.])[B-DF-HJ-NP-TVXY](?![\w'’])")


def _plain_word(token: str) -> bool:
    """A capitals token the lexicon reads as one word («ZUS», «BLIK», «START»)."""
    spoken = LEXICON.get(token)
    if spoken is not None:
        return " " not in spoken.strip()
    # five capitals or more are read as a word by the rules («UWAGA»), and so
    # are the common words and the Polish ones («MEGA», «CHCĘ»)
    return _caps_word(token)


def needs_rewrite(line: str) -> bool:
    """True when the line holds what XTTS cannot read as written.

    Digits, abbreviations, symbols, a price in «zł», acronyms that are spelled,
    Roman numerals in context and lone capital consonants («punkt B»). Capital
    words the rules read as words («UWAGA», «ZUS») do not count.
    """
    if (re.search(r"\d", line) or _ABBR_ANY.search(line) or _SYMBOL_RE.search(line)
            or _DAY_RANGE.search(line) or _ROMAN_I.search(line)
            or any(_free_unit_after(line[:m.start()]) for m in _FREE_UNIT_RE.finditer(line))):
        return True
    if any(not _plain_word(t) for t in _CAPS.findall(line)):
        return True
    if _ROMAN_AFTER.search(line) and any(m.group(2) for m in _ROMAN_AFTER.finditer(line)):
        return True
    return bool(_CONSONANT.search(line))


def rewrite_prompt(lines: dict) -> str:
    """The request for the text AI: every line spoken out, nothing else touched."""
    payload = json.dumps({str(k): str(v) for k, v in lines.items()}, ensure_ascii=False,
                         indent=0)
    return (
        "You are a Polish speech editor. The lines below will be read aloud by a speech "
        "synthesizer that cannot read digits, symbols or abbreviations.\n\n"
        "In each line, write every number, date, time, price, percentage, unit, symbol, "
        "abbreviation and letter acronym out in words, as a Pole says it aloud, with the "
        "grammatical case and gender the sentence needs. Examples:\n"
        "- z 5 osobami → z pięcioma osobami\n"
        "- 5 000 zł → pięć tysięcy złotych\n"
        "- o 18:30 → o osiemnastej trzydzieści\n"
        "- m.in. → między innymi\n"
        "- 3. miejsce → trzecie miejsce\n"
        "- 2x → dwa razy\n"
        "- w XXI w. → w dwudziestym pierwszym wieku\n"
        "- od 3 do 5 lat → od trzech do pięciu lat\n"
        "- 49,99 zł → czterdzieści dziewięć złotych dziewięćdziesiąt dziewięć groszy\n"
        "- 12.05.2026 → dwunastego maja dwa tysiące dwudziestego szóstego roku\n"
        "- 20% → dwadzieścia procent\n"
        "- CV → ce fał\n\n"
        "Read a letter acronym by its letters (KPI → ka pe i); do not replace it with the "
        "words it stands for. Change nothing else. Every other word keeps its exact form, and the punctuation "
        "and the word order stay exactly as written. Brand names and English words stay as "
        "written. Do not add, remove, translate or improve anything. Return every line, "
        "also one that needs no change. The answer must contain no digits and no dashes "
        "between numbers; a dash between two parts of a sentence may stay or become a comma.\n\n"
        "Output ONLY a JSON object with the same keys, each value the rewritten line, "
        'like {"1": "...", "2": "..."}.\n\n'
        "Lines:\n" + payload
    )


_TOKEN = re.compile(
    r"(?P<abbr>(?<![\w.])(?i:m\.\s?in\.|p\.\s?s\.|np\.|ok\.|tzn\.|tj\.|itd\.|itp\.|tzw\.|"
    r"ul\.|godz\.|min\.|sek\.|prof\.|str\.|zob\.|ds\.|ws\.|tel\.|tys\.|proc\.|mies\.|"
    r"tyg\.|szt\.|św\.|ew\.|dr\.?|nr\.?|wg\.?|mln\.?|mld\.?|ps\.|r\.|w\.|vs\.?|c\.\s?d\.\s?n\.|"
    r"cdn\.|pn\.|pon\.|wt\.|śr\.|czw\.|pt\.|sob\.|nd\.|niedz\.)(?!\w))"
    rf"|(?P<comp>(?<![\w,.])\d{{1,3}}-[{_LOW}]+(?!\w)|(?<![\w.])[IVXL]+-[{_LOW}]+(?!\w)"
    rf"|(?<![\w,.])\d{{1,3}}s?t(?:{_MILESTONE_END})(?!\w))"
    rf"|(?P<num>\d{{1,2}}\.\d{{1,2}}\.\d{{4}}|\d{{4}}-\d{{2}}-\d{{2}}|\d+(?::\d+)+"
    r"|(?<![\w+])\d{2}[ -]\d{3}[ -]\d{2}[ -]\d{2}(?!\d|[ -]\d)"
    rf"|(?:{_INT})(?:[,.]\d+)?)"
    r"|(?P<word>[^\W\d_]+(?:\d+[^\W\d_]+)+|[^\W\d_]+(?:['’][^\W\d_]+)?)"
    r"|(?P<sym>\S)")
_GLUE = {"zł", "gr", "PLN", "EUR", "USD", "km", "kg", "g", "m", "cm", "mm", "l", "ml", "kcal",
         "h", "min", "s", "sek", "godz", "x", "×", "k", "tys", "mln", "mld", "mies", "tyg",
         "szt", "-", "–", "—", "/", ":", ".", ",", "r.", "w.", "°", "ZŁ", "Zł", "os", "rok",
         "mc", "msc"}
_SPEAK_SYM = set("%+=&~≈°$€#")
_NEW_WORD = re.compile(rf"[{_LOW}]+|Celsjusza|Fahrenheita")
_ROMAN_CTX_NEXT = {"w.", "wiek", "wieku", "wiekiem"} | set(_CENT_AFTER)


# abbreviations whose dot never ends a sentence unless the line ends there:
# «ul. Długa», «prof. Kowalski», «tzw. Złota Zasada» (the rules' trailing=False)
# («min.» may end one: «Poczekaj kilka min. Potem…» is «kilka minut.»)
_NO_END_ABBR = {"m.in.", "m. in.", "np.", "tzn.", "tj.", "tzw.", "ul.", "dr.", "prof.",
                "nr.", "str.", "zob.", "wg.", "ds.", "ws.", "tel.", "ew.", "św."}


def _tokens(text: str) -> list[tuple[str, str]]:
    toks = []
    for m in _TOKEN.finditer(text):
        toks.append((m.lastgroup, m.group(0)))
        # «…itd.» at the end or before a new sentence: its dot is also the full
        # stop, which the spoken side writes as a token of its own
        if m.lastgroup == "abbr" and m.group(0).endswith(".") and _end_dot(
                text[m.end():], m.group(0).lower() not in _NO_END_ABBR):
            toks.append(("sym", "."))
    return toks


def _roman_in_context(toks: list, i: int) -> int | None:
    v = _roman(toks[i][1])
    if v is None:
        return None
    nxt = toks[i + 1][1] if i + 1 < len(toks) else ""
    prv = toks[i - 1][1] if i > 0 else ""
    if nxt.lower() in _ROMAN_CTX_NEXT or prv.lower() in _CTX_NOUNS:
        return v
    if toks[i][1] == "I" and nxt.lower() in _ROMAN_I_NOUNS:
        return v                                         # «I miejsce»
    # the rules' other two contexts: «Jan Paweł II», «II etap»
    if len(toks[i][1]) >= 2 and set(toks[i][1]) <= set("IVX") and (
            re.fullmatch(rf"[{_UP}][{_LOW}]+", prv) or re.fullmatch(rf"[{_LOW}]+", nxt)):
        return v
    return None


def _kind(toks: list, i: int) -> str:
    """"speak" (a number, abbreviation, symbol, acronym), "glue" (a unit) or "plain"."""
    k, t = toks[i]
    if k in ("num", "comp"):
        return "speak"
    if k == "abbr":
        return "glue" if t.lower() in ("r.", "w.") else "speak"
    if t in _GLUE:
        # «tysiąc zł»: a unit with no amount in digits before it is read out itself
        if t in _FREE_UNIT and i > 0 and toks[i - 1][0] == "word" and toks[i - 1][1] not in _GLUE:
            return "speak"
        return "glue"
    if k == "sym":
        return "speak" if t in _SPEAK_SYM else "plain"
    if t in LEXICON or t.lower() == "ok":
        return "speak"
    letters = re.sub(r"\d", "", t)
    if len(letters) >= 2 and letters.isupper():
        return "speak"
    if t == "I" and i + 1 < len(toks) and toks[i + 1][1].lower() in _ROMAN_I_NOUNS:
        return "speak"                                   # «I miejsce» opening the line
    if len(t) == 1 and t.isupper() and (i > 0 or t not in "AIOUWZ"):
        return "speak"
    return "plain"


def _drop_zeros(vals: list) -> list:
    """Drop a zero that only leads another number: «0,50 zł» said «pięćdziesiąt
    groszy», «o 0:30» said «o zero trzydzieści». A zero on its own stays: «0 zł»
    said as «złotych» has lost it."""
    return [v for j, v in enumerate(vals) if v != 0 or j == len(vals) - 1]


def _digit_numbers(toks: list, i1: int, i2: int) -> list:
    """The numbers written in digits in toks[i1:i2], in the order they are said.

    A time or a score is two numbers (18:30 → [18, 30]; «:00» is not said, so
    18:00 → [18]), a date [day, month, year] (ISO dates too), a phone number
    its groups. A decimal is its value (2,5 → 2.5), except a price, whose
    fraction is the grosze (49,99 zł → [49, 99]). With tys./mln/mld after it
    the amount is one number (1,5 mln → [1500000]). A number with a written
    ending («2-go», «XX-tego») is its value.
    """
    out: list = []
    skip = -1
    for i in range(i1, i2):
        if i == skip:
            continue
        k, t = toks[i]
        if k == "word" and t.isupper():
            v = _roman_in_context(toks, i)
            if v:
                out.append(v)
            continue
        if k == "comp":
            c = _compound(t)
            if c and c[1] is not None:
                out.append(c[1])
            continue
        scale_word = t.lower().rstrip(".")
        if k == "abbr" and scale_word in ("tys", "mln", "mld") and not (i and toks[i - 1][0] == "num"):
            # «kilka tys. zł» is said «kilka tysięcy złotych», and «tysięcy» reads back as 1000
            out.append(_SCALE_ABBR[scale_word])
            continue
        if k != "num":
            continue
        nxt = toks[i + 1][1] if i + 1 < len(toks) else ""
        prv = toks[i - 1][1] if i > 0 else ""
        if (t == "1" and nxt == "/" and i + 3 < len(toks) and toks[i + 2] == ("num", "2")
                and re.fullmatch(rf"[{_LOW}]+", toks[i + 3][1])):
            out.append(0.5)                              # «1/2 szklanki» said «pół szklanki»
            skip = i + 2
            continue
        if ":" in t:
            vals = [int(x) for x in t.split(":") if not re.fullmatch(r"00+", x)]
        elif re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", t):
            vals = [int(x) for x in t.split(".")]
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
            vals = [int(x) for x in reversed(t.split("-"))]
        elif re.fullmatch(r"\d{2}[ -]\d{3}[ -]\d{2}[ -]\d{2}", t):
            vals = [int(x) for x in re.split(r"[ -]", t)]          # «22 123 45 67»
        else:
            n, frac = _amount(t)
            digits = re.sub(r"\D", "", t.split(",")[0])
            key = nxt.rstrip(".")
            # «k» is a thousand only in small letters, as the rules read it («4K» is a letter)
            scale = _SCALE_ABBR.get(key if key.lower() == "k" else key.lower(), 1)
            groups = re.split(r"[ \u00a0\u202f.]", t)
            price = (nxt in _CURRENCY or nxt.rstrip(".").lower() in _SCALE_ABBR
                     or (len(groups) > 2 and groups[-1] == groups[-2] == "000")
                     or (len(groups) == 1 and digits.endswith("000000")))
            if (len(digits) >= 9 and not price or prv == "+") and not frac and scale == 1:
                vals = [int(g) for g in (groups if len(groups) > 1 else
                                         [digits[j:j + 3] for j in range(0, len(digits), 3)])]
            elif scale > 1:
                fs = frac.rstrip("0")
                v = round(n * scale + (int(fs) * scale / 10 ** len(fs) if fs else 0), 6)
                vals = [int(v) if v == int(v) else v]
            elif re.fullmatch(r"\d{1,2}\.\d{2}", t) and (
                    (prv.lower() in _TIME_DOT_CTX and n <= 24 and int(frac) < 60)
                    or (_short_date(prv.lower()) and 1 <= n <= 31 and 1 <= int(frac) <= 12)
                    or (_in_time_range(toks, i) and n <= 24 and int(frac) < 60)):
                # «o 12.30» a time, «do 30.06» a date. «o 20.00» is said «o
                # dwudziestej»: its «00» is no number, as with «20:00»; kept, it
                # refused every answer to that line (final review, 2026-09-27)
                vals = [n] if frac == "00" else [n, int(frac)]
            elif frac and (nxt in _CURRENCY or prv in ("$", "€")) and len(frac) <= 2:
                cents = int(frac.ljust(2, "0"))
                vals = [n, cents] if cents else [n]
            elif frac.rstrip("0"):
                vals = [float(f"{n}.{frac}")]
            else:
                vals = [n]
        out += _drop_zeros(vals)
    return out


def _in_time_range(toks: list, i: int) -> bool:
    """«9.30-17.30»: a time with a dot is one end of a span of time."""
    pat = r"\d{1,2}[.:]\d{2}"
    nx = toks[i + 1][1] if i + 1 < len(toks) else ""
    pv = toks[i - 1][1] if i else ""
    return bool((nx in ("-", "–", "—") and i + 2 < len(toks) and re.fullmatch(pat, toks[i + 2][1]))
                or (pv in ("-", "–", "—") and i >= 2 and re.fullmatch(pat, toks[i - 2][1])))


def _word_numbers(words: list[str]) -> list:
    """The numbers said in `words`, in order; a month name counts as its number.

    A «zero» that only leads the next number («dziewiątej zero pięć») is
    dropped, as _drop_zeros does on the digits side; after «przecinek» the
    zeros are digits of the fraction and stay.
    """
    ws = [w.lower() for w in words]
    kept = []
    for j, w in enumerate(ws):
        nxt = ws[j + 1] if j + 1 < len(ws) else ""
        prv = ws[j - 1] if j else ""
        if (_WORDS.get(w, ("",))[0] == "z" and prv not in ("przecinek", w)
                and (nxt in _HALF or _WORDS.get(nxt, ("z",))[0] != "z")):
            w = ","                  # still a boundary: «sześćset zero siedemdziesiąt» is 600, 70
        kept.append(w)
    out: list = []
    chunk: list[str] = []
    for w in kept + [""]:
        if w and w not in _MONTHS:
            chunk.append(w)
            continue
        out += words_to_numbers(" ".join(chunk))
        chunk = []
        if w:
            out.append(_MONTHS.index(w) + 1)
    return out


def _same_numbers(want: list, got: list) -> bool:
    return len(want) == len(got) and all(abs(float(x) - float(y)) < 1e-6 for x, y in zip(want, got))


# What must still be heard once a token is spoken out: «20%» said as «dwadzieścia»
# drops the percent, «m.in.» said as «na przykład» changes the meaning.
_MUST_SAY = {
    "%": ("procent",), "proc.": ("procent",), "$": ("dolar",), "usd": ("dolar",),
    "€": ("euro",), "eur": ("euro",), "zł": ("złot", "grosz"), "pln": ("złot", "grosz"),
    "gr": ("grosz",), "+": ("plus", "ponad"), "=": ("równa", "równe"), "&": ("i", "oraz"),
    "°": ("stop",), "km": ("kilometr",), "kg": ("kilogram",), "g": ("gram",), "m": ("metr",),
    "cm": ("centymetr",), "mm": ("milimetr",), "l": ("litr",), "ml": ("mililitr",),
    "kcal": ("kilokalori", "kalori"), "h": ("godzin",), "godz": ("godzin",),
    "godz.": ("godzin",), "min": ("minut", "minimum"), "min.": ("minut", "minimum"),
    "s": ("sekund",), "sek": ("sekund",), "sek.": ("sekund",), "tys": ("tysi",),
    "tys.": ("tysi",), "k": ("tysi",), "mln": ("milion",), "mln.": ("milion",),
    "mld": ("miliard",), "mld.": ("miliard",), "mies": ("miesi",), "mies.": ("miesi",),
    "tyg": ("tydz", "tygod"), "tyg.": ("tydz", "tygod"), "szt": ("sztuk",),
    "szt.": ("sztuk",), "x": ("raz",), "×": ("raz",), "r.": ("rok",), "w.": ("wiek",),
    "m.in.": ("między",), "m. in.": ("między",), "np.": ("przykład",),
    "ok.": ("około", "okej"), "ok": ("około", "okej"), "tzn.": ("znaczy",), "tj.": ("jest",),
    "itd.": ("dalej",), "itp.": ("podobn",), "tzw.": ("zwan",), "ul.": ("ulic",),
    "dr": ("doktor",), "dr.": ("doktor",), "prof.": ("profesor",), "nr": ("numer",),
    "nr.": ("numer",), "str.": ("stron",), "zob.": ("zobacz",), "wg": ("według",),
    "wg.": ("według",), "ds.": ("spraw",), "ws.": ("spraw",), "tel.": ("telefon",),
    "św.": ("święt",), "ew.": ("ewentualn",), "p.s.": ("postscriptum",),
    "p. s.": ("postscriptum",), "ps.": ("postscriptum",), "#": ("numer",),
    "msc": ("miesi",), "mc": ("miesi",), "vs": ("kontra", "wersus", "versus"),
    "vs.": ("kontra", "wersus", "versus"), "cdn.": ("ciąg",), "c.d.n.": ("ciąg",),
    "c. d. n.": ("ciąg",), "pn.": ("poniedział",), "pon.": ("poniedział",), "wt.": ("wtor",),
    "śr.": ("środ", "średni"), "czw.": ("czwart",), "pt.": ("piąt", "tytuł"),
    "sob.": ("sobot",), "nd.": ("niedziel",), "niedz.": ("niedziel",),
}
_MONEY = {"zł": ("złot", "grosz"), "pln": ("złot", "grosz"), "$": ("dolar", "cent"),
          "usd": ("dolar", "cent"), "€": ("euro", "cent"), "eur": ("euro", "cent")}


def _money_unsaid(span: list, words: list[str]) -> str | None:
    """«5 000 zł» said «pięć tysięcy groszy», or «49,99 zł» with the grosze
    first, passed: either word answered «zł» (final review, 2026-09-27). An
    amount of one or more needs its main unit, said before the small one.
    """
    for j, (k, t) in enumerate(span):
        unit = _MONEY.get(t.lower())
        if not unit:
            continue
        near = [tt for kk, tt in span[j - 1::-1] if kk == "num"][:1] if j else []
        near = near or [tt for kk, tt in span[j + 1:] if kk == "num"][:1]
        scaled = any(kk == "abbr" and tt.lower().rstrip(".") in _SCALE_ABBR for kk, tt in span)
        if near and not scaled and _amount(near[0])[0] == 0:
            continue                                     # «0,50 zł» is «pięćdziesiąt groszy»
        main = [n for n, w in enumerate(words) if w.lower().startswith(unit[0])]
        small = [n for n, w in enumerate(words) if w.lower().startswith(unit[1])]
        if not main or (small and small[0] < main[0]):
            return t
    return None
# the units after a slash («zł/rok», «zł/os.»), in small letters only («OS» is an
# acronym): «za 1 rok» said «za jeden miesiąc» must not pass
_MUST_SAY_EXACT = {"rok": ("rok", "roc"), "os": ("osob", "osób")}


def _unsaid(tokens: list[str], said: list[str]) -> str | None:
    """The first token whose spoken word is missing from `said`, or None."""
    for t in tokens:
        # units are case-sensitive («G» in «5G» is a letter, not a gram)
        need = _MUST_SAY_EXACT.get(t) or _MUST_SAY.get(t) or (
            _MUST_SAY.get(t.lower()) if "." in t or (len(t) > 1 and t.isupper()) else None)
        if need and not any(w == p or (len(p) > 2 and w.startswith(p))
                            for w in said for p in need):
            return t
    return None


# The words a number, unit, symbol or abbreviation may turn into. «Mam 5 lat.»
# → «Mam ponad pięć lat.» reads the number back right and still changes the
# sentence, so a span holding one of those may only say it, nothing more.
# Number words, «i» and «przecinek» («dwa i pół») may always be said.
_SPOKEN_WORDS = {"i", "przecinek"} | set(_WORDS) | set(_HALF) | set(_MONTHS)
_SPOKEN_STEMS = ("tysi", "milion", "miliard")
# Every other word only where the span holds what it reads. While they were
# free, «Zarabiam 5 000 zł.» answered «…złotych miesięcznie», «do pięciu
# tysięcy», «minimum pięć tysięcy» or «na przykład pięć tysięcy» passed, and
# «Mam 3 psy.» as «trzy razy psy» (final review, 2026-09-27). The values are
# the span's tokens in small letters, or one of the <marks> _span_marks gives.
_TIED_WORDS = {
    "na": {"/", "np."}, "do": {"-", "–", "—", "ds.", "<score>"}, "za": {"/"}, "plus": {"+"},
    "równa": {"="}, "równe": {"="}, "się": {"="}, "oraz": {"&"}, "między": {"m.in.", "m. in."},
    "innymi": {"m.in.", "m. in."}, "przykład": {"np."}, "okej": {"ok", "ok."},
    "to": {"tzn.", "tj."}, "znaczy": {"tzn."}, "jest": {"tj."}, "tak": {"itd.", "tzw."},
    "dalej": {"itd."}, "tym": {"itp."}, "podobne": {"itp."}, "minimum": {"min.", "min"},
    "zobacz": {"zob."}, "według": {"wg", "wg."}, "spraw": {"ds.", "ws."}, "w": {"ws."},
    "sprawie": {"ws."}, "osobę": {"os"}, "miesięcznie": {"mies", "mies.", "mc", "msc", "m"},
    "rocznie": {"rok", "r", "r."}, "tygodniowo": {"tyg", "tyg."}, "ewentualnie": {"ew."},
    "postscriptum": {"p.s.", "p. s.", "ps.", "ps"}, "numer": {"#", "nr", "nr."},
    "około": {"ok.", "ok", "~", "≈"}, "minus": {"-", "−", "–"}, "ponad": {"+"},
    "od": {"-", "–", "—"},                           # «7-8 h» → «od siedmiu do ośmiu godzin»
    "kontra": {"vs", "vs."}, "wersus": {"vs", "vs."}, "versus": {"vs", "vs."},
    "ciąg": {"cdn.", "c.d.n.", "c. d. n."}, "dalszy": {"cdn.", "c.d.n.", "c. d. n."},
    "nastąpi": {"cdn.", "c.d.n.", "c. d. n."}, "pod": {"pt."}, "średnio": {"śr."},
}
_TIED_STEMS = (
    ("złot", {"zł", "pln"}), ("grosz", {"zł", "pln", "gr"}), ("dolar", {"$", "usd"}),
    ("cent", {"$", "usd", "€", "eur"}), ("euro", {"€", "eur"}), ("procent", {"%", "proc."}),
    ("kilometr", {"km"}), ("kilogram", {"kg"}), ("gram", {"g"}), ("centymetr", {"cm"}),
    ("milimetr", {"mm"}), ("mililitr", {"ml"}), ("metr", {"m"}), ("litr", {"l"}),
    ("kilokalori", {"kcal"}), ("kalori", {"kcal"}), ("minut", {"min", "min.", "<duration>"}),
    ("sekund", {"s", "sek", "sek.", "<duration>"}),
    ("godzin", {"h", "godz", "godz.", "<duration>", "<time>"}),
    ("miesi", {"mies", "mies.", "mc", "msc", "m"}), ("tydz", {"tyg", "tyg."}),
    ("tygod", {"tyg", "tyg."}), ("sztuk", {"szt", "szt."}), ("stop", {"°"}),
    ("celsjusz", {"°", "c"}), ("fahrenheit", {"°", "f"}), ("rok", {"r.", "r", "rok", "<year>"}),
    ("roc", {"r.", "r", "rok"}), ("wiek", {"w.", "<roman>"}), ("kwarta", {"<roman>"}),
    ("edycj", {"<roman>"}), ("tysiąclec", {"<roman>"}), ("doktor", {"dr", "dr."}),
    ("profesor", {"prof."}), ("stron", {"str."}), ("ulic", {"ul."}), ("telefon", {"tel."}),
    ("zwan", {"tzw."}), ("święt", {"św."}), ("raz", {"x", "×"}), ("tytuł", {"pt."}),
    ("poniedział", {"pn.", "pon."}), ("wtor", {"wt."}), ("środ", {"śr."}),
    ("czwart", {"czw."}), ("piąt", {"pt."}), ("sobot", {"sob."}), ("niedziel", {"nd.", "niedz."}),
)


def _span_marks(span: list) -> set:
    """The span's tokens in small letters, and what kind of number it holds:
    <score> anything with a colon («2:1», and «3:10», which may be one too),
    <duration> «1:30:00», <time> «18:30», <year> «2026» or a date with one,
    <roman> «XXI», <caps> an acronym whose letters may be read."""
    marks = set()
    for k, t in span:
        marks.add(t.lower())
        if k == "num":
            if ":" in t:
                marks.add("<score>")
            if t.count(":") == 2:
                marks.add("<duration>")
            if re.fullmatch(r"\d{1,2}[:.]\d{2}", t):
                marks.add("<time>")
            if re.fullmatch(r"(?:19|20)\d{2}|\d{1,2}\.\d{1,2}\.\d{4}|\d{4}-\d{2}-\d{2}", t):
                marks.add("<year>")
        elif k == "word" and t.isupper() and _roman(t):
            marks.add("<roman>")
        if k == "word" and re.fullmatch(rf"[{_UP}\d]+", t):
            marks.add("<caps>")
    return marks


def _stray_words(span: list, said: list[str], allowed: set[str]) -> list[str]:
    """The words in `said` that do not read what the span holds."""
    marks = _span_marks(span)
    lex = {w for _, t in span for key in (t, t.lower()) for w in LEXICON.get(key, "").lower().split()}
    letters = _LETTER_NAMES if "<caps>" in marks else set()

    def reads(w: str) -> bool:
        lw = w.lower()
        if (lw in _SPOKEN_WORDS or lw in lex or w in allowed or lw in letters
                or lw.startswith(_SPOKEN_STEMS) or marks & _TIED_WORDS.get(lw, set())):
            return True
        return any(lw.startswith(stem) and marks & need for stem, need in _TIED_STEMS)
    return [w for w in said if not reads(w)]


# How letters are read: the Polish names, and the English ones Poles use for
# English acronyms («ej aj», «di em»)
_LETTER_NAMES = set(_LETTERS.values()) | set(
    "ej bi si di i ef dżi ejcz ejdż aj dżej kej el em en ou pi kju ar es ti ju wi dablju "
    "dabliu eks łaj zi zet".split())
_CONNECTORS = {"i", "w", "we", "z", "ze", "do", "na", "dla", "od", "o"}
# Acronyms whose expansion may be said instead of the letters («z UE» as «z
# unii europejskiej»). Any words with the right first letters used to pass:
# «DM» as «dobrą myśl», «HR» as «handlu rolnym» (final review, 2026-09-27).
_EXPANSIONS = {"UE": "unia europejska", "NFZ": "narodowy fundusz zdrowia",
               "ZUS": "zakład ubezpieczeń społecznych", "PKB": "produkt krajowy brutto",
               "KRUS": "kasa rolniczego ubezpieczenia społecznego", "USA": "stany zjednoczone",
               "CV": "curriculum vitae"}
_UP_SET = set(_UP.replace("A-Z", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))


def _loud_word(t: str, shouting: bool = False) -> bool:
    """A word the rules read in small letters although it is written in capitals.

    In a line written in capitals that is every capital word the lexicon does
    not say otherwise («NIE RÓB TEGO»); elsewhere only a real word («UWAGA»).
    """
    if not (len(t) >= 2 and t.isalpha() and t.isupper()):
        return False
    return _plain_word(t) or (shouting and t not in LEXICON)


def _acronym_said(tokens: list[str], words: list[str], shouting: bool = False) -> bool:
    """Is `words` a reading of the acronyms in `tokens` and nothing else?

    Letter by letter («ka pe i»), as a word («zus», «zusu»), as the lexicon
    says it («rolki», «rolek»), or in full when the words' first letters are the
    acronym («narodowy fundusz zdrowia»). «Liczy się KPI» answered «Liczy się
    zawsze» must not pass just because KPI is not a number.
    """
    # «KPI» written «kpi» would pass here and never be spelled afterwards, so
    # only what the rules read as a word («ZUS», «UWAGA», «TikTok») may be kept
    stems = [t.lower() for t in tokens if not t.isupper() or _loud_word(t, shouting)] + [
        "okej", "około"] + [w for t in tokens for w in LEXICON.get(t, "").lower().split()]

    def reads(w: str) -> bool:
        return (w in _LETTER_NAMES or w in _WORDS
                or any(w == st or (len(st) >= 3 and w.startswith(st[:max(3, len(st) - 2)]))
                       for st in stems))
    if words and all(reads(w) for w in words):
        return True                      # letter by letter, accept_rewrite counts the letters
    if len(tokens) != 1 or tokens[0] not in _EXPANSIONS:
        return False
    want = [w for w in _EXPANSIONS[tokens[0]].split() if w not in _CONNECTORS]
    got = [w for w in words if w not in _CONNECTORS]
    return len(want) == len(got) and all(g[:3] == e[:3] for g, e in zip(got, want))


# a dash, not the hyphen inside «e-mail» or «3-4»
_DASH = re.compile(r"[—–]|(?<!\w)-|-(?!\w)")


def _final_punct(s: str) -> str:
    return re.search(r"[.!?…:;,]*[\"'”»)\]]*\s*$", s.rstrip()).group(0).strip()


def repair_rewrite(orig: str, new: str) -> str:
    """The AI's line with the closing punctuation put back when it left it off.

    «…na 2026 r.» came back «…na dwa tysiące dwudziesty szósty rok»: the dot of
    «r.» was also the sentence's full stop, and the check threw away an
    otherwise right answer (live test, 2026-09-27). Only a missing ending is
    restored, and a full stop added to a line that had none is taken off: «5
    błędów, które popełniałem» is a title, and its answer with a dot was refused.
    A different ending still fails accept_rewrite. A line that began with a
    small letter (a sentence wrapped from the line above) gets it back: «I pięć
    osób…» would be read as a new sentence (final review, 2026-09-27).
    """
    o, n = str(orig or "").rstrip(), str(new or "").rstrip()
    end = _final_punct(o)
    if end and n and not _final_punct(n):
        n = n + end
    elif not end and _final_punct(n) == ".":
        n = n[:-1].rstrip()
    if o.lstrip()[:1].islower() and n[:1].isupper():
        n = n[0].lower() + n[1:]
    return n


# A sentence dash may stay, become a comma or go: speech_text reads every one
# as a comma anyway, and the prompt asks for no dashes, yet the answer that
# obeyed was refused as «changed text that needs no rewrite: '–' → ','» (final
# review, 2026-09-27). A dash between two numbers is a range and stays.
_SENT_DASH = re.compile(r"(?<=\S)\s+[—–-]+\s+(?=\S)|(?<=[^\W\d_])—(?=[^\W\d_])")


def _dash_to(text: str, rep: str) -> str:
    def sub(m):
        s, e = m.start(), m.end()
        if s and e < len(text) and text[s - 1].isdigit() and text[e].isdigit():
            return m.group(0)                        # «5 - 10»: a range
        return rep
    return _SENT_DASH.sub(sub, text)


def accept_rewrite(orig: str, new: str) -> tuple[bool, str]:
    """Is the AI's version of one line safe to speak? (True, "") or (False, reason).

    The two lines are compared token by token. Only spans holding something
    to be spoken out (a number, abbreviation, symbol, acronym, Roman numeral)
    may change, together with the unit glued to them («zł», «km», «r.»); what
    replaces them must be lowercase Polish words and commas, not too many; the
    numbers read back from those words must be the digits that were there.
    Everything else, and the final punctuation, must be as written; only the
    first letter of the line may change case.
    """
    orig, new = str(orig or "").strip(), str(new or "").strip()
    orig = _r_list(orig)                     # «1. Zapisuj…»: a bullet, never read
    if not new:
        return False, "empty line"
    if "\n" in new:
        return False, "line break in the answer"
    if re.search(r"\d", new):
        return False, "digits left"
    if len(_DASH.findall(new)) > len(_DASH.findall(orig)):
        return False, "dash in the answer"
    if _final_punct(orig) != _final_punct(new):
        return False, f"final punctuation changed: {_final_punct(orig)!r} → {_final_punct(new)!r}"
    ok, why = _accept_tokens(_dash_to(orig, ", "), _dash_to(new, ", "))
    if not ok and _SENT_DASH.search(orig):
        # the dash left out altogether: «Mam pięć zasad sprawdź je.»
        if _accept_tokens(_dash_to(orig, " "), _dash_to(new, " "))[0]:
            return True, ""
    return ok, why


def _accept_tokens(orig: str, new: str) -> tuple[bool, str]:
    """accept_rewrite's token by token comparison, on lines already checked as a whole."""
    a, b = _tokens(orig), _tokens(new)
    if not a:
        return False, "empty original"
    # A word in capitals for emphasis («UWAGA», «JAK ZAROBIĆ») may come back in
    # small letters, as the rules write it; an acronym may not: «kpi» would
    # then never be spelled out.
    loud = _shouting(orig)
    ta = [t.lower() if _loud_word(t, loud) else t for _, t in a]
    # only the capitals written in the original: a number the AI wrote as
    # «PIĘĆ» is not one of them, now that Polish letters make a capital word
    kept_loud = {t for _, t in a if _loud_word(t, loud)}
    tb = [t.lower() if t in kept_loud else t for _, t in b]
    if tb and b[0][0] == "word" and tb[0] != ta[0]:
        first = tb[0][:1].swapcase() + tb[0][1:]
        tb[0] = ta[0] if first == ta[0] else tb[0][:1].lower() + tb[0][1:]
    spans, spelled = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        kinds = [_kind(a, i) for i in range(i1, i2)]
        old = " ".join(ta[i1:i2]) or "(nothing)"
        if "speak" not in kinds:
            return False, f"changed text that needs no rewrite: {old!r} → {' '.join(tb[j1:j2])!r}"
        if "plain" in kinds:
            return False, f"a word or a mark changed: {old!r} → {' '.join(tb[j1:j2])!r}"
        said = tb[j1:j2]
        if not said:
            return False, f"removed: {old!r}"
        bad = [t for t in said if t != "," and not _NEW_WORD.fullmatch(t)]
        if bad:
            return False, f"not plain lowercase words: {' '.join(bad)!r}"
        n_words = sum(t != "," for t in said)
        if n_words > 6 * (i2 - i1) + 4:
            return False, f"too many words for {old!r}"
        if (said[0] == "," and ta[i1] != ",") or (said[-1] == "," and ta[i2 - 1] != ","):
            return False, f"comma added: {old!r} → {' '.join(said)!r}"
        comps = [_compound(t) for k, t in a[i1:i2] if k == "comp"]
        # a compound adjective must stay one word («trzydziestoletni»); a number
        # with a written ending («2-go») is checked by its value below
        if any(c is None or (c[1] is None and c[0] not in said) for c in comps):
            return False, f"compound not spelled as one word: {old!r} → {' '.join(said)!r}"
        words = [t for t in said if t != ","]
        missing = _unsaid(ta[i1:i2], words) or _money_unsaid(a[i1:i2], words)
        if missing:
            return False, f"{missing!r} is not said in {' '.join(said)!r}"
        # next to a number every word must be part of saying it; an acronym
        # alone must be read out, letter by letter, as a word or in full
        if any(k in ("num", "comp", "abbr") or (k == "sym" and t in _SPEAK_SYM) or t in _FREE_UNIT
               for k, t in a[i1:i2]):
            allowed = {w for c in comps for w in c[0].split()}
            stray = _stray_words(a[i1:i2], words, allowed)
            if stray:
                return False, f"words that are not the number read out: {' '.join(stray)!r}"
        else:
            acr = [t for _, t in a[i1:i2] if t not in _GLUE]
            if not _acronym_said(acr, words, loud):
                return False, f"not a reading of {old!r}: {' '.join(said)!r}"
            if all(w in _LETTER_NAMES for w in words):
                spelled.append((old, sum(c in _UP_SET for t in acr for c in t), len(words)))
        spans.append((i1, i2, said))       # with its commas: «zero, pięć» is 0 and 5
    # read letter by letter, every letter is said: «AI» as «aj» or «KPI» as «ka»
    # dropped one and passed (final review, 2026-09-27). Summed over the spans
    # when one is off, since the diff may cut «MIX i DIY» → «em i iks i de i
    # igrek» at another «i».
    if (any(n != m for _, n, m in spelled)
            and sum(n for _, n, _ in spelled) != sum(m for _, _, m in spelled)):
        return False, f"not every letter of {next(o for o, n, m in spelled if n != m)!r} is said"
    # numbers read back in order, span by span («600 700 800» said backwards,
    # or «5 lat i 3 psy» as «trzy lat i pięć psy», must fail); if the diff
    # split one phrase in two («2,5 i 3» → «dwa i pół i trzy»), all spans together
    if any(not _same_numbers(_digit_numbers(a, i1, i2), _word_numbers(w)) for i1, i2, w in spans):
        want = [x for i1, i2, _ in spans for x in _digit_numbers(a, i1, i2)]
        got = [x for _, _, w in spans for x in _word_numbers(w)]
        if not _same_numbers(want, got):
            return False, f"numbers differ: {want} → {got}"
    return True, ""
