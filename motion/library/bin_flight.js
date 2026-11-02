/* @scene {"type":"bin_flight","tags":["less sugar","junk","trash"],"layout":"round-bin-bottom-center-items-arc-from-both-sides","metaphor":"sugar cubes and crumpled wrappers fly in arcs from both sides into a big bin; the lid claps shut on the last word","assets":["round bin","flip lid","crumpled wrappers","sugar cubes"]} */
// {less, lessAt, sugarAt, junk, junkAt, shutAt}
RM.def('bin_flight', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tL = api.T(p.lessAt), tS = api.T(p.sugarAt), tJ = api.T(p.junkAt), tC = api.T(p.shutAt);
  const bx = L.cx, top = L.y(0.5), BW = 460 * k, BH = 400 * k, CS = 92 * k, N = 8;
  const cube = `<rect x="${-CS / 2}" y="${-CS / 2}" width="${CS}" height="${CS}" rx="${12 * k}" fill="var(--paper)" stroke="var(--c1l)" stroke-width="${5 * k}"/>`;
  const wrap = `<path d="M${-60 * k} ${-30 * k} L${-20 * k} ${-58 * k} L${34 * k} ${-46 * k} L${62 * k} ${-8 * k} L${40 * k} ${48 * k} L${-16 * k} ${56 * k} L${-56 * k} ${26 * k} Z" fill="var(--acc)"/><path d="M${-34 * k} ${-14 * k} L${10 * k} ${8 * k} L${-6 * k} ${40 * k} M${10 * k} ${8 * k} L${40 * k} ${-16 * k}" stroke="var(--ink)" stroke-width="${6 * k}" fill="none" opacity=".45"/>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      ${Array.from({ length: N }, (_, i) => `<g class="bf-i">${i < 4 ? cube : wrap}</g>`).join('')}
      <path d="M${bx - BW / 2} ${top} L${bx + BW / 2} ${top} L${bx + BW * 0.4} ${top + BH} Q${bx} ${top + BH + 26 * k} ${bx - BW * 0.4} ${top + BH} Z" fill="var(--c2)" stroke="var(--c1l)" stroke-width="${10 * k}"/>
      ${[-0.22, 0, 0.22].map(u => `<line x1="${bx + BW * u}" x2="${bx + BW * u * 0.8}" y1="${top + 70 * k}" y2="${top + BH - 50 * k}" stroke="var(--c1l)" stroke-width="${12 * k}" stroke-linecap="round" opacity=".55"/>`).join('')}
      <g class="bf-l"><rect x="${-BW * 0.56}" y="${-20 * k}" width="${BW * 1.12}" height="${40 * k}" rx="${20 * k}" fill="var(--c1)"/><rect x="${-46 * k}" y="${-46 * k}" width="${92 * k}" height="${30 * k}" rx="${12 * k}" fill="var(--c1)"/></g></svg>` +
    api.at(L.cx, L.y(0.05), R.tag(p.less || '', 86 * k, 'c1'), { cls: 'bf-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.2), R.tag(p.junk || '', 86 * k, ''), { cls: 'bf-t2', idle: 'wobble' });
  const it = qa(root, '.bf-i'), lid = q(root, '.bf-l'), last = tS + 0.08 * 3 + 0.4 + (tC - tJ - 0.2);
  return t => {
    it.forEach((e, i) => { const a = (i < 4 ? tS - 0.05 + i * 0.1 : tJ - 0.2 + (i - 4) * 0.11), u = (t - a) / 0.44, sd = i % 2 ? 1 : -1;
      if (u <= 0 || u >= 1) { e.style.visibility = 'hidden'; return; }
      const sx = bx + sd * (L.w * 0.62), x = sx + (bx - sx) * u, y = L.y(0.42) + (top + 20 * k - L.y(0.42)) * u - Math.sin(u * Math.PI) * 260 * k;
      R.gx(e, { r: sd * u * 340, s: 1, o: 1 }, x, y); });
    const open = api.prog(t, api.start, api.start + 0.25, 'back') * (1 - api.prog(t, tC - 0.02, tC + 0.1, 'in'));
    R.gx(lid, { r: -46 * open, y: -open * 110 * k, s: 1, o: 1 }, bx - BW * 0.22 * open, top - 16 * k);
    api.tw(q(root, '.bf-t1 .a'), t, api.K.pop(tL - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.bf-t2 .a'), t, api.K.slam(tJ - 0.03, 0.3));
  };
});
