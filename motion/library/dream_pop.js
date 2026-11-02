/* @scene {"type":"dream_pop","tags":["selling you a dream"],"layout":"big-soap-bubble-with-price-tag-bursts","metaphor":"a big shimmering bubble floats on a string with a price tag, then bursts into droplets, leaving only the tag","assets":["soap bubble","price tag"]} */
// {dream, dreamAt}
RM.def('dream_pop', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tD = api.T(p.dreamAt), cx = L.cx, cy = L.y(0.4), r = 310 * k, N = 16, tB = tD + 0.5;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <g class="dp2-b"><circle r="${r}" fill="var(--c1l)" fill-opacity=".16" stroke="var(--c1x)" stroke-width="${10 * k}"/><path d="M${-r * 0.6} ${-r * 0.35} A${r * 0.72} ${r * 0.72} 0 0 1 ${-r * 0.1} ${-r * 0.7}" fill="none" stroke="#fff" stroke-width="${18 * k}" stroke-linecap="round"/></g>
      ${Array.from({ length: N }, () => `<circle class="dp2-d" r="${16 * k}" fill="var(--c1x)"/>`).join('')}
      <line class="dp2-s" x1="${cx}" x2="${cx}" y2="${L.y(0.76)}" stroke="var(--paper)" stroke-width="${6 * k}"/></svg>` +
    api.at(cx, L.y(0.8), api.icon('ph-fill:tag', 170 * k, 'var(--acc)'), { cls: 'dp2-p', idle: 'sway' }) +
    api.at(cx, L.y(0.05), R.tag(p.dream || '', 84 * k, 'bad'), { cls: 'dp2-t1', idle: 'wobble' });
  const b = q(root, '.dp2-b'), ds = qa(root, '.dp2-d'), s = q(root, '.dp2-s');
  return t => {
    const inn = api.prog(t, api.start, api.start + 0.3, 'back'), on = t < tB; R.gx(b, { s: inn * (1 + 0.03 * Math.sin(t * 4)), o: on ? 1 : 0 }, cx, cy + 12 * k * Math.sin(t * 2)); s.setAttribute('y1', cy + r); s.style.opacity = on ? 1 : 1 - api.prog(t, tB, tB + 0.2, 'lin');
    ds.forEach((e, i) => { const u = api.clamp((t - tB) / 0.5, 0, 1), a = i / N * 2 * Math.PI; if (u <= 0 || u >= 1) { e.style.visibility = 'hidden'; return; } R.gx(e, { s: 1 - u * 0.7, o: 1 }, cx + Math.cos(a) * r * (1 + 0.6 * u), cy + Math.sin(a) * r * (1 + 0.6 * u) + 200 * k * u * u); });
    api.tw(q(root, '.dp2-p .a'), t, api.K.pop(api.start + 0.1, 0.26, { o: 0, s: 0.3 }));
    api.tw(q(root, '.dp2-t1 .a'), t, api.K.slam(tD - 0.03, 0.3));
  };
});
