/* @scene {"type":"burger_hopper","tags":["fast food","heavily processed","machine"],"layout":"burger-top-hopper-machine-cubes-belt-bottom","metaphor":"a burger stacks itself layer by layer, drops into a hopper and a stamping machine turns it into identical cubes on a belt","assets":["layered burger","hopper machine","gears","identical cubes on a belt"]} */
// {fast, fastAt, heavy, heavyAt}
RM.def('burger_hopper', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tF = api.T(p.fastAt), tH = api.T(p.heavyAt), tD = tH - 0.35;
  const cx = L.cx, bc = L.y(0.24), rim = L.y(0.38), MW = 640 * k, MH = 250 * k, my = L.y(0.66), belt = L.y(0.93), CS = 86 * k;
  const LY = [['M-200 40 H200 V70 Q200 96 170 96 H-170 Q-200 96 -200 70 Z', 'var(--acc)'], ['M-205 0 H205 V34 H-205 Z', 'var(--bad)'], ['M-215 -4 Q-160 -40 -105 -8 T5 -8 T115 -8 T215 -4 L215 -18 H-215 Z', 'var(--c1)'], ['M-190 -22 H190 L120 -2 L60 -22 Z', 'var(--acc2)'], ['M-200 -30 Q-200 -140 0 -140 Q200 -140 200 -30 Z', 'var(--acc)']];
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <g class="bh-bg">${LY.map(([d, c]) => `<path class="bh-l" d="${d}" fill="${c}"/>`).join('')}</g>
      <path d="M${cx - 300 * k} ${rim} L${cx + 300 * k} ${rim} L${cx + 130 * k} ${my - MH / 2} L${cx - 130 * k} ${my - MH / 2} Z" fill="var(--c2)"/>
      <path d="M${cx - 300 * k} ${rim} H${cx + 300 * k}" stroke="var(--c1x)" stroke-width="${12 * k}" stroke-linecap="round"/>
      <rect x="${cx - MW / 2}" y="${my - MH / 2}" width="${MW}" height="${MH}" rx="${24 * k}" fill="var(--c2)" stroke="var(--c1x)" stroke-width="${8 * k}"/>
      <line x1="${L.x0}" x2="${L.x1}" y1="${belt}" y2="${belt}" stroke="var(--c1l)" stroke-width="${16 * k}" stroke-linecap="round" class="bh-b" stroke-dasharray="${70 * k} ${30 * k}"/>
      ${Array.from({ length: 6 }, () => `<rect class="bh-c" width="${CS}" height="${CS}" rx="${10 * k}" fill="var(--paper)" stroke="var(--c1x)" stroke-width="${4 * k}"/>`).join('')}
      <rect class="bh-pn" x="${cx - 54 * k}" width="${108 * k}" y="${my + MH / 2 - 6 * k}" height="${50 * k}" rx="${8 * k}" fill="var(--c1x)"/></svg>` +
    api.at(cx - 225 * k, my, api.icon('ph-fill:gear', 150 * k, 'var(--c1x)'), { cls: 'bh-g' }) + api.at(cx + 225 * k, my, api.icon('ph-fill:gear', 150 * k, 'var(--c1x)'), { cls: 'bh-g' }) +
    api.at(cx, L.y(0.03), R.tag(p.fast || '', 80 * k, 'c1'), { cls: 'bh-t1', idle: 'sway' }) +
    api.at(cx, my, R.tag(p.heavy || '', 60 * k, ''), { cls: 'bh-t2', idle: 'wobble' });
  const ls = qa(root, '.bh-l'), gs = qa(root, '.bh-g'), cs = qa(root, '.bh-c');
  return t => {
    ls.forEach((e, i) => { const a = api.start + 0.1 + i * 0.24, u = api.prog(t, a, a + 0.32, 'out'); e.setAttribute('transform', `translate(0 ${(-(1 - u) * 300).toFixed(1)})`); e.style.opacity = u > 0 ? 1 : 0; });
    const dr = api.prog(t, tD, tD + 0.5, 'in');
    q(root, '.bh-bg').setAttribute('transform', `translate(${cx} ${(bc + dr * 400 * k).toFixed(1)}) rotate(${(5 * Math.sin(t * 3) * (1 - dr)).toFixed(2)}) scale(${(0.9 * k * (1 - 0.4 * dr)).toFixed(4)})`);
    const on = api.prog(t, tD + 0.3, tD + 0.5, 'lin');
    gs.forEach((e, i) => { q(e, '.i').style.transform = `rotate(${((i ? -1 : 1) * Math.max(0, t - tD) * 260 * on).toFixed(1)}deg)`; api.tw(q(e, '.a'), t, api.K.pop(api.start + 0.15, 0.3, { o: 0, s: 0.3 })); });
    const beat = 0.34, ph = (t - tD - 0.4) / beat, stamp = ph > 0 ? Math.abs(Math.sin(ph * Math.PI)) : 0;
    q(root, '.bh-pn').setAttribute('height', (44 * k + 40 * k * stamp).toFixed(1));
    q(root, '.bh-b').style.strokeDashoffset = (ph > 0 ? -(t - tD - 0.4) * 380 * k : 0).toFixed(1);
    cs.forEach((e, i) => { const a = tD + 0.5 + i * beat, u = t - a; if (u < 0) { e.style.opacity = 0; return; }
      const top = my + MH / 2 + 30 * k, ly = belt - 8 * k - CS, fall = Math.min(1, u / 0.14), slide = Math.max(0, u - 0.14) * 340 * k * (i % 2 ? 1 : -1), x = cx - CS / 2 + slide;
      e.setAttribute('x', x.toFixed(1)); e.setAttribute('y', (top + fall * (ly - top)).toFixed(1)); e.style.opacity = x < L.x0 - 20 || x + CS > L.x1 + 20 ? 0 : 1; });
    api.tw(q(root, '.bh-t1 .a'), t, api.K.pop(tF - 0.05, 0.35, { o: 0, s: 0.3, r: -5 }));
    api.tw(q(root, '.bh-t2 .a'), t, api.K.slam(tH - 0.05, 0.36));
  };
});
