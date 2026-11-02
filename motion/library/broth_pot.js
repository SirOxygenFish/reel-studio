/* @scene {"type":"broth_pot","tags":["bone broth","fish with the skin on","chicken skin","food"],"layout":"big-pot-bottom-steam-items-rise-from-it","metaphor":"a big steaming pot: each food he names rises up out of the steam and floats above it","assets":["steaming pot","foods rising from the pot"]} */
// {broth, brothAt, fish, fishAt, chick, chickAt}
RM.def('broth_pot', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tB = api.T(p.brothAt), tF = api.T(p.fishAt), tC = api.T(p.chickAt), cx = L.cx, top = L.y(0.66), PW = 640 * k, PH = 280 * k;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      ${[-170, 0, 170].map(x => `<path class="bp-s" d="M${cx + x * k} ${top - 10 * k} c${-50 * k} ${-60 * k} ${50 * k} ${-110 * k} 0 ${-170 * k} c${-50 * k} ${-60 * k} ${50 * k} ${-110 * k} 0 ${-170 * k}" fill="none" stroke="var(--c1x)" stroke-width="${18 * k}" stroke-linecap="round" opacity=".55"/>`).join('')}
      <rect x="${cx - PW / 2}" y="${top}" width="${PW}" height="${PH}" rx="${40 * k}" fill="var(--c1)"/><rect x="${cx - PW / 2 - 30 * k}" y="${top - 20 * k}" width="${PW + 60 * k}" height="${44 * k}" rx="${22 * k}" fill="var(--c1l)"/>
      ${[-1, 1].map(s => `<rect x="${cx + s * (PW / 2 + 30 * k) - (s < 0 ? 70 * k : 0)}" y="${top + 60 * k}" width="${70 * k}" height="${34 * k}" rx="${17 * k}" fill="var(--c1l)"/>`).join('')}</svg>` +
    api.at(L.x(0.22), L.y(0.3), api.icon('ph-fill:bone', 220 * k, 'var(--paper)'), { cls: 'bp-i', idle: 'float' }) + api.at(L.x(0.52), L.y(0.2), api.icon('ph-fill:fish', 240 * k, 'var(--acc)'), { cls: 'bp-i', idle: 'sway' }) + api.at(L.x(0.8), L.y(0.3), api.icon('ph-fill:bird', 220 * k, 'var(--acc2)'), { cls: 'bp-i', idle: 'float' }) +
    api.at(cx, L.y(0.94), R.tag(p.broth || '', 92 * k, 'c1'), { cls: 'bp-t', idle: 'sway' }) + api.at(cx, L.y(0.94), R.tag(p.fish || '', 74 * k, ''), { cls: 'bp-t', idle: 'sway' }) + api.at(cx, L.y(0.94), R.tag(p.chick || '', 92 * k, 'paper'), { cls: 'bp-t', idle: 'sway' });
  const ss = qa(root, '.bp-s'), is = qa(root, '.bp-i'), tg = qa(root, '.bp-t'), T = [tB, tF, tC];
  return t => {
    ss.forEach((e, i) => { e.style.strokeDasharray = `${60 * k} ${40 * k}`; e.style.strokeDashoffset = (t * 240 * k + i * 30).toFixed(1); });
    is.forEach((e, i) => api.tw(q(e, '.a'), t, [[T[i] - 0.04, { o: 0, y: top - L.y(0.25), s: 0.4 }], [T[i] + 0.3, { o: 1, y: 0, s: 1 }, 'back']]));
    tg.forEach((e, i) => { const n = T[i + 1]; api.tw(q(e, '.a'), t, api.K.slam(T[i] - 0.03, 0.26).concat(n ? [[n - 0.12, {}], [n - 0.03, { o: 0, s: 0.6 }, 'in']] : [])); });
  };
});
