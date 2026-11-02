/* @scene {"type":"doctor_door","tags":["most important","if it hurts","start with a doctor"],"layout":"perspective-path-to-door-footprints-trail","metaphor":"a path narrows to a lit door with a stethoscope sign; two footprints wait at the bottom, then a trail of footprints runs up the path to the door","assets":["perspective path","door","stethoscope sign","footprints trail"]} */
// {most, hurts, hurtsAt, start, startAt}
RM.def('doctor_door', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tH = api.T(p.hurtsAt), tS = api.T(p.startAt);
  const cx = L.cx, dy = L.y(0.4), DW = 250 * k, DH = 370 * k, FP = Array.from({ length: 9 }, (_, i) => { const v = i / 8, s = 1 - 0.74 * v ** 0.8; return { y: L.y(0.95) + (dy + 40 * k - L.y(0.95)) * (1 - (1 - v) ** 1.6), x: cx + (i % 2 ? 1 : -1) * 62 * k * s, s }; });
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <path d="M${cx - DW * 0.5} ${dy} L${cx + DW * 0.5} ${dy} L${L.x(0.98)} ${L.y1 + 20 * k} L${L.x(0.02)} ${L.y1 + 20 * k} Z" fill="rgba(46,196,182,.2)"/>
      <path d="M${cx} ${dy + 30 * k} L${cx} ${L.y1 + 20 * k}" stroke="var(--c1l)" stroke-width="${10 * k}" stroke-dasharray="${50 * k} ${44 * k}" fill="none"/>
      <rect x="${cx - DW / 2 - 18 * k}" y="${dy - DH - 18 * k}" width="${DW + 36 * k}" height="${DH + 18 * k}" rx="${14 * k}" fill="var(--c2)"/>
      <rect x="${cx - DW / 2}" y="${dy - DH}" width="${DW}" height="${DH}" fill="var(--acc-soft)"/>
      <rect class="dd-l" x="${cx - DW / 2}" y="${dy - DH}" width="${DW}" height="${DH}" fill="var(--paper)"/>
      ${FP.map(() => `<g class="dd-fp"><ellipse cy="${-16 * k}" rx="${40 * k}" ry="${54 * k}" fill="var(--paper)"/><ellipse cy="${62 * k}" rx="${30 * k}" ry="${30.5 * k}" fill="var(--paper)"/></g>`).join('')}</svg>` +
    api.at(cx + DW * 0.5 + 170 * k, dy - DH * 0.6, `<div style="width:${210 * k}px;height:${210 * k}px;border-radius:50%;background:var(--paper);display:flex;align-items:center;justify-content:center;box-shadow:var(--sh)">${api.icon('ph:stethoscope', 150 * k, 'var(--c2)')}</div>`, { cls: 'dd-s' }) +
    api.at(cx, L.y(0.58), R.tag(p.most || '', 84 * k, ''), { cls: 'dd-t0', idle: 'sway' }) +
    api.at(cx, L.y(0.58), R.tag(p.hurts || '', 92 * k, 'bad'), { cls: 'dd-t1', idle: 'wobble' }) +
    api.at(cx, L.y(0.58), R.tag(p.start || '', 84 * k, 'c1'), { cls: 'dd-t2', idle: 'sway' });
  const fp = R.qa(root, '.dd-fp'), lf = q(root, '.dd-l');
  return t => {
    fp.forEach((e, i) => { const a = i < 2 ? api.start + 0.1 + i * 0.12 : tS - 0.1 + (i - 2) * (api.end - tS - 0.05) / 6, u = api.prog(t, a, a + 0.18, 'back'), f = FP[i];
      R.gx(e, { s: Math.max(0.01, u * f.s), r: i % 2 ? 6 : -6, o: u > 0 ? 1 : 0 }, f.x, f.y); });
    lf.setAttribute('width', (DW * (1 - 0.8 * api.prog(t, tS - 0.2, tS + 0.4, 'out'))).toFixed(1));
    api.tw(q(root, '.dd-s .a'), t, api.K.pop(api.start + 0.25, 0.4, { o: 0, s: 0 }));
    api.tw(q(root, '.dd-t0 .a'), t, api.K.pop(api.start + 0.05, 0.3, { o: 0, s: 0.4 }).concat([[tH - 0.15, {}], [tH - 0.02, { o: 0, s: 0.7 }, 'in']]));
    api.tw(q(root, '.dd-t1 .a'), t, api.K.pop(tH, 0.3, { o: 0, s: 0.4 }).concat([[tS - 0.15, {}], [tS - 0.02, { o: 0, s: 0.7 }, 'in']]));
    api.tw(q(root, '.dd-t2 .a'), t, api.K.slam(tS - 0.02, 0.32));
  };
});
