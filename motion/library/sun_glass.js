/* @scene {"type":"sun_glass","tags":["water","drink enough","during the day","not only when you remember"],"layout":"sky-arc-top-tall-glass-bottom","metaphor":"the sun crosses a dotted arc from morning to evening; each time it passes a point a drop falls into a tall glass that fills up through the day","assets":["sun on a dotted arc","falling drops","tall glass"]} */
// {day, dayAt, not, notAt}
RM.def('sun_glass', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tD = api.T(p.dayAt), tN = api.T(p.notAt), T0 = api.start + 0.15, T1 = api.end - 0.15;
  const ax = u => L.x(0.08) + (L.x(0.92) - L.x(0.08)) * u, ay = u => L.y(0.42) - Math.sin(u * Math.PI) * L.y(0.42) * 0 - (L.y(0.42) - L.y(0.06)) * Math.sin(u * Math.PI);
  const gl = 300 * k, gh = 460 * k, gx = L.cx, gt = L.y(0.46), id = 'sg' + Math.round(api.start * 100), DU = [0.14, 0.32, 0.5, 0.68, 0.86];
  let arc = ''; for (let i = 0; i <= 40; i++) arc += `${i ? 'L' : 'M'}${ax(i / 40).toFixed(1)} ${ay(i / 40).toFixed(1)} `;
  const glass = `M${-gl / 2} 0 L${-gl * 0.4} ${gh} Q0 ${gh + 20 * k} ${gl * 0.4} ${gh} L${gl / 2} 0 Z`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <defs><clipPath id="${id}"><path d="${glass}"/></clipPath></defs>
      <path d="${arc}" fill="none" stroke="var(--c1l)" stroke-width="${10 * k}" stroke-dasharray="${6 * k} ${34 * k}" stroke-linecap="round"/>
      ${DU.map(() => `<path class="sg-dr" d="M0 ${-38 * k} C${26 * k} ${-4 * k} ${30 * k} ${24 * k} 0 ${30 * k} C${-30 * k} ${24 * k} ${-26 * k} ${-4 * k} 0 ${-38 * k} Z" fill="var(--c1l)"/>`).join('')}
      <g transform="translate(${gx} ${gt})"><g clip-path="url(#${id})"><path class="sg-w" fill="var(--c1)"/></g><path d="${glass}" fill="none" stroke="var(--paper)" stroke-width="${12 * k}" stroke-linejoin="round"/></g></svg>` +
    api.at(0, 0, api.icon('ph-fill:sun', 190 * k, 'var(--acc)'), { cls: 'sg-s' }) +
    api.at(L.cx, L.y(0.33), R.tag(p.day || '', 76 * k, ''), { cls: 'sg-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.93), R.tag(p.not || '', 70 * k, 'c1'), { cls: 'sg-t2', idle: 'wobble' });
  const ds = qa(root, '.sg-dr'), w = q(root, '.sg-w'), s = q(root, '.sg-s');
  return t => {
    const u = Math.max(0, Math.min(1, (t - T0) / (T1 - T0)));
    s.style.left = ax(u) + 'px'; s.style.top = ay(u) + 'px'; q(s, '.i').style.transform = `rotate(${(t * 70).toFixed(1)}deg)`;
    api.tw(q(s, '.a'), t, api.K.pop(api.start + 0.03, 0.24, { o: 0, s: 0.3 }));
    let fill = 0;
    DU.forEach((v, i) => { const a = T0 + v * (T1 - T0), f = (t - a) / 0.3, y0 = ay(v), y1 = gt + gh * 0.5;
      if (f <= 0 || f >= 1) ds[i].style.visibility = 'hidden'; else R.gx(ds[i], { s: 1, o: 1 }, ax(v) + (gx - ax(v)) * f, y0 + (y1 - y0) * f * f);
      fill += api.prog(t, a + 0.26, a + 0.5, 'back') / DU.length; });
    const lvl = gh * (1 - 0.9 * fill); let d = `M${-gl} ${gh + 40 * k}`; for (let x = -gl; x <= gl; x += 20 * k) d += ` L${x.toFixed(1)} ${(lvl + 11 * k * Math.sin(x / (46 * k) + t * 7)).toFixed(1)}`;
    w.setAttribute('d', d + ` L${gl} ${gh + 40 * k} Z`);
    api.tw(q(root, '.sg-t1 .a'), t, api.K.pop(tD - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.sg-t2 .a'), t, api.K.slam(tN - 0.03, 0.3));
  };
});
