/* @scene {"type":"umbrella_shield","tags":["strong muscles","take the load off","joints"],"layout":"umbrella-center-over-small-ring-blocks-falling","metaphor":"heavy blocks rain down on a small ring; a big umbrella opens over it and the blocks slide off to the sides","assets":["big umbrella","falling blocks","small ring"]} */
// {strong, strongAt, take, takeAt, joint, jointAt}
RM.def('umbrella_shield', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.strongAt), tT = api.T(p.takeAt), tJ = api.T(p.jointAt), cx = L.cx, ry = L.y(0.76), uy = L.y(0.42), UW = 430 * k, N = 11, CS = 86 * k;
  const canopy = `M${-UW} 0 A${UW} ${UW * 0.82} 0 0 1 ${UW} 0 Q${UW * 0.66} ${-46 * k} ${UW / 3} 0 Q0 ${-46 * k} ${-UW / 3} 0 Q${-UW * 0.66} ${-46 * k} ${-UW} 0 Z`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <circle class="us-r" cx="${cx}" cy="${ry}" fill="none" stroke="var(--bad)" stroke-width="${16 * k}"/><circle cx="${cx}" cy="${ry}" r="${40 * k}" fill="var(--c1x)"/>
      ${Array.from({ length: N }, () => `<rect class="us-b" x="${-CS / 2}" y="${-CS / 2}" width="${CS}" height="${CS}" rx="${14 * k}" fill="var(--paper)"/>`).join('')}
      <line class="us-h" x1="${cx}" x2="${cx}" y1="${uy}" stroke="var(--c1l)" stroke-width="${16 * k}" stroke-linecap="round"/>
      <g class="us-u"><path d="${canopy}" fill="var(--acc)"/></g></svg>` +
    api.at(cx, L.y(0.05), R.tag(p.strong || '', 84 * k, 'c1'), { cls: 'us-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.05), R.tag(p.take || '', 74 * k, ''), { cls: 'us-t2', idle: 'wobble' }) +
    api.at(cx, L.y(0.95), R.tag(p.joint || '', 84 * k, 'paper'), { cls: 'us-t3', idle: 'sway' });
  const bs = qa(root, '.us-b'), u = q(root, '.us-u'), h = q(root, '.us-h'), r = q(root, '.us-r');
  return t => {
    const op = api.prog(t, tS + 0.05, tS + 0.45, 'back');
    R.gx(u, { s: Math.max(0.02, op), r: 2 * Math.sin(t * 2.4), o: op > 0 ? 1 : 0 }, cx, uy); h.setAttribute('y2', (uy + (ry - 60 * k - uy) * Math.min(1, op)).toFixed(1)); h.style.visibility = op > 0 ? 'visible' : 'hidden';
    r.setAttribute('r', ((70 + (t < tS + 0.4 ? 26 * Math.abs(Math.sin(t * 8)) : 0)) * k).toFixed(1)); r.setAttribute('stroke', t < tS + 0.4 ? 'var(--bad)' : 'var(--c1)');
    bs.forEach((e, i) => { const a = api.start + 0.05 + i * 0.26, f = t - a, sd = i % 2 ? 1 : -1, [j] = R.jit(i + 5, 1), x0 = cx + j * 240 * k, hitY = uy - UW * 0.6;
      if (f <= 0) { e.style.visibility = 'hidden'; return; }
      const sh = a + 0.3 > tS + 0.3, y0 = L.y(-0.12), v = (hitY - y0) / 0.3;
      if (!sh) { const yy = y0 + (ry - y0) * Math.min(1, f / 0.42); if (f > 0.44) { e.style.visibility = 'hidden'; return; } R.gx(e, { r: f * 200 * sd, s: 1, o: 1 }, cx + j * 60 * k, yy); return; }
      if (f < 0.3) { R.gx(e, { r: f * 160 * sd, s: 1, o: 1 }, x0, y0 + v * f); return; }
      const g = f - 0.3; if (g > 0.6) { e.style.visibility = 'hidden'; return; }
      R.gx(e, { r: sd * (50 + g * 120), s: 1, o: 1 }, x0 + sd * 900 * k * g, hitY + 300 * k * g + 1500 * k * g * g); });
    api.tw(q(root, '.us-t1 .a'), t, api.K.pop(tS - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }).concat([[tT - 0.12, {}], [tT - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.us-t2 .a'), t, api.K.slam(tT - 0.03, 0.3));
    api.tw(q(root, '.us-t3 .a'), t, api.K.pop(tJ - 0.04, 0.26, { o: 0, s: 0.3, r: 4 }));
  };
});
