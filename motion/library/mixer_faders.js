/* @scene {"type":"mixer_faders","tags":["more real food","less sugar","junk"],"layout":"two-tall-mixer-faders-side-by-side","metaphor":"a mixing desk with two big faders: one is pushed up for living food, the other is pulled down for sugar and junk","assets":["mixing desk","two faders","level lights"]} */
// {more, moreAt, less, lessAt, junk, junkAt}
RM.def('mixer_faders', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tM = api.T(p.moreAt), tL = api.T(p.lessAt), tJ = api.T(p.junkAt);
  const xs = [L.x(0.27), L.x(0.73)], y0 = L.y(0.16), y1 = L.y(0.7), H = y1 - y0, N = 13, KW = 280 * k, KH = 110 * k;
  const leds = x => Array.from({ length: N }, (_, i) => `<rect class="mf-l" x="${x - 150 * k}" y="${y1 - (i + 0.8) * H / N}" width="${300 * k}" height="${H / N * 0.56}" rx="${10 * k}"/>`).join('');
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <rect x="${L.x(0.02)}" y="${y0 - 40 * k}" width="${L.w * 0.96}" height="${H + 80 * k}" rx="${34 * k}" fill="var(--bgDeep)" stroke="var(--c2)" stroke-width="${8 * k}"/>
      ${xs.map(leds).join('')}
      ${xs.map(x => `<g class="mf-k"><rect x="${-KW / 2}" y="${-KH / 2}" width="${KW}" height="${KH}" rx="${18 * k}" fill="var(--paper)"/><rect x="${-KW / 2 + 24 * k}" y="${-7 * k}" width="${KW - 48 * k}" height="${14 * k}" fill="var(--ink)"/></g>`).join('')}</svg>` +
    api.at(xs[0], L.y(0.78), api.icon('ph-fill:carrot', 100 * k, 'var(--acc)'), { cls: 'mf-i' }) + api.at(xs[1], L.y(0.78), api.icon('ph-fill:cube', 100 * k, 'var(--paper)'), { cls: 'mf-i' }) +
    api.at(L.cx, L.y(0.05), R.tag(p.more || '', 76 * k, 'c1'), { cls: 'mf-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.05), R.tag(p.less || '', 84 * k, ''), { cls: 'mf-t2', idle: 'sway' }) +
    api.at(L.cx, L.y(0.93), R.tag(p.junk || '', 84 * k, 'bad'), { cls: 'mf-t3', idle: 'wobble' });
  const ks = qa(root, '.mf-k'), ls = qa(root, '.mf-l'), is = qa(root, '.mf-i');
  return t => {
    const a = 0.3 + 0.62 * api.prog(t, tM + 0.1, tM + 0.75, 'back'), b = 0.72 - 0.08 * 0 - 0.62 * api.prog(t, tL + 0.15, tJ + 0.5, 'out');
    [a, b].forEach((v, c) => { const y = y1 - v * H; R.gx(ks[c], { s: 1, o: 1 }, xs[c], y);
      for (let i = 0; i < N; i++) { const e = ls[c * N + i], on = (i + 0.5) / N < v + 0.03 * Math.sin(t * 16 + i); e.setAttribute('fill', on ? (c === 0 ? 'var(--c1)' : 'var(--acc)') : 'var(--c2)'); e.style.opacity = on ? 1 : 0.4; } });
    is.forEach((e, i) => api.tw(q(e, '.a'), t, api.K.pop(api.start + 0.08 + i * 0.08, 0.26, { o: 0, s: 0.3 })));
    api.tw(q(root, '.mf-t1 .a'), t, api.K.pop(tM - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }).concat([[tL - 0.14, {}], [tL - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.mf-t2 .a'), t, api.K.slam(tL - 0.03, 0.3));
    api.tw(q(root, '.mf-t3 .a'), t, api.K.slam(tJ - 0.03, 0.3));
  };
});
