/* @scene {"type":"energy_battery","tags":["energy","stress budget","spend","direction"],"layout":"battery-left-cable-to-path","metaphor":"everyone's battery of strength drains; the energy runs down a cable into a path that leads somewhere","assets":["battery with charge bars","glowing cable","winding path with flag"]} */
// {tag, tagAt, drainAt, spendAt, path, pathAt}
RM.def('energy_battery', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tT = api.T(p.tagAt), tD = api.T(p.drainAt), tS = api.T(p.spendAt), tP = api.T(p.pathAt);
  const BW = 400 * k, BH = 690 * k, bx = L.x(0.25), by = L.y(0.55);
  const bat = `<svg width="${BW}" height="${BH}" viewBox="0 0 300 520" overflow="visible">
      <rect x="105" y="0" width="90" height="40" rx="12" fill="var(--c2)"/><rect x="10" y="30" width="280" height="480" rx="44" fill="var(--paper)" stroke="var(--c2)" stroke-width="16"/>
      ${[0, 1, 2, 3, 4].map(i => `<rect class="eb-bar" data-i="${i}" x="42" y="${438 - i * 88}" width="216" height="70" rx="18" fill="${i < 2 ? 'var(--c1)' : 'var(--acc)'}"/>`).join('')}
      <path d="M170 140 L120 260 H165 L130 380 L215 230 H168 L205 140 Z" fill="var(--paper)" opacity=".85" class="eb-bolt"/></svg>`;
  const pathD = `M ${bx + 150 * k} ${by + 120 * k} C ${L.x(0.55)} ${by + 160 * k} ${L.x(0.45)} ${L.y(0.62)} ${L.x(0.62)} ${L.y(0.5)} S ${L.x(0.9)} ${L.y(0.36)} ${L.x(0.8)} ${L.y(0.18)}`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <path class="eb-road" d="${pathD}" fill="none" stroke="var(--c1l)" stroke-width="${110 * k}" stroke-linecap="round"/>
      <path class="eb-flow" d="${pathD}" fill="none" stroke="var(--acc)" stroke-width="${26 * k}" stroke-linecap="round" stroke-dasharray="${20 * k} ${26 * k}"/></svg>` +
    api.at(bx, by, bat, { cls: 'eb-b', idle: 'breathe' }) +
    api.at(L.x(0.8), L.y(0.1), `<svg width="${210 * k}" height="${240 * k}" viewBox="0 0 150 170"><path d="M20 165 V10" stroke="var(--c2)" stroke-width="12" stroke-linecap="round"/><path class="eb-fl" d="M26 14 Q80 -6 140 22 Q96 44 140 70 Q80 50 26 70 Z" fill="var(--acc)"/></svg>`, { cls: 'eb-flag' }) +
    api.at(bx, L.y(0.04), R.tag(p.tag || '', 80 * k, 'c1'), { cls: 'eb-t', idle: 'sway' }) +
    api.at(L.x(0.66), L.y(0.86), R.tag(p.path || '', 64 * k, ''), { cls: 'eb-p', idle: 'sway' });
  const bars = qa(root, '.eb-bar');
  return t => {
    api.tw(q(root, '.eb-b .a'), t, api.K.spring(api.start, 0.6, { o: 0, s: 0.3, y: 200 * k }));
    const lvl = 5 - 3 * api.prog(t, tD, tP + 0.8, 'io');                  // 5 bars -> 2
    bars.forEach(b => { const i = +b.dataset.i, f = Math.max(0, Math.min(1, lvl - i)); b.style.opacity = f; b.setAttribute('transform', `translate(${(216 * (1 - f) / 2).toFixed(1)} 0)`); b.setAttribute('width', (216 * f).toFixed(1)); });
    q(root, '.eb-bolt').style.opacity = 0.5 + 0.4 * Math.sin(t * 6);
    const road = q(root, '.eb-road'), flow = q(root, '.eb-flow');
    R.draw(road, api.prog(t, tS - 0.2, tS + 0.7, 'io'));
    const fu = api.prog(t, tS + 0.2, tP + 0.4, 'io');
    flow.style.strokeDasharray = `${20 * k} ${26 * k}`; flow.style.strokeDashoffset = (-t * 300 * k).toFixed(1); flow.style.opacity = fu > 0.02 ? 1 : 0;
    const len = road.getTotalLength(); flow.style.clipPath = ''; flow.setAttribute('stroke-dasharray', `${20 * k} ${26 * k}`);
    flow.style.strokeDasharray = fu < 1 ? `${20 * k} ${26 * k}` : ''; flow.style.strokeWidth = (26 * k) + 'px';
    flow.style.visibility = fu > 0.02 ? 'visible' : 'hidden';
    api.tw(q(root, '.eb-flag .a'), t, api.K.drop(tP - 0.1, 0.45, -260 * k));
    q(root, '.eb-fl').setAttribute('transform', `skewY(${(5 * Math.sin(t * 5)).toFixed(2)})`);
    api.tw(q(root, '.eb-t .a'), t, api.K.pop(tT - 0.05, 0.4, { o: 0, s: 0.3, r: -10 }));
    api.tw(q(root, '.eb-p .a'), t, api.K.pop(tP - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
