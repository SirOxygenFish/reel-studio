/* @scene {"type":"juggle_overload","tags":["overload","everything at once","calls","exhaustion"],"layout":"figure-center-orbit-objects","metaphor":"a person juggling more and more ringing phones until they all crash down","assets":["juggling figure (open peeps)","ringing phones"]} */
// {peep:{...}, addFrom, addTo, n, tag1, tag1At, dropAt, tag2, tag2At}
RM.def('juggle_overload', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tA = api.T(p.addFrom), tB = api.T(p.addTo), tD = api.T(p.dropAt), t1 = api.T(p.tag1At), t2 = api.T(p.tag2At ?? p.dropAt);
  const N = p.n || 8, cx = L.cx, cy = L.y(0.33), rx = 380 * k, ry = 230 * k;
  const peep = Object.assign({ body: 'Explaining', head: 'ShortTwo', faces: { Smile: 0 } }, p.peep || {});
  root.innerHTML = api.at(cx, L.y(0.7), api.peep(Object.assign({ size: 500 * k }, peep)), { cls: 'jo-fig' }) +
    Array.from({ length: N }, (_, i) => api.at(cx, cy, `<div class="badge ${i % 3 === 1 ? 'acc' : i % 3 ? 'paper' : 'c2'}" style="font-size:${150 * k}px">${api.icon('ph-fill:phone-call', 86 * k, i % 3 === 2 ? 'var(--c1)' : 'currentColor')}</div>`, { cls: 'jo-ph' })).join('') +
    api.at(cx, L.y(0.02), R.tag(p.tag1 || '', 72 * k, 'c1'), { cls: 'jo-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.02), R.tag(p.tag2 || '', 80 * k, 'bad'), { cls: 'jo-t2', idle: 'wobble' });
  const fig = q(root, '.jo-fig'), phs = qa(root, '.jo-ph');
  const appear = phs.map((_, i) => (i < 2 ? api.start + 0.15 * i : tA + (tB - tA) * (i - 2) / Math.max(1, N - 3)));
  return t => {
    api.tw(q(fig, '.a'), t, api.K.rise(api.start, 0.45, 300 * k).concat([[tD, {}], [tD + 0.4, { y: 40 * k, s: 0.96 }, 'out']]));
    api.peepUpdate(fig, t, peep, [[api.start, tD]]);
    const n = phs.filter((_, i) => t >= appear[i]).length, speed = 2.2 + 0.55 * n;
    phs.forEach((ph, i) => {
      const a = t * speed + i * 6.283 / Math.max(1, n), fall = Math.max(0, t - tD - i * 0.04);
      let x = cx + rx * Math.cos(a), y = cy + ry * Math.sin(a) - 40 * k * Math.abs(Math.sin(a * 2));
      if (fall > 0) { x += (i % 2 ? 1 : -1) * (120 + i * 30) * k * fall; y += 1900 * k * fall * fall; }
      ph.style.left = x.toFixed(1) + 'px'; ph.style.top = y.toFixed(1) + 'px';
      api.tw(q(ph, '.a'), t, [[appear[i], { o: 0, s: 0.2 }], [appear[i] + 0.3, { o: 1, s: 1, r: 0 }, 'back'], [tD, {}], [tD + 0.45, { r: (i % 2 ? 1 : -1) * 160, o: 0.8 }, 'in'], [tD + 0.6, { o: 0 }, 'lin']]);
    });
    api.tw(q(root, '.jo-t1 .a'), t, api.K.pop(t1 - 0.05, 0.4, { o: 0, s: 0.3, r: -14 }).concat([[t2 - 0.25, {}], [t2, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.jo-t2 .a'), t, api.K.pop(t2, 0.4, { o: 0, s: 0.3, r: -10 }));
  };
});
