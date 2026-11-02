/* @scene {"type":"bridge_lift","tags":["strong muscles","take the load off","joints"],"layout":"side-view-suspension-bridge-two-towers","metaphor":"a loaded bridge deck rests on one small pier; thick cables tighten from two towers and lift the deck clear of the pier","assets":["suspension bridge","towers","thick cables","small pier"]} */
// {strong, strongAt, take, takeAt, load, joint, jointAt}
RM.def('bridge_lift', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.strongAt), tT = api.T(p.takeAt), tJ = api.T(p.jointAt);
  const xL = L.x(0.09), xR = L.x(0.91), cx = L.cx, top = L.y(0.14), base = L.y(0.84), dy = L.y(0.6), DW = L.w * 0.86, DH = 44 * k, N = 4;
  const ANCH = [-0.36, -0.15, 0.15, 0.36];
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      ${[xL, xR].map(x => `<rect x="${x - 34 * k}" y="${top}" width="${68 * k}" height="${base - top}" rx="${14 * k}" fill="var(--c2)" stroke="var(--c1l)" stroke-width="${6 * k}"/>`).join('')}
      <path d="M${L.x0 - 200} ${base} H${L.x1 + 200} V2000 H${L.x0 - 200} Z" fill="var(--c2)" opacity=".55"/>
      <path d="M${cx - 80 * k} ${base} L${cx - 36 * k} ${dy + 30 * k} H${cx + 36 * k} L${cx + 80 * k} ${base} Z" fill="var(--c1x)"/>
      <circle class="bl-r" cx="${cx}" cy="${dy + 38 * k}" fill="none" stroke="var(--bad)" stroke-width="${12 * k}"/>
      ${ANCH.map(() => `<line class="bl-c" stroke="var(--acc)" stroke-linecap="round"/>`).join('')}
      <g class="bl-d"><rect x="${-DW / 2}" y="${-DH / 2}" width="${DW}" height="${DH}" rx="${14 * k}" fill="var(--paper)"/>
        ${[-0.3, -0.1, 0.12, 0.3].map((u, i) => `<rect class="bl-k" x="${DW * u - 66 * k}" y="${-DH / 2 - (110 + i % 2 * 40) * k}" width="${132 * k}" height="${(110 + i % 2 * 40) * k}" rx="${12 * k}" fill="var(--c1)" stroke="var(--ink)" stroke-width="${4 * k}"/>`).join('')}</g></svg>` +
    api.at(cx, L.y(0.05), R.tag(p.strong || '', 84 * k, 'c1'), { cls: 'bl-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.23), R.tag(p.take || '', 72 * k, ''), { cls: 'bl-t2', idle: 'wobble' }) +
    api.at(cx, L.y(0.94), R.tag(p.joint || '', 84 * k, 'paper'), { cls: 'bl-t3', idle: 'sway' });
  const cs = qa(root, '.bl-c'), d = q(root, '.bl-d'), ring = q(root, '.bl-r');
  return t => {
    const lift = api.prog(t, tT - 0.05, tT + 0.45, 'back'), sag = 12 * k * Math.sin(t * 13) * (1 - lift), y = dy - 110 * k * lift + sag + (1 - api.prog(t, api.start, api.start + 0.25, 'back')) * -360 * k;
    R.gx(d, { r: 0, s: 1, o: 1 }, cx, y);
    const grow = api.prog(t, tS - 0.05, tS + 0.3, 'out'), th = (10 + 22 * api.prog(t, api.T(p.strongAt) + 0.3, tT + 0.2, 'out')) * k;
    cs.forEach((c, i) => { const tw = i < 2 ? xL : xR, u = ANCH[i], tx = cx + DW * u, ty = y - 150 * k; c.setAttribute('x1', tw); c.setAttribute('y1', top + 20 * k); c.setAttribute('x2', (tw + (tx - tw) * grow).toFixed(1)); c.setAttribute('y2', (top + 20 * k + (ty - top - 20 * k) * grow).toFixed(1)); c.setAttribute('stroke-width', th.toFixed(1)); c.style.visibility = grow > 0.01 ? 'visible' : 'hidden'; });
    const hurt = 1 - lift; ring.setAttribute('r', ((54 + 16 * Math.abs(Math.sin(t * 7))) * k).toFixed(1)); ring.style.opacity = (Math.max(0.05, hurt) * 0.95).toFixed(3);
    api.tw(q(root, '.bl-t1 .a'), t, api.K.pop(tS - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.bl-t2 .a'), t, api.K.slam(tT - 0.03, 0.3));
    api.tw(q(root, '.bl-t3 .a'), t, api.K.pop(tJ - 0.04, 0.26, { o: 0, s: 0.3, r: 4 }));
  };
});
