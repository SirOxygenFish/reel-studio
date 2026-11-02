/* @scene {"type":"crane_hook","tags":["strong muscles","take the load off","joints"],"layout":"crane-arm-from-top-right-weight-on-cushion","metaphor":"a heavy block squashes a small cushion; a crane hook lowers, grabs the block and hoists it away, and the cushion springs back","assets":["crane arm","hook and cable","heavy block","squashed cushion"]} */
// {strong, strongAt, take, takeAt, joint, jointAt}
RM.def('crane_hook', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tS = api.T(p.strongAt), tT = api.T(p.takeAt), tJ = api.T(p.jointAt);
  const cx = L.x(0.5), gy = L.y(0.82), BW = 330 * k, BH = 230 * k, CW = 340 * k, arm = L.y(0.14), cH = 110 * k;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <rect x="${L.x(0.88)}" y="${arm - 30 * k}" width="${70 * k}" height="${gy - arm + 700 * k}" fill="var(--c2)" stroke="var(--c1l)" stroke-width="${6 * k}"/>
      <path d="M${L.x0 - 200} ${arm + 20 * k} H${L.x(0.96)}" stroke="var(--acc)" stroke-width="${44 * k}"/>
      ${[0.1, 0.25, 0.4, 0.55, 0.7, 0.85].map(u => `<path d="M${L.x(u)} ${arm + 4 * k} l${40 * k} ${32 * k} l${40 * k} ${-32 * k}" stroke="var(--ink)" stroke-width="${8 * k}" fill="none"/>`).join('')}
      <line class="ch-c" x1="${cx}" x2="${cx}" y1="${arm + 40 * k}" stroke="var(--paper)" stroke-width="${14 * k}"/>
      <path d="M${L.x0 - 200} ${gy} H${L.x1 + 200} V2000 H${L.x0 - 200} Z" fill="var(--c2)" opacity=".6"/>
      <rect class="ch-cu" x="${cx - CW / 2}" width="${CW}" rx="${50 * k}" fill="var(--c1)"/>
      <g class="ch-b"><rect x="${-BW / 2}" y="${-BH}" width="${BW}" height="${BH}" rx="${20 * k}" fill="var(--paper)"/><rect x="${-BW * 0.32}" y="${-BH * 0.72}" width="${BW * 0.64}" height="${BH * 0.2}" rx="${10 * k}" fill="var(--c2)"/></g>
      <path class="ch-h" d="M${-34 * k} 0 a${34 * k} ${34 * k} 0 0 0 ${68 * k} 0" fill="none" stroke="var(--acc)" stroke-width="${18 * k}" stroke-linecap="round"/></svg>` +
    api.at(cx, L.y(0.26), R.tag(p.strong || '', 80 * k, 'c1'), { cls: 'ch-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.26), R.tag(p.take || '', 74 * k, ''), { cls: 'ch-t2', idle: 'wobble' }) +
    api.at(cx, L.y(0.93), R.tag(p.joint || '', 84 * k, 'paper'), { cls: 'ch-t3', idle: 'sway' });
  const b = q(root, '.ch-b'), cb = q(root, '.ch-c'), hk = q(root, '.ch-h'), cu = q(root, '.ch-cu');
  return t => {
    const down = api.prog(t, tS, tT - 0.05, 'out'), up = api.prog(t, tT, tT + 0.55, 'back'), inn = api.prog(t, api.start, api.start + 0.22, 'out');
    const squash = (1 - up), ch = cH * (0.34 + 0.66 * (1 - squash)) + (up ? 6 * k * Math.sin(t * 16) * (1 - api.prog(t, tT + 0.4, tT + 0.9, 'lin')) : 0);
    const by = gy - ch - up * (gy - L.y(0.6)) - (1 - inn) * 500 * k, hy = (by - BH - 6 * k) * down + (arm + 60 * k) * (1 - down);
    cu.setAttribute('y', (gy - ch).toFixed(1)); cu.setAttribute('height', (ch + 8 * k).toFixed(1));
    R.gx(b, { r: up ? 2 * Math.sin(t * 6) : 0, s: 1, o: 1 }, cx, by);
    cb.setAttribute('y2', hy.toFixed(1)); hk.setAttribute('transform', `translate(${cx} ${hy.toFixed(1)})`);
    api.tw(q(root, '.ch-t1 .a'), t, api.K.pop(tS - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }).concat([[tT - 0.14, {}], [tT - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.ch-t2 .a'), t, api.K.slam(tT - 0.03, 0.3));
    api.tw(q(root, '.ch-t3 .a'), t, api.K.pop(tJ - 0.04, 0.26, { o: 0, s: 0.3, r: 4 }));
  };
});
