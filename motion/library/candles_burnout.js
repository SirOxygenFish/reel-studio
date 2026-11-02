/* @scene {"type":"candles_burnout","tags":["motivation","quitting","fire","burnout","most people"],"layout":"row-of-candles","metaphor":"a row of candle-people lit with fire that go out one by one, only a few keep burning","assets":["candles with faces","flames","smoke curls"]} */
// {tag, tagAt, fireAt, fireTag, fireTagAt, outAt, outTag, stay:[i,...]}
RM.def('candles_burnout', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tF = api.T(p.fireAt), tO = api.T(p.outAt), tTag = p.tag ? api.T(p.tagAt ?? api.start + 0.2) : 0;
  const tFT = api.T(p.fireTagAt ?? p.fireAt), stay = p.stay || [2, 5], N = 7;
  const H = [300, 360, 420, 330, 390, 450, 310], W = 900 * k, sp = 128;
  let order = 0; const outT = H.map((_, i) => (stay.includes(i) ? Infinity : tO + 0.05 + (order++) * 0.17));
  const candle = (h, i) => `<g class="cb-c" data-i="${i}" transform="translate(${(i - 3) * sp} 0)">
      <rect x="-42" y="${-h}" width="84" height="${h}" rx="18" fill="var(--paper)" stroke="var(--c2)" stroke-width="7"/>
      <path d="M-42 ${-h + 40} q 20 26 42 0 q 22 -26 42 0" fill="none" stroke="var(--c1l)" stroke-width="9"/>
      <g class="cb-eyes"><circle cx="-14" cy="${-h + 90}" r="7" fill="var(--ink)"/><circle cx="14" cy="${-h + 90}" r="7" fill="var(--ink)"/></g>
      <path class="cb-sleep" d="M-22 ${-h + 92} h16 M6 ${-h + 92} h16" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"/>
      <path d="M0 ${-h} v-22" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"/>
      <g class="cb-fl" transform="translate(0 ${-h - 22})"><path d="M0 0 C -30 -20 -24 -62 0 -96 C 24 -62 30 -20 0 0 Z" fill="var(--c1)"/><path d="M0 -6 C -14 -18 -12 -40 0 -58 C 12 -40 14 -18 0 -6 Z" fill="var(--paper)" opacity=".85"/></g>
      <path class="cb-sm" d="M0 ${-h - 30} c -18 -30 18 -50 0 -80 c -18 -30 18 -50 0 -80" fill="none" stroke="var(--muted)" stroke-width="7" stroke-linecap="round" opacity=".6"/></g>`;
  root.innerHTML = api.at(L.cx, L.y(0.6), `<svg width="${W}" height="${W * 0.85}" viewBox="-450 -720 900 765" overflow="visible">
      <rect x="-450" y="0" width="900" height="26" rx="13" fill="var(--c2)"/>${H.map(candle).join('')}</svg>`, { cls: 'cb-row' }) +
    (p.tag ? api.at(L.x(0.26), L.y(0.08), R.tag(p.tag, 72 * k, 'c1'), { cls: 'cb-t0', idle: 'sway' }) : '') +
    api.at(L.cx, L.y(0.2), R.tag(p.fireTag || '', 70 * k, ''), { cls: 'cb-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.2), R.tag(p.outTag || '', 74 * k, 'bad'), { cls: 'cb-t2', idle: 'sway' });
  const cs = qa(root, '.cb-c');
  return t => {
    api.tw(q(root, '.cb-row .a'), t, api.K.rise(api.start, 0.5, 300 * k));
    cs.forEach((c, i) => {
      const on = api.prog(t, tF + i * 0.11, tF + i * 0.11 + 0.3, 'back'), off = api.prog(t, outT[i], outT[i] + 0.25, 'in');
      const v = Math.max(0, on * (1 - (isFinite(outT[i]) ? off : 0))), fl = q(c, '.cb-fl'), y = -H[i] - 22;
      fl.setAttribute('transform', `translate(0 ${y}) scale(${(v * (1 + 0.08 * Math.sin(t * 17 + i * 2))).toFixed(3)} ${(v * (1 + 0.12 * Math.sin(t * 11 + i))).toFixed(3)}) rotate(${(5 * Math.sin(t * 7 + i)).toFixed(1)})`);
      fl.style.opacity = v > 0.01 ? 1 : 0;
      const sm = q(c, '.cb-sm'), live = isFinite(outT[i]) && t > outT[i];
      if (live) R.draw(sm, api.prog(t, outT[i] + 0.1, outT[i] + 0.8, 'out'));
      sm.style.opacity = live ? 0.6 * (1 - api.prog(t, outT[i] + 0.8, outT[i] + 1.4, 'lin')) : 0;
      q(c, '.cb-eyes').style.opacity = t < outT[i] + 0.15 ? 1 : 0; q(c, '.cb-sleep').style.opacity = t < outT[i] + 0.15 ? 0 : 1;
      c.setAttribute('transform', `translate(${(i - 3) * sp} ${(t > outT[i] ? 10 * api.prog(t, outT[i], outT[i] + 0.4, 'out') : -6 * on * Math.abs(Math.sin(t * 3 + i))).toFixed(1)})`);
    });
    if (p.tag) api.tw(q(root, '.cb-t0 .a'), t, api.K.pop(tTag, 0.4, { o: 0, s: 0.3, r: -14 }).concat([[tFT - 0.2, {}], [tFT + 0.1, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.cb-t1 .a'), t, api.K.pop(tFT - 0.05, 0.4, { o: 0, s: 0.3, r: 12 }).concat([[tO - 0.2, {}], [tO + 0.05, { o: 0, y: -60 * k }, 'in']]));
    api.tw(q(root, '.cb-t2 .a'), t, api.K.slam(tO, 0.4));
  };
});
