/* @scene {"type":"hinge_oil","tags":["getting older","less of something","smooth movement","fluid"],"layout":"gauge-left-hinge-right","metaphor":"a reservoir gauge drains as the years tick up; then a drop of oil lets a hinge swing smoothly","assets":["reservoir gauge with drop","year ticker","door hinge","oil drop"]} */
// {older, olderAt, less, lessAt, smoothAt, smooth}
RM.def('hinge_oil', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tO = api.T(p.olderAt ?? api.start), tL = api.T(p.lessAt), tS = api.T(p.smoothAt);
  const GW = 260 * k, GH = 560 * k, gx = L.x(0.24), gy = L.y(0.56);
  root.innerHTML = api.at(gx, gy, `<div style="position:relative;width:${GW}px;height:${GH}px;border-radius:${GW / 2}px ${GW / 2}px ${40 * k}px ${40 * k}px;border:${12 * k}px solid var(--c2);overflow:hidden;background:var(--paper)">
        <div class="ho-lvl" style="position:absolute;left:0;right:0;bottom:0;height:85%;background:linear-gradient(180deg,var(--c1l),var(--c1))"></div>
        ${[0.25, 0.5, 0.75].map(u => `<div style="position:absolute;left:0;width:30%;top:${u * 100}%;height:${6 * k}px;background:var(--c2)"></div>`).join('')}</div>`, { cls: 'ho-g' }) +
    api.at(L.cx, L.y(0.06), R.tag(p.older || '', 64 * k, 'c1'), { cls: 'ho-yr', idle: 'sway' }) +
    api.at(L.x(0.7), L.y(0.5), `<svg width="${380 * k}" height="${520 * k}" viewBox="-100 -140 200 280" overflow="visible">
        <rect x="-16" y="-130" width="32" height="260" rx="14" fill="var(--c2)"/>
        <g class="ho-leaf"><rect x="10" y="-110" width="150" height="220" rx="14" fill="var(--c1)"/><ellipse cx="40" cy="-60" rx="12" ry="12" fill="var(--paper)"/><ellipse cx="40" cy="60" rx="12" ry="12" fill="var(--paper)"/></g>
        <rect x="-26" y="-120" width="52" height="60" rx="12" fill="var(--muted)"/><rect x="-26" y="60" width="52" height="60" rx="12" fill="var(--muted)"/>
        <path class="ho-drop" d="M0 -230 C -20 -200 -22 -184 0 -172 C 22 -184 20 -200 0 -230 Z" fill="var(--acc)"/></svg>`, { cls: 'ho-h' }) +
    api.at(gx, L.y(0.96), R.tag(p.less || '', 54 * k, ''), { cls: 'ho-t1', idle: 'sway' }) +
    api.at(L.x(0.7), L.y(0.96), R.tag(p.smooth || '', 58 * k, 'c1'), { cls: 'ho-t2', idle: 'wobble' });
  return t => {
    api.tw(q(root, '.ho-g .a'), t, api.K.rise(api.start, 0.45, 260 * k));
    q(root, '.ho-lvl').style.height = (85 - 55 * api.prog(t, tO, tL + 0.8, 'io')).toFixed(1) + '%';
    api.tw(q(root, '.ho-yr .a'), t, api.K.pop(tO, 0.35, { o: 0, s: 0.4 }));
    api.tw(q(root, '.ho-h .a'), t, api.K.spring(api.start + 0.2, 0.6, { o: 0, s: 0.3 }));
    const dropU = api.prog(t, tS - 0.6, tS - 0.1, 'in');
    q(root, '.ho-drop').setAttribute('transform', `translate(0 ${(220 * dropU).toFixed(1)})`); q(root, '.ho-drop').style.opacity = t > tS - 0.6 && t < tS ? 1 : 0;
    const stiff = t < tS ? 6 * Math.sin(t * 9) * Math.exp(-((t - api.start) % 1.4) * 3) : 0, smooth = t > tS ? 38 * Math.sin((t - tS) * 3.2) : 0;
    q(root, '.ho-leaf').setAttribute('transform', `scale(${Math.cos((stiff + smooth) / 57.3).toFixed(3)} 1)`);
    api.tw(q(root, '.ho-t1 .a'), t, api.K.pop(tL - 0.05, 0.4, { o: 0, s: 0.3, r: -6 }));
    api.tw(q(root, '.ho-t2 .a'), t, api.K.pop(tS, 0.4, { o: 0, s: 0.3, r: 6 }));
  };
});
