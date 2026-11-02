/* @scene {"type":"week_grid","tags":["study","12 weeks","not two"],"layout":"three-by-four-grid-of-week-cells","metaphor":"twelve week cells fill one by one; the first two glow, the other ten keep going past them","assets":["twelve week cells"]} */
// {study, studyAt, twelve, twelveAt, two, twoAt}
RM.def('week_grid', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.studyAt), tW = api.T(p.twelveAt), tT = api.T(p.twoAt), N = 12, C = 3, S = 230 * k, Gp = 26 * k, x0 = L.cx - (C * S + (C - 1) * Gp) / 2, y0 = L.y(0.16);
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">${Array.from({ length: N }, (_, i) => `<rect class="wg-c" x="${x0 + (i % C) * (S + Gp)}" y="${y0 + Math.floor(i / C) * (S * 0.62 + Gp)}" width="${S}" height="${S * 0.62}" rx="${20 * k}"/>`).join('')}
      <rect class="wg-r" x="${x0 - 18 * k}" y="${y0 - 18 * k}" width="${2 * S + Gp + 36 * k}" height="${S * 0.62 + 36 * k}" rx="${30 * k}" fill="none" stroke="var(--acc)" stroke-width="${12 * k}"/></svg>` +
    api.at(L.cx, L.y(0.05), R.tag(p.study || '', 70 * k, 'c1'), { cls: 'wg-t0', idle: 'sway' }) +
    api.at(L.cx, L.y(0.93), R.tag(p.twelve || '', 110 * k, ''), { cls: 'wg-t1', idle: 'wobble' }) +
    api.at(L.x(0.56), L.y(0.3), R.tag(p.two || '', 100 * k, 'bad'), { cls: 'wg-t2', idle: 'wobble' });
  const cs = qa(root, '.wg-c'), r = q(root, '.wg-r');
  return t => {
    cs.forEach((e, i) => { const a = tS + i * (tW + 0.3 - tS) / N, on = t >= a; e.setAttribute('fill', on ? (i < 2 ? 'var(--acc)' : 'var(--c1)') : 'var(--c2)'); e.style.opacity = on ? 1 : 0.5; });
    r.style.opacity = t >= tT - 0.05 ? 0.6 + 0.4 * Math.sin(t * 9) : 0;
    api.tw(q(root, '.wg-t0 .a'), t, api.K.pop(tS - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.wg-t1 .a'), t, api.K.slam(tW - 0.03, 0.3));
    api.tw(q(root, '.wg-t2 .a'), t, api.K.slam(tT - 0.03, 0.3));
  };
});
