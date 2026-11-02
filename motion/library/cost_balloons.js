/* @scene {"type":"cost_balloons","tags":["rising costs","rent","taxes","fewer customers","squeeze"],"layout":"balloons-rise-crowd-shrinks","metaphor":"cost balloons (rent, costs, taxes) float up and up while the row of customers below thins out","assets":["labelled balloons with strings","row of customer figures"]} */
// {balloons:[{label, at}], fewer, fewerAt}
RM.def('cost_balloons', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const bs = p.balloons || [], tb = bs.map(b => api.T(b.at)), tF = api.T(p.fewerAt), N = 8;
  const cols = ['var(--bad)', 'var(--c1)', 'var(--c2)'];
  const bal = (b, i) => `<div style="position:relative;display:flex;flex-direction:column;align-items:center">
      <div style="width:${290 * k}px;height:${340 * k}px;border-radius:50% 50% 48% 48% / 56% 56% 44% 44%;background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.35),transparent 40%),${cols[i % 3]};display:flex;align-items:center;justify-content:center;box-shadow:var(--sh)">
        <div class="big cb-l" style="font-size:${58 * k}px;color:var(--on-acc);text-align:center;white-space:normal;padding:0 ${20 * k}px">${R.esc(b.label)}</div></div>
      <svg width="${40 * k}" height="${220 * k}" viewBox="0 0 40 220"><path d="M20 0 q 16 50 0 100 q -16 50 0 120" stroke="var(--c2)" stroke-width="4" fill="none"/></svg></div>`;
  const fig = `<svg width="${90 * k}" height="${140 * k}" viewBox="-35 -55 70 110"><circle cx="0" cy="-33" r="17" fill="var(--acc)"/><path d="M-24 55 Q-26 -8 0 -12 Q26 -8 24 55 Z" fill="var(--acc)"/></svg>`;
  root.innerHTML = bs.map((b, i) => api.at(L.x(0.2 + i * 0.3), L.y(0.62), bal(b, i), { cls: 'cb-b' })).join('') +
    Array.from({ length: N }, (_, i) => api.at(L.x(0.08 + i * 0.12), L.y(0.93), fig, { cls: 'cb-f' })).join('') +
    api.at(L.x(0.72), L.y(0.8), R.tag(p.fewer || '', 62 * k, 'bad'), { cls: 'cb-t', idle: 'wobble' });
  return t => {
    qa(root, '.cb-b').forEach((b, i) => api.tw(q(b, '.a'), t, [[tb[i] - 0.1, { o: 0, y: 500 * k, s: 0.6 }], [tb[i] + 0.4, { o: 1, y: 0, s: 1 }, 'back'], [tb[i] + 0.41, {}], [api.end + 1, { y: -420 * k }, 'lin']]));
    qa(root, '.cb-b').forEach((b, i) => { q(b, '.i').style.transform = `rotate(${(5 * Math.sin(t * 1.7 + i * 2)).toFixed(2)}deg)`; });
    qa(root, '.cb-f').forEach((f, i) => { const gone = [1, 3, 4, 6, 7].indexOf(i); const a = tF + gone * 0.12;
      api.tw(q(f, '.a'), t, gone < 0 ? api.K.pop(api.start + i * 0.04, 0.3, { o: 0, s: 0.3 }) : api.K.pop(api.start + i * 0.04, 0.3, { o: 0, s: 0.3 }).concat([[a, {}], [a + 0.3, { o: 0, y: 40 * k, s: 0.6 }, 'in']])); });
    api.tw(q(root, '.cb-t .a'), t, api.K.pop(tF, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
