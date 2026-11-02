/* @scene {"type":"balloon_lift","tags":["strong muscles","take the load off","joints"],"layout":"block-on-coiled-spring-balloons-inflate-above","metaphor":"a heavy block squeezes a coiled spring; three balloons inflate on strings, lift the block and the spring stretches back out","assets":["coiled spring","heavy block","three balloons"]} */
// {strong, strongAt, take, takeAt, joint, jointAt}
RM.def('balloon_lift', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.strongAt), tT = api.T(p.takeAt), tJ = api.T(p.jointAt), cx = L.cx, gy = L.y(0.86), BW = 380 * k, BH = 190 * k, B = [[-230, -300, 'var(--c1)'], [0, -390, 'var(--acc)'], [230, -300, 'var(--c1l)']];
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <path d="M${L.x0 - 200} ${gy} H${L.x1 + 200}" stroke="var(--c1l)" stroke-width="${12 * k}"/>
      <path class="bl2-sp" fill="none" stroke="var(--c1)" stroke-width="${22 * k}" stroke-linecap="round" stroke-linejoin="round"/>
      ${B.map(() => `<line class="bl2-l" stroke="var(--paper)" stroke-width="${5 * k}"/><ellipse class="bl2-e"/>`).join('')}
      <g class="bl2-b"><rect x="${-BW / 2}" y="${-BH}" width="${BW}" height="${BH}" rx="${22 * k}" fill="var(--paper)"/><rect x="${-BW * 0.3}" y="${-BH * 0.68}" width="${BW * 0.6}" height="${BH * 0.24}" rx="${10 * k}" fill="var(--c2)"/></g></svg>` +
    api.at(cx, L.y(0.05), R.tag(p.strong || '', 84 * k, 'c1'), { cls: 'bl2-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.05), R.tag(p.take || '', 76 * k, ''), { cls: 'bl2-t2', idle: 'wobble' }) +
    api.at(cx, L.y(0.95), R.tag(p.joint || '', 88 * k, 'paper'), { cls: 'bl2-t3', idle: 'sway' });
  const sp = q(root, '.bl2-sp'), bk = q(root, '.bl2-b'), ls = qa(root, '.bl2-l'), es = qa(root, '.bl2-e');
  return t => {
    const inf = api.prog(t, tS + 0.05, tT + 0.1, 'out'), up = api.prog(t, tT, tT + 0.6, 'back'), h = 56 * k + 200 * k * up + (up ? 6 * k * Math.sin(t * 10) : 0), by = gy - h - (1 - api.prog(t, api.start, api.start + 0.22, 'out')) * 500 * k;
    let d = `M${cx} ${gy}`; const n = 10; for (let i = 1; i <= n; i++) d += ` L${cx + (i === n ? 0 : (i % 2 ? 1 : -1) * 110 * k)} ${(gy - h * i / n).toFixed(1)}`; sp.setAttribute('d', d);
    R.gx(bk, { r: up ? 1.5 * Math.sin(t * 5) : 0, s: 1, o: 1 }, cx, by);
    B.forEach(([dx, dy, c], i) => { const r = (40 + 110 * inf) * k, s = 0.3 + 0.7 * inf, x = cx + dx * k * s + 8 * k * Math.sin(t * 3 + i), y = by - BH + dy * k * s; es[i].setAttribute('cx', x.toFixed(1)); es[i].setAttribute('cy', y.toFixed(1)); es[i].setAttribute('rx', r.toFixed(1)); es[i].setAttribute('ry', (r * 1.2).toFixed(1)); es[i].setAttribute('fill', c);
      ls[i].setAttribute('x1', cx + dx * 0.3 * k); ls[i].setAttribute('y1', by - BH); ls[i].setAttribute('x2', x.toFixed(1)); ls[i].setAttribute('y2', (y + r * 1.2).toFixed(1));
      const vis = t >= tS ? 'visible' : 'hidden'; es[i].style.visibility = vis; ls[i].style.visibility = vis; });
    api.tw(q(root, '.bl2-t1 .a'), t, api.K.pop(tS - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }).concat([[tT - 0.12, {}], [tT - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.bl2-t2 .a'), t, api.K.slam(tT - 0.03, 0.3));
    api.tw(q(root, '.bl2-t3 .a'), t, api.K.pop(tJ - 0.04, 0.26, { o: 0, s: 0.3, r: 4 }));
  };
});
