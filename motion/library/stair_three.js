/* @scene {"type":"stair_three","tags":["walking","pool","strength training","movement"],"layout":"staircase-rising-left-to-right-marker-hops","metaphor":"a ball hops up a three-step staircase: each step slides in with its activity when she names it","assets":["three-step staircase","hopping ball"]} */
// {walk, walkAt, swim, swimAt, lift, liftAt}
RM.def('stair_three', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const ts = [api.T(p.walkAt), api.T(p.swimAt), api.T(p.liftAt)], SW = L.w * 0.34, base = L.y1 + 40 * k, sx = i => L.x0 + i * SW, top = i => L.y(0.72 - i * 0.24);
  const S = [['ph-fill:person-simple-walk', 'var(--c2)', p.walk, 'var(--paper)'], ['ph-fill:person-simple-swim', 'var(--c1)', p.swim, 'var(--ink)'], ['ph-fill:barbell', 'var(--acc)', p.lift, 'var(--ink)']];
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">${S.map((s, i) => `<rect class="st-s" x="${sx(i)}" y="${top(i)}" width="${SW}" height="${base - top(i) + 900 * k}" fill="${s[1]}"/>`).join('')}
      <circle class="st-b" r="${42 * k}" fill="var(--paper)" stroke="var(--ink)" stroke-width="${6 * k}"/></svg>` +
    S.map((s, i) => api.at(sx(i) + SW / 2, top(i) + 130 * k, api.icon(s[0], 170 * k, s[3]), { cls: 'st-i', idle: 'sway' })).join('') +
    S.map((s, i) => api.at(L.x(0.34 + i * 0.07), L.y(0.1 + (2 - i) * 0.0), R.tag(s[2] || '', i === 2 ? 72 * k : 96 * k, 'paper'), { cls: 'st-t', idle: 'sway' })).join('');
  const ss = qa(root, '.st-s'), is = qa(root, '.st-i'), tg = qa(root, '.st-t'), b = q(root, '.st-b');
  return t => {
    ss.forEach((e, i) => { const u = api.prog(t, ts[i] - 0.1, ts[i] + 0.14, 'back'); e.setAttribute('transform', `translate(0 ${((1 - u) * 1200 * k).toFixed(1)})`); });
    is.forEach((e, i) => api.tw(q(e, '.a'), t, api.K.spring(ts[i] + 0.05, 0.36)));
    tg.forEach((e, i) => { const n = ts[i + 1]; api.tw(q(e, '.a'), t, api.K.slam(ts[i] - 0.03, 0.26).concat(n ? [[n - 0.12, {}], [n - 0.03, { o: 0, s: 0.6 }, 'in']] : [])); });
    let i = 0; while (i < 2 && t >= ts[i + 1]) i++;
    const f = i > 0 ? api.prog(t, ts[i], ts[i] + 0.3, 'out') : 1, x0 = sx(Math.max(0, i - 1)) + SW * 0.82, x1 = sx(i) + SW * 0.82, y0 = top(Math.max(0, i - 1)) - 46 * k, y1 = top(i) - 46 * k;
    b.setAttribute('cx', (x0 + (x1 - x0) * f).toFixed(1)); b.setAttribute('cy', (y0 + (y1 - y0) * f - Math.sin(f * Math.PI) * 120 * k - 16 * k * Math.abs(Math.sin(t * 7))).toFixed(1));
    b.style.visibility = t >= ts[0] + 0.05 ? 'visible' : 'hidden';
  };
});
