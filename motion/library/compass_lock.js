/* @scene {"type":"compass_lock","tags":["if it hurts","doctor first","not a blogger"],"layout":"round-compass-dial-center-needle","metaphor":"a compass needle wobbles, swings at the phone mark, gets knocked away and locks onto the stethoscope","assets":["compass dial","needle","phone mark"]} */
// {pain, painAt, first, firstAt, blog, blogAt, doc, docAt}
RM.def('compass_lock', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tP = api.T(p.painAt), tF = api.T(p.firstAt), tB = api.T(p.blogAt), tD = api.T(p.docAt), cx = L.cx, cy = L.y(0.5), r = 400 * k;
  const a0 = -52, a1 = 52, mark = a => [cx + Math.sin(a * Math.PI / 180) * r * 0.74, cy - Math.cos(a * Math.PI / 180) * r * 0.74];
  const [lx, ly] = mark(a0), [rx, ry] = mark(a1);
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="var(--bgDeep)" stroke="var(--c1l)" stroke-width="${14 * k}"/>
      ${Array.from({ length: 24 }, (_, i) => { const a = i * 15 * Math.PI / 180, r0 = r * (i % 6 ? 0.92 : 0.86); return `<line x1="${cx + Math.sin(a) * r0}" y1="${cy - Math.cos(a) * r0}" x2="${cx + Math.sin(a) * r * 0.97}" y2="${cy - Math.cos(a) * r * 0.97}" stroke="var(--c1l)" stroke-width="${6 * k}"/>`; }).join('')}
      <circle class="cl-p" cx="${cx}" cy="${cy}" fill="none" stroke="var(--bad)" stroke-width="${12 * k}"/>
      <g class="cl-n"><path d="M0 ${-r * 0.56} L${34 * k} 0 L${-34 * k} 0 Z" fill="var(--acc)"/><path d="M0 ${r * 0.4} L${34 * k} 0 L${-34 * k} 0 Z" fill="var(--c2)"/><circle r="${30 * k}" fill="var(--paper)"/></g></svg>` +
    api.at(lx, ly, `<svg width="${170 * k}" height="${170 * k}" viewBox="-50 -50 100 100"><rect x="-26" y="-44" width="52" height="88" rx="10" fill="var(--c1x)"/><path d="M-9 -14 L14 0 L-9 14 Z" fill="var(--c2)"/></svg>`, { cls: 'cl-a' }) +
    api.at(lx, ly, `<svg width="${220 * k}" height="${220 * k}" viewBox="-50 -50 100 100"><path d="M-36 -36 L36 36 M36 -36 L-36 36" stroke="var(--bad)" stroke-width="14" stroke-linecap="round"/></svg>`, { cls: 'cl-x' }) +
    api.at(rx, ry, `<div style="width:${180 * k}px;height:${180 * k}px;border-radius:50%;background:var(--paper);display:flex;align-items:center;justify-content:center">${api.icon('ph-fill:stethoscope', 120 * k, 'var(--c2)')}</div>`, { cls: 'cl-d', idle: 'sway' }) +
    api.at(cx, L.y(0.03), R.tag(p.pain || '', 92 * k, 'bad'), { cls: 'cl-t1', idle: 'wobble' }) +
    api.at(cx, L.y(0.03), R.tag(p.first || '', 82 * k, 'c1'), { cls: 'cl-t2', idle: 'sway' }) +
    api.at(cx, L.y(0.97), R.tag(p.blog || '', 84 * k, ''), { cls: 'cl-t3', idle: 'sway' }) +
    api.at(cx, L.y(0.97), R.tag(p.doc || '', 104 * k, 'c1'), { cls: 'cl-t4', idle: 'wobble' });
  const n = q(root, '.cl-n'), pr = q(root, '.cl-p');
  return t => {
    const wob = 16 * Math.sin(t * 9), toB = api.prog(t, tB - 0.12, tB + 0.1, 'out'), toD = api.prog(t, tD - 0.05, tD + 0.3, 'back'), first = api.prog(t, tF - 0.05, tF + 0.3, 'back') * (1 - toB);
    const ang = wob * (1 - Math.max(toB, first)) * (1 - toD) + a1 * 0.7 * first + (a0 * toB) * (1 - toD) + a1 * toD;
    R.gx(n, { r: ang, s: 1, o: 1 }, cx, cy);
    pr.setAttribute('r', ((70 + 90 * Math.abs(Math.sin(t * 6))) * k).toFixed(1)); pr.style.opacity = t > tP - 0.05 && t < tF ? 0.9 : 0;
    api.tw(q(root, '.cl-a .a'), t, api.K.pop(api.start + 0.1, 0.26, { o: 0, s: 0.3 }));
    api.tw(q(root, '.cl-d .a'), t, api.K.pop(api.start + 0.18, 0.26, { o: 0, s: 0.3 }));
    api.tw(q(root, '.cl-x .a'), t, api.K.slam(tB + 0.12, 0.26));
    api.tw(q(root, '.cl-t1 .a'), t, api.K.pop(tP - 0.03, 0.24, { o: 0, s: 0.3 }).concat([[tF - 0.1, {}], [tF - 0.02, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.cl-t2 .a'), t, api.K.slam(tF - 0.02, 0.28));
    api.tw(q(root, '.cl-t3 .a'), t, api.K.pop(tB - 0.1, 0.24, { o: 0, s: 0.3, r: -4 }).concat([[tD - 0.12, {}], [tD - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.cl-t4 .a'), t, api.K.slam(tD - 0.03, 0.3));
  };
});
