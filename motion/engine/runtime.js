// ReelsMotion runtime: a deterministic motion-graphics timeline for 9:16 Reels.
// Everything on screen is a pure function of time: window.RM.seek(t) sets every element, so the renderer can capture
// frames in any order, in parallel. Scenes come from scenes.js (RM.def), the storyboard and words from window.CFG.
(function () {
  'use strict';
  const CFG = window.CFG, TH = CFG.theme, MO = TH.motion;
  const W = CFG.W, H = CFG.H, FPS = CFG.fps;

  // ---------- math, easing, springs ----------
  const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
  const lerp = (a, b, u) => a + (b - a) * u;
  const smooth = (a, b, x) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };
  const E = {
    lin: u => u,
    in: u => u * u * u,
    out: u => 1 - Math.pow(1 - u, 3),
    io: u => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2),
    outQ: u => 1 - Math.pow(1 - u, 5),
    inE: u => (u <= 0 ? 0 : Math.pow(2, 10 * u - 10)),
    outE: u => (u >= 1 ? 1 : 1 - Math.pow(2, -10 * u)),
    ioE: u => (u <= 0 ? 0 : u >= 1 ? 1 : u < 0.5 ? Math.pow(2, 20 * u - 10) / 2 : (2 - Math.pow(2, -20 * u + 10)) / 2),
    back: u => { const c = MO.overshoot, d = c + 1; return 1 + d * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); },
    anti: u => { const c = 1.6, d = c + 1; return d * u * u * u - c * u * u; },               // anticipation (pull back first)
    elastic: u => (u <= 0 ? 0 : u >= 1 ? 1 : Math.pow(2, -10 * u) * Math.sin((u * 10 - 0.75) * (2 * Math.PI) / 3) + 1),
    // damped spring step response, u in seconds/duration units: overshoot ~10-25 %, settles by u=1
    spring: u => (u <= 0 ? 0 : u >= 1 ? 1 : 1 - Math.exp(-6.5 * u) * (Math.cos(13 * u) + 0.5 * Math.sin(13 * u))),
  };
  const prog = (t, a, b, e = 'out') => E[e](clamp((t - a) / Math.max(1e-6, b - a)));

  // deterministic random
  function rng(seed) { let s = (seed * 2654435761) >>> 0 || 1; return () => ((s = (s ^ (s << 13)) >>> 0, s = (s ^ (s >>> 17)) >>> 0, s = (s ^ (s << 5)) >>> 0) / 4294967296); }

  // ---------- keyframes ----------
  // keys: [[time, {o,x,y,s,sx,sy,r,rx,ry,blur}, ease], ...]; the ease shapes the segment that ENDS at that key
  const DEF = { o: 1, x: 0, y: 0, s: 1, sx: 1, sy: 1, r: 0, rx: 0, ry: 0, blur: 0 };
  function val(keys, t) {
    let prev = Object.assign({}, DEF, keys[0][1]);
    if (t <= keys[0][0]) return prev;
    for (let i = 1; i < keys.length; i++) {
      const [kt, kv, ke] = keys[i], pt = keys[i - 1][0], cur = Object.assign({}, prev, kv);
      if (t < kt) {
        const p = E[ke || 'out'](clamp((t - pt) / Math.max(1e-6, kt - pt))), r = {};
        for (const k in cur) r[k] = prev[k] + (cur[k] - prev[k]) * p;
        return r;
      }
      prev = cur;
    }
    return prev;
  }
  const xf = v => `translate(${v.x.toFixed(2)}px,${v.y.toFixed(2)}px)` + (v.rx || v.ry ? ` perspective(1600px) rotateX(${v.rx}deg) rotateY(${v.ry}deg)` : '') +
    ` rotate(${v.r.toFixed(3)}deg) scale(${(v.s * v.sx).toFixed(4)},${(v.s * v.sy).toFixed(4)})`;
  function apply(el, v) {
    el.style.opacity = clamp(v.o);
    el.style.transform = xf(v);
    el.style.filter = v.blur > 0.05 ? `blur(${v.blur.toFixed(2)}px)` : '';
    el.style.visibility = v.o <= 0.003 ? 'hidden' : 'visible';
  }
  const list = el => (!el ? [] : el instanceof Element ? [el] : Array.from(el));
  const tw = (el, t, keys) => list(el).forEach(e => apply(e, val(keys, t)));
  const setv = (el, v) => list(el).forEach(e => apply(e, Object.assign({}, DEF, v)));

  // ready-made entrances (all with anticipation/overshoot from the theme's motion tokens)
  const D = MO.enter;
  const K = {
    pop: (at, d = D, from = { o: 0, s: 0.35, r: -8 }) => [[at, from], [at + d * 0.35, { o: 1 }, 'out'], [at + d, { s: 1, r: 0, x: 0, y: 0 }, 'back']],
    spring: (at, d = D * 1.5, from = { o: 0, s: 0.2 }) => [[at, from], [at + 0.08, { o: 1 }, 'lin'], [at + d, { s: 1, x: 0, y: 0, r: 0 }, 'spring']],
    rise: (at, d = D, dy = 90) => [[at, { o: 0, y: dy, s: 0.96 }], [at + d, { o: 1, y: 0, s: 1 }, 'back']],
    drop: (at, d = D, dy = -140) => [[at, { o: 0, y: dy }], [at + d, { o: 1, y: 0 }, 'spring']],
    slide: (at, dx, d = D) => [[at, { o: 0, x: dx, blur: 10 }], [at + d, { o: 1, x: 0, blur: 0 }, 'back']],
    slam: (at, d = D * 0.8) => [[at, { o: 0, s: 2.4, blur: 14 }], [at + d * 0.55, { o: 1, s: 0.94, blur: 0 }, 'in'], [at + d, { s: 1 }, 'back']],
    // anticipation: dips before shooting in
    antic: (at, dx = 0, dy = 60, d = D) => [[at, { o: 0, x: dx, y: dy, s: 0.9 }], [at + d * 0.25, { o: 1, x: dx * 1.08, y: dy * 1.15, s: 0.86 }, 'out'], [at + d, { x: 0, y: 0, s: 1 }, 'back']],
    out: (keys, at, d = 0.3, to = { o: 0, s: 0.8, blur: 6 }) => keys.concat([[at, {}], [at + d, to, 'in']]),
  };

  // ---------- secondary (idle) motion: nothing is ever fully still ----------
  // data-idle="float sway breathe bob wobble spin pulse"; data-amp scales it; phase comes from the element's index
  const IDLE = {
    float: (t, p, a) => ({ y: 9 * a * Math.sin(t * 1.9 + p) }),
    sway: (t, p, a) => ({ r: 2.2 * a * Math.sin(t * 1.3 + p * 1.7) }),
    breathe: (t, p, a) => ({ s: 1 + 0.022 * a * Math.sin(t * 2.4 + p) }),
    bob: (t, p, a) => ({ y: -7 * a * Math.abs(Math.sin(t * 3.6 + p)) }),
    wobble: (t, p, a) => ({ s: 1 + 0.014 * a * Math.sin(t * 5.1 + p), r: 1.2 * a * Math.sin(t * 2.3 + p) }),   // uniform only: circles stay circles
    spin: (t, p, a) => ({ r: (t * 14 * a + p * 40) % 360 }),
    pulse: (t, p, a) => ({ s: 1 + 0.045 * a * (0.5 + 0.5 * Math.sin(t * 4.2 + p)) }),
    drift: (t, p, a) => ({ x: 12 * a * Math.sin(t * 0.7 + p), y: 10 * a * Math.cos(t * 0.9 + p) }),
  };
  let idleEls = [];
  function idle(t) {
    for (const [el, kinds, ph, amp0] of idleEls) {
      const amp = amp0 * (MO.idleAmp || 1);
      if (el.offsetParent === null && el.style.position !== 'fixed') continue;
      const v = Object.assign({}, DEF);
      for (const k of kinds) { const d = IDLE[k](t, ph, amp); for (const p in d) v[p] = p === 's' || p === 'sx' || p === 'sy' ? v[p] * d[p] : v[p] + d[p]; }
      el.style.transform = xf(v);
    }
  }

  // ---------- words and time references ----------
  const norm = s => (s || '').toLowerCase().replace(/[^\p{L}\p{N}%]/gu, '');
  const WORDS = CFG.words.map(w => ({ s: w[0], e: w[1], t: w[2], n: norm(w[2]) }));
  const SENT = WORDS.length ? [0] : [];                        // indices of sentence starts (none: a wordless video, e.g. a tutorial)
  WORDS.forEach((w, i) => { if (i && /[.?!…]["”»]?$/.test(WORDS[i - 1].t)) SENT.push(i); });
  const PHRASE = WORDS.map((w, i) => i === 0 || /[,;:.?!…]["”»]?$/.test(WORDS[i - 1].t)).map((b, i) => (b ? i : -1)).filter(i => i >= 0);
  const onsets = WORDS.map(w => w.s);
  function nearestOnset(x, within = 0.3) {
    let best = null, bd = within;
    for (const o of onsets) { const d = Math.abs(o - x); if (d <= bd) { bd = d; best = o; } }
    return best === null ? x : best;
  }
  // ref: number (snapped to a word onset within 0.3 s) | "word" (first at/after ctxStart) | "word#2" (2nd in the video)
  //      | "@12" (word index) | "end:word" | any of these + "+0.2" / "-0.1"
  function T(ref, ctxStart = -1) {
    if (ref === undefined || ref === null) return null;
    if (typeof ref === 'number') return CFG.snap === false ? ref : nearestOnset(ref);
    let s = String(ref).trim(), off = 0;
    const m = s.match(/^(.*?)([+-]\d+(?:\.\d+)?)$/);
    if (m && m[1] && !/^@?\d+$/.test(s)) { s = m[1]; off = parseFloat(m[2]); }
    let useEnd = false;
    if (s.startsWith('end:')) { useEnd = true; s = s.slice(4); }
    let w = null;
    if (/^@\d+$/.test(s)) w = WORDS[+s.slice(1)];
    else if (/^-?\d+(\.\d+)?$/.test(s)) return nearestOnset(parseFloat(s)) + off;
    else {
      const [txt, nth] = s.split('#'), n = norm(txt);
      if (nth) { let k = 0; w = WORDS.find(x => x.n === n && ++k === +nth); }
      else w = WORDS.find(x => x.n === n && x.s >= ctxStart - 0.05) || WORDS.find(x => x.n.startsWith(n) && x.s >= ctxStart - 0.05) || WORDS.find(x => x.n === n);
    }
    if (!w) throw new Error('time ref not found: ' + ref);
    return (useEnd ? w.e : w.s) + off;
  }
  // onsets for each word of `text` inside [a, b]: greedy match against the transcript, interpolated where unmatched
  function times(text, a, b) {
    const toks = text.split(/\s+/).filter(Boolean), win = WORDS.filter(w => w.s >= a - 0.35 && w.s <= b + 0.1);
    const out = []; let j = 0;
    for (const tk of toks) {
      const n = norm(tk); let hit = -1;
      for (let k = j; k < win.length && k < j + 4; k++) if (win[k].n === n || (n.length > 3 && win[k].n.startsWith(n.slice(0, 4)))) { hit = k; break; }
      if (hit >= 0) { out.push(win[hit].s); j = hit + 1; } else out.push(null);
    }
    for (let i = 0; i < out.length; i++) if (out[i] === null) {        // interpolate gaps
      let p = i - 1; while (p >= 0 && out[p] === null) p--; let q = i + 1; while (q < out.length && out[q] === null) q++;
      const ta = p >= 0 ? out[p] : a, tb = q < out.length ? out[q] : b;
      out[i] = ta + (tb - ta) * (i - p) / (q - p);
    }
    return out;
  }
  const sentenceStart = i => WORDS[SENT[clamp(i, 0, SENT.length - 1)]].s;

  // ---------- assets ----------
  let uid = 0;
  function icon(name, size = 120, color = 'currentColor', cls = '') {
    let svg = CFG.icons[name];
    if (!svg) { console.warn('missing icon ' + name); return `<span class="ic ${cls}" style="width:${size}px;height:${size}px"></span>`; }
    const id = 'u' + (uid++);                                  // namespace ids (Noto emoji reuse gradient ids)
    svg = svg.replace(/id="([^"]+)"/g, `id="${id}$1"`).replace(/url\(#([^)]+)\)/g, `url(#${id}$1)`).replace(/href="#([^"]+)"/g, `href="#${id}$1"`);
    if (!name.startsWith('noto:') && !/^<svg[^>]*\s(fill|stroke)=/.test(svg)) svg = svg.replace('<svg', '<svg fill="currentColor"');
    return `<span class="ic ${cls}" style="width:${size}px;height:${size}px;color:${color}">${svg}</span>`;
  }
  // Open Peeps bust: body + head group (hair, face(s), beard, accessory). faces: {Name: startTime} swaps the face over time
  function peep(spec) {
    const P = CFG.peeps, g = P.groups, f = P.fix, body = P.body[spec.body || 'Explaining'];
    const faces = Object.keys(spec.faces || { [spec.face || 'Smile']: 0 });
    const hair = spec.head ? P.head[spec.head] : null, beard = spec.beard ? P.beard[spec.beard] : null, acc = spec.accessory ? P.accessory[spec.accessory] : null;
    const hx = f.head[spec.body] || '';
    const html = `<svg class="peep" viewBox="${P.viewBox}" overflow="visible" style="width:${spec.size || 600}px">
      <g class="pb" transform="${g.Body}">${body.svg}</g>
      <g transform="${hx}"><g class="phd">
        ${hair ? `<g transform="${g.Hair}"><g transform="${f.hair[spec.head] || ''}">${hair.svg}</g></g>` : ''}
        ${faces.map(fc => `<g class="pf" data-f="${fc}" transform="${g.Face}">${P.face[fc].svg}</g>`).join('')}
        ${beard ? `<g transform="${g.Beard}"><g transform="${f.beard[spec.beard] || ''}">${beard.svg}</g></g>` : ''}
        ${acc ? `<g transform="${g.Accessories}"><g transform="${f.accessory[spec.accessory] || ''}">${acc.svg}</g></g>` : ''}
      </g></g></svg>`;
    return html;
  }
  function peepUpdate(root, t, spec, talk = []) {   // face swaps + head motion (nods while "talking" windows are on)
    const fs = Object.entries(spec.faces || {}).map(([k, v]) => [k, typeof v === 'number' ? v : T(v)]).sort((a, b) => a[1] - b[1]);
    if (fs.length) {
      let cur = fs[0][0]; for (const [k, at] of fs) if (t >= at) cur = k;
      root.querySelectorAll('.pf').forEach(e => { e.style.display = e.dataset.f === cur ? '' : 'none'; });
    }
    const hd = root.querySelector('.phd'); if (!hd) return;
    let talking = talk.some(([a, b]) => t >= a && t <= b) ? 1 : 0;
    const r = 2.2 * Math.sin(t * 1.7) + talking * 3.5 * Math.sin(t * 9.5), y = 4 * Math.sin(t * 2.1) + talking * 6 * Math.abs(Math.sin(t * 7.3));
    hd.setAttribute('transform', `translate(0 ${y.toFixed(2)}) rotate(${r.toFixed(2)} 620 760)`);
    const pb = root.querySelector('.pb');
    if (pb) pb.setAttribute('transform', `${CFG.peeps.groups.Body} translate(0 ${(3 * Math.sin(t * 2.4)).toFixed(2)})`);
  }

  // ---------- kinetic text ----------
  // kt(text, {cls, hl: [words to highlight], mode: rise|pop|slam|type}) -> html; ktUpdate(el, t, wordTimes)
  function kt(text, o = {}) {
    const hl = (o.hl || []).map(norm);
    return `<div class="kt ${o.cls || ''}" data-mode="${o.mode || 'rise'}">` + text.split(/\s+/).filter(Boolean).map((w, i) => {
      const h = hl.includes(norm(w)) ? ' hl' : '';
      return `<span class="kw${h}" data-i="${i}"><span class="kmark"></span>` +
        Array.from(w).map(c => `<span class="kc">${c.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</span>`).join('') + '</span>';
    }).join(' ') + '</div>';
  }
  function ktUpdate(el, t, wt, o = {}) {
    if (!el) return;
    const mode = el.dataset.mode, st = o.stagger ?? MO.letter;
    el.querySelectorAll('.kw').forEach((w, i) => {
      const at = wt[Math.min(i, wt.length - 1)] - (o.lead ?? 0.06);
      const cs = w.querySelectorAll('.kc');
      cs.forEach((c, k) => {
        const a = at + k * st;
        if (mode === 'type') { c.style.opacity = t >= a ? 1 : 0; return; }
        if (o.ghost) {                                      // karaoke: the line waits faintly, each word lights up and lifts
          const u = prog(t, a, a + 0.22, 'out'), b = prog(t, a, a + 0.32, 'back');
          apply(c, Object.assign({}, DEF, { o: 0.26 + 0.74 * u, y: 10 * (1 - b) - 6 * Math.sin(Math.PI * clamp((t - a) / 0.32)), s: 1 + 0.06 * Math.sin(Math.PI * clamp((t - a) / 0.32)) }));
          return;
        }
        if (mode === 'slam') apply(c, val(K.slam(a, 0.32), t));
        else if (mode === 'pop') apply(c, val([[a, { o: 0, s: 0.2, y: 20 }], [a + 0.05, { o: 1 }, 'lin'], [a + 0.34, { s: 1, y: 0 }, 'back']], t));
        else apply(c, val([[a, { o: 0, y: 70, r: 10, s: 0.8 }], [a + 0.05, { o: 1 }, 'lin'], [a + 0.36, { y: 0, r: 0, s: 1 }, 'back']], t));
      });
      if (w.classList.contains('hl')) {                     // marker sweep behind highlighted words
        const m = w.querySelector('.kmark'); const p = prog(t, at + 0.12, at + 0.45, 'io');
        m.style.transform = `scaleX(${p})`; w.classList.toggle('on', p > 0.5);
      }
    });
  }

  // ---------- particles (canvas) ----------
  const PART = [];
  function initParticles() {
    const r = rng(7), n = TH.particles?.count ?? 26;
    for (let i = 0; i < n; i++) PART.push({ x: r() * W, y: r() * H, z: 0.4 + r() * 1.1, ph: r() * 6.28, sz: 3 + r() * 9, c: r() < 0.35 ? 1 : 0 });
  }
  const BURSTS = [];      // [t0, x, y, n, color]
  function drawParticles(ctx, t, cam) {
    ctx.clearRect(0, 0, W, H);
    const cols = TH.particles?.colors || ['rgba(255,255,255,0.5)', 'rgba(255,241,118,0.6)'];
    for (const p of PART) {
      const sp = TH.particles?.speed ?? 1;                    // theme: how lively the background drift is
      const y = ((p.y - t * 26 * sp * p.z) % (H + 60) + H + 60) % (H + 60) - 30;
      const x = p.x + 18 * sp * Math.sin(t * 0.6 * sp * p.z + p.ph) - cam.x * 0.3 * p.z;
      const a = 0.25 + 0.25 * Math.sin(t * 1.3 + p.ph);
      const g = ctx.createRadialGradient(x, y, 0, x, y, p.sz * p.z * 2.2);
      g.addColorStop(0, cols[p.c]); g.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.globalAlpha = a; ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, p.sz * p.z * 2.2, 0, 6.283); ctx.fill();
    }
    ctx.globalAlpha = 1;
    for (const [t0, bx, by, n, col] of BURSTS) {             // sparkle bursts on emphasis
      const a = t - t0; if (a < 0 || a > 0.9) continue;
      const r = rng(Math.round(t0 * 100));
      for (let i = 0; i < n; i++) {
        const ang = r() * 6.283, sp = 260 + r() * 520, d = sp * E.outQ(a / 0.9) * 0.9;
        const x = bx + Math.cos(ang) * d, y = by + Math.sin(ang) * d + 120 * a * a, s = (1 - a / 0.9) * (5 + r() * 9);
        ctx.fillStyle = col || TH.colors.acc; ctx.globalAlpha = clamp(1.4 - a * 1.6);
        ctx.save(); ctx.translate(x, y); ctx.rotate(ang + a * 6); ctx.fillRect(-s, -s * 0.35, s * 2, s * 0.7); ctx.restore();
      }
    }
    ctx.globalAlpha = 1;
  }

  // ---------- layout box ----------
  // the content box (safe area) for a scene; while the title shows, the box starts under it
  function layout(box) {
    const [x0, y0, x1, y1] = box, w = x1 - x0, h = y1 - y0;
    return { x0, y0, x1, y1, w, h, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, k: h / 1000,
             x: u => x0 + w * u, y: v => y0 + h * v };
  }

  // ---------- scenes ----------
  const DEFS = {};
  const def = (name, d) => { DEFS[name] = d; };
  const SC = [];                 // built scenes: {spec, start, end, el, update, L, tr}
  const stage = document.getElementById('stage');

  function at(x, y, inner, o = {}) {      // a zero-size point centring its child; .m = match layer, .a = tween, .i = idle
    const idl = o.idle ? ` data-idle="${o.idle}"` + (o.amp ? ` data-amp="${o.amp}"` : '') : '';
    return `<div class="pt ${o.cls || ''}" style="left:${x.toFixed(1)}px;top:${y.toFixed(1)}px;${o.z ? 'z-index:' + o.z + ';' : ''}"${o.match ? ` data-match="${o.match}"` : ''}>` +
      `<div class="m"><div class="a"${o.content === false ? ' data-c="0"' : ''}><div class="i"${idl}>${inner}</div></div></div></div>`;
  }

  function build() {
    const sb = CFG.board, list = sb.scenes;
    const titleTo = sb.title ? T(sb.title.to ?? 5) : -1;
    // resolve scene starts: explicit at, else the next sentence; snap numbers to sentence/phrase starts within 0.45 s
    let sentPtr = Math.max(0, SENT.filter(k => WORDS[k].s <= CFG.t0 + 0.3).length - 1);   // segments start mid-video
    let prevStart = CFG.t0;
    const starts = list.map((s, i) => {
      if (i === 0 && s.at === undefined) return 0;
      let t;
      if (s.at === undefined) t = sentenceStart(++sentPtr) - MO.lead;
      else if (typeof s.at === 'number') {
        const cand = PHRASE.map(k => WORDS[k].s).reduce((b, x) => (Math.abs(x - s.at) < Math.abs(b - s.at) ? x : b), 1e9);
        t = Math.abs(cand - s.at) <= 0.45 ? cand - MO.lead : s.at;
      } else t = T(s.at, prevStart + 0.2) - MO.lead;      // word refs resolve after the previous scene, never earlier in the video
      prevStart = Math.max(0, t);
      return prevStart;
    });
    list.forEach((spec, i) => {
      const start = i === 0 ? CFG.t0 : starts[i], end = i + 1 < list.length ? starts[i + 1] : CFG.t1;
      const box = (spec.box || CFG.box).slice();
      if (titleTo > start + 0.3 && sb.title && !spec.box) box[1] = Math.max(box[1], CFG.titleBottom);
      let L = layout(box);
      const el = document.createElement('section');
      el.className = 'scene'; el.dataset.type = spec.type; el.dataset.i = i;
      const BG = TH.bgs.map(b => (Array.isArray(b) ? { a: b[0], b: b[1] } : b)), norm_ = BG.map((b, j) => j).filter(j => !BG[j].alt);
      const bgv = BG[spec.bg !== undefined ? spec.bg % BG.length : norm_[i % norm_.length]];
      el.style.setProperty('--sbg0', bgv.a); el.style.setProperty('--sbg1', bgv.b); if (bgv.alt) el.classList.add('alt');
      stage.appendChild(el);
      // optional heading (any scene): kinetic, word-synced, on top of the box; the scene gets the rest of the box
      let head = null;
      if (spec.heading) {
        const hd = document.createElement('div'); hd.className = 'sh'; el.appendChild(hd);
        hd.innerHTML = at(L.cx, 0, kt(spec.heading, { cls: 'lemon sh-t', mode: 'rise', hl: spec.headingHl }), { cls: 'sh-p' });
        const t_ = hd.querySelector('.kt'); t_.style.cssText = 'font-family:var(--f-display);font-weight:var(--w-display);white-space:nowrap;text-transform:uppercase;font-size:' + (90 * L.k) + 'px';
        fit(t_, L.w * 0.96, 30);
        const hh = t_.getBoundingClientRect().height;
        hd.querySelector('.pt').style.top = (L.y0 + hh / 2) + 'px';
        L = layout([box[0], box[1] + hh + 30 * L.k, box[2], box[3]]);
        head = { el: t_, wt: null, a: hd.querySelector('.a') };
      }
      const body = document.createElement('div'); body.className = 'sb'; el.appendChild(body);
      const d = DEFS[spec.type];
      if (!d) throw new Error('unknown scene type ' + spec.type);
      const api = { spec, p: spec, L, start, end, T: r => T(r, start), times, at, icon, peep, peepUpdate, kt, ktUpdate, tw, setv, K, E, prog, clamp, lerp, smooth, rng, TH, CFG,
                    burst: (t0, x, y, n = 18, c) => BURSTS.push([t0, x, y, n, c]) };
      const upd0 = d(api, body) || (() => {});
      if (head) head.wt = times(spec.heading, spec.headingAt !== undefined ? T(spec.headingAt, start) : start, end);
      const upd = head ? (t => { ktUpdate(head.el, t, head.wt); setv(head.a, {}); upd0(t); }) : upd0;
      SC.push({ spec, start, end, el, update: upd, L, api });
    });
    // transitions between consecutive scenes (theme cycle unless the scene says "in")
    SC.forEach((s, i) => {
      if (i === 0) { s.tin = { type: CFG.tin || 'none', d: 0.45 }; return; }
      const type = s.spec.in || TH.transitions[(i - 1) % TH.transitions.length];
      s.tin = { type, d: type === 'cut' ? 0 : (s.spec.inDur || MO.trans), focus: s.spec.focus };
    });
    // camera punches: storyboard "punch" refs + per-scene
    PUNCH.push(...(sb.punch || []).map(r => T(r)));
    SC.forEach(s => (s.spec.punch || []).forEach(r => PUNCH.push(T(r, s.start))));
    // title
    if (sb.title) {
      const tl = document.getElementById('title');
      tl.innerHTML = sb.title.lines.map((l, i) => `<div class="tl l${i}">${kt(l, { cls: 'tk', hl: sb.title.hl, mode: 'pop' })}</div>`).join('');
      TITLE.el = tl; TITLE.from = T(sb.title.from ?? 0.05); TITLE.to = titleTo;
      TITLE.wt = sb.title.lines.map((l, i) => l.split(/\s+/).map((_, k) => TITLE.from + 0.18 * i + 0.07 * k));
      tl.querySelectorAll('.tl').forEach(l => fit(l.firstChild, CFG.box[2] - CFG.box[0] - 20));
    }
    document.querySelectorAll('[data-idle]').forEach((el, i) => idleEls.push([el, el.dataset.idle.split(/\s+/), i * 1.91, parseFloat(el.dataset.amp || '1')]));
  }
  const PUNCH = [], TITLE = {};

  function fit(el, maxW, minFs = 30) {     // shrink font until el fits maxW
    let fs = parseFloat(getComputedStyle(el).fontSize);
    while (el.getBoundingClientRect().width > maxW && fs > minFs) el.style.fontSize = (fs -= 2) + 'px';
  }

  // ---------- camera ----------
  function camera(t) {
    const s = SC.find(x => t >= x.start && t < x.end) || SC[SC.length - 1];
    const i = SC.indexOf(s), u = clamp((t - s.start) / Math.max(0.5, s.end - s.start));
    const dir = i % 2 ? 1 : -1, cm = s.spec.camera || {};
    if (cm.still) return { z: 1, x: 0, y: 0, r: 0 };                    // screens with text to read: no drift, no zoom, no tilt
    let z = lerp(cm.z0 ?? 1.0, cm.z1 ?? (MO.camZ || 1.055), E.io(u));   // slow push-in per scene (theme motion.camZ)
    let x = dir * 16 * Math.sin(u * Math.PI * 0.8) + 7 * Math.sin(t * 0.37), y = -10 * u + 6 * Math.cos(t * 0.29);
    let r = (cm.r ?? 0.5) * dir * (u - 0.5) * 2;
    for (const p of PUNCH) { const a = t - p; if (a >= 0 && a < 0.6) z += 0.05 * (1 - E.spring(a / 0.6)) * (a < 0.06 ? a / 0.06 : 1) * 1; }
    if (s.tin && s.tin.type === 'cut') { const a = t - s.start; if (a >= 0 && a < 0.4) z += 0.08 * (1 - E.spring(a / 0.4)); }
    return { z, x, y, r };
  }

  // ---------- transitions ----------
  const blurX = document.getElementById('mbx'), blurY = document.getElementById('mby');
  const wipe = document.getElementById('wipe'), irisRing = document.getElementById('iris');
  function clear(el) { el.style.transform = ''; el.style.opacity = ''; el.style.filter = ''; el.style.clipPath = ''; el.style.visibility = ''; el.style.background = ''; el.style.zIndex = ''; }
  function transition(t) {
    SC.forEach(s => { s.el.style.display = 'none'; clear(s.el); });
    if (HAS_MATCH) document.querySelectorAll('section.scene .m').forEach(m => { m.style.transform = ''; m.style.opacity = ''; });
    wipe.style.display = 'none'; irisRing.style.display = 'none';
    blurX.setAttribute('stdDeviation', '0 0'); blurY.setAttribute('stdDeviation', '0 0');
    const vis = [];
    SC.forEach((s, i) => {
      const nx = SC[i + 1], dIn = s.tin.d / 2, dOut = nx ? nx.tin.d / 2 : 0;
      const a = i === 0 ? s.start : s.start - dIn, b = nx ? s.end + dOut : s.end + 0.001;
      if (t >= a && t < b) vis.push(s);
    });
    for (const B of vis) {
      const i = SC.indexOf(B); if (i === 0) continue;
      const A = SC[i - 1], tr = B.tin, d = tr.d;
      if (!d) continue;
      const u = clamp((t - (B.start - d / 2)) / d);
      if (u <= 0 || u >= 1) continue;
      const e = E.io(u), mb = Math.sin(Math.PI * u);
      if (tr.type === 'push' || tr.type === 'whip') {
        const k = tr.type === 'whip' ? 1.0 : 0.62, dist = W * k;
        A.el.style.transform = `translateX(${-dist * e}px)`; B.el.style.transform = `translateX(${dist * (1 - e)}px)`;
        A.el.style.opacity = 1 - smooth(0.45, 0.9, u); B.el.style.opacity = smooth(0.1, 0.55, u);
        blurX.setAttribute('stdDeviation', `${(tr.type === 'whip' ? 60 : 32) * mb} 0`);
        A.el.style.filter = B.el.style.filter = 'url(#mbxf)';
      } else if (tr.type === 'rise') {
        const dist = H * 0.45;
        A.el.style.transform = `translateY(${-dist * e}px)`; B.el.style.transform = `translateY(${dist * (1 - e)}px)`;
        A.el.style.opacity = 1 - smooth(0.4, 0.85, u); B.el.style.opacity = smooth(0.15, 0.6, u);
        blurY.setAttribute('stdDeviation', `0 ${36 * mb}`);
        A.el.style.filter = B.el.style.filter = 'url(#mbyf)';
      } else if (tr.type === 'zoom') {
        A.el.style.transform = `scale(${1 + 1.6 * E.inE(u)})`; A.el.style.opacity = 1 - smooth(0.35, 0.75, u);
        A.el.style.filter = `blur(${(18 * smooth(0.2, 0.8, u)).toFixed(1)}px)`;
        B.el.style.transform = `scale(${0.55 + 0.45 * E.outQ(smooth(0.35, 1, u))})`; B.el.style.opacity = smooth(0.38, 0.72, u);
        B.el.style.filter = `blur(${(14 * (1 - smooth(0.4, 0.95, u))).toFixed(1)}px)`;
      } else if (tr.type === 'iris') {
        const f = tr.focus || [B.L.cx, B.L.cy], R = 1500 * E.ioE(u);
        B.el.style.clipPath = `circle(${R.toFixed(1)}px at ${f[0]}px ${f[1]}px)`;
        B.el.style.zIndex = 2; A.el.style.zIndex = 1;
        B.el.style.background = `radial-gradient(130% 85% at 50% 38%, var(--sbg1) 0%, var(--sbg0) 62%, ${TH.colors.bgDeep} 100%)`;   // opaque inside the circle
        A.el.style.transform = `scale(${1 + 0.12 * e})`;
        irisRing.style.display = 'block';
        Object.assign(irisRing.style, { left: f[0] - R + 'px', top: f[1] - R + 'px', width: 2 * R + 'px', height: 2 * R + 'px', opacity: 1 - smooth(0.7, 1, u) });
      } else if (tr.type === 'wipe') {
        wipe.style.display = 'block';
        const x = lerp(-W * 1.9, W * 1.9, E.io(u));
        wipe.style.transform = `translateX(${x}px) skewX(-14deg)`;
        if (u < 0.5) B.el.style.opacity = 0; else A.el.style.opacity = 0;      // (visibility would not hide children that set their own)
        A.el.style.transform = `translateX(${-90 * e}px)`; B.el.style.transform = `translateX(${90 * (1 - e)}px)`;
      } else if (tr.type === 'match') {
        A.el.style.opacity = 1 - smooth(0.0, 0.55, u); B.el.style.opacity = 1;
        B.el.querySelectorAll('.pt:not([data-match]) > .m').forEach(m => { m.style.opacity = smooth(0.35, 0.9, u); });
        for (const mm of B.matches || []) {
          const k = E.io(u);
          mm.el.style.transform = `translate(${mm.dx * (1 - k)}px,${mm.dy * (1 - k)}px) scale(${lerp(mm.s, 1, k)})`;
          if (mm.src) mm.src.style.opacity = 0;
        }
      } else if (tr.type === 'fade') {                                    // plain cross-fade: text stays sharp
        A.el.style.opacity = 1 - e; B.el.style.opacity = e;
      } else if (tr.type === 'blur') {
        A.el.style.opacity = 1 - e; A.el.style.filter = `blur(${(20 * e).toFixed(1)}px)`;
        B.el.style.opacity = e; B.el.style.filter = `blur(${(20 * (1 - e)).toFixed(1)}px)`;
      }
    }
    vis.forEach(s => { s.el.style.display = 'block'; });
    return vis;
  }

  // ---------- global layers ----------
  const world = document.getElementById('world'), bg = document.getElementById('bg'), fxc = document.getElementById('fx');
  const fctx = fxc.getContext('2d');
  function background(t, vis, cam) {
    // the background follows the dominant scene's palette; crossfades during transitions
    const s = vis[vis.length - 1] || SC[0];
    const b0 = getComputedStyle(s.el).getPropertyValue('--sbg0'), b1 = getComputedStyle(s.el).getPropertyValue('--sbg1');
    const A = vis.length > 1 ? vis[0] : null;
    const L1 = document.getElementById('bgA'), L2 = document.getElementById('bgB');
    L2.style.background = `radial-gradient(130% 85% at 50% 38%, ${b1} 0%, ${b0} 62%, ${TH.colors.bgDeep} 100%)`;
    if (A) {
      const a0 = getComputedStyle(A.el).getPropertyValue('--sbg0'), a1 = getComputedStyle(A.el).getPropertyValue('--sbg1');
      L1.style.background = `radial-gradient(130% 85% at 50% 38%, ${a1} 0%, ${a0} 62%, ${TH.colors.bgDeep} 100%)`;
      const B = vis[vis.length - 1], u = clamp((t - (B.start - B.tin.d / 2)) / Math.max(0.01, B.tin.d));
      L2.style.opacity = B.tin.d ? smooth(0.2, 0.8, u) : 1;
    } else L2.style.opacity = 1;
    // light sweep: a broad soft band crossing the frame slowly
    const sw = document.getElementById('sweep');
    const ph = (t * 0.07) % 1;
    sw.style.transform = `translate(${lerp(-900, 900, ph)}px, ${lerp(500, -500, ph)}px) rotate(-30deg)`;
    sw.style.opacity = 0.55 * Math.sin(Math.PI * ph);
    document.querySelectorAll('#bg .orb').forEach((o, i) => {
      const os = TH.particles?.speed ?? 1;
      const px = [0.2, 0.8, 0.45][i] * W + 140 * Math.sin(t * (0.21 + i * 0.07) * os + i * 2) - cam.x * 0.25;
      const py = [0.18, 0.5, 0.85][i] * H + 120 * Math.cos(t * (0.17 + i * 0.05) * os + i) - cam.y * 0.25;
      o.style.transform = `translate(${px.toFixed(1)}px,${py.toFixed(1)}px)`;
    });
    const grid = document.getElementById('grid');
    grid.style.transform = `translate(${(-cam.x * 0.35).toFixed(1)}px, ${((t * 12) % 90 - cam.y * 0.35).toFixed(1)}px) scale(${1 + (cam.z - 1) * 0.4})`;
  }

  // ---------- seek: the whole frame from t ----------
  function seek(t) {
    const vis = transition(t);
    const cam = camera(t);
    world.style.transform = `translate(${cam.x.toFixed(2)}px,${cam.y.toFixed(2)}px) rotate(${cam.r.toFixed(3)}deg) scale(${cam.z.toFixed(4)})`;
    background(t, vis, cam);
    for (const s of vis) s.update(t);
    idle(t);
    if (TITLE.el) {
      const ls = TITLE.el.querySelectorAll('.tl');
      ls.forEach((l, i) => {
        ktUpdate(l.firstChild, t, TITLE.wt[i], { lead: 0, stagger: 0.018 });
        const out = prog(t, TITLE.to - 0.1 + 0.06 * i, TITLE.to + 0.25 + 0.06 * i, 'in');
        l.style.transform = `translateY(${(-80 * out).toFixed(1)}px)`; l.style.opacity = 1 - out; l.style.filter = out > 0.01 ? `blur(${(10 * out).toFixed(1)}px)` : '';
        l.style.visibility = t < TITLE.from - 0.05 || out >= 1 ? 'hidden' : 'visible';
      });
    }
    drawParticles(fctx, t, cam);
    if (CFG.alphaIn || CFG.alphaOut) alphaEdges(t);
  }

  // hybrid clips: transparent edges so the face video shows through (iris in from the face, zoom/blur out)
  function alphaEdges(t) {
    const root = document.getElementById('frame');
    root.style.clipPath = ''; root.style.opacity = 1; root.style.transform = ''; root.style.filter = '';
    if (CFG.alphaIn) {
      const a = t - CFG.t0, d = (TH.motion && TH.motion.edgeIn) || 0.42;
      if (a < d) {
        const f = CFG.alphaIn.focus || [W / 2, H * 0.32], R = 1600 * E.ioE(clamp(a / d));
        root.style.clipPath = `circle(${R.toFixed(1)}px at ${f[0]}px ${f[1]}px)`;
      }
    }
    if (CFG.alphaOut) {
      const a = CFG.t1 - t, d = (TH.motion && TH.motion.edgeOut) || 0.36;
      if (a < d) {
        const u = 1 - clamp(a / d);
        root.style.opacity = 1 - E.in(u); root.style.transform = `scale(${1 + 0.35 * E.in(u)})`;
        root.style.filter = `blur(${(16 * u).toFixed(1)}px)`;
      }
    }
  }

  // match moves: measure the paired elements at the transition's edges (pure seek makes this exact)
  let HAS_MATCH = false;
  function measureMatches() {
    HAS_MATCH = SC.some((B, i) => i && B.tin.type === 'match');
    SC.forEach((B, i) => {
      if (!i || B.tin.type !== 'match') return;
      const A = SC[i - 1], d = B.tin.d;
      B.matches = [];
      B.el.querySelectorAll('[data-match]').forEach(pt => {
        const key = pt.dataset.match, src = A.el.querySelector(`[data-match="${key}"]`);
        if (!src) return;
        seek(B.start - d / 2 + 0.001); A.el.style.display = 'block';
        const ra = src.querySelector('.a').getBoundingClientRect();
        seek(B.start + d / 2 - 0.001); B.el.style.display = 'block';
        const rb = pt.querySelector('.a').getBoundingClientRect();
        const z = camera(B.start).z;
        B.matches.push({ el: pt.querySelector('.m'), src: src.querySelector('.m'),
          dx: ((ra.x + ra.width / 2) - (rb.x + rb.width / 2)) / z, dy: ((ra.y + ra.height / 2) - (rb.y + rb.height / 2)) / z,
          s: Math.max(0.2, Math.min(4, (ra.width / Math.max(1, rb.width)))) });
      });
    });
  }

  // QC report: boxes of visible content elements (not background/particles), in frame pixels
  function report(t) {
    seek(t);
    const out = [];
    document.querySelectorAll('section.scene .a:not([data-c="0"]), #title .tl').forEach(a => {
      if (a.closest('section') && a.closest('section').style.display === 'none') return;
      const cs = getComputedStyle(a); if (cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) return;
      const r = a.getBoundingClientRect(); if (r.width < 4 || r.height < 4) return;
      out.push([Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)]);
    });
    return out;
  }

  // every round element must stay round: bounding box width/height within 2 % on every frame (render.mjs logs it)
  function circleCheck() {
    let worst = 0, what = '';
    document.querySelectorAll('section.scene .round, section.scene .badge, section.scene .disc, section.scene .ring, section.scene .avatar, section.scene svg circle').forEach(el => {
      const sec = el.closest('section'); if (!sec || sec.style.display === 'none') return;
      if (getComputedStyle(el).visibility === 'hidden') return;
      if (el.tagName === 'circle' && parseFloat(el.getAttribute('r')) < 12) return;
      const r = el.getBoundingClientRect(); if (r.width < 10 || r.height < 10) return;
      const dev = Math.abs(r.width / r.height - 1);
      if (dev > worst) { worst = dev; what = `${sec.dataset.type}: ${el.tagName.toLowerCase()}.${(el.getAttribute('class') || '').trim().replace(/\s+/g, '.')} ${Math.round(r.width)}x${Math.round(r.height)}`; }
    });
    return [+worst.toFixed(4), what];
  }

  // ---------- boot ----------
  // sound-effect cues (tools/sfx.py): a whoosh on every transition, pop/tick on emphasis punches; times relative to t0
  function events() {
    const ev = [];
    SC.forEach((s, i) => { if (!i) return; const tr = s.tin; if (tr.type === 'cut') ev.push([s.start, 'pop']); else if (tr.type !== 'blur' && tr.type !== 'fade') ev.push([s.start - tr.d / 2, 'whoosh']); });
    PUNCH.forEach((p, i) => ev.push([p, i % 2 ? 'tick' : 'pop']));          // alternate kinds; sfx.py also varies the recipe + thins
    (CFG.board.cues || []).forEach(c => ev.push([c[0], c[1]]));             // explicit cues (tutorials: clicks), no camera punch
    return ev.filter(e => e[0] >= CFG.t0 && e[0] < CFG.t1).map(e => [+(e[0] - CFG.t0).toFixed(3), e[1]]).sort((x, y) => x[0] - y[0]);
  }
  window.RM = { def, seek, report, events, circleCheck, T, times, E, K, tw, prog, icon, kt, ktUpdate, CFG, get scenes() { return SC.map(s => ({ type: s.spec.type, start: s.start, end: s.end, tin: s.tin.type })); } };
  window.RM_BOOT = async function () {
    initParticles();
    const F = TH.fonts, loads = [];                         // load the theme fonts before any text is measured
    for (const [fam, f] of Object.entries(F.files)) for (const w of f.weights) loads.push(document.fonts.load(`${w} 80px "${fam}"`, 'AąĘżŁśćЯяЖж'));
    await Promise.all(loads).catch(() => {});
    build();
    await document.fonts.ready;
    measureMatches();
    seek(CFG.t0);
    window.__ready = true;
  };
})();
