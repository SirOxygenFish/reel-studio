/* @scene {"type":"quiet_exit","tags":["silent churn","after purchase","no follow up","customer leaves"],"layout":"shop-door-right-customer-walks","metaphor":"after the purchase nobody says a word; the customer fades and quietly walks out of the shop door","assets":["shop door with bell","shopping customer figure","fading footprints"]} */
// {buyAt, silentAt, silent}
RM.def('quiet_exit', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tB = api.T(p.buyAt ?? api.start), tS = api.T(p.silentAt);
  const DW = 330 * k, DH = 640 * k;
  const cust = `<svg width="${280 * k}" height="${504 * k}" viewBox="-60 -110 120 220" overflow="visible">
      <circle cx="0" cy="-78" r="28" fill="var(--c1l)" stroke="var(--c2)" stroke-width="5"/><path d="M-40 70 Q-44 -40 0 -44 Q44 -40 40 70 Z" fill="var(--c1)"/>
      <path class="qe-l1" d="M-14 70 L-18 108" stroke="var(--c2)" stroke-width="14" stroke-linecap="round"/><path class="qe-l2" d="M14 70 L18 108" stroke="var(--c2)" stroke-width="14" stroke-linecap="round"/>
      <g transform="translate(48 10)"><path d="M-20 -10 h40 l-6 50 h-28 z" fill="var(--acc)"/><path d="M-10 -10 q10 -22 20 0" stroke="var(--acc)" stroke-width="5" fill="none"/></g></svg>`;
  root.innerHTML = `<div style="position:absolute;left:${L.x0}px;top:${L.y(0.86)}px;width:${L.w}px;height:${20 * k}px;border-radius:${10 * k}px;background:var(--c2)"></div>` +
    api.at(L.x(0.8), L.y(0.86) - DH / 2, `<div style="position:relative;width:${DW + 40 * k}px;height:${DH + 20 * k}px">
        <div style="position:absolute;inset:0;border:${20 * k}px solid var(--c2);border-bottom:0;border-radius:${12 * k}px ${12 * k}px 0 0;background:var(--c1x)"></div>
        <div style="position:absolute;left:${20 * k}px;top:${20 * k}px;width:${DW}px;height:${DH}px;perspective:${1000 * k}px"><div class="qe-door" style="position:absolute;inset:0;background:var(--acc);transform-origin:100% 50%;border-radius:${6 * k}px">
          <div style="position:absolute;left:${30 * k}px;top:${40 * k}px;right:${30 * k}px;height:${200 * k}px;border-radius:${10 * k}px;background:var(--acc-soft)"></div></div></div>
        <div class="qe-bell" style="position:absolute;right:${-10 * k}px;top:${-50 * k}px">${api.icon('ph-fill:bell', 90 * k, 'var(--c1)')}</div></div>`, { cls: 'qe-d', content: false }) +
    api.at(L.x(0.25), L.y(0.86) - 250 * k, cust, { cls: 'qe-c' }) +
    [0, 1, 2, 3].map(i => api.at(0, 0, `<div style="width:${32 * k}px;height:${18 * k}px;border-radius:50%;background:var(--c1l)"></div>`, { cls: 'qe-fp', content: false })).join('') +
    api.at(L.x(0.3), L.y(0.2), `<div class="bubble" style="font-size:${80 * k}px;padding:.2em .6em;color:var(--muted)">…</div>`, { cls: 'qe-b' }) +
    api.at(L.cx, L.y(0.06), R.tag(p.silent || '', 66 * k, 'bad'), { cls: 'qe-t', idle: 'sway' });
  const c = q(root, '.qe-c'), x0 = L.x(0.25), x1 = L.x(0.8);
  return t => {
    const walk = api.prog(t, tS - 0.2, api.end - 0.15, 'io');
    c.style.left = (x0 + (x1 - x0) * walk) + 'px';
    api.tw(q(c, '.a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0.3 }).concat([[tS, { o: 1 }], [api.end - 0.1, { o: 0.15 }, 'lin']]));
    const st = Math.sin(t * 10) * (walk > 0 && walk < 1 ? 1 : 0);
    q(c, '.qe-l1').setAttribute('d', `M-14 70 L${(-14 - 12 * st).toFixed(1)} 108`); q(c, '.qe-l2').setAttribute('d', `M14 70 L${(14 + 12 * st).toFixed(1)} 108`);
    q(root, '.qe-door').style.transform = `rotateY(${(70 * api.prog(t, tS + 0.4, tS + 1.0, 'io')).toFixed(1)}deg)`;
    qa(root, '.qe-fp').forEach((f, i) => { const u = (i + 1) / 5; f.style.left = (x0 + (x1 - x0) * u) + 'px'; f.style.top = (L.y(0.86) - 6 * k) + 'px';
      f.style.opacity = walk > u ? Math.max(0, 1 - (walk - u) * 2.5) : 0; });
    api.tw(q(root, '.qe-b .a'), t, api.K.pop(tB + 0.2, 0.4, { o: 0, s: 0.3 }).concat([[tS, {}], [tS + 0.4, { o: 0, s: 0.6, y: -40 * k }, 'in']]));
    api.tw(q(root, '.qe-t .a'), t, api.K.pop(tS, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
