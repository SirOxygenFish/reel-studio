/* @scene {"type":"excuse_mask","tags":["excuses","shame","fear","unmasking"],"layout":"big-face-center-mask","metaphor":"a calm paper mask carries the excuse; the question knocks it off and reveals a blushing, scared face underneath","assets":["paper mask on a stick","blushing face"]} */
// {rounds:[{excuse, at, truth, truthAt}]}
RM.def('excuse_mask', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const rs = p.rounds || [], ta = rs.map(r => api.T(r.at)), tt = rs.map(r => api.T(r.truthAt));
  const F = 560 * k, cx = L.cx, cy = L.y(0.5);
  const face = `<svg width="${F}" height="${F}" viewBox="-150 -150 300 300" overflow="visible">
      <circle r="140" fill="var(--c1l)" stroke="var(--c2)" stroke-width="10"/>
      <ellipse class="em-blush" cx="-74" cy="40" rx="34" ry="20" fill="var(--bad)" opacity="0"/><ellipse class="em-blush" cx="74" cy="40" rx="34" ry="20" fill="var(--bad)" opacity="0"/>
      <path d="M-60 -34 q14 -14 28 0 M32 -34 q14 -14 28 0" stroke="var(--ink)" stroke-width="9" fill="none" stroke-linecap="round"/>
      <ellipse cx="0" cy="62" rx="22" ry="14" fill="var(--ink)"/><path class="em-sweat" d="M108 -60 q12 22 0 34 q-12 -12 0 -34 Z" fill="var(--paper)" stroke="var(--c2)" stroke-width="4"/></svg>`;
  const mask = i => `<svg width="${F * 1.02}" height="${F * 1.25}" viewBox="-150 -150 300 370" overflow="visible">
      <path d="M0 150 V 216" stroke="var(--c2)" stroke-width="14" stroke-linecap="round"/>
      <ellipse rx="146" ry="150" fill="var(--paper)" stroke="var(--c2)" stroke-width="8"/>
      <path d="M-70 -30 q20 -16 40 0 M30 -30 q20 -16 40 0" stroke="var(--ink)" stroke-width="10" fill="none" stroke-linecap="round"/>
      <path d="M-60 50 Q0 100 60 50" stroke="var(--ink)" stroke-width="10" fill="none" stroke-linecap="round"/></svg>`;
  root.innerHTML = api.at(cx, cy, face, { cls: 'em-f', idle: 'wobble' }) +
    rs.map((r, i) => api.at(cx, cy + 50 * k, mask(i), { cls: 'em-m em-m' + i }) +
      api.at(cx, L.y(0.06), R.tag(r.excuse, 64 * k, 'paper'), { cls: 'em-x em-x' + i, idle: 'sway' }) +
      api.at(cx, L.y(0.95), R.tag(r.truth, 64 * k, 'bad'), { cls: 'em-tr em-tr' + i, idle: 'wobble' })).join('');
  return t => {
    api.tw(q(root, '.em-f .a'), t, api.K.spring(api.start, 0.6, { o: 0, s: 0.3 }));
    let blush = 0;
    rs.forEach((r, i) => {
      const next = i + 1 < rs.length ? ta[i + 1] : 1e9, d = i % 2 ? 1 : -1;
      api.tw(q(root, `.em-m${i} .a`), t, [[ta[i] - 0.15, { o: 0, y: 500 * k, r: d * 10 }], [ta[i] + 0.25, { o: 1, y: 0, r: 0 }, 'back'],
        [tt[i] - 0.05, {}], [tt[i] + 0.12, { r: d * -14, x: d * -30 * k }, 'out'], [tt[i] + 0.55, { r: d * 70, x: d * 700 * k, y: 300 * k, o: 0 }, 'in']]);
      api.tw(q(root, `.em-x${i} .a`), t, api.K.pop(ta[i], 0.4, { o: 0, s: 0.3, r: -8 }).concat([[tt[i], {}], [tt[i] + 0.3, { o: 0.35, s: 0.9 }, 'lin'], [next - 0.1, {}], [next, { o: 0 }, 'lin']]));
      api.tw(q(root, `.em-tr${i} .a`), t, api.K.slam(tt[i] + 0.1, 0.4).concat([[next - 0.2, {}], [next + 0.05, { o: 0 }, 'lin']]));
      if (t > tt[i] && t < next) blush = Math.max(blush, api.prog(t, tt[i], tt[i] + 0.4, 'out'));
    });
    qa(root, '.em-blush').forEach(b => b.setAttribute('opacity', (0.75 * blush).toFixed(2)));
    q(root, '.em-sweat').setAttribute('transform', `translate(0 ${(blush * 30 * ((t * 1.3) % 1)).toFixed(1)})`); q(root, '.em-sweat').style.opacity = blush;
  };
});
