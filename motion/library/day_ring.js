/* @scene {"type":"day_ring","tags":["time","what is missing","ask","listen"],"layout":"ring-center-question-card","metaphor":"a day drawn as a ring of 24 hour slices fills up; one slice stays empty and pulses: what is missing?","assets":["24-hour ring","empty pulsing slice","ear icon"]} */
// {ask, askAt, gapAt, listen, listenAt}
RM.def('day_ring', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tA = api.T(p.askAt ?? api.start), tG = api.T(p.gapAt), tL = p.listen ? api.T(p.listenAt) : 0;
  const D = 620 * k, gap = 17;
  const seg = i => { const a0 = (i / 24) * 6.283 - 1.571 + 0.02, a1 = ((i + 1) / 24) * 6.283 - 1.571 - 0.02, r0 = 90, r1 = 140;
    const P = (a, r) => `${(Math.cos(a) * r).toFixed(1)} ${(Math.sin(a) * r).toFixed(1)}`;
    return `M${P(a0, r0)} L${P(a0, r1)} A${r1} ${r1} 0 0 1 ${P(a1, r1)} L${P(a1, r0)} A${r0} ${r0} 0 0 0 ${P(a0, r0)} Z`; };
  root.innerHTML = api.at(L.cx, L.y(0.6), `<svg width="${D}" height="${D}" viewBox="-160 -160 320 320" overflow="visible">
        ${Array.from({ length: 24 }, (_, i) => `<path class="dr-s${i === gap ? ' dr-gap' : ''}" data-i="${i}" d="${seg(i)}" fill="${i === gap ? 'none' : ['var(--c1)', 'var(--c2)', 'var(--acc)', 'var(--c1l)'][i % 4]}" ${i === gap ? 'stroke="var(--bad)" stroke-width="5" stroke-dasharray="8 6"' : ''}/>`).join('')}</svg>`, { cls: 'dr-r' }) +
    api.at(L.cx, L.y(0.6), `<div style="font-size:0">${api.icon('ph:ear', 150 * k, 'var(--acc)')}</div>`, { cls: 'dr-ear' }) +
    api.at(L.cx, L.y(0.12), `<div class="card" style="width:${L.w * 0.94}px;padding:.35em .6em;text-align:center;font-family:var(--f-display);font-weight:900;font-size:${62 * k}px;line-height:1.1">${R.esc(p.ask || '')}</div>`, { cls: 'dr-q' }) +
    (p.listen ? api.at(L.cx, L.y(0.98), R.tag(p.listen, 66 * k, ''), { cls: 'dr-l', idle: 'sway' }) : '');
  return t => {
    qa(root, '.dr-s').forEach(s => { const i = +s.dataset.i, a = api.start + 0.1 + i * 0.05; s.style.opacity = t > a ? 1 : 0;
      if (s.classList.contains('dr-gap')) s.style.opacity = t > tG ? 0.6 + 0.4 * Math.sin(t * 7) : 0; });
    q(root, '.dr-r svg').style.transform = `rotate(${(4 * Math.sin(t * 0.9)).toFixed(2)}deg)`;
    api.tw(q(root, '.dr-q .a'), t, api.K.pop(tA - 0.05, 0.45, { o: 0, s: 0.4, y: -60 * k }));
    api.tw(q(root, '.dr-ear .a'), t, p.listen ? api.K.spring(tL - 0.05, 0.55, { o: 0, s: 0.2 }) : [[0, { o: 0 }]]);
    if (p.listen) api.tw(q(root, '.dr-l .a'), t, api.K.pop(tL, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
