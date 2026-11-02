/* @scene {"type":"polaroid_then_now","tags":["old methods","today different","social media","then vs now"],"layout":"pinned-polaroids-then-phone-slides-in","metaphor":"polaroids of the old ways fade to sepia and curl; a bright phone with a personal profile slides in: today it looks different","assets":["polaroid photos","sepia fade","smartphone with profile grid"]} */
// {items:[{icon, label, at}], nowAt, now}
RM.def('polaroid_then_now', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const it = p.items || [], ti = it.map(x => api.T(x.at)), tN = api.T(p.nowAt);
  const PW = 300 * k, PH = 360 * k, slots = [[0.22, 0.24, -8], [0.72, 0.3, 6], [0.4, 0.62, -3]];
  root.innerHTML = it.map((x, i) => api.at(L.x(slots[i][0]), L.y(slots[i][1]), `<div class="pt-ph" style="width:${PW}px;height:${PH}px;background:var(--paper);padding:${18 * k}px ${18 * k}px ${70 * k}px;box-shadow:var(--sh);transform:rotate(${slots[i][2]}deg);position:relative">
        <div class="pt-img" style="width:100%;height:100%;background:var(--acc-soft);display:flex;align-items:center;justify-content:center">${api.icon(x.icon, 150 * k, 'var(--c2)')}</div>
        <div class="label" style="position:absolute;left:0;right:0;bottom:${16 * k}px;text-align:center;font-size:${34 * k}px;color:var(--ink)">${R.esc(x.label)}</div>
        <div style="position:absolute;left:50%;top:${-14 * k}px;width:${30 * k}px;height:${30 * k}px;margin-left:${-15 * k}px;border-radius:50%;background:var(--bad)"></div></div>`, { cls: 'pt-p' })).join('') +
    api.at(L.x(0.74), L.y(0.62), `<div style="width:${360 * k}px;height:${700 * k}px;border-radius:${56 * k}px;background:var(--ink);padding:${20 * k}px;box-shadow:var(--sh)">
        <div style="width:100%;height:100%;border-radius:${40 * k}px;background:var(--paper);overflow:hidden;display:flex;flex-direction:column;align-items:center;padding-top:${40 * k}px;gap:${16 * k}px">
          <div class="round" style="width:${130 * k}px;height:${130 * k}px;background:radial-gradient(circle at 40% 35%,var(--c1l),var(--c1))"></div>
          <div style="width:60%;height:${18 * k}px;border-radius:9px;background:var(--c2)"></div><div style="width:40%;height:${14 * k}px;border-radius:7px;background:var(--muted)"></div>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:${8 * k}px;width:88%;margin-top:${12 * k}px">${Array.from({ length: 9 }, (_, j) => `<div class="pt-g" style="aspect-ratio:1/1;border-radius:${8 * k}px;background:${['var(--acc)', 'var(--c1l)', 'var(--c1)'][j % 3]}"></div>`).join('')}</div>
          <div class="pt-heart" style="font-size:0">${api.icon('ph-fill:heart', 80 * k, 'var(--bad)')}</div></div></div>`, { cls: 'pt-now' }) +
    api.at(L.x(0.3), L.y(0.95), R.tag(p.now || '', 66 * k, ''), { cls: 'pt-t', idle: 'sway' });
  return t => {
    qa(root, '.pt-p').forEach((e, i) => {
      api.tw(q(e, '.a'), t, api.K.drop(ti[i] - 0.1, 0.5, -400 * k).concat([[tN - 0.1, {}], [tN + 0.5, { x: -160 * k, s: 0.85, o: 0.55 }, 'io']]));
      const sep = api.prog(t, tN - 0.2, tN + 0.5, 'io');
      q(e, '.pt-ph').style.filter = `sepia(${(0.15 + 0.85 * sep).toFixed(2)}) saturate(${(1 - 0.5 * sep).toFixed(2)})`;
    });
    api.tw(q(root, '.pt-now .a'), t, [[tN - 0.05, { o: 0, x: 500 * k, r: 12 }], [tN + 0.5, { o: 1, x: 0, r: -3 }, 'back']]);
    qa(root, '.pt-g').forEach((g, j) => { g.style.opacity = t > tN + 0.3 + j * 0.05 ? 1 : 0; });
    api.tw(q(root, '.pt-heart'), t, [[tN + 0.8, { o: 0, s: 0.2 }], [tN + 1.1, { o: 1, s: 1.2 }, 'back'], [tN + 1.4, { s: 1 }, 'io']]);
    api.tw(q(root, '.pt-t .a'), t, api.K.pop(tN, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
