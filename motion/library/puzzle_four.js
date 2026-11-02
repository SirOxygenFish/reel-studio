/* @scene {"type":"puzzle_four","tags":["several things at once","joints need"],"layout":"four-pieces-fly-from-corners-lock-into-square","metaphor":"four jigsaw pieces fly in from the corners and lock into one square at the same moment","assets":["four jigsaw pieces"]} */
// {need, needAt, once, onceAt}
RM.def('puzzle_four', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tN = api.T(p.needAt), tO = api.T(p.onceAt), s = 300 * k, b = 62 * k;
  const cx = L.cx, cy = L.y(0.5);
  // each piece: a square of side s with a tab on one shared edge and a socket on the other
  const tabH = (x, y, dir) => `L${x + s * 0.36} ${y} C${x + s * 0.3} ${y + dir * b * 1.2} ${x + s * 0.7} ${y + dir * b * 1.2} ${x + s * 0.64} ${y} `;
  const tabV = (x, y, dir) => `L${x} ${y + s * 0.36} C${x + dir * b * 1.2} ${y + s * 0.3} ${x + dir * b * 1.2} ${y + s * 0.7} ${x} ${y + s * 0.64} `;
  const back = (x, y, dir) => `L${x + s * 0.64} ${y} C${x + s * 0.7} ${y + dir * b * 1.2} ${x + s * 0.3} ${y + dir * b * 1.2} ${x + s * 0.36} ${y} `;
  const P = [
    { d: `M${-s} ${-s} L0 ${-s} ${tabV(0, -s, 1)}L0 0 ${back(-s, 0, -1)}L${-s} 0 Z`, c: 'var(--c1)', fx: -1, fy: -1 },
    { d: `M0 ${-s} L${s} ${-s} L${s} 0 ${back(0, 0, 1).replace(/^L[^ ]+ [^ ]+ /, `L${s * 0.64} 0 `)}L0 0 L0 ${-s * 0.36} C${b * 1.2} ${-s * 0.3} ${b * 1.2} ${-s * 0.7} 0 ${-s * 0.64} Z`, c: 'var(--acc)', fx: 1, fy: -1 },
    { d: `M${-s} 0 ${tabH(-s, 0, -1)}L0 0 L0 ${s * 0.36} C${-b * 1.2} ${s * 0.3} ${-b * 1.2} ${s * 0.7} 0 ${s * 0.64} L0 ${s} L${-s} ${s} Z`, c: 'var(--paper)', fx: -1, fy: 1 },
    { d: `M0 0 ${tabH(0, 0, 1)}L${s} 0 L${s} ${s} L0 ${s} L0 ${s * 0.64} C${-b * 1.2} ${s * 0.7} ${-b * 1.2} ${s * 0.3} 0 ${s * 0.36} Z`, c: 'var(--c1l)', fx: 1, fy: 1 }];
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">${P.map(x => `<path class="pf-p" d="${x.d}" fill="${x.c}" stroke="var(--bgDeep)" stroke-width="${7 * k}" stroke-linejoin="round"/>`).join('')}
      <circle class="pf-r" cx="${cx}" cy="${cy}" fill="none" stroke="var(--c1l)" stroke-width="${10 * k}"/></svg>` +
    api.at(cx, L.y(0.05), R.tag(p.need || '', 84 * k, 'c1'), { cls: 'pf-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.94), R.tag(p.once || '', 96 * k, ''), { cls: 'pf-t2', idle: 'wobble' });
  const ps = qa(root, '.pf-p'), ring = q(root, '.pf-r');
  return t => {
    const hit = Math.exp(-Math.max(0, t - tO - 0.1) * 6) * (t > tO + 0.1 ? 1 : 0);
    ps.forEach((e, i) => { const a = tN - 0.1 + i * 0.09, u = api.prog(t, a, Math.max(a + 0.3, tO + 0.08), 'in'), o = P[i], gap = (1 - u) * 300 * k;
      R.gx(e, { x: o.fx * gap, y: o.fy * gap * 1.2, r: (1 - u) * o.fx * 34, s: 1 + 0.05 * hit, o: t >= a ? 1 : 0 }, cx, cy); });
    ring.setAttribute('r', (330 * k + 340 * k * (1 - hit)).toFixed(1)); ring.style.opacity = (hit * 0.8).toFixed(3);
    api.tw(q(root, '.pf-t1 .a'), t, api.K.pop(tN - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.pf-t2 .a'), t, api.K.slam(tO - 0.03, 0.3));
  };
});
