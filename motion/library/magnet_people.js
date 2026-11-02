/* @scene {"type":"magnet_people","tags":["target audience","your people","don't chase everyone","attraction"],"layout":"scatter-crowd-magnet-top","metaphor":"a crowd of little figures runs in every direction; a magnet lifts out only the ones of your colour","assets":["horseshoe magnet","crowd of small figures","tip numeral"]} */
// {num, chaseAt, chase, pullAt, pull}
RM.def('magnet_people', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tC = api.T(p.chaseAt ?? api.start), tP = api.T(p.pullAt), N = 18, rnd = R.jit(7, N * 3);
  const fig = (c) => `<svg width="${105 * k}" height="${150 * k}" viewBox="-35 -50 70 100"><circle cx="0" cy="-30" r="16" fill="${c}"/><path d="M-22 40 Q-24 -8 0 -10 Q24 -8 22 40 Z" fill="${c}"/></svg>`;
  const mine = i => i % 4 === 0;
  root.innerHTML = Array.from({ length: N }, (_, i) => api.at(0, 0, fig(mine(i) ? 'var(--acc)' : 'var(--muted)'), { cls: 'mp-f' + (mine(i) ? ' mp-m' : '') })).join('') +
    api.at(L.cx, L.y(0.12), `<svg width="${300 * k}" height="${260 * k}" viewBox="-150 -40 300 260" overflow="visible">
        <path d="M-110 200 V60 A110 110 0 0 1 110 60 V200" fill="none" stroke="var(--bad)" stroke-width="64"/>
        <rect x="-142" y="170" width="64" height="50" fill="var(--paper)"/><rect x="78" y="170" width="64" height="50" fill="var(--paper)"/>
        <path class="mp-w" d="M-150 250 q 20 20 40 0 M110 250 q 20 20 40 0" stroke="var(--acc)" stroke-width="8" fill="none"/></svg>`, { cls: 'mp-mag', idle: 'sway' }) +
    api.at(L.x(0.12), L.y(0.08), `<div class="badge acc" style="font-size:${150 * k}px;font-family:var(--f-display);font-weight:900"><span style="font-size:.52em">${R.esc(p.num || '')}</span></div>`, { cls: 'mp-n' }) +
    api.at(L.x(0.5), L.y(0.98), R.tag(p.chase || '', 58 * k, 'bad'), { cls: 'mp-t1', idle: 'sway' }) +
    api.at(L.x(0.5), L.y(0.44), R.tag(p.pull || '', 66 * k, ''), { cls: 'mp-t2', idle: 'sway' });
  const fs = qa(root, '[class*="mp-f"]');
  const slots = [];                                                       // where "my people" line up under the magnet
  return t => {
    let m = 0;
    fs.forEach((f, i) => {
      const ox = L.x(0.08 + 0.84 * (rnd[i * 3] + 0.5)), oy = L.y(0.5 + 0.42 * (rnd[i * 3 + 1] + 0.5)), sp = 1.2 + rnd[i * 3 + 2];
      let x = ox + 90 * k * Math.sin(t * sp * 2 + i), y = oy + 40 * k * Math.cos(t * sp * 3 + i * 2);
      if (f.classList.contains('mp-m')) {
        const u = api.prog(t, tP + m * 0.08, tP + 0.6 + m * 0.08, 'back'), tx = L.cx + (m - 2) * 120 * k, ty = L.y(0.3);
        x += (tx - x) * u; y += (ty - y) * u; m++;
      }
      f.style.left = x.toFixed(1) + 'px'; f.style.top = y.toFixed(1) + 'px';
      api.tw(q(f, '.a'), t, api.K.pop(api.start + (i % 6) * 0.05, 0.35, { o: 0, s: 0.2 }));
      const run = q(f, '.i'); run.style.transform = `rotate(${(8 * Math.sin(t * 14 + i)).toFixed(1)}deg)`;
    });
    api.tw(q(root, '.mp-mag .a'), t, api.K.drop(tP - 0.3, 0.45, -300 * k));
    qa(root, '.mp-w').forEach(w => w.style.opacity = t > tP ? 0.5 + 0.5 * Math.sin(t * 12) : 0);
    api.tw(q(root, '.mp-n .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0 }));
    api.tw(q(root, '.mp-t1 .a'), t, api.K.pop(tC, 0.4, { o: 0, s: 0.3, r: 8 }).concat([[tP - 0.2, {}], [tP + 0.1, { o: 0.4 }, 'lin']]));
    api.tw(q(root, '.mp-t2 .a'), t, api.K.pop(tP + 0.3, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
