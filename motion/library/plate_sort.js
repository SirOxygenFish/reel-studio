/* @scene {"type":"plate_sort","tags":["real food","less sugar","less junk","diet"],"layout":"top-down-plate-center-items-flicked-off","metaphor":"a top-down plate: real food lands on it while the sugar cube and the burger are flicked off the edge","assets":["top-down plate","food icons","sugar cube","burger"]} */
// {real, realAt, less, lessAt, sugarAt, junkAt}
RM.def('plate_sort', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tR = api.T(p.realAt), tL = api.T(p.lessAt), tS = api.T(p.sugarAt), tJ = api.T(p.junkAt);
  const cx = L.cx, cy = L.y(0.52), P = 350 * k;
  root.innerHTML = api.at(cx, cy, `<svg width="${P * 2.1}" height="${P * 2.1}" viewBox="-105 -105 210 210" style="overflow:visible"><circle r="100" fill="var(--paper)"/><circle r="76" fill="none" stroke="var(--c1x)" stroke-width="3"/></svg>`, { cls: 'pl-p' }) +
    api.at(cx - 190 * k, cy - 150 * k, api.icon('ph:carrot', 180 * k, 'var(--acc)'), { cls: 'pl-r' }) +
    api.at(cx + 40 * k, cy - 215 * k, api.icon('ph:orange', 180 * k, 'var(--acc)'), { cls: 'pl-r' }) +
    api.at(cx + 200 * k, cy - 60 * k, api.icon('ph:fish', 180 * k, 'var(--c2)'), { cls: 'pl-r' }) +
    api.at(cx - 215 * k, cy + 70 * k, api.icon('ph:leaf', 180 * k, 'var(--c1)'), { cls: 'pl-r' }) +
    api.at(cx + 110 * k, cy + 165 * k, api.icon('ph:avocado', 180 * k, 'var(--c1)'), { cls: 'pl-r' }) +
    api.at(cx - 80 * k, cy + 195 * k, api.icon('ph:egg', 180 * k, 'var(--c2)'), { cls: 'pl-r' }) +
    api.at(cx - 40 * k, cy + 10 * k, api.icon('ph-fill:hamburger', 210 * k, 'var(--bad)'), { cls: 'pl-j' }) +
    api.at(cx + 100 * k, cy + 30 * k, api.icon('ph-fill:cube', 130 * k, 'var(--c2)'), { cls: 'pl-s' }) +
    api.at(cx, L.y(0.05), R.tag(p.real || '', 86 * k, 'c1'), { cls: 'pl-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.96), R.tag(p.less || '', 78 * k, ''), { cls: 'pl-t2', idle: 'wobble' });
  return t => {
    const fl = (e, at, dir) => { const u = api.prog(t, at, at + 0.5, 'in'); q(e, '.i').style.transform = `translate(${(dir * L.w * 0.75 * u).toFixed(1)}px,${(-90 * k * Math.sin(u * 3.14)).toFixed(1)}px) rotate(${(dir * 200 * u).toFixed(1)}deg)`; e.style.opacity = 1 - api.prog(t, at + 0.3, at + 0.5, 'lin'); };
    api.tw(q(root, '.pl-p .a'), t, api.K.pop(api.start, 0.45, { o: 0, s: 0.4, r: -30 }));
    api.tw(q(root, '.pl-j .a'), t, api.K.pop(api.start + 0.2, 0.35, { o: 0, s: 0.2 }));
    api.tw(q(root, '.pl-s .a'), t, api.K.pop(api.start + 0.3, 0.35, { o: 0, s: 0.2 }));
    fl(q(root, '.pl-s'), tS, 1); fl(q(root, '.pl-j'), tJ, -1);
    qa(root, '.pl-r').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.drop(tR + i * 0.13, 0.4, -260 * k)));
    api.tw(q(root, '.pl-t1 .a'), t, api.K.pop(tR, 0.4, { o: 0, s: 0.3, r: -5 }));
    api.tw(q(root, '.pl-t2 .a'), t, api.K.pop(tL, 0.4, { o: 0, s: 0.3, r: 5 }));
  };
});
