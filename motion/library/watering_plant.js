/* @scene {"type":"watering_plant","tags":["follow up","care","relationship grows","three messages"],"layout":"pot-center-watering-can-cards-around","metaphor":"a purchase is a seedling; three waterings (day 3, week 2, month 1), each a short question, grow it into a fruit tree","assets":["flower pot","watering can","water drops","growing tree with fruit","leaf-shaped cards"]} */
// {three, threeAt, waters:[{when, msg, at}], stays, staysAt}
RM.def('watering_plant', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const ws = p.waters || [], tw = ws.map(w => api.T(w.at)), t3 = api.T(p.threeAt ?? api.start), tSt = p.stays ? api.T(p.staysAt) : 0;
  const px = L.x(0.5), py = L.y(0.86);
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <path class="wp-st" d="M${px} ${py - 120 * k} C ${px - 20 * k} ${py - 300 * k} ${px + 30 * k} ${py - 420 * k} ${px} ${py - 600 * k}" stroke="var(--good)" stroke-width="${26 * k}" fill="none" stroke-linecap="round"/>
      ${[[-1, 0.35], [1, 0.55], [-1, 0.75], [1, 0.9]].map(([d, u], i) => `<path class="wp-lf" data-i="${i}" d="M${px} ${py - 120 * k - 480 * k * u} q ${d * 140 * k} ${-60 * k} ${d * 220 * k} ${10 * k} q ${-d * 100 * k} ${70 * k} ${-d * 220 * k} ${-10 * k} Z" fill="var(--acc)"/>`).join('')}
      <circle class="wp-cr" cx="${px}" cy="${py - 640 * k}" r="${170 * k}" fill="var(--good)"/>
      ${[[-70, -660], [60, -700], [10, -590], [-20, -740]].map(([x, y], i) => `<circle class="wp-fr" cx="${px + x * k}" cy="${py + y * k}" r="${26 * k}" fill="var(--bad)"/>`).join('')}</svg>` +
    api.at(px, py, `<svg width="${300 * k}" height="${240 * k}" viewBox="0 0 150 120"><path d="M10 10 H140 L120 116 H30 Z" fill="var(--c1)"/><rect x="2" y="2" width="146" height="24" rx="8" fill="var(--c2)"/></svg>`, { cls: 'wp-pot' }) +
    api.at(L.x(0.78), L.y(0.36), `<svg width="${300 * k}" height="${200 * k}" viewBox="0 0 150 100" overflow="visible"><path d="M30 30 H110 V90 H30 Z" fill="var(--c2)"/><path d="M110 40 L150 10" stroke="var(--c2)" stroke-width="10" stroke-linecap="round"/><path d="M50 30 Q70 0 90 30" stroke="var(--c2)" stroke-width="8" fill="none"/></svg>`, { cls: 'wp-can' }) +
    Array.from({ length: 5 }, (_, i) => `<div class="wp-dr" style="position:absolute;width:${18 * k}px;height:${26 * k}px;border-radius:50% 50% 50% 50% / 60% 60% 40% 40%;background:var(--acc-soft);opacity:0"></div>`).join('') +
    ws.map((w, i) => api.at(L.x(i === 1 ? 0.76 : 0.24), L.y(0.2 + i * 0.22), `<div class="card" style="padding:.25em .6em .35em;border-radius:${40 * k}px ${8 * k}px ${40 * k}px ${8 * k}px;border-left:${14 * k}px solid var(--acc)">
        <div class="label" style="font-size:${32 * k}px;color:var(--muted)">${R.esc(w.when)}</div><div class="big" style="font-size:${54 * k}px;color:var(--ink)">${R.esc(w.msg)}</div></div>`, { cls: 'wp-c', idle: 'sway' })).join('') +
    api.at(L.x(0.26), L.y(0.04), `<div class="big" style="font-size:${100 * k}px;color:var(--c2)">${R.esc(p.three || '')}</div>`, { cls: 'wp-3' }) +
    (p.stays ? api.at(L.x(0.74), L.y(0.95), R.tag(p.stays, 60 * k, ''), { cls: 'wp-s', idle: 'wobble' }) : '');
  const st = q(root, '.wp-st'), lfs = qa(root, '.wp-lf'), cr = q(root, '.wp-cr'), frs = qa(root, '.wp-fr'), drs = qa(root, '.wp-dr');
  return t => {
    const g = Math.min(1, (tw.filter(x => t > x).length + api.prog(t, tw[0] ?? api.start, (tw[0] ?? api.start) + 0.01, 'lin') * 0) / Math.max(1, ws.length));
    const gs = ws.map((_, i) => api.prog(t, tw[i] + 0.2, tw[i] + 0.9, 'out')).reduce((a, b) => a + b, 0) / Math.max(1, ws.length);
    R.draw(st, 0.15 + 0.85 * gs);
    lfs.forEach((l, i) => { const u = api.prog(t, (tw[Math.min(i, ws.length - 1)] ?? 0) + 0.4, (tw[Math.min(i, ws.length - 1)] ?? 0) + 0.8, 'back'); l.style.opacity = u > 0.01 ? 1 : 0; l.style.transformOrigin = `${px}px ${py}px`; l.style.transform = `scale(${Math.max(0.01, u).toFixed(3)})`; });
    const last = tw[ws.length - 1] ?? 0, cu = api.prog(t, last + 0.5, last + 1.1, 'back');
    cr.setAttribute('r', (170 * k * cu).toFixed(1)); cr.style.opacity = cu > 0.01 ? 0.9 : 0;
    frs.forEach((f, i) => f.style.opacity = t > last + 0.9 + i * 0.1 ? 1 : 0);
    api.tw(q(root, '.wp-pot .a'), t, api.K.rise(api.start, 0.4, 200 * k));
    const pour = tw.some(x => t > x - 0.2 && t < x + 0.7);
    api.tw(q(root, '.wp-can .a'), t, [[t3 - 0.1, { o: 0, x: 200 * k }], [t3 + 0.3, { o: 1, x: 0 }, 'back']]);
    q(root, '.wp-can .i').style.transform = `rotate(${pour ? 28 : 0}deg)`;
    drs.forEach((d, i) => { const ph = ((t * 2.2) + i / 5) % 1, x0 = L.x(0.78) + 150 * k, y0 = L.y(0.36) - 20 * k;
      d.style.left = (x0 - 260 * k * ph) + 'px'; d.style.top = (y0 + 380 * k * ph * ph) + 'px'; d.style.opacity = pour ? 1 - ph * 0.6 : 0; });
    qa(root, '.wp-c').forEach((c, i) => api.tw(q(c, '.a'), t, api.K.pop(tw[i] + 0.05, 0.4, { o: 0, s: 0.3, r: i % 2 ? 6 : -6 })));
    api.tw(q(root, '.wp-3 .a'), t, api.K.slam(t3 - 0.05, 0.4));
    if (p.stays) api.tw(q(root, '.wp-s .a'), t, api.K.pop(tSt - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
