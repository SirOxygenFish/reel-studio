/* @scene {"type":"fork_road","tags":["if it hurts","doctor first","not a blogger"],"layout":"top-down-y-fork-trunk-bottom-two-branches","metaphor":"a marker starts at a pulsing ring at the foot of a forked road: the left branch to a ring light gets stamped out, the marker runs up the right branch to the stethoscope","assets":["forked road","ring light with phone","stamped cross","moving marker"]} */
// {pain, painAt, first, firstAt, blog, blogAt, doc, docAt}
RM.def('fork_road', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tP = api.T(p.painAt), tF = api.T(p.firstAt), tB = api.T(p.blogAt), tD = api.T(p.docAt);
  const cx = L.cx, by = L.y(0.86), jy = L.y(0.52), lx = L.x(0.2), rx = L.x(0.8), ey = L.y(0.2), RW = 92 * k;
  const pl = `M${cx} ${jy} C${cx} ${jy - 110 * k} ${lx} ${jy - 90 * k} ${lx} ${ey}`, pr = `M${cx} ${jy} C${cx} ${jy - 110 * k} ${rx} ${jy - 90 * k} ${rx} ${ey}`;
  const road = (d, c, cls = '') => `<path class="${cls}" d="${d}" fill="none" stroke="${c}" stroke-width="${RW}" stroke-linecap="round"/>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      ${road(`M${cx} ${L.y1 + 120 * k} L${cx} ${jy}`, 'var(--c2)')}${road(pl, 'var(--c2)', 'fr-l')}${road(pr, 'var(--c2)')}
      ${road(pr, 'var(--c1)', 'fr-g')}
      <circle class="fr-p" cx="${cx}" cy="${by}" fill="none" stroke="var(--bad)" stroke-width="${16 * k}"/>
      <path class="fr-rp" d="${pr}" fill="none" stroke="none"/>
      <circle class="fr-m" r="${44 * k}" fill="var(--paper)" stroke="var(--ink)" stroke-width="${6 * k}"/></svg>` +
    api.at(lx, ey - 40 * k, `<svg width="${280 * k}" height="${280 * k}" viewBox="-70 -70 140 140"><circle r="58" fill="none" stroke="var(--c1x)" stroke-width="14"/><rect x="-20" y="-36" width="40" height="72" rx="8" fill="var(--c1x)"/><line x1="0" y1="36" x2="0" y2="64" stroke="var(--c1x)" stroke-width="9"/></svg>`, { cls: 'fr-a' }) +
    api.at(lx, ey - 40 * k, `<svg width="${330 * k}" height="${330 * k}" viewBox="-60 -60 120 120"><path d="M-44 -44 L44 44 M44 -44 L-44 44" stroke="var(--bad)" stroke-width="16" stroke-linecap="round"/></svg>`, { cls: 'fr-x' }) +
    api.at(rx, ey - 40 * k, `<div style="width:${270 * k}px;height:${270 * k}px;border-radius:50%;background:var(--paper);display:flex;align-items:center;justify-content:center;box-shadow:var(--sh)">${api.icon('ph-fill:stethoscope', 180 * k, 'var(--c2)')}</div>`, { cls: 'fr-d', idle: 'sway' }) +
    api.at(cx, L.y(0.68), R.tag(p.pain || '', 92 * k, 'bad'), { cls: 'fr-t1', idle: 'wobble' }) +
    api.at(cx, L.y(0.68), R.tag(p.first || '', 76 * k, ''), { cls: 'fr-t2', idle: 'sway' }) +
    api.at(lx + 70 * k, L.y(0.42), R.tag(p.blog || '', 62 * k, 'paper'), { cls: 'fr-t3', idle: 'sway' }) +
    api.at(cx, L.y(0.92), R.tag(p.doc || '', 104 * k, 'c1'), { cls: 'fr-t4', idle: 'wobble' });
  const m = q(root, '.fr-m'), rp = q(root, '.fr-rp'), g = q(root, '.fr-g'), l = q(root, '.fr-l'), ring = q(root, '.fr-p'), LEN = rp.getTotalLength();
  return t => {
    ring.setAttribute('r', ((80 + 22 * Math.abs(Math.sin(t * 7))) * k).toFixed(1)); ring.style.opacity = (0.35 + 0.65 * api.prog(t, tP - 0.05, tP + 0.1, 'lin')) * (1 - api.prog(t, tF, tF + 0.3, 'lin') * 0.7);
    const up = api.prog(t, tF, tF + 0.45, 'out'), run = api.prog(t, tD - 0.05, tD + 0.5, 'out');
    if (run > 0) { const pt = rp.getPointAtLength(LEN * run); m.setAttribute('cx', pt.x); m.setAttribute('cy', pt.y); } else { m.setAttribute('cx', cx); m.setAttribute('cy', by + (jy - by) * up); }
    R.draw(g, run); l.style.opacity = 1 - 0.65 * api.prog(t, tB + 0.2, tB + 0.45, 'lin');
    api.tw(q(root, '.fr-a .a'), t, api.K.pop(api.start + 0.1, 0.26, { o: 0, s: 0.3 }).concat([[tB + 0.25, {}], [tB + 0.45, { o: 0.4 }, 'lin']]));
    api.tw(q(root, '.fr-d .a'), t, api.K.pop(api.start + 0.18, 0.26, { o: 0, s: 0.3 }));
    api.tw(q(root, '.fr-x .a'), t, api.K.slam(tB + 0.2, 0.28));
    api.tw(q(root, '.fr-t1 .a'), t, api.K.pop(tP - 0.04, 0.24, { o: 0, s: 0.3 }).concat([[tF - 0.12, {}], [tF - 0.02, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.fr-t2 .a'), t, api.K.slam(tF - 0.02, 0.28).concat([[tB - 0.14, {}], [tB - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.fr-t3 .a'), t, api.K.pop(tB - 0.04, 0.24, { o: 0, s: 0.3, r: -5 }));
    api.tw(q(root, '.fr-t4 .a'), t, api.K.slam(tD - 0.03, 0.3));
  };
});
