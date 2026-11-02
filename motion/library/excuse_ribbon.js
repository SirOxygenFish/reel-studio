/* @scene {"type":"excuse_ribbon","tags":["excuses","long explanations","not listening","why it failed"],"layout":"bubble-left-ribbon-snaking","metaphor":"an endless ribbon of excuse-scribbles pours out of a speech bubble and snakes across the screen; an ear switches off","assets":["speech bubble","scribble ribbon","ear with slash"]} */
// {earAt, tag, tagAt, whyAt, why}
RM.def('excuse_ribbon', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tE = api.T(p.earAt), tT = api.T(p.tagAt), tW = p.why ? api.T(p.whyAt) : 0;
  const W = L.w, H = L.h * 0.7, oy = L.y0 + L.h * 0.22;
  // the ribbon path snakes left-right down the box
  let d = `M ${W * 0.18} ${H * 0.05}`;
  for (let i = 0; i < 4; i++) { const y = H * (0.05 + i * 0.24), y2 = y + H * 0.24; d += i % 2 ? ` C ${-W * 0.05} ${y} ${-W * 0.05} ${y2} ${W * 0.2} ${y2}` : ` C ${W * 1.05} ${y} ${W * 1.05} ${y2} ${W * 0.8} ${y2}`; }
  root.innerHTML = `<svg class="er-s" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" style="position:absolute;left:${L.x0}px;top:${oy}px;overflow:visible">
      <path class="er-band" d="${d}" fill="none" stroke="var(--paper)" stroke-width="${120 * k}" stroke-linecap="round" style="filter:drop-shadow(0 ${10 * k}px ${12 * k}px var(--hard-shadow))"/>
      <mask id="erm" maskUnits="userSpaceOnUse" x="${-W}" y="${-H}" width="${3 * W}" height="${3 * H}"><path class="er-mk" d="${d}" fill="none" stroke="#fff" stroke-width="${130 * k}" stroke-linecap="round"/></mask>
      <path class="er-ink" mask="url(#erm)" d="${d}" fill="none" stroke="var(--muted)" stroke-width="${16 * k}" stroke-dasharray="${26 * k} ${12 * k} ${8 * k} ${16 * k}" stroke-linecap="round"/></svg>` +
    api.at(L.x(0.16), L.y(0.12), `<div class="bubble" style="font-size:${90 * k}px;padding:.25em .5em">${api.icon('ph-fill:chat-teardrop-dots', 170 * k, 'var(--c1)')}</div>`, { cls: 'er-bub', idle: 'wobble' }) +
    api.at(L.x(0.8), L.y(0.86), `<div class="round" style="width:${300 * k}px;height:${300 * k}px;background:var(--paper);display:flex;align-items:center;justify-content:center;box-shadow:var(--sh)">${api.icon('ph:ear-slash', 200 * k, 'var(--bad)')}</div>`, { cls: 'er-ear' }) +
    api.at(L.x(0.6), L.y(0.08), R.tag(p.tag || '', 68 * k, 'c1'), { cls: 'er-t', idle: 'sway' }) +
    (p.why ? api.at(L.x(0.36), L.y(0.95), R.tag(p.why, 56 * k, 'bad'), { cls: 'er-w', idle: 'sway' }) : '');
  const band = q(root, '.er-band'), ink = q(root, '.er-ink'), len = band.getTotalLength();
  return t => {
    api.tw(q(root, '.er-bub .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0.3 }));
    const u = api.prog(t, api.start + 0.2, api.end - 0.2, 'lin');
    R.draw(band, u); R.draw(q(root, '.er-mk'), u);                     // the band and its scribbles grow together
    ink.style.strokeDashoffset = (-t * 260 * k).toFixed(1);             // the scribbles keep scrolling along the band
    ink.style.opacity = u > 0.01 ? 1 : 0;
    q(root, '.er-s').style.opacity = 1 - 0.6 * api.prog(t, tE + 0.2, tE + 0.6, 'out');
    api.tw(q(root, '.er-ear .a'), t, api.K.spring(tE - 0.05, 0.55, { o: 0, s: 0.2, r: -25 }));
    api.tw(q(root, '.er-t .a'), t, api.K.pop(tT - 0.05, 0.4, { o: 0, s: 0.3, r: 10 }));
    if (p.why) api.tw(q(root, '.er-w .a'), t, api.K.pop(tW - 0.05, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
