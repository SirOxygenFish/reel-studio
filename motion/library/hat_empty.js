/* @scene {"type":"hat_empty","tags":["magic pill","no magic","trick"],"layout":"magician-hat-center-sparkles-rise-then-puff","metaphor":"a magician's hat shakes, sparkles rise as if something is coming, and only a small puff of smoke comes out","assets":["magician hat","sparkles","smoke puff"]} */
// {magic, magicAt, no, noAt}
RM.def('hat_empty', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tM = api.T(p.magicAt), tN = api.T(p.noAt);
  const cx = L.cx, by = L.y(0.82), HW = 300 * k, HH = 400 * k, S = 9, P = 6;
  const star = r => `M0 ${-r} L${r * 0.26} ${-r * 0.26} L${r} 0 L${r * 0.26} ${r * 0.26} L0 ${r} L${-r * 0.26} ${r * 0.26} L${-r} 0 L${-r * 0.26} ${-r * 0.26} Z`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      ${Array.from({ length: S }, (_, i) => `<path class="he-s" d="${star((22 + i % 3 * 16) * k)}" fill="${i % 2 ? 'var(--acc)' : 'var(--c1l)'}"/>`).join('')}
      ${Array.from({ length: P }, () => `<circle class="he-p" fill="var(--paper)"/>`).join('')}
      <g class="he-h"><path d="M${-HW} ${-HH} H${HW} L${HW * 0.88} 0 H${-HW * 0.88} Z" fill="var(--bgDeep)" stroke="var(--c1l)" stroke-width="${8 * k}"/>
        <path d="M${-HW * 0.94} ${-HH * 0.3} L${HW * 0.94} ${-HH * 0.3} L${HW * 0.9} ${-HH * 0.08} L${-HW * 0.9} ${-HH * 0.08} Z" fill="var(--acc)"/>
        <ellipse cy="0" rx="${HW * 1.5}" ry="${44 * k}" fill="var(--bgDeep)" stroke="var(--c1l)" stroke-width="${8 * k}"/>
        <ellipse cy="${-HH}" rx="${HW}" ry="${40 * k}" fill="#000" stroke="var(--c1l)" stroke-width="${8 * k}"/></g></svg>` +
    api.at(cx, L.y(0.05), R.tag(p.magic || '', 78 * k, 'c1'), { cls: 'he-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.24), R.tag(p.no || '', 160 * k, 'bad'), { cls: 'he-t2', idle: 'wobble' });
  const ss = qa(root, '.he-s'), ps = qa(root, '.he-p'), h = q(root, '.he-h'), mouth = by - HH;
  return t => {
    const inn = api.prog(t, api.start, api.start + 0.26, 'back'), shake = api.prog(t, tM, tM + 0.2, 'lin') * (1 - api.prog(t, tN, tN + 0.2, 'lin'));
    R.gx(h, { y: (1 - inn) * 700 * k + 6 * k * Math.sin(t * 40) * shake, r: 5 * Math.sin(t * 30) * shake, s: 1, o: 1 }, cx, by);
    ss.forEach((e, i) => { const a = tM + i * 0.13, u = (t - a) / 0.62; if (u <= 0 || u >= 1 || t > tN + 0.1) { e.style.visibility = 'hidden'; return; }
      const [j] = R.jit(i + 2, 1); R.gx(e, { r: u * 200, s: Math.sin(u * Math.PI) * 1.25, o: 1 }, cx + j * 520 * k * u, mouth - u * 340 * k); });
    ps.forEach((e, i) => { const u = api.prog(t, tN + i * 0.03, tN + 0.55 + i * 0.03, 'out'), [a, b] = R.jit(i + 9, 2);
      e.setAttribute('cx', (cx + a * 280 * k * u).toFixed(1)); e.setAttribute('cy', (mouth - 40 * k - (60 + 90 * (b + 0.5)) * k * u).toFixed(1));
      e.setAttribute('r', (Math.max(0.1, (30 + i * 9) * k * Math.sin(Math.min(1, u * 1.25) * 2))).toFixed(1)); e.style.opacity = u > 0 ? (0.85 * (1 - u * 0.75)).toFixed(3) : 0; });
    api.tw(q(root, '.he-t1 .a'), t, api.K.pop(tM - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.he-t2 .a'), t, api.K.slam(tN - 0.03, 0.3));
  };
});
