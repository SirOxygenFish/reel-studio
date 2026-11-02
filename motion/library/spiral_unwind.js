/* @scene {"type":"spiral_unwind","tags":["wasted years","going in circles","shortcut","hindsight"],"layout":"spiral-center-straightens","metaphor":"a road wound into a tight spiral with a little car going round and round; knowing earlier straightens it into one short road","assets":["spiral road","small car","straight road arrow"]} */
// {knewAt, saveAt, years, yearsAt, loop, loopAt}
RM.def('spiral_unwind', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tK = api.T(p.knewAt ?? api.start), tS = api.T(p.saveAt), tY = api.T(p.yearsAt ?? p.saveAt), tL = api.T(p.loopAt);
  const cx = L.cx, cy = L.y(0.5), turns = 4.2, N = 220;
  const pts = u => Array.from({ length: N + 1 }, (_, i) => {           // u: 0 spiral -> 1 straight line
    const f = i / N, a = f * turns * 6.283, r = (60 + 360 * f) * k;
    const sx = cx + Math.cos(a) * r, sy = cy + Math.sin(a) * r * 0.82;
    const lx = L.x(0.08) + f * L.w * 0.84, ly = cy + 220 * k - f * 420 * k;
    return [sx + (lx - sx) * u, sy + (ly - sy) * u];
  });
  const dOf = P => 'M' + P.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(' L');
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <path class="su-road" fill="none" stroke="var(--c2)" stroke-width="${44 * k}" stroke-linecap="round" stroke-linejoin="round"/>
      <path class="su-line" fill="none" stroke="var(--c1l)" stroke-width="${6 * k}" stroke-dasharray="${18 * k} ${14 * k}"/></svg>` +
    api.at(0, 0, `<div style="width:${90 * k}px;height:${54 * k}px;border-radius:${16 * k}px;background:var(--acc);box-shadow:var(--sh)"></div>`, { cls: 'su-car' }) +
    api.at(L.x(0.92), L.y(0.12), `<svg width="${150 * k}" height="${170 * k}" viewBox="0 0 150 170"><path d="M20 165 V10" stroke="var(--c2)" stroke-width="12" stroke-linecap="round"/><path d="M26 14 Q80 -6 140 22 Q96 44 140 70 Q80 50 26 70 Z" fill="var(--acc)"/></svg>`, { cls: 'su-flag' }) +
    api.at(L.cx, L.y(0.05), R.tag(p.years || '', 76 * k, 'good'), { cls: 'su-y', idle: 'sway' }) +
    api.at(L.cx, L.y(0.96), R.tag(p.loop || '', 64 * k, 'bad'), { cls: 'su-l', idle: 'sway' });
  const road = q(root, '.su-road'), line = q(root, '.su-line'), car = q(root, '.su-car');
  return t => {
    const u = api.prog(t, tS - 0.1, tS + 0.9, 'io'), P = pts(u), d = dOf(P);
    road.setAttribute('d', d); line.setAttribute('d', d);
    road.style.opacity = line.style.opacity = api.prog(t, api.start, api.start + 0.4, 'out');
    // the car circles the spiral (outside -> in, again and again); once straight it drives to the flag
    const f = u < 1 ? ((t - api.start) * 0.22) % 1 : Math.min(1, (t - tS - 0.9) * 0.9);
    const j = Math.min(N - 1, Math.floor((u < 1 ? 1 - f : f) * N)), a = P[j], b = P[Math.min(N, j + 1)];
    car.style.left = a[0].toFixed(1) + 'px'; car.style.top = a[1].toFixed(1) + 'px';
    q(car, '.m').style.transform = `rotate(${(Math.atan2(b[1] - a[1], b[0] - a[0]) * 57.3 + (u < 1 ? 180 : 0)).toFixed(1)}deg)`;
    api.tw(q(car, '.a'), t, api.K.pop(api.start + 0.2, 0.35, { o: 0, s: 0.3 }));
    api.tw(q(root, '.su-flag .a'), t, api.K.drop(tS + 0.5, 0.45, -260 * k));
    api.tw(q(root, '.su-y .a'), t, api.K.pop(tY - 0.05, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.su-l .a'), t, api.K.pop(tL - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
