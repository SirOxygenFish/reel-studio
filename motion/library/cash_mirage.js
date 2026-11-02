/* @scene {"type":"cash_mirage","tags":["fast money","promises","illusion","honesty"],"layout":"mirage-over-desert-horizon","metaphor":"a shimmering mirage of banknotes floats over a desert and pops like soap bubbles","assets":["desert dunes","heat shimmer","bubble banknotes","tip numeral"]} */
// {num, promise, promiseAt, popAt, self, selfAt}
RM.def('cash_mirage', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tPr = api.T(p.promiseAt), tPo = api.T(p.popAt), tS = api.T(p.selfAt ?? p.popAt), N = 5, rnd = R.jit(3, N * 2);
  const note = `<div style="width:${330 * k}px;height:${170 * k}px;border-radius:${20 * k}px;border:${10 * k}px dashed var(--good);background:rgba(255,255,255,.35);display:flex;align-items:center;justify-content:center">
      <div class="round" style="width:${96 * k}px;height:${96 * k}px;border:${9 * k}px solid var(--good)"></div></div>`;
  root.innerHTML = `<svg style="position:absolute;left:${L.x0}px;top:${L.y0}px;overflow:visible" width="${L.w}" height="${L.h}" viewBox="0 0 ${L.w} ${L.h}">
      <path d="M0 ${L.h * 0.72} Q ${L.w * 0.25} ${L.h * 0.62} ${L.w * 0.5} ${L.h * 0.7} T ${L.w} ${L.h * 0.66} V ${L.h} H0 Z" fill="var(--c1l)"/>
      <path d="M0 ${L.h * 0.84} Q ${L.w * 0.3} ${L.h * 0.76} ${L.w * 0.62} ${L.h * 0.84} T ${L.w} ${L.h * 0.8} V ${L.h} H0 Z" fill="var(--c1)"/>
      ${[0, 1, 2, 3].map(i => `<path class="cm-heat" d="M${L.w * 0.1} ${L.h * (0.6 - i * 0.04)} q 60 -14 120 0 t 120 0 t 120 0 t 120 0 t 120 0 t 120 0 t 120 0" fill="none" stroke="var(--paper)" stroke-width="${6 * k}" opacity=".6"/>`).join('')}</svg>` +
    Array.from({ length: N }, (_, i) => api.at(L.x(0.2 + 0.6 * (i / (N - 1))), L.y(0.22 + 0.3 * Math.abs(i - (N - 1) / 2) / N + 0.08 * rnd[i * 2]), note, { cls: 'cm-n', idle: 'float', amp: 1.5 })).join('') +
    Array.from({ length: N }, (_, i) => `<div class="cm-pop" style="position:absolute;left:${L.x(0.2 + 0.6 * (i / (N - 1))) - 130 * k}px;top:${L.y(0.22 + 0.3 * Math.abs(i - (N - 1) / 2) / N + 0.08 * rnd[i * 2]) - 130 * k}px;width:${260 * k}px;height:${260 * k}px;border-radius:50%;border:${6 * k}px solid var(--good);opacity:0"></div>`).join('') +
    api.at(L.x(0.1), L.y(0.58), `<div class="badge acc" style="font-size:${150 * k}px;font-family:var(--f-display);font-weight:900"><span style="font-size:.52em">${R.esc(p.num || '')}</span></div>`, { cls: 'cm-num' }) +
    api.at(L.x(0.58), L.y(0.08), R.tag(p.promise || '', 64 * k, 'bad'), { cls: 'cm-t1', idle: 'sway' }) +
    api.at(L.x(0.5), L.y(0.9), R.tag(p.self || '', 70 * k, 'paper'), { cls: 'cm-t2', idle: 'wobble' });
  const ns = qa(root, '.cm-n'), pops = qa(root, '.cm-pop');
  return t => {
    qa(root, '.cm-heat').forEach((h, i) => h.setAttribute('transform', `translate(${(-60 * ((t * 0.8 + i * 0.25) % 1)).toFixed(1)} 0)`));
    ns.forEach((n, i) => {
      const tp = tPo + i * 0.09, a = q(n, '.a');
      api.tw(a, t, [[tPr - 0.1 + i * 0.07, { o: 0, s: 0.3, y: 120 * k }], [tPr + 0.35 + i * 0.07, { o: 0.9, s: 1, y: 0 }, 'back'], [tp, { s: 1 }], [tp + 0.12, { s: 1.25, o: 0 }, 'out']]);
      a.style.filter = `blur(${(1.5 + 1.5 * Math.sin(t * 7 + i)).toFixed(1)}px)`;
      const pu = api.prog(t, tp, tp + 0.35, 'out'); pops[i].style.opacity = pu > 0 && pu < 1 ? 1 - pu : 0; pops[i].style.transform = `scale(${(0.5 + pu).toFixed(2)})`;
    });
    api.tw(q(root, '.cm-num .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0 }));
    api.tw(q(root, '.cm-t1 .a'), t, api.K.pop(tPr - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
    api.tw(q(root, '.cm-t2 .a'), t, api.K.pop(tS - 0.05, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
