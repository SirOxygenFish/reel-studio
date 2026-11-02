/* @scene {"type":"garden_rise","tags":["food","real food","living food","garden"],"layout":"soil-band-bottom-stems-grow-up-sun-rises","metaphor":"stems shoot out of the soil one after another, each opens into real food, while a sun rises behind them","assets":["soil band","growing stems","rising sun"]} */
// {food, foodAt, more, moreAt, alive, aliveAt}
RM.def('garden_rise', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tF = api.T(p.foodAt), tM = api.T(p.moreAt), tA = api.T(p.aliveAt);
  const gy = L.y(0.8), P = [[0.14, 0.42, 'ph-fill:carrot', 'var(--acc)'], [0.38, 0.27, 'ph-fill:orange', 'var(--acc2)'], [0.62, 0.36, 'ph-fill:pepper', 'var(--bad)'], [0.86, 0.48, 'ph-fill:cherries', 'var(--c1)']];
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <circle class="gr-sun" cx="${L.cx}" r="${300 * k}" fill="var(--acc)" opacity=".28"/><circle class="gr-sun" cx="${L.cx}" r="${210 * k}" fill="var(--acc)" opacity=".5"/>
      ${P.map(([x, y]) => `<path class="gr-s" d="M${L.x(x)} ${gy + 20 * k} C${L.x(x) - 50 * k} ${(gy + L.y(y)) / 2} ${L.x(x) + 50 * k} ${(gy + L.y(y)) / 2} ${L.x(x)} ${L.y(y) + 90 * k}" fill="none" stroke="var(--c1l)" stroke-width="${18 * k}" stroke-linecap="round"/>`).join('')}
      <path d="M${L.x0 - 300} ${gy + 10 * k} Q${L.cx} ${gy - 50 * k} ${L.x1 + 300} ${gy + 10 * k} V2000 H${L.x0 - 300} Z" fill="var(--c2)"/></svg>` +
    P.map(([x, y, ic, c], i) => api.at(L.x(x), L.y(y), api.icon(ic, 250 * k, c), { cls: 'gr-i', idle: i % 2 ? 'sway' : 'float' })).join('') +
    api.at(L.cx, L.y(0.91), R.tag(p.food || '', 110 * k, ''), { cls: 'gr-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.91), R.tag(p.alive || '', 100 * k, 'c1'), { cls: 'gr-t2', idle: 'wobble' });
  const ss = qa(root, '.gr-s'), is = qa(root, '.gr-i'), suns = qa(root, '.gr-sun');
  return t => {
    const up = api.prog(t, api.start, tA + 0.3, 'out'); suns.forEach(e => e.setAttribute('cy', (gy + 80 * k - up * (gy - L.y(0.32))).toFixed(1)));
    ss.forEach((e, i) => { const a = tM - 0.2 + i * 0.26; R.draw(e, api.prog(t, a, a + 0.34, 'out')); api.tw(q(is[i], '.a'), t, api.K.spring(a + 0.26, 0.42)); });
    api.tw(q(root, '.gr-t1 .a'), t, api.K.pop(tF - 0.05, 0.26, { o: 0, s: 0.3, r: -4 }).concat([[tA - 0.14, {}], [tA - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.gr-t2 .a'), t, api.K.slam(tA - 0.03, 0.3));
  };
});
