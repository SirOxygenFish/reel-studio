/* @scene {"type":"trio_flip","tags":["walking","pool","strength training","movement"],"layout":"three-tall-cards-side-by-side-flip","metaphor":"three tall face-down cards stand in a row and flip over one by one as she names each activity","assets":["three flip cards"]} */
// {walk, walkAt, swim, swimAt, lift, liftAt}
RM.def('trio_flip', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const ts = [api.T(p.walkAt), api.T(p.swimAt), api.T(p.liftAt)], W = L.w * 0.31, H = L.h * 0.7, y = L.y(0.08), I = [['ph-fill:person-simple-walk', 'var(--c1)', p.walk], ['ph-fill:person-simple-swim', 'var(--acc)', p.swim], ['ph-fill:barbell', 'var(--c1l)', p.lift]];
  root.innerHTML = I.map(([ic, bg, tx], i) => `<div class="tf2-c" style="position:absolute;left:${L.x0 + L.w * (0.02 + i * 0.325)}px;top:${y}px;width:${W}px;height:${H}px;border-radius:${30 * k}px">
      <div class="tf2-b" style="position:absolute;inset:0;border-radius:${30 * k}px;background:var(--c2);border:${8 * k}px solid var(--c1l)"></div>
      <div class="tf2-f" style="position:absolute;inset:0;border-radius:${30 * k}px;background:${bg};display:flex;align-items:center;justify-content:center;line-height:0">${api.icon(ic, W * 0.78, 'var(--ink)')}</div></div>`).join('') +
    I.map(([ic, bg, tx], i) => api.at(L.cx, L.y(0.91), R.tag(tx || '', i === 2 ? 80 * k : 100 * k, 'paper'), { cls: 'tf2-t', idle: 'sway' })).join('');
  const cs = qa(root, '.tf2-c'), tg = qa(root, '.tf2-t');
  return t => {
    cs.forEach((c, i) => { const inn = api.prog(t, api.start + i * 0.05, api.start + 0.24 + i * 0.05, 'back'), u = api.prog(t, ts[i] - 0.1, ts[i] + 0.14, 'out'), sx = Math.abs(Math.cos(u * Math.PI));
      c.style.transform = `translateY(${((1 - inn) * 900 * k).toFixed(1)}px) scaleX(${sx.toFixed(3)})`; q(c, '.tf2-f').style.visibility = u > 0.5 ? 'visible' : 'hidden'; q(c, '.tf2-b').style.visibility = u > 0.5 ? 'hidden' : 'visible'; });
    tg.forEach((e, i) => { const n = ts[i + 1]; api.tw(q(e, '.a'), t, api.K.slam(ts[i] - 0.03, 0.26).concat(n ? [[n - 0.12, {}], [n - 0.03, { o: 0, s: 0.6 }, 'in']] : [])); });
  };
});
