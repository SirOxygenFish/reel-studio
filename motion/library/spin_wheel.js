/* @scene {"type":"spin_wheel","tags":["walking","pool","strength training","movement"],"layout":"big-wheel-rising-from-bottom-pointer-top","metaphor":"a big wheel rises from the bottom edge and snaps round to the next activity each time she names one","assets":["segmented wheel","pointer"]} */
// {walk, walkAt, swim, swimAt, lift, liftAt}
RM.def('spin_wheel', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const ts = [api.T(p.walkAt), api.T(p.swimAt), api.T(p.liftAt)], W = [['ph-fill:person-simple-walk', p.walk, 'var(--c1)'], ['ph-fill:person-simple-swim', p.swim, 'var(--acc)'], ['ph-fill:barbell', p.lift, 'var(--c1l)']];
  const cx = L.cx, cy = L.y(0.72), RR = 520 * k, sec = (i, c) => { const a0 = (i * 120 - 60 - 90) * Math.PI / 180, a1 = (i * 120 + 60 - 90) * Math.PI / 180;
    return `<path d="M0 0 L${Math.cos(a0) * RR} ${Math.sin(a0) * RR} A${RR} ${RR} 0 0 1 ${Math.cos(a1) * RR} ${Math.sin(a1) * RR} Z" fill="${c}" stroke="var(--bgDeep)" stroke-width="${14 * k}"/>`; };
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><g class="sw-w">${W.map((w, i) => sec(i, w[2])).join('')}<circle r="${70 * k}" fill="var(--bgDeep)"/></g>
      <path d="M${cx - 56 * k} ${cy - RR - 70 * k} H${cx + 56 * k} L${cx} ${cy - RR + 26 * k} Z" fill="var(--paper)"/></svg>` +
    W.map((w, i) => api.at(0, 0, api.icon(w[0], 250 * k, 'var(--ink)'), { cls: 'sw-i' })).join('') +
    W.map((w, i) => api.at(cx, L.y(0.07), R.tag(w[1] || '', i === 2 ? 76 * k : 100 * k, 'paper'), { cls: 'sw-t', idle: 'sway' })).join('');
  const wh = q(root, '.sw-w'), ic = qa(root, '.sw-i'), tg = qa(root, '.sw-t');
  return t => {
    const inn = api.prog(t, api.start, api.start + 0.28, 'back'), ang = ts.reduce((a, x, i) => a - (i ? 120 * api.prog(t, x - 0.1, x + 0.22, 'back') : 0), 0);
    const y = cy + (1 - inn) * 800 * k; R.gx(wh, { r: ang, s: 1, o: 1 }, cx, y);
    ic.forEach((e, i) => { const a = (i * 120 + ang - 90) * Math.PI / 180, rr = RR * 0.62; e.style.left = cx + Math.cos(a) * rr + 'px'; e.style.top = y + Math.sin(a) * rr + 'px'; q(e, '.i').style.transform = `rotate(${(i * 120 + ang).toFixed(1)}deg)`; });
    tg.forEach((e, i) => { const n = ts[i + 1]; api.tw(q(e, '.a'), t, api.K.slam(ts[i] - 0.03, 0.26).concat(n ? [[n - 0.12, {}], [n - 0.03, { o: 0, s: 0.6 }, 'in']] : [])); });
  };
});
