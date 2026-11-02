/* @scene {"type":"sugar_bottle","tags":["sugary drinks","soda","sweet juices","a lot of sugar","nothing useful"],"layout":"plain-bottle-left-carton-right-cubes-rain-pile","metaphor":"a plain fizzy bottle and a plain juice carton; sugar cubes rain down and pile up in front of them until they are almost buried","assets":["unbranded bottle","unbranded carton","falling sugar cubes","rising bubbles"]} */
// {soda, sodaAt, juice, juiceAt, lot, lotAt, useful, usefulAt}
RM.def('sugar_bottle', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.sodaAt), tJ = api.T(p.juiceAt), tL = api.T(p.lotAt), tU = api.T(p.usefulAt);
  const bx = L.x(0.29), by = L.y(0.53), cx2 = L.x(0.72), gy = L.y(0.86), id = 'sb' + Math.round(api.start * 100);
  const bottle = 'M-52 -340 L-52 -270 C-52 -210 -120 -190 -120 -110 L-120 290 Q-120 330 -80 330 L80 330 Q120 330 120 290 L120 -110 C120 -190 52 -210 52 -270 L52 -340 Z';
  const N = 34, PW = L.w * 0.96, CS = 74 * k, cubes = Array.from({ length: N }, (_, i) => { const row = i < 13 ? 0 : i < 23 ? 1 : i < 30 ? 2 : 3, inr = i - [0, 13, 23, 30][row], cnt = [13, 10, 7, 4][row], [a, b] = R.jit(i + 3, 2);
    return { x: L.cx + (inr - (cnt - 1) / 2) * (PW / 13) + a * 18 * k, y: gy + 40 * k - row * CS * 0.86, r: b * 36, d: i * (1.1 / N) }; });
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <defs><clipPath id="${id}"><path d="${bottle}"/></clipPath></defs>
      <g class="sb-b"><g clip-path="url(#${id})"><rect x="-130" width="260" y="-210" height="560" fill="var(--acc)"/>
        ${Array.from({ length: 12 }, (_, i) => `<circle class="sb-u" r="${5 + (i % 4) * 3}" fill="#fff" opacity=".7"/>`).join('')}</g>
        <path d="${bottle}" fill="none" stroke="var(--paper)" stroke-width="9"/><rect x="-62" y="-378" width="124" height="46" rx="10" fill="var(--c2)"/></g>
      <g class="sb-c"><path d="M-130 -150 L0 -270 L130 -150 Z" fill="var(--c1x)"/><rect x="-130" y="-150" width="260" height="470" rx="12" fill="var(--paper)"/><rect x="-130" y="-20" width="260" height="210" fill="var(--acc)"/></g>
      ${cubes.map(() => `<g class="sb-k"><rect x="${-CS / 2}" y="${-CS / 2}" width="${CS}" height="${CS}" rx="${10 * k}" fill="var(--paper)" stroke="var(--c1x)" stroke-width="${4 * k}"/></g>`).join('')}</svg>` +
    api.at(bx, L.y(0.065), R.tag(p.soda || '', 88 * k, 'c1'), { cls: 'sb-t1', idle: 'sway' }) +
    api.at(cx2, L.y(0.2), R.tag(p.juice || '', 72 * k, ''), { cls: 'sb-t2', idle: 'sway' }) +
    api.at(L.cx, L.y(0.34), R.tag(p.lot || '', 96 * k, 'bad'), { cls: 'sb-t3', idle: 'wobble' }) +
    api.at(L.cx, L.y(0.52), R.tag(p.useful || '', 92 * k, ''), { cls: 'sb-t4', idle: 'wobble' });
  const us = qa(root, '.sb-u'), ks = qa(root, '.sb-k'); ks.forEach(e => { e.style.visibility = 'hidden'; });
  return t => {
    const inn = api.prog(t, api.start, api.start + 0.4, 'back');
    R.gx(q(root, '.sb-b'), { y: (1 - inn) * 500 * k, r: 2.5 * Math.sin(t * 2), s: k, o: 1 }, bx, by);
    us.forEach((e, i) => { const v = ((t * (0.4 + i * 0.03) + i * 0.17) % 1); e.setAttribute('cx', (-90 + (i * 37) % 180).toFixed(0)); e.setAttribute('cy', (320 - 520 * v).toFixed(0)); });
    const cu = api.prog(t, tJ - 0.1, tJ + 0.35, 'back');
    R.gx(q(root, '.sb-c'), { y: (1 - cu) * 600 * k, s: 0.84 * k, r: -2 * Math.sin(t * 1.7), o: cu > 0 ? 1 : 0 }, cx2, L.y(0.56));
    ks.forEach((e, i) => { const c = cubes[i], a = tL + c.d, u = (t - a) / 0.34;
      if (u <= 0) { e.style.visibility = 'hidden'; return; }
      const f = Math.min(1, u), y = c.y - (1 - f * f) * (L.h + 200 * k), hop = f === 1 ? Math.exp(-(u - 1) * 6) * Math.abs(Math.sin((u - 1) * 9)) * 16 * k : 0;
      R.gx(e, { y: y - hop, r: c.r + (1 - f) * 220, s: 1, o: 1 }, c.x, 0); });
    const dim = api.prog(t, tU - 0.1, tU + 0.2, 'lin');
    q(root, '.sb-b').style.opacity = 1 - 0.55 * dim; q(root, '.sb-c').style.opacity = cu > 0 ? 1 - 0.55 * dim : 0;
    api.tw(q(root, '.sb-t1 .a'), t, api.K.pop(tS - 0.05, 0.35, { o: 0, s: 0.3, r: -5 }));
    api.tw(q(root, '.sb-t2 .a'), t, api.K.pop(tJ, 0.35, { o: 0, s: 0.3, r: 5 }));
    api.tw(q(root, '.sb-t3 .a'), t, api.K.slam(tL - 0.05, 0.4));
    api.tw(q(root, '.sb-t4 .a'), t, api.K.slam(tU - 0.05, 0.4));
  };
});
