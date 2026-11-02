/* @scene {"type":"basket_bounce","tags":["more real food","less sugar","junk"],"layout":"wicker-basket-bottom-items-drop-from-top","metaphor":"real food drops into a wicker basket and stays; sugar cubes and wrappers hit the rim and bounce out of the frame","assets":["wicker basket","bouncing junk"]} */
// {more, moreAt, less, lessAt, junk, junkAt}
RM.def('basket_bounce', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tM = api.T(p.moreAt), tL = api.T(p.lessAt), tJ = api.T(p.junkAt), cx = L.cx, rim = L.y(0.56), BW = 640 * k, BH = 300 * k, CS = 90 * k;
  const F = [['ph-fill:carrot', 'var(--acc)', -190, 40, -18], ['ph-fill:orange', 'var(--acc2)', -60, -40, 8], ['ph-fill:pepper', 'var(--bad)', 80, -20, 14], ['ph-fill:fish', 'var(--c1l)', 200, 40, -10]], J = 5;
  const weave = Array.from({ length: 7 }, (_, i) => `<path d="M${cx - BW / 2 + 40 * k * (1 - i / 6) * 0 + i * BW / 6} ${rim} L${cx - BW * 0.4 + i * BW * 0.8 / 6} ${rim + BH}" stroke="var(--c1l)" stroke-width="${10 * k}" opacity=".6"/>`).join('');
  root.innerHTML = F.map(f => api.at(cx + f[2] * k, rim + f[3] * k - 40 * k, api.icon(f[0], 220 * k, f[1]), { cls: 'bb-f' })).join('') +
    `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <path d="M${cx - BW / 2} ${rim} H${cx + BW / 2} L${cx + BW * 0.4} ${rim + BH} H${cx - BW * 0.4} Z" fill="var(--c2)"/>${weave}
      <rect x="${cx - BW / 2 - 24 * k}" y="${rim - 22 * k}" width="${BW + 48 * k}" height="${44 * k}" rx="${22 * k}" fill="var(--c1)"/>
      ${Array.from({ length: J }, (_, i) => `<rect class="bb-j" x="${-CS / 2}" y="${-CS / 2}" width="${CS}" height="${CS}" rx="${12 * k}" fill="${i % 2 ? 'var(--acc)' : 'var(--paper)'}"/>`).join('')}</svg>` +
    api.at(cx, L.y(0.06), R.tag(p.more || '', 80 * k, 'c1'), { cls: 'bb-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.06), R.tag(p.less || '', 84 * k, ''), { cls: 'bb-t2', idle: 'sway' }) +
    api.at(cx, L.y(0.95), R.tag(p.junk || '', 84 * k, 'bad'), { cls: 'bb-t3', idle: 'wobble' });
  const fs = qa(root, '.bb-f'), js = qa(root, '.bb-j');
  return t => {
    fs.forEach((e, i) => api.tw(q(e, '.a'), t, api.K.drop(tM + i * 0.3, 0.42, -760 * k)));
    js.forEach((e, i) => { const a = (i < 2 ? tL + 0.1 + i * 0.3 : tJ - 0.05 + (i - 2) * 0.22), u = t - a, D = 0.3, sd = i % 2 ? 1 : -1, hx = cx + sd * (BW / 2 - 40 * k);
      if (u <= 0) { e.style.visibility = 'hidden'; return; }
      const y = u < D ? rim - (1 - (u / D) ** 2) * 760 * k - 40 * k : rim - 40 * k - 420 * k * (u - D) + 1400 * k * (u - D) ** 2, x = u < D ? hx : hx + sd * 900 * k * (u - D);
      if (y > L.y1 + 300) { e.style.visibility = 'hidden'; return; }
      R.gx(e, { r: sd * u * 360, s: 1, o: 1 }, x, y); });
    api.tw(q(root, '.bb-t1 .a'), t, api.K.pop(tM - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }).concat([[tL - 0.14, {}], [tL - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.bb-t2 .a'), t, api.K.slam(tL - 0.03, 0.3));
    api.tw(q(root, '.bb-t3 .a'), t, api.K.slam(tJ - 0.03, 0.3));
  };
});
