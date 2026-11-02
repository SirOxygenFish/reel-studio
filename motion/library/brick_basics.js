/* @scene {"type":"brick_basics","tags":["basics","protein","vitamin C","sleep","moving","one more brick"],"layout":"wall-builds-row-by-row-last-brick-swings-in","metaphor":"big labelled bricks drop into a wall one by one, and a last brick in another colour swings into the gap","assets":["labelled wall bricks"]} */
// {items:[{t,at}], last, lastAt, one, oneAt}
RM.def('brick_basics', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const I = p.items.map(c => ({ t: c.t, tt: api.T(c.at) })), tL = api.T(p.lastAt), tO = api.T(p.oneAt), BW = L.w * 0.49, BH = 200 * k, G = 12 * k, y0 = L.y(0.78);
  const P = [[-0.5, 0], [0.5, 0], [-0.5, 1], [0.5, 1], [0, 2]], b = (c, ink, tx) => `<div style="width:${BW}px;height:${BH}px;border-radius:${18 * k}px;background:${c};color:${ink};display:flex;align-items:center;justify-content:center;text-align:center;font-family:var(--f-display);font-weight:800;font-size:${58 * k}px;line-height:1.05;padding:0 ${16 * k}px;box-sizing:border-box">${tx}</div>`;
  root.innerHTML = I.map((c, i) => api.at(L.cx + P[i][0] * (BW + G), y0 - P[i][1] * (BH + G), b(i % 3 ? 'var(--c1)' : 'var(--c2)', i % 3 ? 'var(--ink)' : '#fff', c.t), { cls: 'bb2-b' })).join('') +
    api.at(L.cx, y0 - 2 * (BH + G), b('var(--acc)', 'var(--ink)', p.last || ''), { cls: 'bb2-l' }) +
    api.at(L.cx, L.y(0.08), R.tag(p.one || '', 92 * k, 'c1'), { cls: 'bb2-t', idle: 'wobble' });
  const bs = qa(root, '.bb2-b'), l = q(root, '.bb2-l');
  return t => {
    bs.forEach((e, i) => api.tw(q(e, '.a'), t, api.K.drop(I[i].tt - 0.04, 0.36, -700 * k)));
    const u = api.prog(t, tL - 0.05, tL + 0.42, 'back'); l.style.visibility = u > 0 ? 'visible' : 'hidden'; q(l, '.a').style.transform = `translate(${((1 - u) * 900 * k).toFixed(1)}px,${(-Math.sin(u * Math.PI) * 160 * k).toFixed(1)}px) rotate(${((1 - u) * 26).toFixed(1)}deg)`;
    api.tw(q(root, '.bb2-t .a'), t, api.K.slam(tO - 0.03, 0.3));
  };
});
