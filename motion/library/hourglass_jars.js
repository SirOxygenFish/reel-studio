/* @scene {"type":"hourglass_jars","tags":["time","family","priorities","life balance","freedom"],"layout":"hourglass-top-jars-row","metaphor":"the sand of an hourglass pours into jars for the things time is now spent on","assets":["hourglass","glass jars filling","flowing sand"]} */
// {word:"...", wordAt, jars:[{label, at}]}
RM.def('hourglass_jars', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tW = api.T(p.wordAt), jars = p.jars || [], ts = jars.map(j => api.T(j.at)), n = jars.length;
  const HG = 300 * k, hx = L.x(0.62), hy = L.y(0.3), tEnd = ts[n - 1] + 0.6;
  const glass = `<svg width="${HG}" height="${HG * 1.5}" viewBox="-100 -150 200 300" overflow="visible">
      <rect x="-96" y="-150" width="192" height="20" rx="8" fill="var(--c2)"/><rect x="-96" y="130" width="192" height="20" rx="8" fill="var(--c2)"/>
      <clipPath id="hgTop"><path d="M-80 -130 H80 Q80 -40 8 -4 H-8 Q-80 -40 -80 -130 Z"/></clipPath>
      <clipPath id="hgBot"><path d="M-8 4 H8 Q80 40 80 130 H-80 Q-80 40 -8 4 Z"/></clipPath>
      <rect class="hg-top" clip-path="url(#hgTop)" x="-90" y="-130" width="180" height="130" fill="var(--c1)"/>
      <rect class="hg-bot" clip-path="url(#hgBot)" x="-90" y="130" width="180" height="0" fill="var(--c1)"/>
      <path d="M-80 -130 H80 Q80 -40 8 -4 Q80 40 80 130 H-80 Q-80 40 -8 -4 Q-80 -40 -80 -130 Z" fill="none" stroke="var(--c2)" stroke-width="8" opacity=".8"/>
      <rect class="hg-str" x="-3" y="-6" width="6" height="136" fill="var(--c1)"/></svg>`;
  const JW = Math.min(185, 920 / n) * k, jy = L.y(0.78);
  const jar = i => `<svg width="${JW}" height="${JW * 1.25}" viewBox="0 0 100 125" overflow="visible">
      <clipPath id="jc${i}"><path d="M12 22 H88 V112 Q88 122 78 122 H22 Q12 122 12 112 Z"/></clipPath>
      <rect class="jr-f" clip-path="url(#jc${i})" x="0" y="122" width="100" height="0" fill="${['var(--acc)', 'var(--c1)', 'var(--good)', 'var(--c2)', 'var(--bad)'][i % 5]}"/>
      <path d="M12 22 H88 V112 Q88 122 78 122 H22 Q12 122 12 112 Z" fill="none" stroke="var(--c2)" stroke-width="6"/>
      <rect x="6" y="8" width="88" height="16" rx="6" fill="var(--c2)"/></svg>`;
  root.innerHTML = api.at(hx, hy, glass, { cls: 'hg-g', idle: 'sway', amp: 0.5 }) +
    api.at(L.x(0.22), L.y(0.26), `<div class="big" style="font-size:${170 * k}px;color:var(--c2)">${R.esc(p.word || '')}</div>`, { cls: 'hg-w' }) +
    jars.map((j, i) => api.at(L.x((i + 0.5) / n), jy, `<div style="display:flex;flex-direction:column;align-items:center;gap:${12 * k}px">${jar(i)}<div class="label hg-lb" style="font-size:${46 * k}px;color:var(--c2)">${R.esc(j.label)}</div></div>`, { cls: 'hg-j', idle: 'bob', amp: 0.4 })).join('') +
    `<svg class="hg-pour" style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><path class="hg-arc" fill="none" stroke="var(--c1)" stroke-width="${10 * k}" stroke-linecap="round" stroke-dasharray="4 18"/></svg>`;
  qa(root, '.hg-lb').forEach(el => R.fitFont(el, L.w / n - 6 * k, 0, 46 * k, 22));
  return t => {
    api.tw(q(root, '.hg-g .a'), t, api.K.drop(api.start, 0.5, -500 * k));
    api.tw(q(root, '.hg-w .a'), t, api.K.slam(tW, 0.4));
    const u = api.prog(t, tW - 0.2, tEnd, 'lin');
    q(root, '.hg-top').setAttribute('y', (-130 + 130 * u).toFixed(1)); q(root, '.hg-bot').setAttribute('y', (130 - 60 * u).toFixed(1)); q(root, '.hg-bot').setAttribute('height', (60 * u).toFixed(1));
    q(root, '.hg-str').style.opacity = u > 0.01 && u < 0.99 ? 1 : 0;
    let cur = -1;
    qa(root, '.hg-j').forEach((j, i) => {
      api.tw(q(j, '.a'), t, api.K.pop(ts[i] - 0.1, 0.4, { o: 0, s: 0.3, y: 60 * k }));
      const f = api.prog(t, ts[i], (ts[i + 1] ?? tEnd) + 0.1, 'out'); if (t >= ts[i]) cur = i;
      const r = q(j, '.jr-f'); r.setAttribute('y', (122 - 92 * f).toFixed(1)); r.setAttribute('height', (92 * f).toFixed(1));
    });
    // a dotted stream of sand arcs from the hourglass neck into the jar being filled
    const arc = q(root, '.hg-arc');
    if (cur >= 0 && t < tEnd) {
      const x0 = hx, y0 = hy + HG * 0.75, x1 = L.x((cur + 0.5) / n), y1 = jy - JW * 0.5;
      arc.setAttribute('d', `M${x0} ${y0} Q${(x0 + x1) / 2} ${Math.min(y0, y1) - 60 * k} ${x1} ${y1}`);
      arc.style.strokeDashoffset = (-t * 120).toFixed(1); arc.style.opacity = 0.9;
    } else arc.style.opacity = 0;
  };
});
