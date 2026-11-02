/* @scene {"type":"move_morph","tags":["movement","walking","swimming","strength training"],"layout":"single-figure-one-stage-changes-world","metaphor":"one figure on one stage: the ground scrolls while it walks, water rises and it swims, the water drains and it lifts a barbell","assets":["one figure","scrolling ground","rising water","barbell"]} */
// {walk, walkAt, swim, swimAt, lift, liftAt}
RM.def('move_morph', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tW = api.T(p.walkAt), tS = api.T(p.swimAt), tL = api.T(p.liftAt);
  const cx = L.x(0.4), gy = L.y(0.8), FS = 540 * k;
  const wave = (y, ph, a) => { let d = `M${L.x0 - 60} 2000`; for (let x = L.x0 - 60; x <= L.x1 + 60; x += 24) d += ` L${x} ${(y + a * Math.sin(x / (70 * k) + ph)).toFixed(1)}`; return d + ` L${L.x1 + 60} 2000 Z`; };
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <circle class="mm-d" cx="${L.x(0.8)}" cy="${L.y(0.2)}" r="${170 * k}" fill="var(--c1)" opacity=".35"/>
      <line class="mm-g" x1="${L.x0 - 40}" x2="${L.x1 + 40}" y1="${gy}" y2="${gy}" stroke="var(--c1l)" stroke-width="${14 * k}" stroke-linecap="round" stroke-dasharray="${90 * k} ${54 * k}"/></svg>` +
    api.at(cx, gy - FS * 0.47, api.icon('ph-fill:person-simple-walk', FS, 'var(--paper)'), { cls: 'mm-w' }) +
    api.at(cx, L.y(0.52), api.icon('ph-fill:person-simple-swim', FS * 0.95, 'var(--paper)'), { cls: 'mm-s' }) +
    `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><path class="mm-v2" fill="var(--c2)" opacity=".6"/><path class="mm-v1" fill="var(--c1)" opacity=".55"/></svg>` +
    api.at(cx, gy - FS * 0.4, api.icon('ph-fill:person-arms-spread', FS * 0.8, 'var(--paper)'), { cls: 'mm-l' }) +
    api.at(cx, L.y(0.33), api.icon('ph-fill:barbell', FS * 0.68, 'var(--acc)'), { cls: 'mm-b' }) +
    api.at(L.cx, L.y(0.93), R.tag(p.walk || '', 96 * k, ''), { cls: 'mm-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.93), R.tag(p.swim || '', 96 * k, ''), { cls: 'mm-t2', idle: 'sway' }) +
    api.at(L.cx, L.y(0.93), R.tag(p.lift || '', 88 * k, ''), { cls: 'mm-t3', idle: 'sway' });
  const showK = (a, b, d = 0.16) => [[a, { o: 0, s: 0.5 }], [a + d, { o: 1, s: 1 }, 'back'], [b - d, { o: 1, s: 1 }], [b, { o: 0, s: 0.6 }, 'in']];
  return t => {
    const far = api.end + 100;
    q(root, '.mm-g').style.strokeDashoffset = (t * 420 * k).toFixed(1);
    q(root, '.mm-g').style.opacity = 1 - api.prog(t, tS - 0.1, tS + 0.1, 'lin') + api.prog(t, tL - 0.1, tL + 0.1, 'lin');
    const d = q(root, '.mm-d'); d.setAttribute('fill', t < tS ? 'var(--c1)' : t < tL ? 'var(--c2)' : 'var(--acc)'); d.setAttribute('r', (170 * k * (1 + 0.05 * Math.sin(t * 3))).toFixed(1));
    api.tw(q(root, '.mm-w .a'), t, showK(api.start, tS));
    q(root, '.mm-w .i').style.transform = `translateY(${(-14 * k * Math.abs(Math.sin(t * 7))).toFixed(1)}px)`;
    api.tw(q(root, '.mm-s .a'), t, showK(tS - 0.05, tL));
    q(root, '.mm-s .i').style.transform = `translate(${(30 * k * Math.sin(t * 3.4)).toFixed(1)}px,${(16 * k * Math.sin(t * 6)).toFixed(1)}px)`;
    const lvl = api.prog(t, tS - 0.15, tS + 0.3, 'out') - api.prog(t, tL - 0.25, tL + 0.1, 'in'), y = 2000 - (2000 - L.y(0.46)) * lvl;
    q(root, '.mm-v1').setAttribute('d', wave(y, t * 4, 26 * k)); q(root, '.mm-v2').setAttribute('d', wave(y - 34 * k, -t * 3, 22 * k));
    api.tw(q(root, '.mm-l .a'), t, showK(tL - 0.05, far));
    const up = Math.abs(Math.sin((t - tL) * 3.4));
    api.tw(q(root, '.mm-b .a'), t, api.K.drop(tL, 0.35, -220 * k));
    q(root, '.mm-b .i').style.transform = `translateY(${(50 * k * (1 - up)).toFixed(1)}px)`;
    api.tw(q(root, '.mm-t1 .a'), t, showK(tW - 0.05, tS - 0.05)); api.tw(q(root, '.mm-t2 .a'), t, showK(tS - 0.02, tL - 0.05)); api.tw(q(root, '.mm-t3 .a'), t, showK(tL - 0.02, far));
  };
});
