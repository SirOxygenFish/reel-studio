/* @scene {"type":"domino_shops","tags":["bankruptcy","collapse","statistics","chain reaction"],"layout":"domino-line-perspective","metaphor":"a long line of domino tiles, each a little shop with an awning, topples in a chain while the bankruptcy count rolls up","assets":["domino shop tiles","rolling counter","per-day tag"]} */
// {count:{value, label, at}, perDay:{text, at}, fallAt}
RM.def('domino_shops', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tC = api.T(p.count.at), tF = api.T(p.fallAt ?? p.count.at), tD = api.T(p.perDay.at), N = 12;
  const tile = i => `<div class="ds-tile" style="position:relative;width:${130 * k}px;height:${300 * k}px;border-radius:${16 * k}px;background:var(--paper);border:${6 * k}px solid var(--c2);overflow:hidden">
      <div style="position:absolute;left:0;right:0;top:${26 * k}px;height:${34 * k}px;background:repeating-linear-gradient(90deg,${i % 2 ? 'var(--bad)' : 'var(--acc)'} 0 ${14 * k}px,var(--paper) ${14 * k}px ${28 * k}px)"></div>
      <div style="position:absolute;left:${16 * k}px;right:${16 * k}px;bottom:${16 * k}px;height:${70 * k}px;background:var(--c1l);border-radius:${6 * k}px"></div></div>`;
  // the line runs diagonally from back-left (small) to front-right (big)
  const pos = i => { const u = i / (N - 1); return [L.x(0.08 + 0.82 * u), L.y(0.48 + 0.36 * u), 0.6 + 0.55 * u]; };
  root.innerHTML = Array.from({ length: N }, (_, i) => { const [x, y, s] = pos(i); return api.at(x, y, `<div style="transform:scale(${s.toFixed(3)});transform-origin:50% 100%">${tile(i)}</div>`, { cls: 'ds-d', z: i + 1 }); }).join('') +
    api.at(L.x(0.34), L.y(0.12), `<div style="display:flex;align-items:baseline;gap:${16 * k}px"><div class="big ds-n" style="font-size:${170 * k}px;color:var(--bad)">0</div><div class="big" style="font-size:${64 * k}px;color:var(--c2)">${R.esc(p.count.label || '')}</div></div>`, { cls: 'ds-c' }) +
    api.at(L.x(0.75), L.y(0.3), R.tag(p.perDay.text, 66 * k, 'c1'), { cls: 'ds-pd', idle: 'wobble' });
  const ds = qa(root, '.ds-d'), num = q(root, '.ds-n'), val = p.count.value || 0, dec = String(val).includes('.') ? 1 : 0;
  return t => {
    num.textContent = (val * api.prog(t, tC, tC + 1.0, 'out')).toFixed(dec).replace('.', ',');
    api.tw(q(root, '.ds-c .a'), t, api.K.pop(tC - 0.05, 0.4, { o: 0, s: 0.4 }));
    ds.forEach((d, i) => {
      const a = tF + i * 0.16, fall = api.prog(t, a, a + 0.32, 'in');
      api.tw(q(d, '.a'), t, [[api.start + i * 0.03, { o: 0, y: 60 * k }], [api.start + 0.3 + i * 0.03, { o: 1, y: 0 }, 'back']]);
      q(d, '.i').style.transform = `rotate(${(78 * fall).toFixed(1)}deg)`; q(d, '.i').style.transformOrigin = '100% 100%';
    });
    api.tw(q(root, '.ds-pd .a'), t, api.K.slam(tD - 0.05, 0.4));
  };
});
