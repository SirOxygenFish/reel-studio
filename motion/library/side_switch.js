/* @scene {"type":"side_switch","tags":["customers on your side","persuasion","crossing over","trust"],"layout":"split-field-dashed-line","metaphor":"a dashed line splits the field; after the right words part of the customers walk across to your side","assets":["split field","dashed dividing line","walking customers","your flag"]} */
// {sayAt, say, crossAt, side, sideAt}
RM.def('side_switch', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.sayAt ?? api.start), tC = api.T(p.crossAt), tD = api.T(p.sideAt ?? p.crossAt), N = 8, cross = [0, 2, 3, 5, 6];
  const fig = c => `<svg width="${110 * k}" height="${170 * k}" viewBox="-40 -60 80 124"><circle cx="0" cy="-38" r="18" fill="${c}"/><path d="M-26 60 Q-28 -10 0 -14 Q28 -10 26 60 Z" fill="${c}"/></svg>`;
  root.innerHTML = `<div style="position:absolute;left:${L.x0}px;top:${L.y(0.2)}px;width:${L.w / 2}px;height:${L.h * 0.8}px;border-radius:${30 * k}px 0 0 ${30 * k}px;background:var(--acc-soft)"></div>
      <div style="position:absolute;left:${L.cx}px;top:${L.y(0.2)}px;width:${L.w / 2}px;height:${L.h * 0.8}px;border-radius:0 ${30 * k}px ${30 * k}px 0;background:var(--c1x)"></div>
      <div style="position:absolute;left:${L.cx - 5 * k}px;top:${L.y(0.2)}px;width:${10 * k}px;height:${L.h * 0.8}px;background:repeating-linear-gradient(180deg,var(--c2) 0 ${24 * k}px,transparent ${24 * k}px ${44 * k}px)"></div>` +
    api.at(L.x(0.2), L.y(0.3), `<svg width="${150 * k}" height="${200 * k}" viewBox="0 0 150 200"><path d="M20 195 V10" stroke="var(--c2)" stroke-width="12" stroke-linecap="round"/><path class="ss-fl" d="M26 14 Q80 -6 140 22 Q96 44 140 70 Q80 50 26 70 Z" fill="var(--acc)"/></svg>`, { cls: 'ss-flag' }) +
    Array.from({ length: N }, (_, i) => api.at(0, 0, fig(cross.includes(i) ? 'var(--c1)' : 'var(--muted)'), { cls: 'ss-f' })).join('') +
    api.at(L.cx, L.y(0.06), R.tag(p.say || '', 70 * k, 'c1'), { cls: 'ss-t1', idle: 'sway' }) +
    api.at(L.x(0.28), L.y(0.97), R.tag(p.side || '', 66 * k, ''), { cls: 'ss-t2', idle: 'wobble' });
  const fs = qa(root, '.ss-f');
  return t => {
    fs.forEach((f, i) => {
      const c = i % 4, r = Math.floor(i / 4), hx = L.x(0.6 + c * 0.11), hy = L.y(0.48 + r * 0.25) + (c % 2) * 30 * k;
      const go = cross.includes(i) ? api.prog(t, tC + i * 0.08, tC + 0.9 + i * 0.08, 'io') : 0, tx = L.x(0.12 + c * 0.1), ty = hy;
      f.style.left = (hx + (tx - hx) * go) + 'px'; f.style.top = (hy - 14 * k * Math.abs(Math.sin(go * Math.PI * 4))) + 'px';
      api.tw(q(f, '.a'), t, api.K.pop(api.start + i * 0.05, 0.35, { o: 0, s: 0.3 }));
    });
    api.tw(q(root, '.ss-flag .a'), t, api.K.drop(api.start + 0.2, 0.4, -200 * k));
    q(root, '.ss-fl').setAttribute('transform', `skewY(${(5 * Math.sin(t * 5)).toFixed(2)})`);
    api.tw(q(root, '.ss-t1 .a'), t, api.K.pop(tS, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.ss-t2 .a'), t, api.K.pop(tD - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
