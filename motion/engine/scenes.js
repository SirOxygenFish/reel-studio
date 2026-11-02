// ReelsMotion scene library. Each scene fills ~60-70 % of the safe box, enters on the words it illustrates and keeps
// moving (idle layers + the camera). Params come from the storyboard; times are word refs ("cena", "cena#2", "@14",
// "end:cena+0.1") or numbers (snapped to the nearest word onset). Missing times are spread over the scene.
// Scene list (see README.md for every parameter):
//   bigword  hero  stat  versus  steps  flow  timeline  quote  chart  character  chat  icongrid  beforeafter  level  cta  image
(function () {
  'use strict';
  const { def } = window.RM;
  const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const q = (root, s) => root.querySelector(s), qa = (root, s) => Array.from(root.querySelectorAll(s));

  // shrink a one-line (nowrap, shrink-wrapped) element's font until it is at most maxW wide (and maxH tall)
  function fitFont(el, maxW, maxH, max, min = 22) {
    let fs = max; el.style.fontSize = fs + 'px';
    const over = () => el.getBoundingClientRect().width > maxW + 0.5 || (maxH && el.getBoundingClientRect().height > maxH + 0.5);
    while (fs > min && over()) { fs -= 2; el.style.fontSize = fs + 'px'; }
    return fs;
  }
  // shrink wrapping text inside a box of fixed width (explicit width or a flex child) until nothing overflows:
  // no word wider than the box, at most maxH tall
  function fitBox(el, maxH, max, min = 22) {
    let fs = max; el.style.fontSize = fs + 'px'; el.style.overflowWrap = 'normal'; el.style.wordBreak = 'keep-all';
    const over = () => el.scrollWidth > el.clientWidth + 1 || (maxH && el.scrollHeight > maxH + 1);
    while (fs > min && over()) { fs -= 2; el.style.fontSize = fs + 'px'; }
    return fs;
  }
  // when each item appears: explicit "at", else its label's first word inside the scene, else spread evenly
  function itemTimes(api, items, key = 'label') {
    const { start, end } = api, n = items.length;
    return items.map((it, i) => {
      if (it.at !== undefined) return api.T(it.at);
      const w = String(it[key] || '').split(/\s+/)[0];
      if (w) { try { const t = api.T(w); if (t >= start - 0.2 && t < end) return t; } catch (e) {} }
      return start + 0.25 + i * Math.max(0.35, (end - start - 0.7) / Math.max(1, n));
    });
  }
  const anyIcon = (api, ref, size, color) => (ref ? api.icon(ref, size, color) : '');
  const num = n => `<span style="font-size:${String(n).length > 2 ? 0.32 : String(n).length > 1 ? 0.4 : 0.52}em">${n}</span>`;   // digits never widen a badge

  // ===================================================================== bigword: kinetic typography
  // {lines:["JEDNO","PYTANIE"], hl:["pytanie"], mode:"pop|rise|slam", color:"lemon|white", sub, icon, shape:"burst|disc|none", at}
  def('bigword', (api, root) => {
    const { p, L } = api, k = L.k, lines = p.lines || [p.text];
    const shape = p.shape ?? 'burst';
    root.innerHTML =
      (shape !== 'none' ? api.at(L.cx, L.cy, shape === 'burst'
        ? `<svg class="burst" viewBox="-500 -500 1000 1000" style="width:${L.w * 1.25}px;opacity:.9">${Array.from({ length: 18 }, (_, i) =>
            `<path d="M0 0 L${(Math.cos(i / 18 * 6.283 - 0.08) * 520).toFixed(0)} ${(Math.sin(i / 18 * 6.283 - 0.08) * 520).toFixed(0)} L${(Math.cos(i / 18 * 6.283 + 0.08) * 520).toFixed(0)} ${(Math.sin(i / 18 * 6.283 + 0.08) * 520).toFixed(0)}Z" fill="var(--c1)" opacity="${i % 2 ? 0.22 : 0.4}"/>`).join('')}</svg>`
        : `<div class="disc" style="width:${L.w * 0.92}px;height:${L.w * 0.92}px"></div>`, { idle: 'spin', amp: 0.4, cls: 'bw-shape', content: shape !== 'burst' }) : '') +
      (p.icon ? api.at(L.cx, L.y(0.13), anyIcon(api, p.icon, 190 * k, 'var(--acc)'), { idle: 'float sway', cls: 'bw-ic' }) : '') +
      `<div class="bw-lines">${lines.map((ln, i) => api.at(L.cx, 0, api.kt(ln, { cls: (p.color === 'white' ? '' : 'lemon') + ' bw-t', hl: p.hl, mode: p.mode || 'pop' }), { idle: 'float', amp: 0.6, cls: 'bw-l bw-l' + i })).join('')}</div>` +
      (p.sub ? api.at(L.cx, 0, `<div class="label bw-sub" style="font-size:${46 * k}px">${esc(p.sub)}</div>`, { cls: 'bw-s' }) : '');
    // size: the longest line fills ~94 % of the width; the block fits ~70 % of the height
    const ls = qa(root, '.bw-t');
    ls.forEach(el => { el.style.fontFamily = 'var(--f-display)'; el.style.fontWeight = 'var(--w-display)'; el.style.whiteSpace = 'nowrap'; el.style.textTransform = p.upper === false ? 'none' : 'uppercase'; });
    const fs = Math.min(...ls.map(el => fitFont(el, L.w * 0.94, 0, Math.min(p.max || 300, 300) * k)));
    ls.forEach(el => { el.style.fontSize = fs + 'px'; });
    const lh = fs * 1.02, blockH = lh * lines.length + (p.sub ? 90 * k : 0);
    const top = L.cy - blockH / 2 + (p.icon ? 80 * k : 0);
    qa(root, '.bw-l').forEach((pt, i) => { pt.style.top = (top + lh * (i + 0.5)) + 'px'; });
    if (p.sub) q(root, '.bw-s').style.top = (top + lh * lines.length + 50 * k) + 'px';
    const t0 = p.at !== undefined ? api.T(p.at) : api.start + 0.12;
    const allText = lines.join(' ');
    const wt = p.sync === false ? allText.split(/\s+/).map((_, i) => t0 + i * 0.12) : api.times(allText, t0, api.end);
    let wi = 0; const per = lines.map(ln => { const n = ln.split(/\s+/).filter(Boolean).length; const r = wt.slice(wi, wi + n); wi += n; return r; });
    return t => {
      ls.forEach((el, i) => api.ktUpdate(el, t, per[i]));
      api.tw(q(root, '.bw-shape .a'), t, api.K.pop(api.start, 0.6, { o: 0, s: 0.4 }));
      if (p.icon) api.tw(q(root, '.bw-ic .a'), t, api.K.spring(t0 - 0.05));
      if (p.sub) api.tw(q(root, '.bw-s .a'), t, api.K.rise(wt[wt.length - 1] + 0.2));
    };
  });

  // ===================================================================== hero: one big object on a disc + tilted tag
  // {icon:"noto:money-bag" | peep:{...}, label:"NISKA CENA", labelAt, sub, badges:[{icon, at, angle}], shake:[refs], at}
  def('hero', (api, root) => {
    const { p, L } = api, k = L.k;
    const D = Math.min(L.w * 0.88, L.h * 0.66), cy = L.y0 + D / 2 + 10 * k;
    const heroSize = D * (p.scale || 0.62);
    const inner = p.peep ? api.peep(Object.assign({ size: D * 0.9 }, p.peep)) : anyIcon(api, p.icon, heroSize, p.color || 'var(--hero-ic)');
    root.innerHTML =
      api.at(L.cx, cy, `<div class="disc" style="width:${D}px;height:${D}px"></div>`, { cls: 'h-disc', idle: 'breathe', amp: 0.6 }) +
      api.at(L.cx, cy, `<div class="ring" style="width:${D * 1.12}px;height:${D * 1.12}px"></div>`, { cls: 'h-ring', idle: 'spin', amp: 0.5, content: false }) +
      api.at(L.cx, cy + (p.peep ? D * 0.06 : 0), inner, { cls: 'h-hero', idle: 'float wobble' }) +
      (p.badges || []).map((b, i) => {
        const a = (b.angle ?? [-40, 35, 145, 215][i % 4]) * Math.PI / 180, r = D * 0.55;
        return api.at(L.cx + Math.cos(a) * r, cy + Math.sin(a) * r, `<div class="badge ${b.kind || 'acc'}" style="font-size:${150 * k}px">${anyIcon(api, b.icon, 92 * k)}</div>`, { cls: 'h-b', idle: 'float sway' });
      }).join('') +
      (p.label ? api.at(L.cx, cy + D * 0.5 + 40 * k, `<div class="tag ${p.tagKind || ''}" style="font-size:${110 * k}px">${esc(p.label)}</div>`, { cls: 'h-tag', idle: 'sway', amp: 0.5 }) : '') +
      (p.sub ? api.at(L.cx, cy + D * 0.5 + 160 * k, `<div class="label" style="font-size:${48 * k}px;color:var(--text)">${esc(p.sub)}</div>`, { cls: 'h-sub' }) : '');
    const tag = q(root, '.h-tag .tag'); if (tag) fitFont(tag, L.w * 0.96, 0, 110 * k);
    const t0 = p.at !== undefined ? api.T(p.at) : api.start + 0.1, tl = p.labelAt !== undefined ? api.T(p.labelAt) : t0 + 0.35;
    const bt = itemTimes(api, p.badges || [], 'x');
    const shakes = (p.shake || []).map(r => api.T(r));
    return t => {
      api.tw(q(root, '.h-disc .a'), t, api.K.pop(t0 - 0.1, 0.55, { o: 0, s: 0.3 }));
      api.tw(q(root, '.h-ring .a'), t, api.K.pop(t0, 0.6, { o: 0, s: 0.6 }));
      const hk = api.K.spring(t0, 0.7, { o: 0, s: 0.2, r: -18, y: 60 });
      for (const s of shakes) hk.push([s, {}], [s + 0.08, { s: 1.14, r: -6 }, 'out'], [s + 0.2, { r: 6 }, 'io'], [s + 0.32, { r: -3 }, 'io'], [s + 0.55, { s: 1, r: 0 }, 'back']);
      api.tw(q(root, '.h-hero .a'), t, hk);
      qa(root, '.h-b .a').forEach((b, i) => api.tw(b, t, api.K.pop(bt[i], 0.4, { o: 0, s: 0 })));
      api.tw(q(root, '.h-tag .a'), t, [[tl, { o: 0, s: 0.3, r: -14, y: 30 }], [tl + 0.1, { o: 1 }, 'lin'], [tl + 0.42, { s: 1, r: -4, y: 0 }, 'back']]);
      api.tw(q(root, '.h-sub .a'), t, api.K.rise(tl + 0.25));
      if (p.peep) api.peepUpdate(q(root, '.h-hero'), t, p.peep, p.talk || []);
    };
  });

  // ===================================================================== stat: counter + progress ring
  // {value:73000, from:0, decimals:0, prefix:"", suffix:"%", label:"OSÓB", icon, at, dur:1.2, ring:0.73, sub}
  def('stat', (api, root) => {
    const { p, L } = api, k = L.k, D = Math.min(L.w * 0.86, L.h * 0.64), cy = L.y0 + D / 2 + 30 * k, C = Math.PI * 2 * 0.44 * D;
    root.innerHTML =
      api.at(L.cx, cy, `<svg class="round" viewBox="0 0 ${D} ${D}" style="width:${D}px;height:${D}px;overflow:visible">
        <circle cx="${D / 2}" cy="${D / 2}" r="${D * 0.44}" fill="var(--surface)" stroke="var(--line)" stroke-width="${26 * k}"/>
        <circle class="st-arc" cx="${D / 2}" cy="${D / 2}" r="${D * 0.44}" fill="none" stroke="var(--acc)" stroke-width="${30 * k}" stroke-linecap="round"
          transform="rotate(-90 ${D / 2} ${D / 2})" stroke-dasharray="${C}" stroke-dashoffset="${C}"/></svg>`, { cls: 'st-ring', idle: 'breathe', amp: 0.4, content: true }) +
      (p.icon ? api.at(L.cx, cy - D * 0.25, anyIcon(api, p.icon, 150 * k, 'var(--acc)'), { cls: 'st-ic', idle: 'float sway' }) : '') +
      api.at(L.cx, cy + (p.icon ? D * 0.05 : 0), `<div class="big st-num" style="color:var(--hl)">0</div>`, { cls: 'st-n', idle: 'pulse', amp: 0.3 }) +
      (p.label ? api.at(L.cx, cy + D * 0.5 + 30 * k, `<div class="tag" style="font-size:${92 * k}px">${esc(p.label)}</div>`, { cls: 'st-tag', idle: 'sway', amp: 0.5 }) : '') +
      (p.sub ? api.at(L.cx, cy + D * 0.5 + 150 * k, `<div class="label" style="font-size:${46 * k}px;color:var(--text)">${esc(p.sub)}</div>`, { cls: 'st-sub' }) : '');
    const fmt = v => (p.prefix || '') + (p.decimals ? v.toFixed(p.decimals).replace('.', p.comma === false ? '.' : ',') : Math.round(v).toLocaleString('pl-PL').replace(/ /g, ' ')) + (p.suffix || '');
    const num = q(root, '.st-num');
    num.textContent = fmt(p.value); fitFont(num, D * 0.74, 0, 260 * k);
    const stTag = q(root, '.st-tag .tag'); if (stTag) fitFont(stTag, L.w * 0.96, 0, 92 * k);
    const t0 = p.at !== undefined ? api.T(p.at) : api.start + 0.15, dur = p.dur || 1.1;
    const tl = p.labelAt !== undefined ? api.T(p.labelAt) : t0 + dur * 0.6;
    let burst = false;
    return t => {
      const u = api.prog(t, t0, t0 + dur, 'outQ');
      num.textContent = fmt((p.from || 0) + (p.value - (p.from || 0)) * u);
      q(root, '.st-arc').setAttribute('stroke-dashoffset', (C * (1 - (p.ring ?? 1) * api.prog(t, t0, t0 + dur * 1.1, 'io'))).toFixed(1));
      api.tw(q(root, '.st-ring .a'), t, api.K.pop(api.start, 0.5, { o: 0, s: 0.5 }));
      api.tw(q(root, '.st-n .a'), t, [[t0 - 0.05, { o: 0, s: 0.6 }], [t0 + 0.2, { o: 1, s: 1.05 }, 'out'], [t0 + dur, { s: 1 }, 'io'], [t0 + dur + 0.08, { s: 1.12 }, 'out'], [t0 + dur + 0.4, { s: 1 }, 'back']]);
      if (p.icon) api.tw(q(root, '.st-ic .a'), t, api.K.drop(api.start + 0.15));
      api.tw(q(root, '.st-tag .a'), t, [[tl, { o: 0, s: 0.4, r: 10 }], [tl + 0.4, { o: 1, s: 1, r: -3 }, 'back']]);
      api.tw(q(root, '.st-sub .a'), t, api.K.rise(tl + 0.2));
      if (!burst && t >= t0 + dur) { api.burst(t0 + dur, L.cx, cy, 22); burst = true; }
    };
  });

  // ===================================================================== versus: X vs Y (cards or a balance)
  // {left:{label, icon, at, sub}, right:{...}, vs:"VS", pick:"left|right", pickAt, style:"cards|scale"}
  def('versus', (api, root) => {
    const { p, L } = api, k = L.k;
    if (p.style === 'scale') return scale(api, root);
    const cw = L.w * 0.47, ch = Math.min(L.h * 0.74, 760 * k), cy = L.cy + 10 * k;
    const side = (s, i) => `<div class="card ${i ? 'acc' : ''} vs-card" style="width:${cw}px;height:${ch}px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${26 * k}px;padding:${30 * k}px">
        ${anyIcon(api, s.icon, cw * 0.62, i ? 'var(--on-acc)' : 'var(--c1)')}
        <div class="big vs-lab" style="text-align:center;white-space:normal;width:${cw * 0.76}px">${esc(s.label)}</div>
        ${s.sub ? `<div style="font-family:var(--f-head);font-weight:700;font-size:${40 * k}px;opacity:.75;text-align:center">${esc(s.sub)}</div>` : ''}</div>`;
    root.innerHTML =
      [0.25, 0.75].map(u => api.at(L.x(u), cy, `<div class="ghost" style="width:${cw}px;height:${ch}px;border-radius:var(--r-l)"></div>`, { cls: 'vs-g' })).join('') +
      api.at(L.x(0.25), cy, side(p.left, 0), { cls: 'vs-L', idle: 'float', amp: 0.7 }) +
      api.at(L.x(0.75), cy, side(p.right, 1), { cls: 'vs-R', idle: 'float', amp: 0.7 }) +
      api.at(L.cx, cy, `<div class="badge c2" style="font-size:${150 * k}px;font-family:var(--f-display);font-weight:900"><span style="font-size:.36em">${esc(p.vs || 'VS')}</span></div>`, { cls: 'vs-vs', idle: 'pulse' }) +
      (p.pick ? api.at(p.pick === 'left' ? L.x(0.25) : L.x(0.75), cy - ch / 2, `<div class="badge good" style="font-size:${130 * k}px">${api.icon('ph-bold:check', 80 * k)}</div>`, { cls: 'vs-ok' }) +
                api.at(p.pick === 'left' ? L.x(0.75) : L.x(0.25), cy - ch / 2, `<div class="badge bad" style="font-size:${130 * k}px">${api.icon('ph-bold:x', 80 * k)}</div>`, { cls: 'vs-no' }) : '') +
      (p.marks ? ['left', 'right'].filter(sd => p.marks[sd]).map(sd => api.at(sd === 'left' ? L.x(0.25) : L.x(0.75), cy - ch / 2,
        `<div class="badge ${p.marks[sd] === 'x' ? 'bad' : 'good'}" style="font-size:${130 * k}px">${api.icon(p.marks[sd] === 'x' ? 'ph-bold:x' : 'ph-bold:check', 80 * k)}</div>`, { cls: 'vs-mk vs-mk-' + sd })).join('') : '');
    const vsf = Math.min(...qa(root, '.vs-lab').map(el => fitBox(el, ch * 0.3, 92 * k))); qa(root, '.vs-lab').forEach(el => { el.style.fontSize = vsf + 'px'; });
    const ta = p.left.at !== undefined ? api.T(p.left.at) : api.start + 0.1, tb = p.right.at !== undefined ? api.T(p.right.at) : ta + 0.5;
    const tp = p.pickAt !== undefined ? api.T(p.pickAt) : null, tm = p.marks ? (p.marks.at !== undefined ? api.T(p.marks.at) : tb + 0.4) : null;
    return t => {
      const winL = p.pick === 'left';
      const lk = api.K.antic(ta, -260, 0, 0.5), rk = api.K.antic(tb, 260, 0, 0.5);
      if (tp !== null) {
        (winL ? lk : rk).push([tp, {}], [tp + 0.35, { s: 1.07 }, 'back']);
        (winL ? rk : lk).push([tp, {}], [tp + 0.35, { s: 0.9, o: 0.5, r: winL ? 4 : -4, y: 20 }, 'out']);
      }
      if (tm !== null) {                                   // a crossed side steps back
        if (p.marks.left === 'x') lk.push([tm, {}], [tm + 0.35, { s: 0.92, o: 0.6, r: -3, y: 16 }, 'out']);
        if (p.marks.right === 'x') rk.push([tm, {}], [tm + 0.35, { s: 0.92, o: 0.6, r: 3, y: 16 }, 'out']);
        qa(root, '.vs-mk .a').forEach(e => api.tw(e, t, api.K.pop(tm + 0.1, 0.4, { o: 0, s: 0 })));
      }
      api.tw(q(root, '.vs-L .a'), t, lk); api.tw(q(root, '.vs-R .a'), t, rk);
      qa(root, '.vs-g .a').forEach((g, i) => { const tc = i ? tb : ta;                // placeholders until each side arrives
        api.tw(g, t, [[api.start, { o: 0, s: 0.9 }], [api.start + 0.35, { o: 1, s: 1 }, 'out'], [tc, {}], [tc + 0.2, { o: 0 }, 'lin']]); });
      api.tw(q(root, '.vs-vs .a'), t, api.K.slam(Math.max(ta, tb) - 0.05));
      if (tp !== null) { api.tw(q(root, '.vs-ok .a'), t, api.K.pop(tp + 0.15, 0.4, { o: 0, s: 0 })); api.tw(q(root, '.vs-no .a'), t, api.K.pop(tp + 0.25, 0.4, { o: 0, s: 0 })); }
    };
  });

  function scale(api, root) {                    // versus style "scale": a balance that tips
    const { p, L } = api, k = L.k, PIV = L.y(0.3), ARM = L.w * 0.29, HANG = 310 * k;
    const chip = (s, kind) => `<div class="tag ${kind}" style="font-size:${56 * k}px">${esc(s)}</div>`;
    const rightItems = Array.isArray(p.right.label) ? p.right.label : [p.right.label];
    root.innerHTML =
      api.at(L.cx, L.y(0.56), `<div style="width:${44 * k}px;height:${L.h * 0.5}px;border-radius:${22 * k}px;background:linear-gradient(var(--struct),var(--c1))"></div>`, { cls: 'sc-post' }) +
      api.at(L.cx, L.y(0.8), `<div style="width:${360 * k}px;height:${40 * k}px;border-radius:${20 * k}px;background:var(--c1)"></div>`, { cls: 'sc-base' }) +
      `<div class="str strL" style="position:absolute;width:5px;height:${HANG}px;background:var(--struct);opacity:.8"></div><div class="str strR" style="position:absolute;width:5px;height:${HANG}px;background:var(--struct);opacity:.8"></div>` +
      `<div class="pt beam" style="left:${L.cx}px;top:${PIV}px"><div style="width:${ARM * 2 + 60 * k}px;height:${28 * k}px;border-radius:${14 * k}px;background:var(--struct);flex:none"></div></div>` +
      api.at(L.cx, PIV, `<div class="round" style="width:${68 * k}px;height:${68 * k}px;background:var(--acc)"></div>`, { cls: 'sc-piv' }) +
      `<div class="pt panL" style="align-items:flex-end"><div class="a" style="flex:none;display:flex;flex-direction:column;align-items:center">${p.left.icon ? anyIcon(api, p.left.icon, 150 * k, 'var(--acc)') : ''}<div class="iL">${chip(p.left.label, '')}</div><div style="width:${330 * k}px;height:${24 * k}px;border-radius:0 0 ${170 * k}px ${170 * k}px;background:var(--c1l);margin-top:${8 * k}px"></div></div></div>` +
      `<div class="pt panR" style="align-items:flex-end"><div class="a" style="flex:none;display:flex;flex-direction:column;align-items:center;gap:${10 * k}px">${rightItems.map(s => `<div class="iR">${chip(s, 'paper')}</div>`).join('')}<div style="width:${330 * k}px;height:${24 * k}px;border-radius:0 0 ${170 * k}px ${170 * k}px;background:var(--c1l)"></div></div></div>`;
    const ta = p.left.at !== undefined ? api.T(p.left.at) : api.start + 0.1, tb = p.right.at !== undefined ? api.T(p.right.at) : ta + 0.8;
    const tp = p.pickAt !== undefined ? api.T(p.pickAt) : tb + 0.4;
    return t => {
      const sgn = p.pick === 'left' ? -1 : 1;
      const ang = -12 * api.prog(t, ta + 0.15, ta + 0.7, 'back') + (12 + 12 * sgn) * api.prog(t, tp - 0.05, tp + 0.75, 'elastic');
      q(root, '.beam > div').style.transform = `rotate(${ang}deg)`;
      const r = ang * Math.PI / 180;
      [['L', -1], ['R', 1]].forEach(([s, sg]) => {
        const x = L.cx + sg * ARM * Math.cos(r), y = PIV + sg * ARM * Math.sin(r);
        q(root, '.pan' + s).style.left = x + 'px'; q(root, '.pan' + s).style.top = (y + HANG) + 'px';
        q(root, '.str' + s).style.left = (x - 2) + 'px'; q(root, '.str' + s).style.top = y + 'px';
      });
      api.tw(q(root, '.iL'), t, api.K.drop(ta, 0.45, -260 * k));
      qa(root, '.iR').forEach((e, i) => api.tw(e, t, api.K.pop(tb + i * 0.14, 0.35, { o: 0, s: 0.3 })));
      api.tw(q(root, '.sc-post .a'), t, api.K.rise(api.start, 0.4, 200));
    };
  }

  // ===================================================================== steps: numbered list
  // {items:[{label, icon, at, sub}], title}
  def('steps', (api, root) => {
    const { p, L } = api, k = L.k, n = p.items.length, top0 = L.y0 + (p.title ? 110 * k : 0);
    const gap = 26 * k, rh = Math.min((n <= 2 ? 300 : 250) * k, (L.y1 - top0 - gap * (n - 1)) / n), rw = L.w * 0.97;
    const top = top0 + Math.max(0, (L.y1 - top0 - (n * rh + (n - 1) * gap) - (p.tag ? 90 * k : 0)) / 2);   // centred block
    root.innerHTML = (p.title ? api.at(L.cx, L.y0 + 40 * k, `<div class="label" style="font-size:${54 * k}px;color:var(--head2)">${esc(p.title)}</div>`, { cls: 'sp-title' }) : '') +
      p.items.map((it, i) => api.at(L.cx, top + rh / 2 + i * (rh + gap), `<div class="ghost" style="width:${rw}px;height:${rh}px;border-radius:${rh / 2}px;display:flex;align-items:center;padding-left:${18 * k}px"><div class="badge ghost" style="font-size:${Math.min(rh * 0.7, 180 * k)}px;font-family:var(--f-display);font-weight:900">${num(i + 1)}</div></div>`, { cls: 'sp-g' })).join('') +
      `<div class="sp-line" style="position:absolute;left:${L.x0 + rh * 0.5}px;top:${top + rh / 2}px;width:${8 * k}px;height:0;background:var(--acc);border-radius:4px;transform-origin:top"></div>` +
      p.items.map((it, i) => api.at(L.cx, top + rh / 2 + i * (rh + gap),
        `<div class="card sp-row" style="width:${rw}px;height:${rh}px;display:flex;align-items:center;gap:${30 * k}px;padding:0 ${34 * k}px 0 ${18 * k}px;border-radius:${rh / 2}px">
          <div class="badge acc sp-n" style="font-size:${Math.min(rh * 0.7, 180 * k)}px;font-family:var(--f-display);font-weight:900">${num(i + 1)}</div>
          ${it.icon ? anyIcon(api, it.icon, Math.min(rh * 0.55, 135 * k), 'var(--c1)') : ''}
          <div class="big sp-lab" style="flex:1;min-width:0;white-space:normal;line-height:1.02">${esc(it.label)}</div>
          <div class="badge ${it.mark === 'x' ? 'bad' : 'good'} sp-ok" style="font-size:${Math.min(rh * 0.42, 105 * k)}px">${api.icon(it.mark === 'x' ? 'ph-bold:x' : 'ph-bold:check', Math.min(rh * 0.28, 70 * k))}</div></div>`, { cls: 'sp-r', idle: 'float', amp: 0.35 })).join('');
    const spf = Math.min(...qa(root, '.sp-lab').map(el => fitBox(el, rh * 0.84, 96 * k))); qa(root, '.sp-lab').forEach(el => { el.style.fontSize = spf + 'px'; });
    if (p.tag) {
      root.insertAdjacentHTML('beforeend', api.at(L.x(0.72), top + (n - 1) * (rh + gap) + rh * 1.02, `<div class="tag" style="font-size:${62 * k}px">${esc(p.tag.text)}</div>`, { cls: 'sp-tag', idle: 'sway' }));
      const tg = q(root, '.sp-tag .tag'); fitFont(tg, L.w * 0.9, 0, 62 * k);
      const half = tg.getBoundingClientRect().width / 2 + 20 * k;                     // keep the tag (and its tilt) inside the box
      q(root, '.sp-tag').style.left = Math.min(L.x1 - half, Math.max(L.x0 + half, L.x(0.72))) + 'px';
    }
    const ts = itemTimes(api, p.items), tTag = p.tag ? api.T(p.tag.at) : 0;
    return t => {
      if (p.title) api.tw(q(root, '.sp-title .a'), t, api.K.rise(api.start));
      qa(root, '.sp-g').forEach((g, i) => api.tw(q(g, '.a'), t, [[api.start + 0.05 + i * 0.07, { o: 0, x: 60 }], [api.start + 0.4 + i * 0.07, { o: 1, x: 0 }, 'out'], [ts[i], {}], [ts[i] + 0.2, { o: 0 }, 'lin']]));
      const cur = ts.filter(x => t >= x).length - 1;
      qa(root, '.sp-r').forEach((r, i) => {
        const keys = api.K.antic(ts[i] - 0.05, (i % 2 ? 1 : -1) * 420, 0, 0.5);
        if (cur > i) keys.push([ts[i + 1], {}], [ts[i + 1] + 0.3, { s: 0.96, o: 0.82 }, 'out']);
        else if (i === cur) keys.push([ts[i] + 0.5, {}], [ts[i] + 0.7, { s: 1.03 }, 'io']);
        api.tw(q(r, '.a'), t, keys);
        api.tw(q(r, '.sp-ok'), t, p.items[i].mark === 'x' ? api.K.pop(ts[i] + 0.3, 0.35, { o: 0, s: 0 }) : i < cur ? api.K.pop(ts[i + 1], 0.35, { o: 0, s: 0 }) : [[0, { o: 0 }]]);
        q(r, '.sp-row').style.boxShadow = i === cur ? '0 0 0 8px var(--acc), var(--sh)' : '';
      });
      const hh = Math.max(0, (ts.length > 1 ? (rh + gap) * Math.min(n - 1, Math.max(0, cur) + api.prog(t, ts[Math.max(0, cur)] + 0.2, ts[Math.min(n - 1, Math.max(0, cur) + 1)], 'io') * (cur < n - 1 ? 1 : 0)) : 0));
      q(root, '.sp-line').style.height = (t >= ts[0] ? hh : 0) + 'px';
      if (p.tag) api.tw(q(root, '.sp-tag .a'), t, [[tTag, { o: 0, s: 0.3, r: 16 }], [tTag + 0.42, { o: 1, s: 1, r: -4 }, 'back']]);
    };
  });

  // ===================================================================== flow: process with drawn arrows
  // {nodes:[{label, icon, at}], layout:"zigzag|vertical"}
  def('flow', (api, root) => {
    const { p, L } = api, k = L.k, n = p.nodes.length, D = Math.min(400 * k, L.h * 0.92 / n);
    const pos = p.nodes.map((_, i) => [p.layout === 'vertical' ? L.cx : L.x(i % 2 ? 0.68 : 0.32), L.y0 + D * 0.55 + i * (L.h - D * 1.25) / Math.max(1, n - 1)]);
    const path = (a, b) => { const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, bend = (b[0] - a[0]) * 0.25 + 80 * k;
      return `M${a[0]} ${a[1] + D * 0.45} Q ${mx + bend} ${my} ${b[0]} ${b[1] - D * 0.48}`; };
    root.innerHTML = `<svg class="fl-svg" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible">
        <defs><marker id="fl-ah" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="var(--acc)"/></marker></defs>
        ${pos.slice(1).map((b, i) => `<path class="fl-gp" d="${path(pos[i], b)}" fill="none" stroke="var(--line)" stroke-width="${8 * k}" stroke-dasharray="2 ${22 * k}" stroke-linecap="round"/>`).join('')}
        ${pos.slice(1).map((b, i) => `<path class="fl-p" d="${path(pos[i], b)}" fill="none" stroke="var(--acc)" stroke-width="${14 * k}" stroke-linecap="round" marker-end="url(#fl-ah)"/>`).join('')}
        ${pos.slice(1).map((b, i) => `<circle class="fl-dot" r="${14 * k}" fill="var(--c2)"/>`).join('')}</svg>` +
      p.nodes.map((nd, i) => api.at(pos[i][0], pos[i][1], `<div class="round" style="width:${D}px;height:${D}px;border:${6 * k}px dashed var(--line);display:flex;align-items:center;justify-content:center">${anyIcon(api, nd.icon, D * 0.4, 'var(--line)')}</div>`, { cls: 'fl-g', idle: 'breathe', amp: 0.5 })).join('') +
      p.nodes.map((nd, i) => api.at(pos[i][0], pos[i][1], `<div style="display:flex;flex-direction:column;align-items:center;gap:${10 * k}px">
          <div class="disc" style="width:${D}px;height:${D}px;display:flex;align-items:center;justify-content:center">${anyIcon(api, nd.icon, D * 0.56, 'var(--on-disc)')}</div>
          <div class="tag ${i === n - 1 ? '' : 'paper'}" style="font-size:${62 * k}px;margin-top:-${36 * k}px">${esc(nd.label)}</div></div>`, { cls: 'fl-n', idle: 'float', amp: 0.6 })).join('');
    qa(root, '.fl-n .tag').forEach(el => fitFont(el, L.w * 0.6, 0, 62 * k));
    const ps = qa(root, '.fl-p'), dots = qa(root, '.fl-dot'), lens = ps.map(e => e.getTotalLength());
    const ts = itemTimes(api, p.nodes);
    return t => {
      qa(root, '.fl-n').forEach((nd, i) => api.tw(q(nd, '.a'), t, api.K.spring(ts[i], 0.6, { o: 0, s: 0.2, y: 40 })));
      qa(root, '.fl-g').forEach((g, i) => api.tw(q(g, '.a'), t, [[api.start + i * 0.08, { o: 0, s: 0.6 }], [api.start + 0.4 + i * 0.08, { o: 1, s: 1 }, 'back'], [ts[i], {}], [ts[i] + 0.25, { o: 0, s: 1.3 }, 'out']]));
      qa(root, '.fl-gp').forEach(e => { e.style.opacity = api.prog(t, api.start + 0.2, api.start + 0.6); });
      ps.forEach((e, i) => {
        const u = api.prog(t, ts[i] + 0.2, Math.max(ts[i] + 0.5, ts[i + 1] - 0.05), 'io');
        e.style.strokeDasharray = lens[i]; e.style.strokeDashoffset = lens[i] * (1 - u); e.style.opacity = u > 0 ? 1 : 0;
        const d = ((t - ts[i + 1]) * 0.7) % 1;
        if (t > ts[i + 1]) { const pt = e.getPointAtLength(lens[i] * d); dots[i].setAttribute('cx', pt.x); dots[i].setAttribute('cy', pt.y); dots[i].style.opacity = Math.sin(Math.PI * d); }
        else dots[i].style.opacity = 0;
      });
    };
  });

  // ===================================================================== timeline: vertical line, markers, playhead
  // {items:[{label, tag, at}], title}
  def('timeline', (api, root) => {
    const { p, L } = api, k = L.k, n = p.items.length, x = L.x(0.12), top = L.y0 + 40 * k, bot = L.y1 - 40 * k;
    const ys = p.items.map((_, i) => top + (bot - top) * (n === 1 ? 0.5 : i / (n - 1)));
    root.innerHTML = `<div class="tl-line" style="position:absolute;left:${x - 6 * k}px;top:${top}px;width:${12 * k}px;height:${bot - top}px;border-radius:${6 * k}px;background:var(--line);transform-origin:top"></div>
      <div class="tl-fill" style="position:absolute;left:${x - 6 * k}px;top:${top}px;width:${12 * k}px;height:0;border-radius:${6 * k}px;background:var(--acc)"></div>` +
      p.items.map((it, i) => api.at(x, ys[i], `<div class="badge ghost" style="font-size:${84 * k}px"></div>`, { cls: 'tl-gd' }) + api.at(x, ys[i], `<div class="badge acc" style="font-size:${84 * k}px"></div>`, { cls: 'tl-dot' }) +
        api.at(x + 60 * k + L.w * 0.4, ys[i], `<div class="card" style="width:${L.w * 0.8}px;padding:${26 * k}px ${36 * k}px">
          ${it.tag ? `<div class="label" style="font-size:${40 * k}px;color:var(--c1)">${esc(it.tag)}</div>` : ''}
          <div class="big tl-lab" style="white-space:normal">${esc(it.label)}</div></div>`, { cls: 'tl-c', idle: 'float', amp: 0.4 })).join('');
    qa(root, '.tl-lab').forEach(el => fitBox(el, (bot - top) / n * 0.6, 76 * k));
    const ts = itemTimes(api, p.items);
    return t => {
      q(root, '.tl-line').style.transform = `scaleY(${api.prog(api.start, api.start, api.start + 0.5)})`;
      q(root, '.tl-line').style.transform = `scaleY(${api.prog(t, api.start, api.start + 0.6, 'io')})`;
      const cur = ts.filter(x => t >= x).length - 1;
      const hy = cur < 0 ? 0 : ys[cur] - top + (cur < n - 1 ? (ys[cur + 1] - ys[cur]) * 0.15 * api.prog(t, ts[cur], ts[cur] + 0.6) : 0);
      q(root, '.tl-fill').style.height = hy + 'px';
      qa(root, '.tl-dot').forEach((d, i) => api.tw(q(d, '.a'), t, api.K.pop(ts[i], 0.35, { o: 0, s: 0 })));
      qa(root, '.tl-gd').forEach((d, i) => api.tw(q(d, '.a'), t, api.K.pop(api.start + 0.2 + i * 0.08, 0.35, { o: 0, s: 0 })));
      qa(root, '.tl-c').forEach((c, i) => api.tw(q(c, '.a'), t, api.K.slide(ts[i] + 0.05, 300)));
    };
  });

  // ===================================================================== quote: card with word-synced text
  // {text, hl:[...], by, at, mode}
  def('quote', (api, root) => {
    const { p, L } = api, k = L.k, cw = L.w * 0.97;
    root.innerHTML = api.at(L.cx, L.cy, `<div class="card qt-card" style="width:${cw}px;padding:${90 * k}px ${64 * k}px ${70 * k}px">
        <div class="big" style="position:absolute;left:${34 * k}px;top:-${70 * k}px;font-size:${300 * k}px;color:var(--acc);text-shadow:0 10px 0 rgba(0,0,0,.2)">“</div>
        <div class="qt-t" style="width:${cw - 128 * k}px;font-family:var(--f-display);font-weight:var(--w-display);line-height:1.08;text-align:left">${api.kt(p.text, { hl: p.hl, mode: p.mode || 'rise' })}</div>
        ${p.by ? `<div class="label" style="margin-top:${30 * k}px;font-size:${42 * k}px;color:var(--c1)">${esc(p.by)}</div>` : ''}</div>`, { cls: 'qt', idle: 'float', amp: 0.5 });
    const tx = q(root, '.qt-t');
    fitBox(tx, L.h * 0.74, 112 * k);
    const t0 = p.at !== undefined ? api.T(p.at) : api.start + 0.1;
    const wt = api.times(p.text, t0, api.end);
    return t => {
      api.tw(q(root, '.qt .a'), t, [[api.start, { o: 0, rx: 50, y: 120, s: 0.9 }], [api.start + 0.55, { o: 1, rx: 0, y: 0, s: 1, r: -1.5 }, 'back']]);
      api.ktUpdate(q(root, '.kt'), t, wt, { ghost: p.ghost !== false });
    };
  });

  // ===================================================================== chart: bars or line
  // {kind:"bars|line", data:[{label, v, at}], unit:"%", title}
  def('chart', (api, root) => {
    const { p, L } = api, k = L.k, n = p.data.length, max = p.max || Math.max(...p.data.map(d => d.v)) * 1.1;
    const cx0 = L.x0 + 40 * k, cx1 = L.x1 - 40 * k, cy1 = L.y1 - 120 * k, cy0 = L.y0 + (p.title ? 160 * k : 60 * k);
    const bw = (cx1 - cx0) / n * 0.62;
    const X = i => cx0 + (cx1 - cx0) * (i + 0.5) / n, Y = v => cy1 - (cy1 - cy0) * v / max;
    root.innerHTML = (p.title ? api.at(L.cx, L.y0 + 50 * k, `<div class="tag c1" style="font-size:${70 * k}px">${esc(p.title)}</div>`, { cls: 'ch-t' }) : '') +
      `<div style="position:absolute;left:${cx0}px;top:${cy1}px;width:${cx1 - cx0}px;height:${8 * k}px;background:var(--line);border-radius:4px"></div>` +
      (p.kind === 'line'
        ? `<svg style="position:absolute;inset:0;width:100%;height:100%;overflow:visible"><polyline class="ch-pl" fill="none" stroke="var(--acc)" stroke-width="${16 * k}" stroke-linejoin="round" stroke-linecap="round" points="${p.data.map((d, i) => X(i) + ',' + Y(d.v)).join(' ')}"/></svg>` +
          p.data.map((d, i) => api.at(X(i), Y(d.v), `<div class="badge acc" style="font-size:${50 * k}px"></div>`, { cls: 'ch-pt' })).join('')
        : p.data.map((d, i) => `<div class="ch-bar" style="position:absolute;left:${X(i) - bw / 2}px;width:${bw}px;top:${Y(d.v)}px;height:${cy1 - Y(d.v)}px;border-radius:${24 * k}px ${24 * k}px 0 0;background:${i === p.hi ? 'var(--acc)' : 'var(--bar)'};transform-origin:bottom"></div>`).join('')) +
      p.data.map((d, i) => api.at(X(i), Y(d.v) - 60 * k, `<div class="big ch-v" style="font-size:${70 * k}px">${esc(d.show ?? d.v)}${esc(p.unit || '')}</div>`, { cls: 'ch-val' })).join('') +
      p.data.map((d, i) => api.at(X(i), cy1 + 60 * k, `<div class="label" style="font-size:${40 * k}px;color:var(--text)">${esc(d.label)}</div>`, { cls: 'ch-lab' })).join('');
    const ts = itemTimes(api, p.data);
    const pl = q(root, '.ch-pl'), plen = pl ? pl.getTotalLength() : 0;
    return t => {
      if (p.title) api.tw(q(root, '.ch-t .a'), t, api.K.pop(api.start));
      qa(root, '.ch-bar').forEach((b, i) => { const u = api.prog(t, ts[i], ts[i] + 0.7, 'spring'); b.style.transform = `scaleY(${Math.max(0, u)})`; });
      if (pl) { const u = api.prog(t, ts[0], ts[n - 1] + 0.4, 'io'); pl.style.strokeDasharray = plen; pl.style.strokeDashoffset = plen * (1 - u); }
      qa(root, '.ch-pt').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.pop(ts[i] + 0.2, 0.35, { o: 0, s: 0 })));
      qa(root, '.ch-val').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.pop(ts[i] + 0.4)));
      qa(root, '.ch-lab').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.rise(ts[i])));
    };
  });

  // ===================================================================== character: Open Peeps bust + speech + props
  // {peep:{body, head, face, faces:{Smile:0, Fear:"word"}, beard}, bubble:{text, at, side}, bubbles:[...], props:[{icon, at, x, y, size}], away:[refs]}
  def('character', (api, root) => {
    const { p, L } = api, k = L.k, pw = Math.min(L.w * (p.width || 0.8), L.h * 0.7);
    const ph = pw * 1130.6 / 940.3, px = L.x(p.x ?? (p.bubble?.side === 'r' ? 0.38 : 0.6)), pyB = L.y1;
    const bubbles = p.bubbles || (p.bubble ? [p.bubble] : []);
    root.innerHTML =
      api.at(px, pyB - ph * 0.45, `<div class="disc" style="width:${pw * 1.06}px;height:${pw * 1.06}px"></div>`, { cls: 'cr-disc', idle: 'breathe', amp: 0.5 }) +
      api.at(px, pyB - ph / 2, api.peep(Object.assign({ size: pw }, p.peep)), { cls: 'cr-peep' }) +
      bubbles.map((b, i) => api.at(L.x(b.x ?? (b.side === 'r' ? 0.62 : 0.4)), L.y0 + (b.y ?? (0.12 + i * 0.2)) * L.h,
        `<div class="bubble ${b.side === 'r' ? '' : 'r'} ${b.kind || ''}" style="font-size:${(b.size || 70) * k}px;max-width:${L.w * 0.82}px">${api.kt(b.text, { mode: 'pop', hl: b.hl })}</div>`, { cls: 'cr-b', idle: 'float', amp: 0.5 })).join('') +
      (p.props || []).map(pr => api.at(L.x(pr.x ?? 0.15), L.y(pr.y ?? 0.5), anyIcon(api, pr.icon, (pr.size || 170) * k, pr.color || 'var(--acc)'), { cls: 'cr-pr', idle: 'float sway' })).join('');
    const bt = bubbles.map(b => (b.at !== undefined ? api.T(b.at) : api.start + 0.3));
    const bw = bubbles.map((b, i) => api.times(b.text, bt[i], bubbles[i + 1] ? bt[i + 1] : api.end));
    const talk = bw.map(w => [w[0] - 0.1, w[w.length - 1] + 0.4]);
    const prt = itemTimes(api, p.props || [], 'x');
    const away = (p.away || []).map(r => api.T(r)), back = (p.back || []).map(r => api.T(r));
    return t => {
      api.tw(q(root, '.cr-disc .a'), t, api.K.pop(api.start - 0.05, 0.6, { o: 0, s: 0.3 }));
      const pk = [[api.start, { o: 0, y: ph * 0.5 }], [api.start + 0.12, { o: 1 }, 'lin'], [api.start + 0.55, { y: 0 }, 'back']];
      away.forEach((a, i) => { pk.push([a, {}], [a + 0.35, { x: L.w * 0.45, r: 8, o: 0.35 }, 'in']); if (back[i] !== undefined) pk.push([back[i], {}], [back[i] + 0.5, { x: 0, r: 0, o: 1 }, 'back']); });
      api.tw(q(root, '.cr-peep .a'), t, pk);
      api.peepUpdate(q(root, '.cr-peep'), t, p.peep, talk);
      qa(root, '.cr-b').forEach((b, i) => {
        api.tw(q(b, '.a'), t, [[bt[i] - 0.08, { o: 0, s: 0.3, y: 40 }], [bt[i] + 0.02, { o: 1 }, 'lin'], [bt[i] + 0.4, { s: 1, y: 0 }, 'back']]);
        api.ktUpdate(q(b, '.kt'), t, bw[i], { lead: 0.03 });
      });
      qa(root, '.cr-pr').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.spring(prt[i], 0.6, { o: 0, s: 0, r: -30 })));
    };
  });

  // ===================================================================== chat: phone with messages
  // {title, messages:[{from:"them|me", text, at}], badge}
  def('chat', (api, root) => {
    const { p, L } = api, k = L.k, pw = Math.min(L.w * 0.74, L.h * 0.98 / 1.55), ph = pw * 1.55;
    root.innerHTML = api.at(L.cx, L.cy, `<div class="phone" style="width:${pw}px;height:${ph}px">
        <div class="screen" style="height:100%">
          <div class="ch-head" style="height:${130 * k}px;display:flex;align-items:center;gap:${20 * k}px;padding:0 ${34 * k}px;font-family:var(--f-head);font-weight:800;font-size:${44 * k}px">
            <div class="badge paper" style="font-size:${78 * k}px">${api.icon('ph-fill:user', 48 * k)}</div>${esc(p.title || '')}</div>
          <div class="ch-list" style="position:absolute;left:0;right:0;top:${150 * k}px;bottom:${30 * k}px"></div>
        </div></div>`, { cls: 'ph', idle: 'float', amp: 0.6 });
    const listEl = q(root, '.ch-list');
    let y = 10 * k;
    const msgs = p.messages.map(m => {
      const d = document.createElement('div');
      d.className = 'msg ' + (m.from === 'me' ? 'me' : 'them'); d.style.fontSize = pw * 0.1 + 'px'; d.style.maxWidth = pw * 0.84 + 'px';
      d.innerHTML = esc(m.text); d.style.top = y + 'px'; listEl.appendChild(d);
      const h = d.getBoundingClientRect().height; y += h + 22 * k; return { d, h };
    });
    const dots = document.createElement('div'); dots.className = 'msg them'; dots.style.fontSize = pw * 0.1 + 'px';
    dots.innerHTML = '<span class="dt">●</span> <span class="dt">●</span> <span class="dt">●</span>'; listEl.appendChild(dots);
    const ts = itemTimes(api, p.messages, 'text');
    const avail = ph - 190 * k;
    return t => {
      api.tw(q(root, '.ph .a'), t, [[api.start, { o: 0, y: 260, r: -8, s: 0.9 }], [api.start + 0.6, { o: 1, y: 0, r: -2, s: 1 }, 'back']]);
      let shown = 0, scroll = 0;
      msgs.forEach((m, i) => {
        const a = ts[i];
        api.tw(m.d, t, [[a, { o: 0, s: 0.5, x: (p.messages[i].from === 'me' ? 120 : -120), y: 30 }], [a + 0.05, { o: 1 }, 'lin'], [a + 0.4, { s: 1, x: 0, y: 0 }, 'back']]);
        if (t >= a) { shown = i; const bottom = parseFloat(m.d.style.top) + m.h; scroll = Math.max(scroll, bottom - avail); }
      });
      listEl.style.transform = `translateY(${-Math.max(0, scroll)}px)`;
      const nx = ts.findIndex(a => a > t), them = nx >= 0 && p.messages[nx].from !== 'me' && ts[nx] - t < 0.55 && ts[nx] - t > 0.05;
      dots.style.display = them ? '' : 'none';
      if (them) {
        const prevEnd = nx > 0 ? parseFloat(msgs[nx - 1].d.style.top) + msgs[nx - 1].h + 22 * k : 10 * k;
        dots.style.top = prevEnd + 'px';
        qa(dots, '.dt').forEach((e, i) => { e.style.opacity = 0.3 + 0.7 * Math.abs(Math.sin(t * 6 + i * 0.8)); });
      }
    };
  });

  // ===================================================================== icongrid: tiles or a quantity grid
  // tiles: {items:[{icon, label, at}]}   quantity: {icon, count:24, cols:6, at, dur, highlight:{index, at, label}}
  def('icongrid', (api, root) => {
    const { p, L } = api, k = L.k;
    if (p.items) {
      const n = p.items.length, cols = p.cols || (n <= 3 ? 1 : 2), rows = Math.ceil(n / cols);
      const tw_ = cols === 1 ? L.w * 0.9 : L.w * 0.47,   /* 0.9 (was 0.96): the spring entry overshot the frame edge (QC safe-zone, 2026-10-27) */ th = Math.min((L.h - 30 * k * (rows - 1)) / rows, cols === 1 ? 300 * k : 470 * k);
      root.innerHTML = p.items.map((it, i) => {
        const c = i % cols, r = Math.floor(i / cols);
        const x = cols === 1 ? L.cx : L.x(c ? 0.755 : 0.245), y = L.cy + (r - (rows - 1) / 2) * (th + 30 * k);
        const inner = cols === 1
          ? `<div class="card ${i % 2 ? 'acc' : ''}" style="width:${tw_}px;height:${th}px;display:flex;align-items:center;gap:${36 * k}px;padding:0 ${44 * k}px">${anyIcon(api, it.icon, th * 0.66, i % 2 ? 'var(--on-acc)' : 'var(--c1)')}<div class="big ig-lab" style="flex:1;min-width:0;white-space:normal">${esc(it.label)}</div></div>`
          : `<div class="card ${i % 3 === 1 ? 'acc' : ''}" style="width:${tw_}px;height:${th}px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${20 * k}px">${anyIcon(api, it.icon, th * 0.5, i % 3 === 1 ? 'var(--on-acc)' : 'var(--c1)')}<div class="big ig-lab" style="text-align:center;white-space:normal;width:${tw_ * 0.86}px">${esc(it.label)}</div></div>`;
        return api.at(x, y, `<div style="width:${tw_}px;height:${th}px;border-radius:var(--r-l);border:${6 * k}px dashed var(--line)"></div>`, { cls: 'ig-g' }) + api.at(x, y, inner, { cls: 'ig-t', idle: 'float', amp: 0.5 });
      }).join('');
      const igf = Math.min(...qa(root, '.ig-lab').map(el => fitBox(el, cols === 1 ? th * 0.8 : th * 0.36, 96 * k))); qa(root, '.ig-lab').forEach(el => { el.style.fontSize = igf + 'px'; });
      const ts = itemTimes(api, p.items);
      return t => {
        qa(root, '.ig-g').forEach((e, i) => api.tw(q(e, '.a'), t, [[api.start + i * 0.07, { o: 0, s: 0.8 }], [api.start + 0.4 + i * 0.07, { o: 1, s: 1 }, 'back'], [ts[i], {}], [ts[i] + 0.2, { o: 0 }, 'lin']]));
        qa(root, '.ig-t').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.spring(ts[i] - 0.05, 0.6, { o: 0, s: 0.2, r: i % 2 ? 12 : -12 })));
      };
    }
    const n = p.count || 20, cols = p.cols || 5, rows = Math.ceil(n / cols), cell = Math.min(L.w / cols, (L.h - 160 * k) / rows);
    root.innerHTML = Array.from({ length: n }, (_, i) => api.at(L.cx + (i % cols - (cols - 1) / 2) * cell, L.cy - 60 * k + (Math.floor(i / cols) - (rows - 1) / 2) * cell,
        anyIcon(api, p.icon, cell * 0.78, i === p.highlight?.index ? 'var(--acc)' : 'var(--dim)'), { cls: 'ig-i', idle: 'bob', amp: 0.3 })).join('') +
      (p.highlight ? api.at(L.cx, L.y1 - 70 * k, `<div class="tag" style="font-size:${84 * k}px">${esc(p.highlight.label || '')}</div>`, { cls: 'ig-hl' }) : '');
    const t0 = p.at !== undefined ? api.T(p.at) : api.start + 0.1, dur = p.dur || Math.min(1.6, (api.end - t0) * 0.6);
    const th = p.highlight?.at !== undefined ? api.T(p.highlight.at) : t0 + dur + 0.3;
    return t => {
      qa(root, '.ig-i').forEach((e, i) => {
        const keys = api.K.pop(t0 + dur * i / n, 0.3, { o: 0, s: 0 });
        if (p.highlight) keys.push([th, {}], [th + 0.35, i === p.highlight.index ? { s: 1.6 } : { o: 0.35, s: 0.85 }, 'back']);
        api.tw(q(e, '.a'), t, keys);
      });
      if (p.highlight) api.tw(q(root, '.ig-hl .a'), t, api.K.pop(th + 0.15));
    };
  });

  // ===================================================================== beforeafter: a wipe reveals the change
  // {before:{label, icon}, after:{label, icon}, at, swipeAt}
  def('beforeafter', (api, root) => {
    const { p, L } = api, k = L.k, cw = L.w * 0.97, chh = L.h * 0.86;
    const half = (s, kind) => `<div class="card ${kind}" style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${30 * k}px">
        ${anyIcon(api, s.icon, chh * 0.42, kind === 'acc' ? 'var(--on-acc)' : 'var(--c1)')}<div class="big" style="font-size:${100 * k}px;text-align:center;white-space:normal;width:${cw * 0.85}px">${esc(s.label)}</div></div>`;
    root.innerHTML = api.at(L.cx, L.cy, `<div style="position:relative;width:${cw}px;height:${chh}px">
        ${half(p.before, '')}<div class="ba-after" style="position:absolute;inset:0">${half(p.after, 'acc')}</div>
        <div class="ba-bar" style="position:absolute;top:-${20 * k}px;bottom:-${20 * k}px;width:${16 * k}px;margin-left:-${8 * k}px;background:var(--paper);border-radius:${8 * k}px;box-shadow:0 0 30px var(--hard-shadow)"></div></div>`, { cls: 'ba', idle: 'float', amp: 0.4 });
    qa(root, '.ba .big').forEach(el => fitBox(el, chh * 0.3, 100 * k));
    const t0 = p.at !== undefined ? api.T(p.at) : api.start + 0.1, ts = p.swipeAt !== undefined ? api.T(p.swipeAt) : t0 + 1.2;
    return t => {
      api.tw(q(root, '.ba .a'), t, api.K.pop(t0 - 0.1, 0.5, { o: 0, s: 0.7, r: -4 }));
      const u = api.prog(t, ts, ts + 0.7, 'io');
      q(root, '.ba-after').style.clipPath = `inset(0 0 0 ${(100 - 100 * u).toFixed(2)}%)`;
      q(root, '.ba-bar').style.left = (100 - 100 * u) + '%'; q(root, '.ba-bar').style.opacity = u > 0 && u < 1 ? 1 : 0;
    };
  });

  // ===================================================================== level: a container whose liquid level changes
  // {container:"vial|battery", label, levels:[[0.8, at], [0.35, "less"]], tag:{text, at, kind}, sub}
  def('level', (api, root) => {
    const { p, L } = api, k = L.k, vh = Math.min(L.h * 0.8, 900 * k), vw = Math.min(L.w * 0.5, vh * 0.56), cx = L.x(p.x ?? 0.46), cy = L.cy - 30 * k;
    root.innerHTML = api.at(cx, cy, `<svg viewBox="0 0 ${vw} ${vh}" style="width:${vw}px;height:${vh}px;overflow:visible">
        <defs><clipPath id="lv-clip"><rect x="${12 * k}" y="${12 * k}" width="${vw - 24 * k}" height="${vh - 24 * k}" rx="${vw * 0.32}"/></clipPath></defs>
        <rect x="0" y="0" width="${vw}" height="${vh}" rx="${vw * 0.36}" fill="var(--surface)" stroke="var(--outline)" stroke-width="${12 * k}"/>
        <g clip-path="url(#lv-clip)"><path class="lv-liq" fill="var(--c1)"/><path class="lv-liq2" fill="var(--c1l)" opacity=".55"/>${Array.from({ length: 8 }, () => `<circle class="lv-bub" r="${8 * k}" fill="var(--paper)" opacity=".6"/>`).join('')}</g>
        <rect x="${vw * 0.16}" y="${vh * 0.08}" width="${vw * 0.1}" height="${vh * 0.6}" rx="${vw * 0.05}" fill="var(--paper)" opacity=".3"/></svg>`, { cls: 'lv', idle: 'float sway', amp: 0.4 }) +
      (p.label ? api.at(cx, cy + vh / 2 + 70 * k, `<div class="tag paper" style="font-size:${66 * k}px">${esc(p.label)}</div>`, { cls: 'lv-lab' }) : '') +
      (p.tag ? api.at(cx + vw * 0.62, cy - vh * 0.05, `<div class="tag ${p.tag.kind || ''}" style="font-size:${84 * k}px">${p.tag.icon ? api.icon(p.tag.icon, 70 * k) : ''}${esc(p.tag.text)}</div>`, { cls: 'lv-tag', idle: 'sway' }) : '');
    const lv = (p.levels || [[0.75, api.start]]).map(([v, a]) => [v, typeof a === 'number' && a < 0 ? api.start : api.T(a)]);
    const tt = p.tag ? (p.tag.at !== undefined ? api.T(p.tag.at) : lv[lv.length - 1][1] + 0.3) : 0;
    const liq = q(root, '.lv-liq'), liq2 = q(root, '.lv-liq2'), bubs = qa(root, '.lv-bub');
    return t => {
      api.tw(q(root, '.lv .a'), t, api.K.spring(api.start, 0.7, { o: 0, s: 0.3, y: 100 }));
      let v = lv[0][0];
      for (let i = 1; i < lv.length; i++) v = api.lerp(v, lv[i][0], api.prog(t, lv[i][1], lv[i][1] + 1.0, 'spring'));
      const fill = api.prog(t, api.start + 0.1, api.start + 0.8, 'out');
      const surf = vh - (vh - 24 * k) * v * fill - 12 * k;
      const wave = (ph, a) => { let d = `M0 ${vh} L0 ${surf}`; for (let x = 0; x <= vw; x += vw / 16) d += ` L${x.toFixed(1)} ${(surf + a * Math.sin(x / vw * 6.28 * 1.5 + t * 3.2 + ph)).toFixed(1)}`; return d + ` L${vw} ${vh} Z`; };
      liq.setAttribute('d', wave(0, 12 * k)); liq2.setAttribute('d', wave(2, 18 * k));
      bubs.forEach((b, i) => { const ph = ((t * 0.5 + i * 0.137) % 1); b.setAttribute('cx', vw * (0.2 + 0.6 * ((i * 0.37) % 1)) + 10 * Math.sin(t * 3 + i)); b.setAttribute('cy', vh - ph * (vh - surf)); });
      if (p.label) api.tw(q(root, '.lv-lab .a'), t, api.K.rise(api.start + 0.3));
      if (p.tag) api.tw(q(root, '.lv-tag .a'), t, [[tt, { o: 0, s: 0.3, r: 20 }], [tt + 0.42, { o: 1, s: 1, r: -5 }, 'back']]);
    };
  });

  // ===================================================================== cta: profile + actions
  // {handle:"@yourhandle", monogram:"Y", actions:[{kind:"follow|save|comment|like|share", label, done, at}], bubble:{text, at}}
  def('cta', (api, root) => {
    const { p, L } = api, k = L.k, D = 360 * k;
    const ICON = { follow: ['ph-bold:user-plus', 'ph-bold:check'], save: ['ph-bold:bookmark-simple', 'ph-fill:bookmark-simple'], comment: ['ph-bold:chat-circle', 'ph-fill:chat-circle'],
      like: ['ph-bold:heart', 'ph-fill:heart'], share: ['ph-bold:paper-plane-tilt', 'ph-fill:paper-plane-tilt'] };
    const acts = p.actions || [];
    root.innerHTML =
      api.at(L.cx, L.y0 + D * 0.62, `<div class="disc" style="width:${D}px;height:${D}px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 ${14 * k}px var(--acc),var(--sh)"><span class="big" style="font-size:${D * 0.56}px;color:var(--on-disc)">${esc(p.monogram || 'Z')}</span></div>`, { cls: 'ct-av', idle: 'float breathe' }) +
      api.at(L.cx, L.y0 + D * 1.42, `<div class="big ct-h" style="font-size:${98 * k}px">${esc(p.handle)}</div>`, { cls: 'ct-hd' }) +
      acts.map((a, i) => api.at(L.cx, L.y0 + D * 1.42 + (190 + i * 200) * k,
        `<div class="btn ct-btn ${i % 2 ? '' : 'acc'}" style="font-size:${76 * k}px;position:relative"><span class="ct-i0">${api.icon(ICON[a.kind][0], 70 * k)}</span><span class="ct-i1" style="position:absolute;left:.55em">${api.icon(ICON[a.kind][1], 70 * k)}</span><span class="ct-l0">${esc(a.label)}</span><span class="ct-l1" style="display:none">${esc(a.done || a.label)}</span></div>`, { cls: 'ct-a', idle: 'float', amp: 0.4 })).join('') +
      (p.bubble ? api.at(L.x(0.76), L.y0 + 120 * k, `<div class="bubble r acc" style="font-size:${64 * k}px">${esc(p.bubble.text)}</div>`, { cls: 'ct-bub', idle: 'float sway' }) : '');
    fitFont(q(root, '.ct-h'), L.w * 0.96, 0, 98 * k);
    const ta = itemTimes(api, acts, 'label'), tbub = p.bubble ? api.T(p.bubble.at ?? api.end - 0.8) : 0;
    const bursted = new Set();
    return t => {
      api.tw(q(root, '.ct-av .a'), t, api.K.spring(api.start, 0.7, { o: 0, s: 0, r: -90 }));
      api.tw(q(root, '.ct-hd .a'), t, api.K.rise(api.start + 0.2));
      qa(root, '.ct-a').forEach((e, i) => {
        const a = ta[i];
        api.tw(q(e, '.a'), t, [[api.start + 0.3 + i * 0.12, { o: 0, y: 80 }], [api.start + 0.7 + i * 0.12, { o: 1, y: 0 }, 'back'],
          [a, {}], [a + 0.1, { s: 0.88 }, 'out'], [a + 0.45, { s: 1.06 }, 'back'], [a + 0.7, { s: 1 }, 'io']]);
        const on = t >= a + 0.1;
        q(e, '.ct-i0').style.opacity = on ? 0 : 1; q(e, '.ct-i1').style.opacity = on ? 1 : 0;
        q(e, '.ct-l0').style.display = on ? 'none' : ''; q(e, '.ct-l1').style.display = on ? '' : 'none';
        if (on && !bursted.has(i)) { const r = e.getBoundingClientRect(); api.burst(a + 0.1, r.left + r.width / 2, r.top + r.height / 2, 16); bursted.add(i); }
      });
      if (p.bubble) api.tw(q(root, '.ct-bub .a'), t, api.K.pop(tbub, 0.4, { o: 0, s: 0.2, y: 30 }));
    };
  });

  // ===================================================================== image: AI still with parallax + highlights
  // {src:"bg.jpg", focus:[0.5,0.4], highlights:[{x,y,r,at}], labels:[{text,x,y,at}], frame:"card|full"}
  def('image', (api, root) => {
    const { p, L } = api, k = L.k, full = p.frame === 'full';
    const w = full ? api.CFG.W : L.w * 0.97, h = full ? api.CFG.H : L.h * 0.9;
    const src = p.src;
    root.innerHTML = (full ? '' : `<div class="im-back" style="position:absolute;inset:-60px;background:url('${src}') center/cover;filter:blur(40px) brightness(.55);opacity:.6"></div>`) +
      api.at(full ? api.CFG.W / 2 : L.cx, full ? api.CFG.H / 2 : L.cy, `<div class="${full ? '' : 'card'} im-card" style="width:${w}px;height:${h}px;overflow:hidden;border-radius:${full ? 0 : 'var(--r-l)'}">
        <div class="im-img" style="position:absolute;inset:-6%;background:url('${src}') ${((p.focus || [0.5, 0.5])[0] * 100)}% ${((p.focus || [0.5, 0.5])[1] * 100)}%/cover"></div>
        ${(p.highlights || []).map(hh => `<div class="im-hl round" style="position:absolute;left:${hh.x * 100}%;top:${hh.y * 100}%;width:${(hh.r || 0.12) * 2 * w}px;height:${(hh.r || 0.12) * 2 * w}px;margin:-${(hh.r || 0.12) * w}px 0 0 -${(hh.r || 0.12) * w}px;border:${12 * k}px solid var(--acc)"></div>`).join('')}
      </div>`, { cls: 'im', content: true }) +
      (p.labels || []).map(lb => api.at(L.x(lb.x ?? 0.5), L.y(lb.y ?? 0.85), `<div class="tag ${lb.kind || ''}" style="font-size:${(lb.size || 80) * k}px">${esc(lb.text)}</div>`, { cls: 'im-lab', idle: 'sway' })).join('');
    const ht = itemTimes(api, p.highlights || [], 'x'), lt = itemTimes(api, p.labels || [], 'text');
    return t => {
      const u = api.prog(t, api.start, api.end, 'lin');
      q(root, '.im-img').style.transform = `scale(${1.04 + 0.1 * u}) translate(${(-1.5 + 3 * u).toFixed(2)}%, ${(1 - 2 * u).toFixed(2)}%)`;
      api.tw(q(root, '.im .a'), t, full ? [[api.start, { o: 1 }]] : api.K.pop(api.start, 0.55, { o: 0, s: 0.85, r: -3 }));
      qa(root, '.im-hl').forEach((e, i) => { const a = t - ht[i]; e.style.opacity = a > 0 ? 1 : 0; e.style.transform = `scale(${a > 0 ? (1 + 0.6 * (1 - api.E.spring(Math.min(1, a / 0.6))) + 0.04 * Math.sin(t * 5)) : 0})`; });
      qa(root, '.im-lab').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.pop(lt[i], 0.42, { o: 0, s: 0.3, r: -12 })));
    };
  });
  // ===================================================================== joint: stylised knee (literal illustration only)
  // {fluidAt, pulseAt, moveAt, labels:[{text, at, x, y, kind}]}  bones build, capsule draws, fluid fills, the lower bone swings
  def('joint', (api, root) => {
    const { p, L } = api, k = L.k, Hh = L.h * 0.98, Ww = Math.min(L.w, Hh * 0.56), cx = L.cx, cy = L.cy;
    const cart = 'var(--c1x)';
    root.innerHTML = api.at(cx, cy, `<div class="round" style="width:${Ww * 1.5}px;height:${Ww * 1.5}px;background:radial-gradient(closest-side, var(--c1) 0%, transparent 100%);opacity:.35"></div>`, { cls: 'jt-glow', idle: 'breathe' }) +
      api.at(cx, cy, `<svg viewBox="220 0 560 1000" preserveAspectRatio="xMidYMid slice" style="width:${Ww}px;height:${Hh}px;overflow:visible">
        <defs><radialGradient id="jt-fl" cx="50%" cy="50%" r="60%"><stop offset="0" stop-color="var(--c1l)" stop-opacity=".95"/><stop offset="1" stop-color="var(--c1)" stop-opacity=".75"/></radialGradient>
          <linearGradient id="jt-b" x1="0" x2="1"><stop offset="0" stop-color="#d8cfc0"/><stop offset=".45" stop-color="${'#fbf6ec'}"/><stop offset="1" stop-color="#cfc4b2"/></linearGradient></defs>
        <g class="jt-up"><path d="M420 -40 L580 -40 L585 360 Q640 380 650 430 Q655 470 610 490 Q560 505 500 492 Q440 505 390 490 Q345 470 350 430 Q360 380 415 360 Z" fill="url(#jt-b)" stroke="rgba(0,0,0,.25)" stroke-width="4"/>
          <path class="jt-c1" d="M362 452 Q380 500 440 500 Q470 497 500 494 Q530 497 560 500 Q620 500 638 452" fill="none" stroke="${cart}" stroke-width="22" stroke-linecap="round"/></g>
        <ellipse class="jt-cap" cx="500" cy="530" rx="235" ry="140" fill="none" stroke="var(--c1)" stroke-width="10" stroke-dasharray="1500" stroke-dashoffset="1500"/>
        <ellipse class="jt-fluid" cx="500" cy="532" rx="190" ry="78" fill="url(#jt-fl)" opacity="0"/>
        ${Array.from({ length: 10 }, () => '<circle class="jt-p" r="7" fill="var(--paper)" opacity="0"/>').join('')}
        <g class="jt-lo"><path d="M395 575 Q400 555 440 552 Q470 556 500 558 Q530 556 560 552 Q600 555 605 575 Q615 600 575 615 L565 1040 L435 1040 L425 615 Q385 600 395 575 Z" fill="url(#jt-b)" stroke="rgba(0,0,0,.25)" stroke-width="4"/>
          <path d="M405 566 Q450 555 500 560 Q550 555 595 566" fill="none" stroke="${cart}" stroke-width="20" stroke-linecap="round"/></g>
        <circle class="jt-ring" cx="500" cy="530" r="250" fill="none" stroke="var(--acc)" stroke-width="8" opacity="0"/>
      </svg>`, { cls: 'jt', idle: 'float', amp: 0.4 }) +
      (p.labels || []).map(lb => api.at(L.x(lb.x ?? 0.5), L.y(lb.y ?? 0.1), `<div class="tag ${lb.kind || ''}" style="font-size:${(lb.size || 70) * k}px">${esc(lb.text)}</div>`, { cls: 'jt-lab', idle: 'sway' })).join('');
    const tf = p.fluidAt !== undefined ? api.T(p.fluidAt) : api.start + 0.6, tp = p.pulseAt !== undefined ? api.T(p.pulseAt) : null, tm = p.moveAt !== undefined ? api.T(p.moveAt) : null;
    const lt = itemTimes(api, p.labels || [], 'text');
    const cap = q(root, '.jt-cap'), fl = q(root, '.jt-fluid'), lo = q(root, '.jt-lo'), up = q(root, '.jt-up'), ring = q(root, '.jt-ring'), ps = qa(root, '.jt-p');
    return t => {
      const b = api.prog(t, api.start, api.start + 0.6, 'back');
      up.setAttribute('transform', `translate(0 ${(-380 * (1 - b)).toFixed(1)})`);
      const sw = tm !== null && t > tm ? 16 * Math.sin((t - tm) * 2 * Math.PI * 0.55) * api.prog(t, tm, tm + 0.4) : 0;
      lo.setAttribute('transform', `translate(0 ${(420 * (1 - b)).toFixed(1)}) rotate(${sw.toFixed(2)} 500 545)`);
      cap.style.strokeDashoffset = 1500 * (1 - api.prog(t, tf - 0.45, tf, 'io'));
      const f = api.prog(t, tf, tf + 0.5, 'out'); fl.setAttribute('opacity', (0.95 * f).toFixed(3));
      fl.setAttribute('ry', (78 + 6 * Math.sin(t * 2.4)).toFixed(1));
      ps.forEach((c, i) => { c.setAttribute('cx', (340 + ((i * 37 + t * 40) % 320)).toFixed(1)); c.setAttribute('cy', (532 + 46 * Math.sin(t * 2 + i)).toFixed(1)); c.setAttribute('opacity', (0.7 * f).toFixed(2)); });
      if (tp !== null) { const a = t - tp; ring.setAttribute('opacity', a > 0 && a < 1 ? (1 - a).toFixed(2) : 0); ring.setAttribute('r', (250 + 160 * Math.max(0, Math.min(1, a))).toFixed(1)); }
      api.tw(q(root, '.jt .a'), t, [[api.start, { o: 0, s: 0.9 }], [api.start + 0.3, { o: 1, s: 1 }, 'out']]);
      qa(root, '.jt-lab').forEach((e, i) => api.tw(q(e, '.a'), t, [[lt[i], { o: 0, s: 0.3, r: 14 }], [lt[i] + 0.42, { o: 1, s: 1, r: -4 }, 'back']]));
    };
  });
})();
