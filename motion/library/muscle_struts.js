/* @scene {"type":"muscle_struts","tags":["strong muscles","take pressure off","joints","support"],"layout":"block-on-hinge-two-struts-grow-either-side","metaphor":"a heavy block presses down on one small hinge; two muscle-shaped struts grow beside it and lift the block clear of the hinge","assets":["heavy block","small hinge","muscle-shaped struts","stress marks"]} */
// {block, joint, strong, strongAt, takeAt, offAt}
RM.def('muscle_struts', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.strongAt), tT = api.T(p.takeAt), tO = api.T(p.offAt);
  const cx = L.cx, gy = L.y(0.86), hy = L.y(0.62), HR = 74 * k, BW = 680 * k, BH = 220 * k, LIFT = 120 * k, by0 = hy - HR - BH / 2 + 8 * k, sx = 262 * k;
  const h0 = gy - (by0 + BH / 2);
  const mus = `M-34 0 C-120 ${-h0 * 0.25} -125 ${-h0 * 0.72} -36 ${-h0} L36 ${-h0} C125 ${-h0 * 0.72} 120 ${-h0 * 0.25} 34 0 Z`;
  const fib = `M-40 ${-h0 * 0.3} Q0 ${-h0 * 0.36} 44 ${-h0 * 0.28} M-46 ${-h0 * 0.55} Q0 ${-h0 * 0.62} 48 ${-h0 * 0.55}`;
  const zig = (a, d) => { const c = Math.cos(a), s = Math.sin(a), pt = (r, o) => `${(cx + c * r - s * o).toFixed(1)} ${(hy + s * r + c * o).toFixed(1)}`; return `M${pt(d, 0)} L${pt(d + 40 * k, 20 * k)} L${pt(d + 70 * k, -20 * k)} L${pt(d + 110 * k, 0)}`; };
  const ZB = [0.15, 0.85, 2.3, 3.0].map(a => zig(a, HR + 26 * k));
  const m = `<path d="${mus}" fill="var(--c1)"/><path d="${fib}" fill="none" stroke="var(--c1x)" stroke-width="${8 * k}" stroke-linecap="round"/>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <line x1="${L.x0 + 20}" x2="${L.x1 - 20}" y1="${gy}" y2="${gy}" stroke="var(--c1l)" stroke-width="${12 * k}" stroke-linecap="round"/>
      <rect x="${cx - 26 * k}" y="${hy}" width="${52 * k}" height="${gy - hy}" fill="var(--c2)"/>
      <g class="ms-m">${m}</g><g class="ms-m">${m}</g>
      ${ZB.map(d => `<path class="ms-z" d="${d}" fill="none" stroke="var(--bad)" stroke-width="${13 * k}" stroke-linecap="round" stroke-linejoin="round"/>`).join('')}
      <circle class="ms-h" cx="${cx}" cy="${hy}" r="${HR}" fill="var(--paper)" stroke="var(--bad)" stroke-width="${16 * k}"/><circle cx="${cx}" cy="${hy}" r="${22 * k}" fill="var(--c2)"/></svg>` +
    api.at(cx, by0, `<div style="width:${BW}px;height:${BH}px;border-radius:${26 * k}px;background:linear-gradient(170deg,var(--paper),var(--c1x));box-shadow:var(--sh);display:flex;align-items:center;justify-content:center;font-family:var(--f-display);font-weight:800;font-size:${88 * k}px;color:var(--ink)">${R.esc(p.block || '')}</div>`, { cls: 'ms-bk' }) +
    api.at(cx, L.y(0.95), R.tag(p.joint || '', 62 * k, ''), { cls: 'ms-j' }) +
    api.at(cx, L.y(0.06), R.tag(p.strong || '', 92 * k, 'c1'), { cls: 'ms-t1', idle: 'sway' });
  const ms = qa(root, '.ms-m'), bk = q(root, '.ms-bk');
  return t => {
    const u = api.prog(t, tO - 0.1, tO + 0.4, 'out'), g = api.prog(t, tS, tT + 0.1, 'out');
    bk.style.top = (by0 - LIFT * u + (u < 0.01 ? 6 * k * Math.abs(Math.sin(t * 9)) : 0)) + 'px';
    api.tw(q(bk, '.a'), t, api.K.drop(api.start, 0.4, -300 * k));
    ms.forEach((e, i) => e.setAttribute('transform', `translate(${cx + (i ? sx : -sx)} ${gy}) scale(${(1 + 0.08 * u * Math.sin(t * 7 + i)).toFixed(3)} ${Math.max(0.001, g * (h0 + LIFT * u) / h0).toFixed(4)})`));
    qa(root, '.ms-z').forEach((e, i) => { const a = 1 - api.prog(t, tO, tO + 0.3, 'lin'); e.style.opacity = a * (0.55 + 0.45 * Math.sin(t * 11 + i * 2)); });
    q(root, '.ms-h').setAttribute('stroke', t > tO + 0.1 ? 'var(--good)' : 'var(--bad)');
    api.tw(q(root, '.ms-j .a'), t, api.K.pop(api.start + 0.25, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.ms-t1 .a'), t, api.K.slam(tS - 0.08, 0.4));
  };
});
