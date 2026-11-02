/* @scene {"type":"shadow_boxer","tags":["own fear","inner enemy","shame","losing to yourself"],"layout":"boxing-ring-side-view","metaphor":"in the boxing ring the opponent called 'the market' never moves; the boxer is knocked down by his own growing shadow","assets":["boxing ring ropes","boxer figure with gloves","growing shadow","idle opponent"]} */
// {smartAt, market, marketAt, shame, shameAt}
RM.def('shadow_boxer', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tS = api.T(p.smartAt ?? api.start), tM = api.T(p.marketAt), tH = api.T(p.shameAt);
  const fig = (c, glove) => `<svg width="${320 * k}" height="${535 * k}" viewBox="-80 -140 160 270" overflow="visible">
      <circle cx="0" cy="-100" r="32" fill="${c}"/><path d="M-36 120 L-26 -60 Q0 -72 26 -60 L36 120" fill="${c}"/>
      <path class="sb-arm" d="M20 -40 L70 -60" stroke="${c}" stroke-width="20" stroke-linecap="round"/><circle class="sb-gl" cx="76" cy="-62" r="${glove}" fill="var(--bad)"/></svg>`;
  root.innerHTML = `<svg style="position:absolute;left:${L.x0}px;top:${L.y0}px;overflow:visible" width="${L.w}" height="${L.h}" viewBox="0 0 ${L.w} ${L.h}">
      <path d="M0 ${L.h * 0.86} H${L.w}" stroke="var(--c2)" stroke-width="${30 * k}"/>
      ${[0.42, 0.56, 0.7].map(y => `<path d="M0 ${L.h * y} H${L.w}" stroke="var(--bad)" stroke-width="${10 * k}" opacity=".8"/>`).join('')}
      <rect x="${L.w * 0.02}" y="${L.h * 0.36}" width="${26 * k}" height="${L.h * 0.5}" fill="var(--c2)"/><rect x="${L.w * 0.98 - 26 * k}" y="${L.h * 0.36}" width="${26 * k}" height="${L.h * 0.5}" fill="var(--c2)"/></svg>` +
    api.at(L.x(0.38), L.y(0.56), `<div class="sb-sh" style="width:${330 * k}px;height:${540 * k}px;border-radius:${150 * k}px ${120 * k}px ${20 * k}px ${20 * k}px;background:var(--ink);opacity:.82;transform-origin:50% 100%"></div>`, { cls: 'sb-shp', content: false }) +
    api.at(L.x(0.3), L.y(0.66), fig('var(--acc)', 26), { cls: 'sb-b' }) +
    api.at(L.x(0.8), L.y(0.66), `<div style="transform:scaleX(-1)">${fig('var(--muted)', 26)}</div>`, { cls: 'sb-o' }) +
    api.at(L.x(0.8), L.y(0.3), R.tag(p.market || '', 62 * k, 'paper'), { cls: 'sb-t1', idle: 'sway' }) +
    api.at(L.x(0.38), L.y(0.12), R.tag(p.shame || '', 70 * k, 'bad'), { cls: 'sb-t2', idle: 'wobble' });
  return t => {
    const grow = api.prog(t, tM - 0.2, tH + 0.2, 'io'), hit = api.prog(t, tH, tH + 0.35, 'in');
    q(root, '.sb-sh').style.transform = `scale(${(0.9 + 1.0 * grow).toFixed(3)}) translateX(${(40 * grow).toFixed(1)}px)`;
    api.tw(q(root, '.sb-shp .a'), t, [[api.start, { o: 0 }], [api.start + 0.4, { o: 1 }]]);
    const bounce = 8 * k * Math.abs(Math.sin(t * 6));
    api.tw(q(root, '.sb-b .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0.3 }).concat([[tH, { r: 0 }], [tH + 0.35, { r: 80, x: 60 * k, y: 120 * k }, 'in'], [tH + 0.5, { r: 86 }, 'out']]));
    q(root, '.sb-b .i').style.transform = `translateY(${(t < tH ? -bounce : 0).toFixed(1)}px)`;
    api.tw(q(root, '.sb-o .a'), t, api.K.pop(api.start + 0.15, 0.4, { o: 0, s: 0.3 }));
    q(root, '.sb-o .i').style.transform = `translateY(${(-3 * k * Math.sin(t * 2)).toFixed(1)}px)`;
    api.tw(q(root, '.sb-t1 .a'), t, api.K.pop(tM - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
    api.tw(q(root, '.sb-t2 .a'), t, api.K.slam(tH - 0.05, 0.4));
  };
});
