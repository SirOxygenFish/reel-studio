/* @scene {"type":"sweet_scale","tags":["balance","nothing about banning","sweets"],"layout":"beam-balance-center-ban-sign-dissolves","metaphor":"a beam balance tips to the cookie, a ban sign pops over the cookie and dissolves, then the beam settles level between the cookie and an orange","assets":["beam balance","cookie","orange","ban sign"]} */
// {ban, banAt, bal, balAt}
RM.def('sweet_scale', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tB = api.T(p.banAt), tA = api.T(p.balAt);
  const cx = L.cx, py = L.y(0.3), BL = 300 * k, gy = L.y(0.82), PL = 210 * k;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <path d="M${cx - 150 * k} ${gy} H${cx + 150 * k}" stroke="var(--c1l)" stroke-width="${26 * k}" stroke-linecap="round"/><rect x="${cx - 18 * k}" y="${py}" width="${36 * k}" height="${gy - py}" fill="var(--c1l)"/>
      <line class="ss-b" stroke="var(--paper)" stroke-width="${26 * k}" stroke-linecap="round"/><circle cx="${cx}" cy="${py}" r="${36 * k}" fill="var(--acc)"/>
      <path class="ss-pl" fill="none" stroke="var(--c1x)" stroke-width="${8 * k}" stroke-linejoin="round"/><path class="ss-pr" fill="none" stroke="var(--c1x)" stroke-width="${8 * k}" stroke-linejoin="round"/>
      <path class="ss-dl" fill="var(--c1x)"/><path class="ss-dr" fill="var(--c1x)"/></svg>` +
    api.at(0, 0, api.icon('ph-fill:cookie', 230 * k, 'var(--acc)'), { cls: 'ss-c' }) + api.at(0, 0, api.icon('ph-fill:orange', 210 * k, 'var(--acc2)'), { cls: 'ss-o' }) +
    api.at(0, 0, `<svg width="${320 * k}" height="${320 * k}" viewBox="-60 -60 120 120"><circle r="50" fill="none" stroke="var(--bad)" stroke-width="13"/><line x1="-35" y1="-35" x2="35" y2="35" stroke="var(--bad)" stroke-width="13"/></svg>`, { cls: 'ss-n' }) +
    api.at(cx, L.y(0.06), R.tag(p.ban || '', 66 * k, ''), { cls: 'ss-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.95), R.tag(p.bal || '', 104 * k, 'c1'), { cls: 'ss-t2', idle: 'wobble' });
  return t => {
    const lv = api.prog(t, tA - 0.15, tA + 0.5, 'spring'), ang = (-14 + 2 * Math.sin(t * 3)) * (1 - lv) * Math.PI / 180, s = Math.sin(ang), c = Math.cos(ang);
    const ax = cx - c * BL, ay = py - s * BL, bx = cx + c * BL, by = py + s * BL, b = q(root, '.ss-b');
    b.setAttribute('x1', ax); b.setAttribute('y1', ay); b.setAttribute('x2', bx); b.setAttribute('y2', by);
    [[ax, ay, '.ss-pl', '.ss-dl', '.ss-c'], [bx, by, '.ss-pr', '.ss-dr', '.ss-o']].forEach(([x, y, a, d, it]) => { const w = 150 * k, yp = y + PL;
      q(root, a).setAttribute('d', `M${x - w} ${yp} L${x} ${y} L${x + w} ${yp}`); q(root, d).setAttribute('d', `M${x - w - 20 * k} ${yp} H${x + w + 20 * k} Q${x} ${yp + 90 * k} ${x - w - 20 * k} ${yp} Z`);
      const e = q(root, it); e.style.left = x + 'px'; e.style.top = (yp - 100 * k) + 'px'; });
    api.tw(q(root, '.ss-c .a'), t, api.K.pop(api.start + 0.05, 0.3, { o: 0, s: 0.3 })); api.tw(q(root, '.ss-o .a'), t, api.K.pop(api.start + 0.15, 0.3, { o: 0, s: 0.3 }));
    const n = q(root, '.ss-n'); n.style.left = ax + 'px'; n.style.top = (ay + PL - 100 * k) + 'px';
    api.tw(q(n, '.a'), t, api.K.pop(tB - 0.05, 0.3, { o: 0, s: 0.4 }).concat([[tA - 0.4, {}], [tA - 0.1, { o: 0, s: 1.5 }, 'lin']]));
    api.tw(q(root, '.ss-t1 .a'), t, api.K.pop(tB - 0.05, 0.3, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.ss-t2 .a'), t, api.K.slam(tA - 0.05, 0.4));
  };
});
