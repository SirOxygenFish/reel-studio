"""reel-tool subs <job> [--title "line one|line two"] [--title-end SEC] [--title-margin PX] [--phrases "keep together|these words"] [--keywords "a|b"]
                         [--second-voice "T0-T1,T0-T1"]

Word-timed subtitles (1-3 words, the spoken word in the active colour with a small bump, each line pops in) plus the title.
Options are remembered in edit.json. Numbers are shown as digits, phantom Whisper echoes dropped, dashes removed.
Writes subs.ass and words.json (display words, the ones scene refs use); prints every line with its time for review.
"""
import json, re, sys
from pathlib import Path

import common as C
from autoedit import subs as S


def main(argv):
    job = C.job_dir(argv[0]); argv = argv[1:]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    J = C.job_sync(job); cut = C.load_json(job / "cut.json") or C.fail("no cut.json")
    E = C.load_json(job / "edit.json", {}) or {}
    if opt("--title") is not None:
        E["title"] = [x.strip() for x in opt("--title").split("|") if x.strip()]
    if opt("--title-end"):
        E["title_end"] = float(opt("--title-end"))
    if opt("--title-margin"):
        E["title_margin"] = int(opt("--title-margin"))
    if opt("--phrases") is not None:
        E["phrases"] = [x.strip() for x in opt("--phrases").split("|") if x.strip()]
    if opt("--keywords") is not None:
        E["keywords"] = [x.strip() for x in opt("--keywords").split("|") if x.strip()]
    if opt("--second-voice") is not None:
        E["roles"] = [[float(x) for x in r.split("-")] for r in opt("--second-voice").split(",") if r]
    C.save_json(job / "edit.json", E)
    B = C.brand(J.get("brand")); S.configure(dict(B["subs"], **({"title_margin_v": E["title_margin"]} if E.get("title_margin") else {})))
    # raw Reel-time words come straight from the cut, so a re-run after subs never works on display words
    from autoedit import speech  # noqa: F401 (keeps the import order of the package simple)
    pieces = cut["pieces"]; o = 0.0; raw = []
    for p in pieces:
        for w in p["words"]:
            s = max(w[0], p["a"]) - p["a"] + o; e = min(w[1], p["b"]) - p["a"] + o
            raw.append([round(s, 3), round(max(e, s + 0.05), 3), w[2], w[3] if len(w) > 3 else 1.0])
        o += p["b"] - p["a"]
    lang = cut.get("lang") or "en"
    ws = S.subtitle_words(raw, lang)
    if lang != "de":                                       # a piece's first word can carry a capital from Whisper's window edge
        starts = {round(max(p["words"][0][0], p["a"]) - p["a"] + sum(q["b"] - q["a"] for q in pieces[:k]), 2) for k, p in enumerate(pieces) if p["words"]}
        for x, y in zip(ws, ws[1:]):
            t = y[2]
            if any(abs(y[0] - st) < 0.06 for st in starts) and len(t) > 1 and t[0].isupper() and t[1:].lower() == t[1:] \
                    and not t.startswith(("I'", "I’")) and not re.search(r"[.?!…:]$", x[2]):
                y[2] = t[0].lower() + t[1:]
    C.save_json(job / "words.json", {"total": round(o, 3), "words": [[w[0], w[1], w[2]] for w in ws]})
    title = E.get("title") or None
    secs = E.get("title_end", 7.0)
    doc = S.ass_document(ws, o, title=title, lang=lang, phrases=E.get("phrases") or (), title_secs=secs,
                         keywords=E.get("keywords") or (), roles=E.get("roles") or ())
    S.write_ass(job / "subs.ass", doc)
    small = S.SMALL_BY_LANG.get(lang, frozenset())
    clean = [[float(w[0]), float(w[1]), S._safe(w[2])] for w in ws]
    ch = S.chunk(clean, E.get("phrases") or (), small)
    long_ = [c for c in ch if len(" ".join(S.clean(x[2]) for x in c)) > 24]
    for c in ch:
        print(f"{c[0][0]:6.2f}  {' '.join(S.clean(x[2]) for x in c)}")
    print(f"total {o:.2f} s, {len(ws)} words, {len(ch)} lines, {len(long_)} over 24 characters; title: {title} until {secs}")


if __name__ == "__main__":
    main(sys.argv[1:])
