/* @scene {"type":"stepping_stones","tags":["do your part","daily habits","small steps"],"layout":"stones-across-water-figure-hops","metaphor":"a little figure hops across stepping stones over water; each stone lights up with one habit as it is named","assets":["water with ripples","stepping stones","hopping figure"]} */
// {stones:[{label, icon, at}]}
RM.def('stepping_stones', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const st = p.stones || [], ts = st.map(s => api.T(s.at)), n = st.length;
  const pos = i => [L.x(0.18 + 0.64 * (i / Math.max(1, n - 1))), L.y(0.66 - 0.22 * (i % 2))];
  root.innerHTML = `<div style="position:absolute;left:${L.x0}px;top:${L.y(0.4)}px;width:${L.w}px;height:${L.h * 0.6}px;border-radius:${40 * k}px;background:linear-gradient(180deg,var(--c2),var(--bgDeep))"></div>` +
    [0, 1, 2, 3, 4].map(i => `<div class="ss-rip" style="position:absolute;left:${L.x(0.1 + i * 0.2)}px;top:${L.y(0.5 + (i % 3) * 0.14)}px;width:${120 * k}px;height:${24 * k}px;border-radius:50%;border:${4 * k}px solid var(--c1l);opacity:.5"></div>`).join('') +
    st.map((s, i) => { const [x, y] = pos(i); return api.at(x, y, `<div style="display:flex;flex-direction:column;align-items:center;gap:${10 * k}px">
        <div class="ss-st" style="width:${250 * k}px;height:${110 * k}px;border-radius:50%;background:var(--muted);display:flex;align-items:center;justify-content:center">${api.icon(s.icon, 80 * k, 'var(--ink)')}</div>
        <div class="tag" style="font-size:${46 * k}px">${R.esc(s.label)}</div></div>`, { cls: 'ss-s' }); }).join('') +
    api.at(0, 0, `<svg width="${110 * k}" height="${170 * k}" viewBox="-40 -60 80 124"><circle cx="0" cy="-38" r="18" fill="var(--acc)"/><path d="M-26 60 Q-28 -10 0 -14 Q28 -10 26 60 Z" fill="var(--acc)"/></svg>`, { cls: 'ss-f' });
  const f = q(root, '.ss-f');
  return t => {
    qa(root, '.ss-rip').forEach((r, i) => { const ph = (t * 0.6 + i * 0.2) % 1; r.style.transform = `scale(${(0.6 + ph).toFixed(2)})`; r.style.opacity = (0.6 * (1 - ph)).toFixed(2); });
    qa(root, '.ss-s').forEach((s, i) => { api.tw(q(s, '.a'), t, api.K.pop(api.start + i * 0.1, 0.4, { o: 0, s: 0.3 }));
      q(s, '.ss-st').style.background = t > ts[i] ? 'var(--c1)' : 'var(--muted)'; q(s, '.tag').style.opacity = t > ts[i] ? 1 : 0.15; });
    let cur = -1; ts.forEach((x, i) => { if (t >= x - 0.35) cur = i; });
    let x, y;
    if (cur < 0) { [x, y] = pos(0); x -= 200 * k; }
    else { const a = ts[cur] - 0.35, u = api.prog(t, a, a + 0.35, 'io'), [x1, y1] = pos(cur), [x0, y0] = cur ? pos(cur - 1) : [x1 - 200 * k, y1];
      x = x0 + (x1 - x0) * u; y = y0 + (y1 - y0) * u - 160 * k * Math.sin(Math.PI * u); }
    f.style.left = x + 'px'; f.style.top = (y - 130 * k) + 'px';
    api.tw(q(f, '.a'), t, api.K.pop(api.start + 0.2, 0.3, { o: 0, s: 0.3 }));
  };
});
