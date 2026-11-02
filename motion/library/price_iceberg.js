/* @scene {"type":"price_iceberg","tags":["price is the tip","hidden value","quality","trust"],"layout":"iceberg-waterline","metaphor":"price is only the tip of the iceberg above the water; quality, results and trust are the big part underneath","assets":["iceberg","waterline with waves","depth labels"]} */
// {tip, tipAt, below:[{label, at}], notOnly, notOnlyAt}
RM.def('price_iceberg', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tT = api.T(p.tipAt ?? api.start), bl = p.below || [], tb = bl.map(b => api.T(b.at)), tN = p.notOnly ? api.T(p.notOnlyAt) : 0;
  const wy = L.y(0.3), cx = L.cx;
  root.innerHTML = `<div class="ib-sea" style="position:absolute;left:${L.x0}px;top:${wy}px;width:${L.w}px;height:${L.y1 - wy + 20 * k}px;border-radius:${20 * k}px;background:linear-gradient(180deg,var(--acc),var(--c2))"></div>` +
    api.at(cx, wy + 300 * k, `<svg width="${760 * k}" height="${900 * k}" viewBox="-380 -300 760 900" overflow="visible">
        <path d="M-120 0 L-40 -260 L30 -200 L90 -280 L150 0 Z" fill="var(--paper)" stroke="var(--c2)" stroke-width="10" stroke-linejoin="round"/><path d="M-40 -260 L-20 -120 L30 -200 M90 -280 L70 -120" stroke="var(--acc-soft)" stroke-width="8" fill="none"/>
        <path d="M-150 0 L150 0 L330 260 L240 560 L-60 600 L-320 380 L-300 160 Z" fill="var(--acc-soft)" opacity=".85"/></svg>`, { cls: 'ib-ice', idle: 'float', amp: 0.6, content: false }) +
    `<svg class="ib-wave" style="position:absolute;left:${L.x0}px;top:${wy - 20 * k}px;overflow:visible" width="${L.w}" height="${40 * k}"><path fill="none" stroke="var(--paper)" stroke-width="${8 * k}" stroke-linecap="round"/></svg>` +
    api.at(cx + 10 * k, wy - 140 * k, R.tag(p.tip || '', 76 * k, 'bad'), { cls: 'ib-tip' }) +
    bl.map((b, i) => api.at(cx + (i % 2 ? 150 : -150) * k, wy + (170 + i * 190) * k, R.tag(b.label, 66 * k, 'paper'), { cls: 'ib-b', idle: 'sway' })).join('') +
    (p.notOnly ? api.at(L.x(0.75), L.y(0.06), R.tag(p.notOnly, 64 * k, 'c1'), { cls: 'ib-n', idle: 'wobble' }) : '');
  const wave = q(root, '.ib-wave path');
  return t => {
    let d = ''; for (let i = 0; i <= 40; i++) d += (i ? ' L' : 'M') + (L.w * i / 40).toFixed(1) + ' ' + (20 * k + 8 * k * Math.sin(i * 0.7 + t * 3)).toFixed(1); wave.setAttribute('d', d);
    api.tw(q(root, '.ib-ice .a'), t, [[api.start, { o: 0, y: 200 * k }], [api.start + 0.6, { o: 1, y: 0 }, 'back']]);
    api.tw(q(root, '.ib-tip .a'), t, api.K.pop(tT, 0.4, { o: 0, s: 0.3, r: -10 }));
    qa(root, '.ib-b').forEach((b, i) => api.tw(q(b, '.a'), t, api.K.rise(tb[i] - 0.05, 0.45, 140 * k)));
    if (p.notOnly) api.tw(q(root, '.ib-n .a'), t, api.K.slam(tN - 0.05, 0.4));
  };
});
