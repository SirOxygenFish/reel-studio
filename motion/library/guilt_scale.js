/* @scene {"type":"guilt_scale","tags":["guilt","blame","charges","justice","innocent"],"layout":"balance-scale-center","metaphor":"charges land on the scale of guilt and are struck off one by one until it swings empty","assets":["balance scale","money bag","locked rulebook","storybook"]} */
// {charges:[{label, at, kind:"..."}], verdict:"...", verdictAt}
RM.def('guilt_scale', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const ch = p.charges || [], ts = ch.map(c => api.T(c.at)), tV = api.T(p.verdictAt);
  const S = 720 * k;                                   // scale drawing width
  const ART = {
    money: `<path d="M-62 -40 Q-90 60 -40 88 L40 88 Q90 60 62 -40 Z" fill="var(--c1)" stroke="var(--c2)" stroke-width="8"/><path d="M-36 -46 L-50 -84 L50 -84 L36 -46 Z" fill="var(--c1)" stroke="var(--c2)" stroke-width="8"/><rect x="-44" y="-56" width="88" height="18" rx="9" fill="var(--c2)"/><circle cx="0" cy="26" r="30" fill="none" stroke="var(--paper)" stroke-width="9"/><path d="M0 2 V50" stroke="var(--paper)" stroke-width="9"/>`,
    rules: `<rect x="-70" y="-84" width="140" height="172" rx="12" fill="var(--c2)"/><rect x="-56" y="-84" width="12" height="172" fill="var(--ink)" opacity=".35"/><rect x="-30" y="-50" width="76" height="12" rx="6" fill="var(--c1l)"/><rect x="-30" y="-26" width="56" height="12" rx="6" fill="var(--c1l)"/><rect x="-6" y="14" width="56" height="46" rx="8" fill="var(--acc)"/><path d="M6 14 V0 A16 16 0 0 1 38 0 V14" fill="none" stroke="var(--acc)" stroke-width="9"/>`,
    tale: `<path d="M0 -60 Q-50 -86 -96 -70 V76 Q-50 60 0 84 Q50 60 96 76 V-70 Q50 -86 0 -60 Z" fill="var(--paper)" stroke="var(--c2)" stroke-width="8"/><path d="M0 -60 V84" stroke="var(--c2)" stroke-width="6"/><path d="M-50 -26 l8 16 18 3 -13 12 3 18 -16 -8 -16 8 3 -18 -13 -12 18 -3 Z" fill="var(--c1)"/><path d="M30 -30 H70 M30 -6 H70 M30 18 H62" stroke="var(--c1l)" stroke-width="8" stroke-linecap="round"/>`,
  };
  const scale = `<svg width="${S}" height="${S * 0.95}" viewBox="-450 -80 900 860" overflow="visible">
      <path d="M-120 760 Q0 700 120 760 Z" fill="var(--c2)"/><rect x="-14" y="40" width="28" height="700" rx="12" fill="var(--c2)"/>
      <circle cx="0" cy="40" r="36" fill="var(--c1)" stroke="var(--c2)" stroke-width="8"/>
      <g class="gs-beam"><rect x="-400" y="28" width="800" height="24" rx="12" fill="var(--c2)"/>
        <g class="gs-panL" transform="translate(-370 40)"><g class="gs-hangL"><path d="M0 0 L-120 300 M0 0 L120 300" stroke="var(--struct)" stroke-width="6"/><path d="M-160 300 Q0 380 160 300 Z" fill="var(--c1)" stroke="var(--c2)" stroke-width="8"/>
          <g class="gs-load" transform="translate(0 220)">${ch.map((c, i) => `<g class="gs-ch" data-i="${i}" transform="translate(${(i - (ch.length - 1) / 2) * 120} 0) scale(.95)">${ART[c.kind] || ART.money}</g>`).join('')}</g></g></g>
        <g class="gs-panR" transform="translate(370 40)"><g class="gs-hangR"><path d="M0 0 L-120 300 M0 0 L120 300" stroke="var(--struct)" stroke-width="6"/><path d="M-160 300 Q0 380 160 300 Z" fill="var(--c1)" stroke="var(--c2)" stroke-width="8"/></g></g></g></svg>`;
  root.innerHTML = api.at(L.cx, L.y(0.62), scale, { cls: 'gs-sc' }) +
    ch.map((c, i) => api.at(L.cx, L.y(0.06) + i * 122 * k, `<div class="card gs-card" style="display:flex;align-items:center;gap:${24 * k}px;padding:${14 * k}px ${34 * k}px;font-size:${86 * k}px"><span class="big">${R.esc(c.label)}</span></div>`, { cls: 'gs-c gs-c' + i })).join('') +
    ch.map((c, i) => api.at(L.cx, L.y(0.06) + i * 122 * k, `<div style="width:${1}px;height:${12 * k}px;background:var(--bad);border-radius:${6 * k}px"></div>`, { cls: 'gs-strike gs-s' + i })).join('') +
    api.at(L.cx, L.y(0.47), `<div class="tag bad gs-v" style="font-size:${150 * k}px">${R.esc(p.verdict || '')}</div>`, { cls: 'gs-ver', idle: 'wobble' });
  qa(root, '.gs-card .big').forEach(el => R.fitFont(el, L.w * 0.86, 0, 86 * k));
  return t => {
    api.tw(q(root, '.gs-sc .a'), t, api.K.rise(api.start, 0.5, 220 * k));
    // weight on the left pan: each charge lands (+), then is struck off (-) as the next sentence starts
    let load = 0;
    ch.forEach((c, i) => {
      const land = ts[i] + 0.25, off = (i + 1 < ch.length ? ts[i + 1] : tV) - 0.1;
      const inn = api.prog(t, ts[i], land, 'out'), out = api.prog(t, off, off + 0.35, 'in');
      load += inn - out;
      const g = q(root, `.gs-ch[data-i="${i}"]`), base = `translate(${(i - (ch.length - 1) / 2) * 120} 0)`;
      g.setAttribute('transform', `${base} translate(0 ${(-420 * (1 - inn) - 260 * out).toFixed(1)}) scale(${(0.95 * (1 - 0.4 * out)).toFixed(3)})`);
      g.style.opacity = (inn > 0 ? 1 : 0) * (1 - out);
      // the charge as text: pops in on its word, a strike line crosses it, then it fades
      api.tw(q(root, `.gs-c${i} .a`), t, api.K.pop(ts[i] - 0.05, 0.4, { o: 0, s: 0.4, r: i % 2 ? 6 : -6 }).concat([[off + 0.35, {}], [off + 0.6, { o: 0.32, s: 0.92 }, 'lin']]));
      const sw = q(root, `.gs-s${i} .a > .i > div`), w = q(root, `.gs-c${i} .gs-card`).getBoundingClientRect().width;
      sw.style.width = (w * 1.04 * api.prog(t, off, off + 0.25, 'out')) + 'px';
      api.tw(q(root, `.gs-s${i} .a`), t, [[off, { o: 0 }], [off + 0.02, { o: 1 }], [off + 0.35, {}], [off + 0.6, { o: 0.5 }]]);
    });
    const tilt = Math.max(-1, Math.min(1, load)) * -11 + (t > tV ? 4 * Math.exp(-(t - tV) * 2.5) * Math.sin((t - tV) * 9) : 0);
    q(root, '.gs-beam').setAttribute('transform', `rotate(${tilt.toFixed(2)})`);
    q(root, '.gs-hangL').setAttribute('transform', `rotate(${(-tilt).toFixed(2)})`); q(root, '.gs-hangR').setAttribute('transform', `rotate(${(-tilt).toFixed(2)})`);
    api.tw(q(root, '.gs-ver .a'), t, api.K.slam(tV - 0.05, 0.45).map(kf => [kf[0], Object.assign({ r: -6 }, kf[1]), kf[2]]));
  };
});
