/* @scene {"type":"iceberg_skin","tags":["skin","the part you can see"],"layout":"iceberg-tip-above-water-huge-mass-below","metaphor":"an iceberg: only the small tip shows above the waterline, the camera dips and reveals the huge part below","assets":["iceberg","waterline"]} */
// {skin, skinAt, part, partAt}
RM.def('iceberg_skin', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tS = api.T(p.skinAt), tP = api.T(p.partAt), cx = L.cx, wy = L.y(0.3);
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <path class="ib-u" d="M${cx - 200 * k} ${wy} L${cx - 380 * k} ${wy + 180 * k} L${cx - 260 * k} ${wy + 420 * k} L${cx - 90 * k} ${wy + 640 * k} L${cx + 130 * k} ${wy + 560 * k} L${cx + 340 * k} ${wy + 300 * k} L${cx + 220 * k} ${wy} Z" fill="var(--c1)"/>
      <path class="ib-w" fill="var(--c2)" opacity=".55"/>
      <path d="M${cx - 200 * k} ${wy} L${cx - 90 * k} ${wy - 170 * k} L${cx + 10 * k} ${wy - 260 * k} L${cx + 120 * k} ${wy - 120 * k} L${cx + 220 * k} ${wy} Z" fill="var(--paper)"/></svg>` +
    api.at(L.x(0.2), wy - 110 * k, R.tag(p.skin || '', 84 * k, 'c1'), { cls: 'ib-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.94), R.tag(p.part || '', 84 * k, ''), { cls: 'ib-t2', idle: 'wobble' });
  const w = q(root, '.ib-w'), u = q(root, '.ib-u');
  return t => {
    let d = `M${L.x0 - 80} 2000`; for (let x = L.x0 - 80; x <= L.x1 + 80; x += 24) d += ` L${x} ${(wy + 12 * k * Math.sin(x / (70 * k) + t * 3)).toFixed(1)}`; w.setAttribute('d', d + ` L${L.x1 + 80} 2000 Z`);
    u.style.opacity = 0.25 + 0.75 * api.prog(t, tP - 0.3, tP + 0.2, 'out');
    api.tw(q(root, '.ib-t1 .a'), t, api.K.pop(tS - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.ib-t2 .a'), t, api.K.slam(tP - 0.03, 0.3));
  };
});
