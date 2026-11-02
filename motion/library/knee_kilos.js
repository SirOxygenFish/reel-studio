/* @scene {"type":"knee_kilos","tags":["gain weight","every extra kilo","pressure on your knees"],"layout":"standing-figure-left-tray-stack-tags-right","metaphor":"a standing line figure carries a tray overhead; kilo weights land on it one by one, the knees bend a little more each time and a ring on the knee grows","assets":["line figure with bending knee","tray","kilo weights","knee ring"]} */
// {gain, gainAt, kilo, kiloAt, more, moreAt, drops:[word or time ...]}
RM.def('knee_kilos', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tG = api.T(p.gainAt), tK = api.T(p.kiloAt), tM = api.T(p.moreAt), tD = (p.drops || []).map(x => api.T(x));
  const fx = L.x(0.2), gy = L.y(0.985), TH = 205 * k, SH = 205 * k, TO = 215 * k, HD = 54 * k, WW = 270 * k, WH = 78 * k;
  const wrap = (s, fs, cls) => `<div class="tag ${cls}" style="font-size:${fs}px;white-space:normal;text-align:center;width:${L.w * 0.44}px;line-height:1.15">${R.esc(s)}</div>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <line x1="${L.x0 + 20}" x2="${L.x1 - 20}" y1="${gy}" y2="${gy}" stroke="var(--c1l)" stroke-width="${12 * k}" stroke-linecap="round"/>
      <path class="kk-leg" fill="none" stroke="var(--paper)" stroke-width="${54 * k}" stroke-linecap="round" stroke-linejoin="round"/>
      <path class="kk-ft" fill="none" stroke="var(--paper)" stroke-width="${38 * k}" stroke-linecap="round"/>
      <path class="kk-to" fill="none" stroke="var(--c1)" stroke-width="${84 * k}" stroke-linecap="round"/>
      <path class="kk-ar" fill="none" stroke="var(--paper)" stroke-width="${30 * k}" stroke-linecap="round" stroke-linejoin="round"/>
      <circle class="kk-r" fill="none" stroke="var(--bad)" stroke-width="${14 * k}"/>
      <circle class="kk-h" r="${HD}" fill="var(--paper)"/><rect class="kk-t" x="${-WW * 0.6}" width="${WW * 1.2}" height="${18 * k}" rx="${9 * k}" fill="var(--c1x)"/>
      ${tD.map(() => `<g class="kk-w"><rect x="${-WW / 2}" y="${-WH}" width="${WW}" height="${WH - 6 * k}" rx="${16 * k}" fill="var(--acc)"/></g>`).join('')}</svg>` +
    tD.map(() => api.at(0, 0, `<div style="font-family:var(--f-display);font-weight:800;font-size:${50 * k}px;color:var(--ink)">kilo</div>`, { cls: 'kk-l' })).join('') +
    api.at(L.x(0.77), L.y(0.16), wrap(p.gain || '', 72 * k, 'c1'), { cls: 'kk-t1', idle: 'sway' }) +
    api.at(L.x(0.77), L.y(0.4), wrap(p.kilo || '', 72 * k, ''), { cls: 'kk-t2', idle: 'sway' }) +
    api.at(L.x(0.77), L.y(0.7), wrap(p.more || '', 60 * k, 'bad'), { cls: 'kk-t3', idle: 'wobble' });
  const ws = qa(root, '.kk-w'), ll = qa(root, '.kk-l');
  return t => {
    let dip = 5 * k * Math.sin(t * 2.2), n = 0; tD.forEach((a, i) => { const u = t - a - 0.22; if (u >= 0) { n = i + 1; dip += 26 * k * (1 + 0.8 * Math.exp(-u * 7) * Math.cos(u * 26)); } });
    const hipY = gy - (TH + SH) * 0.985 + 18 * k + dip, H = gy - 30 * k - hipY, hx = fx - dip * 0.25, kx = fx + Math.sqrt(Math.max(0, TH * TH - (H / 2) ** 2)) + 4 * k, ky = hipY + H / 2;
    q(root, '.kk-leg').setAttribute('d', `M${hx} ${hipY} L${kx} ${ky} L${fx} ${gy - 30 * k}`);
    q(root, '.kk-ft').setAttribute('d', `M${fx} ${gy - 16 * k} L${fx + 90 * k} ${gy - 16 * k}`);
    const shY = hipY - TO; q(root, '.kk-to').setAttribute('d', `M${hx} ${hipY - 20 * k} L${hx} ${shY + 20 * k}`);
    const hy = shY - HD - 40 * k, ty = hy - HD - 24 * k;
    q(root, '.kk-ar').setAttribute('d', `M${hx - 40 * k} ${shY + 40 * k} L${hx - 118 * k} ${shY - 60 * k} L${hx - 118 * k} ${ty + 8 * k} M${hx + 40 * k} ${shY + 40 * k} L${hx + 118 * k} ${shY - 60 * k} L${hx + 118 * k} ${ty + 8 * k}`);
    const h = q(root, '.kk-h'); h.setAttribute('cx', hx); h.setAttribute('cy', hy);
    q(root, '.kk-t').setAttribute('transform', `translate(${hx} ${ty})`);
    ws.forEach((e, i) => { const a = tD[i], u = Math.min(1, Math.max(0, (t - a) / 0.22)), rest = ty - i * WH, y = rest - (1 - u * u) * (L.h * 0.8); R.gx(e, { y, s: 1, o: t > a ? 1 : 0 }, hx, 0);
      const l = ll[i]; l.style.left = hx + 'px'; l.style.top = (y - WH * 0.52) + 'px'; q(l, '.a').style.opacity = t > a ? 1 : 0; });
    const r = q(root, '.kk-r'); r.setAttribute('cx', kx); r.setAttribute('cy', ky); r.setAttribute('r', (56 * k + 16 * k * n + 8 * k * Math.sin(t * 7)).toFixed(1)); r.style.opacity = Math.min(1, n) * (0.7 + 0.3 * Math.sin(t * 7));
    api.tw(q(root, '.kk-t1 .a'), t, api.K.pop(tG - 0.05, 0.35, { o: 0, s: 0.3, r: 5 }));
    api.tw(q(root, '.kk-t2 .a'), t, api.K.pop(tK - 0.05, 0.35, { o: 0, s: 0.3, r: -5 }));
    api.tw(q(root, '.kk-t3 .a'), t, api.K.slam(tM - 0.05, 0.4));
  };
});
