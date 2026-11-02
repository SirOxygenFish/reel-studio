/* @scene {"type":"past_box","tags":["old ways","outdated","catalogues","cold calling","past"],"layout":"cardboard-box-bottom-items-drop","metaphor":"the old ways (catalogues, calling relatives, hard selling) drop into a cardboard box marked 'the past' and the lid shuts","assets":["cardboard box with flaps","catalogue","old phone","speech bubble"]} */
// {title, titleAt, items:[{icon, label, at}], past, pastAt}
RM.def('past_box', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const it = p.items || [], ti = it.map(x => api.T(x.at)), tP = api.T(p.pastAt), tT = api.T(p.titleAt ?? api.start);
  const bx = L.cx, by = L.y(0.78), BW = 640 * k, BH = 360 * k;
  root.innerHTML = api.at(bx, L.y(0.08), R.tag(p.title || '', 74 * k, 'c1'), { cls: 'pb-ti', idle: 'sway' }) +
    it.map((x, i) => api.at(0, 0, `<div style="display:flex;flex-direction:column;align-items:center;gap:${8 * k}px"><div class="badge paper" style="font-size:${200 * k}px">${api.icon(x.icon, 120 * k, 'var(--c2)')}</div><div class="tag paper" style="font-size:${52 * k}px">${R.esc(x.label)}</div></div>`, { cls: 'pb-it' })).join('') +
    api.at(bx, by, `<div style="position:relative;width:${BW}px;height:${BH}px">
        <div class="pb-fl" style="position:absolute;left:0;top:0;width:50%;height:${120 * k}px;background:var(--c1);transform-origin:0 0;border-radius:${8 * k}px"></div>
        <div class="pb-fr" style="position:absolute;right:0;top:0;width:50%;height:${120 * k}px;background:var(--c1);transform-origin:100% 0;border-radius:${8 * k}px"></div>
        <div style="position:absolute;inset:0;background:var(--c1l);border:${8 * k}px solid var(--c1);border-radius:${12 * k}px;display:flex;align-items:center;justify-content:center">
          <div class="big pb-p" style="font-size:${84 * k}px;color:var(--c2);transform:rotate(-4deg);border:${6 * k}px solid var(--c2);padding:.05em .3em;border-radius:${10 * k}px">${R.esc(p.past || '')}</div></div></div>`, { cls: 'pb-b' });
  const its = qa(root, '.pb-it');
  return t => {
    api.tw(q(root, '.pb-ti .a'), t, api.K.pop(tT, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.pb-b .a'), t, api.K.rise(api.start, 0.45, 260 * k));
    its.forEach((e, i) => {
      const hx = L.x(i % 2 ? 0.64 : 0.3), hy = L.y(0.22 + i * 0.15), drop = api.prog(t, tP + i * 0.08, tP + 0.5 + i * 0.08, 'in');
      e.style.left = (hx + (bx - hx) * drop) + 'px'; e.style.top = (hy + (by - hy) * drop) + 'px';
      api.tw(q(e, '.a'), t, [[ti[i] - 0.05, { o: 0, s: 0.3, r: (i - 1) * 20 }], [ti[i] + 0.35, { o: 1, s: 1, r: 0 }, 'back'], [tP + i * 0.08 + 0.35, { s: 1 }], [tP + i * 0.08 + 0.5, { o: 0, s: 0.5 }, 'in']]);
    });
    const shut = api.prog(t, tP + 0.6, tP + 0.95, 'back');
    q(root, '.pb-fl').style.transform = `rotate(${(-150 + 150 * shut).toFixed(1)}deg)`; q(root, '.pb-fr').style.transform = `rotate(${(150 - 150 * shut).toFixed(1)}deg)`;
    api.tw(q(root, '.pb-p'), t, [[tP - 0.05, { o: 0.25, s: 0.8 }], [tP + 0.3, { o: 1, s: 1 }, 'back']]);
  };
});
