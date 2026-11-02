/* @scene {"type":"burst_vs_rhythm","tags":["consistency","system","habit","rhythm","sprint"],"layout":"line-graph-pulse","metaphor":"one huge spike that crashes to zero versus a small steady heartbeat line","assets":["spike line","heartbeat line"]} */
// {spikeAt, spike:"...", beatAt, beat:"..."}
RM.def('burst_vs_rhythm', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tS = api.T(p.spikeAt), tB = api.T(p.beatAt), W = L.w, H = L.h * 0.62;
  const base = H * 0.86;
  const spike = `M0 ${base} L${W * 0.22} ${base} L${W * 0.3} ${H * 0.06} L${W * 0.36} ${base} L${W} ${base}`;
  let beat = `M0 ${base * 0.98}`;
  for (let i = 0; i < 9; i++) { const x = W * (0.04 + i * 0.11); beat += ` L${x} ${base * 0.98} L${x + W * 0.02} ${base * 0.72} L${x + W * 0.04} ${base * 1.04} L${x + W * 0.055} ${base * 0.98}`; }
  root.innerHTML = api.at(L.cx, L.y(0.58), `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" overflow="visible">
      <path d="M0 ${base + 8} H${W}" stroke="var(--line)" stroke-width="6"/>
      ${[0.25, 0.5, 0.75].map(u => `<path d="M0 ${H * u} H${W}" stroke="var(--line)" stroke-width="3" stroke-dasharray="10 14"/>`).join('')}
      <path class="br-sp" d="${spike}" fill="none" stroke="var(--bad)" stroke-width="${14 * k}" stroke-linejoin="round" stroke-linecap="round"/>
      <path class="br-bt" d="${beat}" fill="none" stroke="var(--acc)" stroke-width="${14 * k}" stroke-linejoin="round" stroke-linecap="round"/>
      <circle class="br-dot" r="${16 * k}" fill="var(--acc)"/></svg>`, { cls: 'br-g' }) +
    api.at(L.x(0.33), L.y(0.12), `<div style="display:flex;align-items:center;gap:${16 * k}px">${R.tag(p.spike || '', 64 * k, 'bad')}<div class="badge bad br-x" style="font-size:${90 * k}px">${api.icon('ph-bold:x', 52 * k)}</div></div>`, { cls: 'br-t1', idle: 'sway' }) +
    api.at(L.x(0.6), L.y(0.95), `<div style="display:flex;align-items:center;gap:${16 * k}px">${R.tag(p.beat || '', 68 * k, '')}<div class="badge good br-ok" style="font-size:${90 * k}px">${api.icon('ph-bold:check', 52 * k)}</div></div>`, { cls: 'br-t2', idle: 'sway' });
  const sp = q(root, '.br-sp'), bt = q(root, '.br-bt'), dot = q(root, '.br-dot');
  return t => {
    api.tw(q(root, '.br-g .a'), t, api.K.rise(api.start, 0.45, 200 * k));
    R.draw(sp, api.prog(t, tS - 0.3, tS + 0.5, 'io'));
    sp.style.opacity = 1 - 0.65 * api.prog(t, tB - 0.1, tB + 0.3, 'out');
    const u = api.prog(t, tB - 0.05, api.end - 0.1, 'lin'); R.draw(bt, u);
    const L2 = bt.getTotalLength(), pt = bt.getPointAtLength(L2 * Math.max(0.001, u));
    dot.setAttribute('cx', pt.x); dot.setAttribute('cy', pt.y); dot.style.opacity = u > 0.002 && u < 0.999 ? 1 : 0;
    api.tw(q(root, '.br-t1 .a'), t, api.K.pop(tS - 0.05, 0.4, { o: 0, s: 0.3, r: -12 }));
    api.tw(q(root, '.br-x'), t, api.K.pop(tS + 0.6, 0.35, { o: 0, s: 0 }));
    api.tw(q(root, '.br-t2 .a'), t, api.K.pop(tB, 0.4, { o: 0, s: 0.3, r: 10 }));
    api.tw(q(root, '.br-ok'), t, api.K.pop(tB + 0.4, 0.35, { o: 0, s: 0 }));
  };
});
