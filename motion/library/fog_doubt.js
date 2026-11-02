/* @scene {"type":"fog_doubt","tags":["uncertainty","doubt","is it for me","fog"],"layout":"figure-on-path-into-fog","metaphor":"a person stands at the start of a path that vanishes into drifting fog, a question mark hovering: not sure it's for them","assets":["path into fog","fog bands","hesitant figure","question mark"]} */
// {notSure, notSureAt, forMe, forMeAt}
RM.def('fog_doubt', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tN = api.T(p.notSureAt ?? api.start), tF = p.forMe ? api.T(p.forMeAt) : 0;
  root.innerHTML = `<svg style="position:absolute;left:${L.x0}px;top:${L.y0}px;overflow:visible" width="${L.w}" height="${L.h}" viewBox="0 0 ${L.w} ${L.h}">
      <path d="M${L.w * 0.32} ${L.h} L${L.w * 0.47} ${L.h * 0.3} L${L.w * 0.53} ${L.h * 0.3} L${L.w * 0.68} ${L.h} Z" fill="var(--c1l)"/>
      <path d="M${L.w * 0.5} ${L.h} L${L.w * 0.5} ${L.h * 0.32}" stroke="var(--paper)" stroke-width="${10 * k}" stroke-dasharray="${30 * k} ${24 * k}"/></svg>` +
    [0, 1, 2, 3, 4].map(i => `<div class="fd-fog" style="position:absolute;left:${L.x0 - 200 * k}px;top:${L.y(0.12 + i * 0.09)}px;width:${L.w + 400 * k}px;height:${150 * k}px;border-radius:50%;background:radial-gradient(closest-side,var(--paper),transparent);opacity:.85"></div>`).join('') +
    api.at(L.cx, L.y(0.78), `<svg width="${200 * k}" height="${320 * k}" viewBox="-60 -100 120 192" overflow="visible"><circle cx="0" cy="-70" r="26" fill="var(--c1)"/><path d="M-36 92 Q-40 -30 0 -36 Q40 -30 36 92 Z" fill="var(--c1)"/></svg>`, { cls: 'fd-f' }) +
    api.at(L.cx + 120 * k, L.y(0.5), `<div class="big" style="font-size:${240 * k}px;color:var(--c1)">?</div>`, { cls: 'fd-q', idle: 'float wobble' }) +
    api.at(L.x(0.3), L.y(0.08), R.tag(p.notSure || '', 66 * k, 'c1'), { cls: 'fd-t1', idle: 'sway' }) +
    (p.forMe ? api.at(L.x(0.72), L.y(0.95), R.tag(p.forMe, 62 * k, ''), { cls: 'fd-t2', idle: 'sway' }) : '');
  return t => {
    qa(root, '.fd-fog').forEach((f, i) => { f.style.transform = `translateX(${(((t * (20 + i * 9)) % 200) - 100) * k * (i % 2 ? 1 : -1)}px)`; f.style.opacity = 0.6 + 0.3 * Math.sin(t * 0.8 + i); });
    api.tw(q(root, '.fd-f .a'), t, api.K.rise(api.start, 0.45, 200 * k));
    q(root, '.fd-f .i').style.transform = `translateX(${(14 * k * Math.sin(t * 1.6)).toFixed(1)}px) rotate(${(3 * Math.sin(t * 1.6)).toFixed(1)}deg)`;
    api.tw(q(root, '.fd-q .a'), t, api.K.spring(tN - 0.05, 0.6, { o: 0, s: 0.2 }));
    api.tw(q(root, '.fd-t1 .a'), t, api.K.pop(tN, 0.4, { o: 0, s: 0.3, r: -8 }));
    if (p.forMe) api.tw(q(root, '.fd-t2 .a'), t, api.K.pop(tF - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
