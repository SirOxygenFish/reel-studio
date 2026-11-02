/* @scene {"type":"cliff_gap","tags":["knowing vs doing","gap","understanding","action"],"layout":"two-cliffs-split","metaphor":"understanding and doing are two cliffs that split apart, with a gap you have to jump","assets":["two cliffs","light bulb","hammer","gap with falling pebbles"]} */
// {splitAt, left:{label, at}, right:{label, at}}
RM.def('cliff_gap', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.splitAt), tL = api.T(p.left.at), tR = api.T(p.right.at);
  const CW = 520 * k, CH = 600 * k, cy = L.y(0.68);
  const cliff = (flip) => `<svg width="${CW}" height="${CH}" viewBox="0 0 520 560" overflow="visible" style="${flip ? 'transform:scaleX(-1)' : ''}">
      <path d="M0 40 H470 Q490 40 486 60 L440 200 L470 300 L420 420 L450 560 H0 Z" fill="var(--c1)"/>
      <path d="M0 40 H470 Q490 40 486 60 L478 84 H0 Z" fill="var(--acc)"/>
      <path d="M40 160 l60 20 M120 260 l80 -10 M60 380 l70 30 M220 200 l50 30 M280 330 l60 -20" stroke="var(--c2)" stroke-width="8" stroke-linecap="round" opacity=".5"/></svg>`;
  root.innerHTML =
    api.at(L.cx - CW / 2, cy, cliff(false), { cls: 'cg-l', content: false }) + api.at(L.cx + CW / 2, cy, cliff(true), { cls: 'cg-r', content: false }) +
    [0, 1, 2, 3].map(i => api.at(L.cx, cy - CH / 2 + 60 * k, `<div class="round" style="width:${(26 + i * 8) * k}px;height:${(26 + i * 8) * k}px;background:var(--c2)"></div>`, { cls: 'cg-pb' })).join('') +
    api.at(L.x(0.3), cy - CH / 2 - 90 * k, api.icon('ph:lightbulb', 260 * k, 'var(--c1)'), { cls: 'cg-bulb', idle: 'float' }) +
    api.at(L.x(0.7), cy - CH / 2 - 90 * k, api.icon('ph:hammer', 260 * k, 'var(--c2)'), { cls: 'cg-ham' }) +
    api.at(L.x(0.24), L.y(0.12), R.tag(p.left.label, 72 * k, 'c1'), { cls: 'cg-tl', idle: 'sway' }) +
    api.at(L.x(0.76), L.y(0.12), R.tag(p.right.label, 72 * k, ''), { cls: 'cg-tr', idle: 'sway' });
  return t => {
    const sp = api.prog(t, tS - 0.1, tS + 0.6, 'back');
    api.tw(q(root, '.cg-l .a'), t, [[api.start, { o: 0, y: 300 * k }], [api.start + 0.45, { o: 1, y: 0 }, 'back'], [tS - 0.1, {}], [tS + 0.6, { x: -120 * k }, 'back']]);
    api.tw(q(root, '.cg-r .a'), t, [[api.start, { o: 0, y: 300 * k }], [api.start + 0.45, { o: 1, y: 0 }, 'back'], [tS - 0.1, {}], [tS + 0.6, { x: 120 * k }, 'back']]);
    qa(root, '.cg-pb').forEach((e, i) => { const a = tS + 0.15 + i * 0.18, u = Math.max(0, t - a);
      api.tw(q(e, '.a'), t, [[a, { o: 0 }], [a + 0.02, { o: 1, x: (i - 1.5) * 30 * k }], [a + 1.2, { o: 0, y: 1200 * k, x: (i - 1.5) * 50 * k }, 'in']]); });
    const b = q(root, '.cg-bulb'), h = q(root, '.cg-ham');
    b.style.left = (L.x(0.3) - 120 * k * sp) + 'px'; h.style.left = (L.x(0.7) + 120 * k * sp) + 'px';
    api.tw(q(b, '.a'), t, api.K.spring(tL - 0.05, 0.6, { o: 0, s: 0.2 }));
    api.tw(q(h, '.a'), t, [[tR - 0.05, { o: 0, s: 0.2, r: -60 }], [tR + 0.35, { o: 1, s: 1, r: 20 }, 'back'], [tR + 0.55, { r: -25 }, 'io'], [tR + 0.75, { r: 15 }, 'io'], [tR + 0.95, { r: -10 }, 'io']]);
    api.tw(q(root, '.cg-tl .a'), t, api.K.pop(tL, 0.4, { o: 0, s: 0.3, r: -12 }));
    api.tw(q(root, '.cg-tr .a'), t, api.K.pop(tR, 0.4, { o: 0, s: 0.3, r: 12 }));
  };
});
