/* @scene {"type":"comfy_couch","tags":["shame","silence","comfort of others","status quo"],"layout":"corner-figure-left-sofa-right","metaphor":"you sit silent in the corner with a zipped mouth while the others lounge deeper into a comfy sofa","assets":["zipped-mouth figure","sofa with lounging figures"]} */
// {quietAt, quiet, theyAt, they}
RM.def('comfy_couch', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tQ = api.T(p.quietAt), tY = api.T(p.theyAt);
  const head = (c, mouth) => `<circle cx="0" cy="0" r="46" fill="var(--c1l)" stroke="var(--c2)" stroke-width="6"/><circle cx="-16" cy="-6" r="6" fill="var(--ink)"/><circle cx="16" cy="-6" r="6" fill="var(--ink)"/>${mouth}`;
  const zip = `<g class="cc-zip"><path d="M-22 20 H22" stroke="var(--ink)" stroke-width="7" stroke-linecap="round"/>${[-14, -4, 6, 16].map(x => `<path d="M${x} 14 v12" stroke="var(--ink)" stroke-width="4"/>`).join('')}</g>`;
  const me = `<svg width="${380 * k}" height="${530 * k}" viewBox="-110 -80 220 300" overflow="visible">
      <path d="M-70 210 Q-80 70 0 66 Q80 70 70 210 Z" fill="var(--muted)"/><g transform="translate(0 10)">${head('', zip)}</g>
      <path d="M-60 120 Q-90 170 -40 190 M60 120 Q90 170 40 190" stroke="var(--muted)" stroke-width="22" fill="none" stroke-linecap="round"/></svg>`;
  const lounger = (x, c) => `<g class="cc-p" transform="translate(${x} 0)"><path d="M-60 120 Q-60 30 0 26 Q60 30 60 120 Z" fill="${c}"/><g transform="translate(0 -30)">${head('', '<path d="M-18 16 Q0 32 18 16" stroke="var(--ink)" stroke-width="6" fill="none" stroke-linecap="round"/>')}</g>
      <path d="M-44 70 Q-110 60 -110 20" stroke="${c}" stroke-width="20" fill="none" stroke-linecap="round"/></g>`;
  const sofa = `<svg width="${760 * k}" height="${546 * k}" viewBox="-320 -170 640 460" overflow="visible">
      <rect x="-300" y="20" width="600" height="190" rx="50" fill="var(--c1)"/><rect x="-300" y="-40" width="600" height="120" rx="50" fill="var(--c2)"/>
      ${lounger(-170, 'var(--acc)')}${lounger(0, 'var(--bad)')}${lounger(170, 'var(--c1l)')}
      <rect x="-320" y="40" width="80" height="200" rx="34" fill="var(--c2)"/><rect x="240" y="40" width="80" height="200" rx="34" fill="var(--c2)"/>
      <rect x="-260" y="150" width="520" height="70" rx="24" fill="var(--c1)"/><path d="M-250 230 v50 M250 230 v50" stroke="var(--ink)" stroke-width="14"/></svg>`;
  root.innerHTML = api.at(L.x(0.16), L.y(0.66), me, { cls: 'cc-me' }) + api.at(L.x(0.64), L.y(0.62), sofa, { cls: 'cc-s' }) +
    api.at(L.x(0.22), L.y(0.36), R.tag(p.quiet || '', 62 * k, 'paper'), { cls: 'cc-t1', idle: 'sway' }) +
    api.at(L.x(0.62), L.y(0.08), R.tag(p.they || '', 72 * k, 'c1'), { cls: 'cc-t2', idle: 'sway' });
  const ps = qa(root, '.cc-p');
  return t => {
    api.tw(q(root, '.cc-s .a'), t, api.K.rise(api.start, 0.5, 260 * k));
    const shrink = api.prog(t, tQ - 0.1, tQ + 0.6, 'io');
    api.tw(q(root, '.cc-me .a'), t, api.K.pop(api.start + 0.1, 0.4, { o: 0, s: 0.3 }).concat([[tQ - 0.1, {}], [tQ + 0.6, { s: 0.82, x: -20 * k, y: 40 * k }, 'io']]));
    q(root, '.cc-zip').style.opacity = shrink > 0.3 ? 1 : 0;
    const sink = api.prog(t, tY - 0.1, tY + 0.8, 'io');
    ps.forEach((g, i) => g.setAttribute('transform', `translate(${(i - 1) * 170} ${(20 * sink + 4 * Math.sin(t * 2 + i)).toFixed(1)}) rotate(${((i - 1) * 6 * sink + 3 * Math.sin(t * 1.5 + i)).toFixed(1)})`));
    api.tw(q(root, '.cc-t1 .a'), t, api.K.pop(tQ, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.cc-t2 .a'), t, api.K.pop(tY, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
