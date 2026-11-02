/* @scene {"type":"bottle_marks","tags":["drink enough","during the day","not only when you remember"],"layout":"one-tall-bottle-center-tick-marks-side","metaphor":"one tall bottle with tick marks: the level drops step by step, mark by mark, while the sun gives way to the moon","assets":["tall bottle with marks","sun and moon"]} */
// {drink, drinkAt, day, dayAt, not, notAt}
RM.def('bottle_marks', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tD = api.T(p.drinkAt), tY = api.T(p.dayAt), tN = api.T(p.notAt), T0 = api.start + 0.2, T1 = api.end - 0.2, cx = L.cx, top = L.y(0.17), H = 640 * k, W = 170 * k, N = 5, id = 'bm' + Math.round(api.start * 100);
  const body = `M${-W * 0.42} ${-H * 0.5} H${W * 0.42} V${-H * 0.4} C${W * 0.42} ${-H * 0.32} ${W} ${-H * 0.3} ${W} ${-H * 0.16} V${H * 0.44} Q${W} ${H * 0.5} ${W * 0.8} ${H * 0.5} H${-W * 0.8} Q${-W} ${H * 0.5} ${-W} ${H * 0.44} V${-H * 0.16} C${-W} ${-H * 0.3} ${-W * 0.42} ${-H * 0.32} ${-W * 0.42} ${-H * 0.4} Z`, cy = top + H / 2;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><defs><clipPath id="${id}"><path d="${body}"/></clipPath></defs>
      <g transform="translate(${cx} ${cy})"><g clip-path="url(#${id})"><path class="bm-w" fill="var(--c1)"/></g><path d="${body}" fill="none" stroke="var(--paper)" stroke-width="${12 * k}"/>
      ${Array.from({ length: N }, (_, i) => `<line x1="${W * 0.5}" x2="${W}" y1="${H * (-0.16 + i * 0.13)}" y2="${H * (-0.16 + i * 0.13)}" stroke="var(--paper)" stroke-width="${8 * k}"/>`).join('')}</g></svg>` +
    api.at(0, 0, api.icon('ph-fill:sun', 170 * k, 'var(--acc)'), { cls: 'bm-s' }) + api.at(0, 0, api.icon('ph-fill:moon', 150 * k, 'var(--c1x)'), { cls: 'bm-m' }) +
    api.at(cx, L.y(0.05), R.tag(p.drink || '', 84 * k, 'c1'), { cls: 'bm-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.94), R.tag(p.day || '', 84 * k, ''), { cls: 'bm-t2', idle: 'sway' }) +
    api.at(cx, L.y(0.94), R.tag(p.not || '', 66 * k, 'paper'), { cls: 'bm-t3', idle: 'wobble' });
  const w = q(root, '.bm-w'), s = q(root, '.bm-s'), m = q(root, '.bm-m');
  return t => {
    const u = api.clamp((t - T0) / (T1 - T0), 0, 1), st = Math.floor(u * N), e = st + api.prog((u * N) % 1, 0.65, 1, 'back'), y = H * (-0.2 + Math.min(N, e) * 0.13);
    let d = `M${-W * 2} ${H}`; for (let x = -W * 2; x <= W * 2; x += 24 * k) d += ` L${x.toFixed(1)} ${(y + 10 * k * Math.sin(x / (40 * k) + t * 6)).toFixed(1)}`; w.setAttribute('d', d + ` L${W * 2} ${H} Z`);
    const arc = a => [L.x(0.14 + a * 0.2), L.y(0.42 - Math.sin(a * Math.PI) * 0.14)]; const [sx, sy] = arc(u); s.style.left = sx + 'px'; s.style.top = sy + 'px'; q(s, '.a').style.opacity = 1 - api.clamp((u - 0.6) * 4, 0, 1);
    const [mx, my] = [L.x(0.86), L.y(0.5 - 0.2 * api.clamp((u - 0.55) * 2, 0, 1))]; m.style.left = mx + 'px'; m.style.top = my + 'px'; q(m, '.a').style.opacity = api.clamp((u - 0.55) * 5, 0, 1);
    api.tw(q(root, '.bm-t1 .a'), t, api.K.pop(tD - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.bm-t2 .a'), t, api.K.pop(tY - 0.04, 0.26, { o: 0, s: 0.3 }).concat([[tN - 0.12, {}], [tN - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.bm-t3 .a'), t, api.K.slam(tN - 0.03, 0.3));
  };
});
