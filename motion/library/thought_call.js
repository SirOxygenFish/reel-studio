/* @scene {"type":"thought_call","tags":["fear","imagination","phone","future","reproach","call"],"layout":"phone-and-thought-cloud","metaphor":"a phone call that spirals into an imagined reproach inside a thought cloud","assets":["candybar phone","thought cloud","tear-off calendar","grumpy face"]} */
// {year:"...", yearAt, callAt, cloudAt, calAt, calTag:"...", faceAt, quote:"..."}
RM.def('thought_call', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const T = (r, d) => (r === undefined ? d : api.T(r));
  const tYear = T(p.yearAt, api.start + 0.2), tCall = T(p.callAt, tYear + 1.5), tCloud = T(p.cloudAt, tCall + 1), tCal = T(p.calAt, tCloud + 1), tFace = T(p.faceAt, tCal + 1.2);
  const PW = 360 * k, PH = 685 * k;
  const keys = Array.from({ length: 12 }, (_, i) => `<rect x="${31 + (i % 3) * 49}" y="${224 + Math.floor(i / 3) * 34}" width="40" height="24" rx="11" fill="var(--c1l)"/>`).join('');
  const phone = `<svg width="${PW}" height="${PH}" viewBox="0 0 200 380" overflow="visible">
      <rect x="146" y="-28" width="20" height="44" rx="9" fill="var(--c2)"/>
      <rect x="0" y="0" width="200" height="380" rx="58" fill="var(--c2)"/>
      <rect x="9" y="9" width="182" height="362" rx="50" fill="none" stroke="var(--c1l)" stroke-width="3" opacity=".45"/>
      <rect x="27" y="50" width="146" height="122" rx="16" fill="var(--acc-soft)" stroke="var(--ink)" stroke-width="5"/>
      <text x="100" y="128" text-anchor="middle" style="font-family:var(--f-display);font-weight:900;font-size:50px" fill="var(--ink)">${R.esc(p.year || '')}</text>
      <ellipse cx="100" cy="197" rx="34" ry="12" fill="var(--c1)"/>${keys}</svg>`;
  const waves = `<svg width="${260 * k}" height="${260 * k}" viewBox="-130 -130 260 260" overflow="visible">${[0, 1, 2].map(i =>
      `<path class="tc-w" d="M ${40 + i * 30} ${-40 - i * 30} A ${57 + i * 42} ${57 + i * 42} 0 0 1 ${40 + i * 30} ${40 + i * 30}" fill="none" stroke="var(--acc)" stroke-width="12" stroke-linecap="round"/>`).join('')}</svg>`;
  const CW = 900 * k, CH = 640 * k;
  const blobs = [[450, 330, 250], [250, 360, 175], [650, 360, 180], [330, 210, 165], [570, 200, 175], [450, 160, 150], [160, 300, 110], [740, 290, 115], [450, 470, 170]];
  const cloud = `<svg width="${CW}" height="${CH}" viewBox="0 0 900 640" overflow="visible" style="filter:drop-shadow(0 ${22 * k}px ${30 * k}px var(--hard-shadow))">
      ${blobs.map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r + 7}" fill="var(--c1l)"/>`).join('')}${blobs.map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="var(--paper)"/>`).join('')}</svg>`;
  const dots = [0, 1, 2].map(i => api.at(0, 0, `<div class="round" style="width:${(46 + i * 26) * k}px;height:${(46 + i * 26) * k}px;background:var(--paper);box-shadow:0 0 0 ${7 * k}px var(--c1l)"></div>`, { cls: 'tc-dot tc-dot' + i })).join('');
  const page = i => `<g class="tc-pg" data-i="${i}"><rect x="-150" y="-175" width="300" height="350" rx="22" fill="var(--paper)" stroke="var(--c2)" stroke-width="7"/>
      <rect x="-150" y="-175" width="300" height="78" rx="22" fill="${i % 2 ? 'var(--c1)' : 'var(--acc)'}"/><rect x="-150" y="-120" width="300" height="24" fill="${i % 2 ? 'var(--c1)' : 'var(--acc)'}"/>
      ${[-90, -30, 30, 90].map(x => `<circle cx="${x}" cy="-175" r="11" fill="var(--c2)"/>`).join('')}
      ${Array.from({ length: 20 }, (_, d) => `<rect x="${-118 + (d % 5) * 50}" y="${-70 + Math.floor(d / 5) * 58}" width="36" height="36" rx="9" fill="var(--c1x)"/>`).join('')}</g>`;
  const cal = `<svg width="${340 * k}" height="${390 * k}" viewBox="-170 -195 340 390" overflow="visible">${[5, 4, 3, 2, 1, 0].map(page).join('')}</svg>`;
  const face = `<svg width="${300 * k}" height="${300 * k}" viewBox="-150 -150 300 300" overflow="visible">
      <circle cx="0" cy="0" r="128" fill="var(--c1l)" stroke="var(--c2)" stroke-width="9"/>
      <path class="tc-brow" d="M -78 -44 L -22 -24 M 78 -44 L 22 -24" stroke="var(--ink)" stroke-width="15" stroke-linecap="round"/>
      <circle cx="-48" cy="-2" r="13" fill="var(--ink)"/><circle cx="48" cy="-2" r="13" fill="var(--ink)"/>
      <path d="M -52 72 Q 0 30 52 72" fill="none" stroke="var(--ink)" stroke-width="14" stroke-linecap="round"/></svg>`;
  const cx = L.cx, cy = L.y(0.37);
  root.innerHTML =
    api.at(cx + 20 * k, cy, cloud, { cls: 'tc-cloud', idle: 'breathe', amp: 0.6 }) + dots +
    api.at(cx, cy + 10 * k, cal, { cls: 'tc-cal' }) +
    api.at(cx - 255 * k, cy + 5 * k, face, { cls: 'tc-face', idle: 'wobble' }) +
    api.at(cx + 175 * k, cy + 5 * k, `<div class="bubble acc tc-bub" style="font-size:${56 * k}px;width:${470 * k}px;white-space:normal">${api.kt(p.quote || '', { mode: 'pop' })}</div>`, { cls: 'tc-q' }) +
    (p.calTag ? api.at(cx + 230 * k, cy + 215 * k, R.tag(p.calTag, 70 * k, 'c1'), { cls: 'tc-tag', idle: 'sway' }) : '') +
    api.at(0, 0, waves, { cls: 'tc-waves' }) +
    (p.year ? api.at(cx, L.y(0.1), `<div class="big tc-big" style="font-size:${230 * k}px;color:var(--c2)">${R.esc(p.year)}</div>`, { cls: 'tc-y', idle: 'float' }) : '') +
    api.at(cx, L.y(0.62), phone, { cls: 'tc-phone' });
  const bub = q(root, '.tc-bub .kt'), wt = api.times(p.quote || '', tFace - 0.1, api.end);
  const ph = q(root, '.tc-phone'), wv = q(root, '.tc-waves');
  const P0 = [cx, L.y(0.62)], P1 = [L.x(0.15), L.y(0.83)];
  return t => {
    // phone: drops in, rings, then moves to the corner and the thought grows out of it
    const u = api.prog(t, tCloud - 0.15, tCloud + 0.45, 'io');
    const px = P0[0] + (P1[0] - P0[0]) * u, py = P0[1] + (P1[1] - P0[1]) * u;
    ph.style.left = px + 'px'; ph.style.top = py + 'px';
    const ring = t > tCall && t < tCloud + 0.3 ? Math.sin((t - tCall) * 38) * 5 : 0;
    api.tw(q(ph, '.a'), t, api.K.drop(api.start, 0.55, -420 * k).concat([[tCloud - 0.15, {}], [tCloud + 0.45, { s: 0.5, r: -12 }, 'io']]));
    q(ph, '.i').style.transform = `rotate(${ring.toFixed(2)}deg)`;
    api.tw(q(root, '.tc-y .a'), t, api.K.slam(tYear - 0.05, 0.4).concat([[tCloud - 0.3, {}], [tCloud + 0.05, { o: 0, s: 0.4, y: 300 * k }, 'in']]));
    wv.style.left = (px + 120 * k * (1 - u * 0.5)) + 'px'; wv.style.top = (py - 260 * k * (1 - u * 0.5)) + 'px';
    qa(wv, '.tc-w').forEach((w, i) => { const c = ((t - tCall) * 2.2 - i * 0.22) % 1; w.style.opacity = t > tCall && t < tCloud + 0.2 ? Math.max(0, 1 - c) * (c > 0 ? 1 : 0) : 0; });
    // thought: three bubbles from the phone, then the cloud
    qa(root, '.tc-dot').forEach((d, i) => {
      const f = (i + 1) / 4, x = P1[0] + 60 * k + (cx - P1[0]) * f * 0.75, y = P1[1] - 120 * k + (cy + 230 * k - P1[1]) * f;
      d.style.left = x + 'px'; d.style.top = y + 'px';
      api.tw(q(d, '.a'), t, api.K.pop(tCloud + 0.1 + i * 0.1, 0.35, { o: 0, s: 0 }));
    });
    api.tw(q(root, '.tc-cloud .a'), t, api.K.spring(tCloud + 0.3, 0.7, { o: 0, s: 0.15 }));
    // calendar: half a year of pages tears off, then gives way to the reproach
    api.tw(q(root, '.tc-cal .a'), t, api.K.pop(tCloud + 0.55, 0.45, { o: 0, s: 0.3, r: -10 }).concat([[tFace - 0.25, {}], [tFace + 0.05, { o: 0, s: 0.6, x: 120 * k }, 'in']]));
    qa(root, '.tc-pg').forEach(g => {
      const i = +g.dataset.i, a = tCal + i * 0.14;
      if (i === 5) { g.setAttribute('transform', ''); return; }
      const v = api.prog(t, a, a + 0.32, 'in');
      g.setAttribute('transform', `translate(${(-60 * v).toFixed(1)} ${(380 * v * v).toFixed(1)}) rotate(${(-38 * v).toFixed(1)})`);
      g.style.opacity = 1 - api.prog(t, a + 0.15, a + 0.32, 'lin');
    });
    if (p.calTag) api.tw(q(root, '.tc-tag .a'), t, [[tCal + 0.15, { o: 0, s: 0.3, r: 18 }], [tCal + 0.55, { o: 1, s: 1, r: -5 }, 'back'], [tFace - 0.25, {}], [tFace + 0.05, { o: 0, s: 0.7 }, 'in']]);
    api.tw(q(root, '.tc-face .a'), t, api.K.spring(tFace - 0.12, 0.6, { o: 0, s: 0.2, r: -20 }));
    api.tw(q(root, '.tc-q .a'), t, api.K.pop(tFace - 0.05, 0.45, { o: 0, s: 0.3, x: -120 * k }));
    q(root, '.tc-brow').setAttribute('transform', `translate(0 ${(t > tFace ? 6 * Math.abs(Math.sin((t - tFace) * 7)) : 0).toFixed(1)})`);
    api.ktUpdate(bub, t, wt);
  };
});
