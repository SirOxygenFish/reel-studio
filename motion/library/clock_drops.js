/* @scene {"type":"clock_drops","tags":["drink","during the day","not only when you remember"],"layout":"big-clock-face-rim-of-drops-center","metaphor":"a big clock: the hand sweeps round and a ring of drops lights up hour by hour instead of one forgotten drop at the end","assets":["clock face","sweeping hand","ring of drops"]} */
// {drink, drinkAt, day, dayAt, not, notAt}
RM.def('clock_drops', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tD = api.T(p.drinkAt), tY = api.T(p.dayAt), tN = api.T(p.notAt), N = 12, cx = L.cx, cy = L.y(0.5), r = 340 * k;
  const drop = `<path d="M0 ${-40 * k} C${28 * k} ${-4 * k} ${32 * k} ${26 * k} 0 ${32 * k} C${-32 * k} ${26 * k} ${-28 * k} ${-4 * k} 0 ${-40 * k} Z"/>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <circle cx="${cx}" cy="${cy}" r="${r * 1.28}" fill="var(--bgDeep)" stroke="var(--c2)" stroke-width="${12 * k}"/>
      ${Array.from({ length: N }, (_, i) => { const a = i / N * 2 * Math.PI; return `<g class="cd-d" transform="translate(${cx + Math.sin(a) * r} ${cy - Math.cos(a) * r})">${drop}</g>`; }).join('')}
      <line class="cd-h" x1="${cx}" y1="${cy}" stroke="var(--acc)" stroke-width="${20 * k}" stroke-linecap="round"/><circle cx="${cx}" cy="${cy}" r="${30 * k}" fill="var(--acc)"/></svg>` +
    api.at(cx, L.y(0.05), R.tag(p.drink || '', 86 * k, 'c1'), { cls: 'cd-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.5), R.tag(p.day || '', 62 * k, 'paper'), { cls: 'cd-t2', idle: 'sway' }) +
    api.at(cx, L.y(0.95), R.tag(p.not || '', 66 * k, ''), { cls: 'cd-t3', idle: 'wobble' });
  const ds = qa(root, '.cd-d'), h = q(root, '.cd-h'), T0 = api.start + 0.1, T1 = api.end - 0.1;
  return t => {
    const u = api.clamp((t - T0) / (T1 - T0), 0, 1), a = u * 2 * Math.PI;
    h.setAttribute('x2', (cx + Math.sin(a) * r * 0.76).toFixed(1)); h.setAttribute('y2', (cy - Math.cos(a) * r * 0.76).toFixed(1));
    ds.forEach((e, i) => { const on = u * N >= i, age = (u * N - i) * (T1 - T0) / N, pop = on ? 1 + 0.5 * Math.exp(-age * 8) : 0.7; e.setAttribute('fill', on ? 'var(--c1)' : 'var(--c2)');
      const tr = e.getAttribute('transform').split(' scale')[0]; e.setAttribute('transform', `${tr} scale(${pop.toFixed(3)})`); });
    api.tw(q(root, '.cd-t1 .a'), t, api.K.pop(tD - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.cd-t2 .a'), t, api.K.pop(tY - 0.04, 0.26, { o: 0, s: 0.3 }).concat([[tN - 0.14, {}], [tN - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.cd-t3 .a'), t, api.K.slam(tN - 0.03, 0.3));
  };
});
