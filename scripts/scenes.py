"""Small commands: scene-list, scene-kit, pieces, status, config."""
import json, re, sys
from pathlib import Path

import common as C

STOCK = {
    "bigword": "kinetic typography, word-synced: lines, hl, mode pop|rise|slam, color, icon, sub, shape burst|disc|none",
    "hero": "one big object on a disc + tilted tag: icon or peep, label, labelAt, sub, badges[{icon,at,angle}], shake[]",
    "stat": "counter + progress ring: value, from, decimals, prefix, suffix, label, icon, at, dur, ring",
    "versus": "X vs Y cards or a balance (style: scale): left{label,icon,at}, right{...}, pick, pickAt, marks",
    "steps": "numbered list, checks, tag: items[{label,icon,at,mark}], title, tag{text,at}",
    "flow": "process: nodes + drawn arrows + travelling dot: nodes[{label,icon,at}], layout zigzag|vertical",
    "timeline": "vertical line, markers, playhead: items[{label,tag,at}]",
    "quote": "card with karaoke text: text, hl, by, ghost",
    "chart": "bars or a drawn line: kind, data[{label,v,at,show}], unit, title, hi",
    "character": "Open Peeps bust, faces swap on words, bubbles, props: peep{body,head,faces{Face:ref}}, bubble{text,at}, props[], away[], back[]",
    "chat": "phone with messages + typing dots: title, messages[{from: them|me, text, at}]",
    "icongrid": "big tiles (items) or a quantity grid (icon, count, highlight): items[{icon,label,at}], cols",
    "beforeafter": "a wipe reveals the change: before{label,icon}, after{...}, swipeAt",
    "level": "vial whose liquid level changes on words: levels[[v, ref]], label, tag{text,at,icon}",
    "cta": "profile + buttons that press and fill: handle, monogram, actions[{kind follow|save|comment|like|share, label, done, at}], bubble",
    "image": "a still with Ken Burns, highlight rings, labels: src, focus, highlights[{x,y,r,at}], labels[], frame card|full",
}
KIT = """Bespoke scene: one file <job>/scenes/<type>.js, plain JS, a pure function of t (frames render in parallel, out of order).

First line, the header the variety check reads:
/* @scene {"type":"<type>","tags":["..."],"layout":"<unique-layout-name>","metaphor":"<one line>","assets":["<key drawn objects>"]} */

RM.def('<type>', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const t1 = api.T(p.moneyAt);                                  // word ref -> seconds
  root.innerHTML = api.at(L.cx, L.y(0.4), `<div class="big" style="font-size:${90 * k}px">${R.esc(p.title)}</div>`, { cls: 'x', idle: 'float' })
                 + R.svg(L, `<path class="line" d="M0 0 L${L.w} ${L.h}" stroke="var(--c1)" stroke-width="${10 * k}" fill="none"/>`);
  return t => {
    api.tw(q(root, '.x .a'), t, api.K.pop(t1 - 0.05, 0.4, { o: 0, s: 0.4 }));
    R.draw(q(root, '.line'), api.prog(t, t1, t1 + 0.8, 'out'));
  };
});

api: p (the scene's params from visuals.json), L (the safe box: L.x(u), L.y(v) 0..1, L.cx, L.cy, L.w, L.h, L.x0, L.y0, L.x1, L.y1, L.k = scale per 1000 px of box
height), api.T(ref) (word ref -> seconds), api.times(text, a, b), api.at(x, y, html, {cls, idle, amp, z}) (places a point with layers .pt>.m>.a>.i; animate .a),
api.tw(el, t, keys) (keyframes [[time, {o, x, y, s, r, rx, ry, blur}, ease?], ...]), api.prog(t, a, b, ease) (0..1), api.K.pop/spring/rise/drop/slide/slam/antic/out(at, dur, from)
(ready-made keys), api.kt / api.ktUpdate (kinetic text), api.icon(ref, size), api.peep / api.peepUpdate (Open Peeps), api.burst.
Idle motion: idle: 'float'|'sway'|'breathe'|'bob'|'wobble'|'spin'|'pulse' (uniform scale only).
window.RMK: svg(L, inner) box-sized SVG layer, draw(el, u) stroke draw-on, gx(el, v, ox, oy) SVG group transform, kv(api, keys, t), tag(text, fs, cls), fitFont(el, maxW, maxH, max, min),
jit(seed, n), esc, q, qa. keepIn runs automatically, so placed elements stay inside the box.
Colours ONLY from theme tokens: var(--c1) var(--c1l) var(--c1x) var(--c2) var(--acc) var(--acc-soft) var(--ink) var(--paper) var(--text) var(--muted) var(--good) var(--bad)
var(--on-acc) var(--on-c1) var(--hl) var(--struct) var(--dim) var(--line). Fonts: var(--f-display), var(--f-head), var(--f-body). CSS classes: .big (display font), .tag, .round, .badge, .disc.
Icons: 'ph:name' (Phosphor duotone, default), 'ph-fill:', 'ph-bold:', 'tb:name' (Tabler), 'noto:name' (emoji, rarely); they are found in the code, so write refs as plain strings.
Rules: elements appear on the word they show, never empty slots waiting; text = the speaker's own words, passed in through params; a word that pops in stays >= 0.8 s; every round
element gets class .round (or .badge/.disc/.ring) with equal width and height; nothing static for > 1 s; content fills 60-70 % of the box; never put text in the subtitle band.
Use in visuals.json: {"type": "<type>", ...params..., "moneyAt": "money"}. Test with reel-tool preview.
"""


def scene_list(argv):
    w = (argv[0].lower() if argv else "")
    for k, v in STOCK.items():
        if w in k or w in v.lower():
            print(f"stock {k}: {v}")
    n = 0
    for d in C.libraries():
        for f in sorted(Path(d).glob("*.js")):
            if f.name.startswith("_"):
                continue
            m = re.search(r"/\*\s*@scene\s*(\{.*?\})\s*\*/", f.read_text(encoding="utf-8"), re.S)
            meta = json.loads(m.group(1)) if m else {}
            if w and w not in json.dumps(meta).lower():
                continue
            n += 1
            print(f"library {f.stem}: {meta.get('metaphor', '')} [{meta.get('layout', '')}]")
    print(f"({n} library scenes. They show what is possible; a Reel needs NEW ones, see reel-tool scene-kit.)")


def scene_show(argv):
    for d in C.libraries():
        f = Path(d) / (argv[0] + ".js")
        if f.exists():
            print(f.read_text(encoding="utf-8")); return
    C.fail("no such library scene: " + argv[0])


def ring(argv):
    """synthesised double ring (400 + 450 Hz, 0.4 s on, 0.2 s off, 0.4 s on); the render mixes it ~5 dB under the voice"""
    import wave
    import numpy as np
    sr = 48000

    def burst(d):
        t = np.arange(int(d * sr)) / sr
        return (0.5 * np.sin(2 * np.pi * 400 * t) + 0.5 * np.sin(2 * np.pi * 450 * t)) * np.minimum(1, np.minimum(t, d - t) / 0.01)
    sig = np.concatenate([burst(0.4), np.zeros(int(0.2 * sr)), burst(0.4)])
    sig = sig / np.sqrt(np.mean(sig[sig != 0] ** 2)) * 10 ** (-24 / 20)
    p = C.job_dir(argv[0]) / "ring.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.stack([sig, sig], 1) * 32767).astype(np.int16).tobytes())
    print(p)


def icon(argv):
    import gzip
    w = (argv[-1] if argv else "").lower()
    for k in ("ph", "tb"):
        names = sorted(json.load(gzip.open(C.MOTION / "assets" / "icons" / f"{k}.json.gz", "rt", encoding="utf-8")))
        hits = [n for n in names if w in n][:60]
        print(f"{k}: " + (" ".join(f"{k}:{n}" for n in hits) or "nothing"))


def pieces(argv):
    import render
    job = C.job_dir(argv[0]).resolve(); J = C.load_json(job / "job.json"); cut = C.load_json(job / "cut.json")
    infos = {x["file"]: x for x in J["info"]}
    for k, p in enumerate(cut["pieces"]):
        render.build_piece(job, k, (J.get("stab") or {}).get(p["file"], p["file"]), p["a"], p["b"], infos[p["file"]])
    print(f"{len(cut['pieces'])} pieces ready")


def status(argv):
    if not argv:
        F = C.folders()
        for d in sorted(F["work"].glob("*/job.json"))[-12:]:
            print(d.parent.name)
        return
    job = C.job_dir(argv[0])
    for f in ("job.json", "cut.json", "job.md", "stutter_report.json", "subs.ass", "visuals.json", "final.mp4", "gate.json", "report.json"):
        print(("yes " if (job / f).exists() else "no  ") + f)
    g = C.load_json(job / "gate.json")
    if g:
        print("gate:", "PASS" if g["pass"] else "FAIL", [r["check"] for r in g["rows"] if not r["ok"]])


def config(argv):
    cfg = C.load_json(C.CONFIG_FILE, {}) or {}
    if len(argv) >= 2:
        v = argv[1]
        try:
            v = json.loads(v)
        except ValueError:
            pass
        cfg[argv[0]] = v; C.save_json(C.CONFIG_FILE, cfg)
    print(json.dumps(C.config(), ensure_ascii=False, indent=1))
    print("data dir:", C.DATA)


def main(cmd, argv):
    if cmd == "scene-list":
        scene_list(argv)
    elif cmd == "scene-kit":
        print(KIT)
    elif cmd == "pieces":
        pieces(argv)
    elif cmd == "status":
        status(argv)
    elif cmd == "config":
        config(argv)
    elif cmd == "scene-show":
        scene_show(argv)
    elif cmd == "ring":
        ring(argv)
    elif cmd == "icon":
        icon(argv)
