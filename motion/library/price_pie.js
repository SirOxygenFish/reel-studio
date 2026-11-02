/* @scene {"type":"price_pie","tags":["price is one factor","quality","deadlines","value"],"layout":"pie-center-callouts","metaphor":"a pie where price is only one slice; quality, deadlines and many other things fill the rest","assets":["pie chart slices","callout labels"]} */
// {slices:[{label, at, v, color}]}
RM.def('price_pie', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const sl = p.slices || [], ts = sl.map(s => api.T(s.at ?? api.start)), tot = sl.reduce((a, s) => a + (s.v || 1), 0);
  const D = 660 * k, cx = L.cx, cy = L.y(0.5), r = 140;
  let a0 = -Math.PI / 2; const geo = sl.map(s => { const a1 = a0 + (s.v || 1) / tot * 2 * Math.PI, g = [a0, a1]; a0 = a1; return g; });
  const arc = (a, b, rr) => `M0 0 L${(Math.cos(a) * rr).toFixed(1)} ${(Math.sin(a) * rr).toFixed(1)} A${rr} ${rr} 0 ${b - a > Math.PI ? 1 : 0} 1 ${(Math.cos(b) * rr).toFixed(1)} ${(Math.sin(b) * rr).toFixed(1)} Z`;
  const cols = ['var(--bad)', 'var(--acc)', 'var(--c1)', 'var(--c2)', 'var(--c1l)'];
  root.innerHTML = api.at(cx, cy, `<svg width="${D}" height="${D}" viewBox="-160 -160 320 320" overflow="visible">
        ${sl.map((s, i) => `<g class="pi-s" data-i="${i}"><path d="${arc(geo[i][0], geo[i][1], r)}" fill="${s.color || cols[i % 5]}" stroke="var(--paper)" stroke-width="5"/></g>`).join('')}
        <circle r="46" fill="var(--paper)"/></svg>`, { cls: 'pi-p', idle: 'float', amp: 0.4 }) +
    sl.map((s, i) => { const m = (geo[i][0] + geo[i][1]) / 2, rx = cx + Math.cos(m) * (D * 0.52), ry = cy + Math.sin(m) * (D * 0.52);
      return api.at(rx, ry, R.tag(s.label, (i === 0 ? 72 : 60) * k, i === 0 ? 'bad' : ['', 'c1', 'paper', 'paper'][i % 4]), { cls: 'pi-l', idle: 'sway' }); }).join('');
  return t => {
    qa(root, '.pi-s').forEach(g => { const i = +g.dataset.i, u = api.prog(t, ts[i] - 0.05, ts[i] + 0.4, 'back'), m = (geo[i][0] + geo[i][1]) / 2, out = i === 0 ? 16 * api.prog(t, ts[i] + 0.4, ts[i] + 0.7, 'out') : 0;
      g.setAttribute('transform', `translate(${(Math.cos(m) * out).toFixed(1)} ${(Math.sin(m) * out).toFixed(1)}) scale(${Math.max(0, u).toFixed(3)})`); g.style.opacity = u > 0.01 ? 1 : 0; });
    qa(root, '.pi-l').forEach((l, i) => api.tw(q(l, '.a'), t, api.K.pop(ts[i] + 0.1, 0.4, { o: 0, s: 0.3, r: (i % 2 ? 8 : -8) })));
  };
});
