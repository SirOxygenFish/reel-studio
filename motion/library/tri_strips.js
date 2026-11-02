/* @scene {"type":"tri_strips","tags":["movement","walking","pool","strength training"],"layout":"three-stacked-bands-accordion-active-grows","metaphor":"three stacked bands slam in from alternating sides, the one she names grows and its figure moves inside it: walk, pool, gym","assets":["accordion bands","figure in each band","waves in a band"]} */
// {walk, walkAt, swim, swimAt, lift, liftAt}
RM.def('tri_strips', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const ts = [api.T(p.walkAt), api.T(p.swimAt), api.T(p.liftAt)], B = [['var(--c2)', 'var(--paper)', p.walk, 'ph-fill:person-simple-walk'], ['var(--c1)', 'var(--ink)', p.swim, 'ph-fill:person-simple-swim'], ['var(--acc)', 'var(--ink)', p.lift, 'ph-fill:barbell']];
  const X0 = L.x0 - 30, W = L.w + 60, Y0 = L.y0, H = L.h;
  root.innerHTML = B.map(([bg, ink, tx, ic], i) => `<div class="ts-b" style="position:absolute;left:${X0}px;width:${W}px;background:${bg};overflow:hidden;border-radius:${30 * k}px">
      <div class="ts-w" style="position:absolute;left:0;right:0;bottom:0;height:0"></div>
      <div class="ts-ic" style="position:absolute;left:${70 * k}px;top:50%;line-height:0">${api.icon(ic, 300 * k, ink)}</div>
      <div class="ts-l" style="position:absolute;right:${60 * k}px;top:50%;max-width:${W * 0.56}px;text-align:right;font-family:var(--f-display);font-weight:900;font-size:${74 * k}px;line-height:1.02;color:${ink}">${R.esc ? R.esc(tx || '') : (tx || '')}</div></div>`).join('');
  const bs = qa(root, '.ts-b'), ics = qa(root, '.ts-ic');
  const ease = api.E && api.E.out ? api.E.out : (x => x);
  return t => {
    const act = t < ts[1] ? 0 : t < ts[2] ? 1 : 2, w = [0, 1, 2].map(i => { const on = api.prog(t, ts[i] - 0.04, ts[i] + 0.16, 'out'), off = i < 2 ? api.prog(t, ts[i + 1] - 0.04, ts[i + 1] + 0.16, 'out') : 0; return 0.56 + 1.5 * (on - off); });
    const vis = [0, 1, 2].map(i => t >= ts[i] - 0.05), sum = w.reduce((a, b) => a + b, 0); let y = Y0;
    bs.forEach((b, i) => { const h = H * w[i] / sum - 12 * k, s = api.prog(t, ts[i] - 0.05, ts[i] + 0.14, 'out');
      b.style.top = y + 'px'; b.style.height = Math.max(10, h) + 'px'; b.style.transform = `translateX(${((1 - s) * (i % 2 ? 1 : -1) * (W + 40)).toFixed(1)}px)`; b.style.visibility = vis[i] ? 'visible' : 'hidden'; y += H * w[i] / sum;
      const a = i === act ? 1 : 0, ph = t * 9, m = [`translate(${(a * 40 * Math.sin(ph / 2)).toFixed(1)}px,${(-a * 12 * Math.abs(Math.sin(ph))).toFixed(1)}px)`, `translate(${(a * 60 * Math.sin(ph / 3)).toFixed(1)}px,${(a * 10 * Math.sin(ph / 1.3)).toFixed(1)}px)`, `translate(0,${(-a * 34 * Math.abs(Math.sin(ph / 1.6))).toFixed(1)}px)`][i];
      const sc = 0.5 + 0.5 * (w[i] - 0.56) / 1.5; ics[i].style.transform = `translateY(-50%) ${m} scale(${sc.toFixed(3)})`; ics[i].style.transformOrigin = 'left center'; });
  };
});
