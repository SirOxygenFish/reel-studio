/* @scene {"type":"compass_day","tags":["direction","hard day","purpose","where it leads"],"layout":"compass-center-horizon","metaphor":"a compass needle spins wildly, then settles and points at a sunrise on the horizon","assets":["compass","sunrise horizon"]} */
// {spinAt, pointAt, ask, askAt}
RM.def('compass_day', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tS = api.T(p.spinAt ?? api.start), tP = api.T(p.pointAt), tA = api.T(p.askAt ?? p.pointAt);
  const C = 680 * k, cx = L.cx, cy = L.y(0.62);
  const comp = `<svg width="${C}" height="${C}" viewBox="-150 -150 300 300" overflow="visible">
      <circle r="146" fill="var(--c2)"/><circle r="128" fill="var(--paper)"/>
      ${Array.from({ length: 36 }, (_, i) => { const a = i / 36 * 6.283, l = i % 9 === 0 ? 22 : 10; return `<path d="M${Math.sin(a) * 124} ${-Math.cos(a) * 124} L${Math.sin(a) * (124 - l)} ${-Math.cos(a) * (124 - l)}" stroke="var(--c2)" stroke-width="${i % 9 ? 3 : 6}"/>`; }).join('')}
      <g class="cd-n"><path d="M0 -104 L16 0 L-16 0 Z" fill="var(--bad)"/><path d="M0 104 L16 0 L-16 0 Z" fill="var(--muted)"/><circle r="14" fill="var(--c2)"/></g></svg>`;
  root.innerHTML = `<div class="cd-sky" style="position:absolute;left:${L.x0}px;top:${L.y0}px;width:${L.w}px;height:${L.h * 0.42}px;border-radius:${40 * k}px;overflow:hidden;background:linear-gradient(180deg,var(--c1x),var(--orb2))">
        <div class="cd-sun round" style="position:absolute;left:50%;width:${220 * k}px;height:${220 * k}px;margin-left:${-110 * k}px;background:radial-gradient(circle,var(--paper),var(--c1l));box-shadow:0 0 ${80 * k}px var(--c1l)"></div>
        <div style="position:absolute;left:0;right:0;bottom:0;height:${70 * k}px;background:var(--acc)"></div></div>` +
    api.at(cx, cy, comp, { cls: 'cd-c' }) +
    api.at(cx, L.y(0.97), R.tag(p.ask || '', 54 * k, 'c1'), { cls: 'cd-t', idle: 'sway' });
  const sun = q(root, '.cd-sun');
  return t => {
    api.tw(q(root, '.cd-c .a'), t, api.K.spring(api.start, 0.6, { o: 0, s: 0.3 }));
    // needle: spins fast, slows, then swings to north (the sunrise) with a damped wobble
    let a = t < tP ? (t - api.start) * 900 * Math.max(0.15, 1 - (t - tS) * 0.3) : 0;
    if (t >= tP) { const u = t - tP; a = 30 * Math.exp(-u * 4) * Math.cos(u * 14); }
    q(root, '.cd-n').setAttribute('transform', `rotate(${(a % 360).toFixed(1)})`);
    const rise = 0.25 + 0.75 * api.prog(t, tP, tP + 1.0, 'out');
    sun.style.top = ((L.h * 0.42) * (0.9 - 0.62 * rise)).toFixed(1) + 'px';
    q(root, '.cd-sky').style.opacity = api.prog(t, api.start, api.start + 0.4, 'out');
    api.tw(q(root, '.cd-t .a'), t, api.K.pop(tA - 0.05, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
