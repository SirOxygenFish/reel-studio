/* @scene {"type":"shelf_search","tags":["magic pill","no pill","search"],"layout":"three-long-shelves-magnifier-sweeps","metaphor":"a big magnifying glass sweeps along bare shelves looking for the one pill and finds nothing","assets":["bare shelves","magnifying glass"]} */
// {magic, magicAt, no, noAt}
RM.def('shelf_search', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tM = api.T(p.magicAt), tN = api.T(p.noAt), ys = [0.3, 0.52, 0.74].map(L.y), r = 170 * k;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      ${ys.map((y, i) => `<g class="ss2-s"><rect x="${L.x0 - 60}" y="${y}" width="${L.w + 120}" height="${26 * k}" rx="${10 * k}" fill="var(--c1l)"/>${[0.12, 0.88].map(u => `<rect x="${L.x(u) - 14 * k}" y="${y + 24 * k}" width="${28 * k}" height="${60 * k}" fill="var(--c2)"/>`).join('')}</g>`).join('')}
      <g class="ss2-g"><line x1="${r * 0.72}" y1="${r * 0.72}" x2="${r * 1.7}" y2="${r * 1.7}" stroke="var(--acc)" stroke-width="${48 * k}" stroke-linecap="round"/>
        <circle r="${r}" fill="var(--paper)" fill-opacity=".14" stroke="var(--acc)" stroke-width="${30 * k}"/><path d="M${-r * 0.55} ${-r * 0.3} A${r * 0.62} ${r * 0.62} 0 0 1 ${-r * 0.1} ${-r * 0.6}" stroke="var(--paper)" stroke-width="${14 * k}" fill="none" stroke-linecap="round"/></g></svg>` +
    api.at(L.cx, L.y(0.06), R.tag(p.magic || '', 78 * k, 'c1'), { cls: 'ss2-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.91), R.tag(p.no || '', 160 * k, 'bad'), { cls: 'ss2-t2', idle: 'wobble' });
  const g = q(root, '.ss2-g');
  return t => {
    const u = api.clamp((t - api.start - 0.1) / (tN - api.start - 0.1), 0, 1), row = Math.min(2, Math.floor(u * 3)), f = u * 3 - row, dir = row % 2 ? -1 : 1, hit = t > tN ? Math.exp(-(t - tN) * 6) : 0;
    R.gx(g, { r: 10 * Math.sin(t * 30) * hit, s: 1 + 0.25 * api.prog(t, tN, tN + 0.2, 'back'), o: api.prog(t, api.start, api.start + 0.12, 'lin') }, L.cx + dir * (f - 0.5) * L.w * 0.72, ys[row] - 70 * k);
    api.tw(q(root, '.ss2-t1 .a'), t, api.K.pop(tM - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.ss2-t2 .a'), t, api.K.slam(tN - 0.03, 0.3));
  };
});
