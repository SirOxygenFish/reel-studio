/* @scene {"type":"mirror_same","tags":["nothing in the mirror","two weeks"],"layout":"oval-standing-mirror-center-days-tick-beside","metaphor":"an oval mirror with a plain face outline: days tick by on the side and the reflection does not change at all","assets":["standing oval mirror","tally ticks"]} */
// {nothing, nothingAt, mirrorAt}
RM.def('mirror_same', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tN = api.T(p.nothingAt), tM = api.T(p.mirrorAt), cx = L.x(0.42), cy = L.y(0.46), RX = 250 * k, RY = 350 * k, N = 14;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <g class="ms-m"><rect x="${-14 * k}" y="${RY}" width="${28 * k}" height="${150 * k}" fill="var(--c1l)"/><rect x="${-120 * k}" y="${RY + 140 * k}" width="${240 * k}" height="${24 * k}" rx="${12 * k}" fill="var(--c1l)"/>
      <ellipse rx="${RX}" ry="${RY}" fill="var(--c1x)" stroke="var(--acc)" stroke-width="${22 * k}"/>
      <path class="ms-s" d="M${-150 * k} ${-RY * 0.5} L${-20 * k} ${RY * 0.5}" stroke="#fff" stroke-width="${46 * k}" opacity=".6"/>
      <circle cy="${-70 * k}" r="${92 * k}" fill="var(--c2)"/><path d="M${-160 * k} ${250 * k} C${-150 * k} ${70 * k} ${150 * k} ${70 * k} ${160 * k} ${250 * k} Z" fill="var(--c2)"/></g>
      ${Array.from({ length: N }, (_, i) => `<rect class="ms-t" x="${L.x(0.8) + (i % 2) * 70 * k}" y="${L.y(0.16) + Math.floor(i / 2) * 84 * k}" width="${44 * k}" height="${54 * k}" rx="${10 * k}" fill="var(--acc)"/>`).join('')}</svg>` +
    api.at(L.cx, L.y(0.93), R.tag(p.nothing || '', 92 * k, 'c1'), { cls: 'ms-t1', idle: 'wobble' });
  const m = q(root, '.ms-m'), ts = qa(root, '.ms-t'), s = q(root, '.ms-s');
  return t => {
    R.gx(m, { y: (1 - api.prog(t, api.start, api.start + 0.3, 'back')) * 800 * k, r: 0, s: 1, o: 1 }, cx, cy);
    ts.forEach((e, i) => { e.style.opacity = t >= api.start + 0.2 + i * (api.end - api.start - 0.5) / N ? 1 : 0.12; });
    s.setAttribute('transform', `translate(${(((t - api.start) * 160) % 360 - 180) * k} 0)`);
    api.tw(q(root, '.ms-t1 .a'), t, api.K.slam(tN - 0.03, 0.3));
  };
});
