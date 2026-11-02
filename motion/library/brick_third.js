/* @scene {"type":"brick_third","tags":["protein","a third","built with it","building blocks"],"layout":"brick-wall-third-lights-up-labels-attach","metaphor":"a wall of protein bricks; one third of them light up as collagen, then the things built with it attach around the wall","assets":["brick wall","highlighted bricks","attached label tags"]} */
// {num, protein, proteinAt, third, thirdAt, parts:[{label, at}]}
RM.def('brick_third', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tP = api.T(p.proteinAt ?? api.start), tT = api.T(p.thirdAt), parts = p.parts || [], tp = parts.map(x => api.T(x.at));
  const C = 6, RW = 6, BW = L.w * 0.8 / C, BH = 86 * k, x0 = L.cx - BW * C / 2, y0 = L.y(0.62) - BH * RW / 2;
  const lit = new Set([1, 4, 8, 11, 13, 16, 19, 22, 26, 29, 31, 34]);
  let html = '';
  for (let r = 0; r < RW; r++) for (let c = 0; c < C; c++) { const i = r * C + c, off = r % 2 ? BW / 2 : 0;
    html += `<div class="bt-b${lit.has(i) ? ' bt-l' : ''}" data-i="${i}" style="position:absolute;left:${x0 + c * BW + off - BW / 4}px;top:${y0 + (RW - 1 - r) * BH}px;width:${BW - 8 * k}px;height:${BH - 8 * k}px;border-radius:${10 * k}px;background:var(--muted)"></div>`; }
  root.innerHTML = html +
    (p.num ? api.at(L.x(0.1), L.y(0.08), `<div class="badge acc" style="font-size:${140 * k}px;font-family:var(--f-display);font-weight:900"><span style="font-size:.52em">${R.esc(p.num)}</span></div>`, { cls: 'bt-n' }) : '') +
    api.at(L.x(0.55), L.y(0.08), R.tag(p.protein || '', 66 * k, ''), { cls: 'bt-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.22), R.tag(p.third || '', 60 * k, 'c1'), { cls: 'bt-t2', idle: 'sway' }) +
    parts.map((x, i) => api.at(L.x([0.2, 0.5, 0.8][i % 3]), L.y(0.97), R.tag(x.label, 54 * k, 'paper'), { cls: 'bt-p' })).join('');
  const bs = qa(root, '[class*="bt-b"]');
  return t => {
    bs.forEach(b => { const i = +b.dataset.i, a = api.start + 0.1 + i * 0.025, u = api.prog(t, a, a + 0.25, 'back');
      b.style.transform = `translateY(${(-160 * k * (1 - u)).toFixed(1)}px)`; b.style.opacity = u > 0.01 ? 1 : 0;
      b.style.background = b.classList.contains('bt-l') && t > tT ? 'var(--c1)' : 'var(--muted)';
      b.style.boxShadow = b.classList.contains('bt-l') && t > tT ? `0 0 ${24 * k}px var(--c1)` : 'none'; });
    if (p.num) api.tw(q(root, '.bt-n .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0 }));
    api.tw(q(root, '.bt-t1 .a'), t, api.K.pop(tP, 0.4, { o: 0, s: 0.3, r: -6 }));
    api.tw(q(root, '.bt-t2 .a'), t, api.K.slam(tT - 0.05, 0.4));
    qa(root, '.bt-p').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.rise(tp[i] - 0.05, 0.4, 120 * k)));
  };
});
