/* @scene {"type":"dot_grid_hits","tags":["conversion","1-2 percent","odds","law of large numbers"],"layout":"ten-by-ten-dot-field","metaphor":"a field of 100 dots fills in; only one or two of them light up green: 1 or 2 percent","assets":["100-dot field","highlight pulse"]} */
// {rate, rateAt, hits:[i], feel, feelAt}
RM.def('dot_grid_hits', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tR = api.T(p.rateAt), tF = p.feel ? api.T(p.feelAt) : 0, hits = p.hits || [37, 82], C = 10, S = Math.min(L.w, L.h * 0.8) * 0.92 / C;
  const ox = L.cx - S * C / 2 + S / 2, oy = L.y(0.52) - S * C / 2 + S / 2;
  root.innerHTML = Array.from({ length: 100 }, (_, i) => `<div class="dg-d${hits.includes(i) ? ' dg-h' : ''}" style="position:absolute;left:${ox + (i % C) * S - S * 0.32}px;top:${oy + Math.floor(i / C) * S - S * 0.32}px;width:${S * 0.64}px;height:${S * 0.64}px;border-radius:50%;background:var(--c1l)"></div>`).join('') +
    api.at(L.x(0.3), L.y(0.05), R.tag(p.rate || '', 80 * k, 'good'), { cls: 'dg-t1', idle: 'sway' }) +
    (p.feel ? api.at(L.x(0.7), L.y(0.97), R.tag(p.feel, 64 * k, 'bad'), { cls: 'dg-t2', idle: 'wobble' }) : '');
  const ds = qa(root, '.dg-d');
  return t => {
    ds.forEach((d, i) => { const a = api.start + 0.05 + ((i % C) + Math.floor(i / C)) * 0.03, u = api.prog(t, a, a + 0.25, 'back');
      let s = u, bg = 'var(--c1l)';
      if (d.classList.contains('dg-h') && t > tR) { s = 1.25 + 0.15 * Math.sin((t - tR) * 8); bg = 'var(--good)'; }
      else if (t > tR) bg = 'var(--c1x)';
      d.style.transform = `scale(${Math.max(0, s * (1 + 0.12 * Math.sin(t * 3.2 - ((i % C) + Math.floor(i / C)) * 0.35))).toFixed(3)})`; d.style.background = bg; d.style.boxShadow = d.classList.contains('dg-h') && t > tR ? `0 0 ${30 * k}px var(--good)` : 'none'; });
    api.tw(q(root, '.dg-t1 .a'), t, api.K.slam(tR - 0.05, 0.4));
    if (p.feel) api.tw(q(root, '.dg-t2 .a'), t, api.K.pop(tF - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
