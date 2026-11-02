/* @scene {"type":"glass_row","tags":["drink enough","during the day","not only when you remember"],"layout":"two-rows-of-three-small-glasses","metaphor":"six small glasses in two rows fill one after another through the day, not all at once","assets":["six small glasses"]} */
// {drink, drinkAt, day, dayAt, not, notAt}
RM.def('glass_row', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tD = api.T(p.drinkAt), tY = api.T(p.dayAt), tN = api.T(p.notAt), T0 = api.start + 0.2, T1 = api.end - 0.25, GW = 190 * k, GH = 270 * k, N = 6, id = 'gr' + Math.round(api.start * 100);
  const pos = i => [L.x(0.5) + ((i % 3) - 1) * 290 * k, L.y(0.2) + Math.floor(i / 3) * 340 * k], gl = `M${-GW / 2} 0 L${-GW * 0.38} ${GH} H${GW * 0.38} L${GW / 2} 0 Z`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><defs><clipPath id="${id}"><path d="${gl}"/></clipPath></defs>
      ${Array.from({ length: N }, (_, i) => { const [x, y] = pos(i); return `<g transform="translate(${x} ${y})"><g clip-path="url(#${id})"><rect class="gr2-w" x="${-GW}" width="${2 * GW}" y="${GH}" height="${GH}" fill="var(--c1)"/></g><path class="gr2-o" d="${gl}" fill="none" stroke="var(--c1l)" stroke-width="${9 * k}" stroke-linejoin="round"/></g>`; }).join('')}</svg>` +
    api.at(L.cx, L.y(0.05), R.tag(p.drink || '', 84 * k, 'c1'), { cls: 'gr2-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.96), R.tag(p.day || '', 84 * k, ''), { cls: 'gr2-t2', idle: 'sway' }) +
    api.at(L.cx, L.y(0.96), R.tag(p.not || '', 68 * k, 'paper'), { cls: 'gr2-t3', idle: 'wobble' });
  const ws = qa(root, '.gr2-w'), os = qa(root, '.gr2-o');
  return t => {
    ws.forEach((e, i) => { const a = T0 + i * (T1 - T0) / N, u = api.prog(t, a, a + (T1 - T0) / N, 'back'); e.setAttribute('y', (GH * (1 - 0.86 * u) + 5 * k * Math.sin(t * 9 + i) * (u > 0 ? 1 : 0)).toFixed(1)); os[i].setAttribute('stroke', u > 0.02 && u < 1 ? 'var(--paper)' : 'var(--c1l)'); });
    api.tw(q(root, '.gr2-t1 .a'), t, api.K.pop(tD - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.gr2-t2 .a'), t, api.K.pop(tY - 0.04, 0.26, { o: 0, s: 0.3 }).concat([[tN - 0.12, {}], [tN - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.gr2-t3 .a'), t, api.K.slam(tN - 0.03, 0.3));
  };
});
