/* @scene {"type":"study_card","tags":["study details","placebo","weeks","participants","university"],"layout":"research-card-people-grid-split","metaphor":"a research index card fills in: a week counter, a grid of 60 people split into two groups (one placebo), and a small university building with a place tag","assets":["research card","60-person grid split","week counter","university building"]} */
// {weeks:{value, label, at}, people:{value, label, at}, placebo:{label, at}, place:{label, at}}
RM.def('study_card', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tW = api.T(p.weeks.at), tP = api.T(p.people.at), tPl = api.T(p.placebo.at), tU = api.T(p.place.at), N = p.people.value || 60;
  const CW = L.w * 0.96, CH = L.h * 0.9;
  root.innerHTML = api.at(L.cx, L.y(0.5), `<div style="width:${CW}px;height:${CH}px;border-radius:${30 * k}px;background:var(--paper);box-shadow:var(--sh)"></div>`, { cls: 'sc-c', content: false }) +
    api.at(L.x(0.26), L.y(0.15), `<div style="display:flex;align-items:baseline;gap:${12 * k}px;color:var(--ink)"><div class="big sc-wn" style="font-size:${130 * k}px;color:var(--c2)">0</div><div class="big" style="font-size:${50 * k}px">${R.esc(p.weeks.label)}</div></div>`, { cls: 'sc-w' }) +
    api.at(L.x(0.74), L.y(0.15), `<div style="display:flex;flex-direction:column;align-items:center;gap:${6 * k}px">${api.icon('ph:bank', 140 * k, 'var(--c2)')}<div class="tag" style="font-size:${46 * k}px">${R.esc(p.place.label)}</div></div>`, { cls: 'sc-u' }) +
    Array.from({ length: N }, (_, i) => { const c = i % 10, r = Math.floor(i / 10); return `<div class="sc-p" data-i="${i}" style="position:absolute;left:${L.x(0.1) + c * L.w * 0.082 + (c >= 5 ? L.w * 0.03 : 0)}px;top:${L.y(0.36) + r * L.h * 0.085}px;font-size:0">${api.icon('ph-fill:user', 62 * k, c >= 5 ? 'var(--muted)' : 'var(--c1)')}</div>`; }).join('') +
    api.at(L.x(0.3), L.y(0.93), R.tag(p.people.label, 50 * k, 'c1'), { cls: 'sc-pl' }) +
    api.at(L.x(0.72), L.y(0.93), R.tag(p.placebo.label, 50 * k, ''), { cls: 'sc-pb' });
  const ps = qa(root, '.sc-p');
  return t => {
    api.tw(q(root, '.sc-c .a'), t, api.K.rise(api.start, 0.45, 200 * k));
    q(root, '.sc-wn').textContent = String(Math.round((p.weeks.value || 0) * api.prog(t, tW, tW + 0.6, 'out')));
    api.tw(q(root, '.sc-w .a'), t, api.K.pop(tW - 0.05, 0.35, { o: 0, s: 0.4 }));
    ps.forEach(e => { const i = +e.dataset.i, a = tP + i * 0.012; e.style.opacity = t > a ? 1 : 0; e.style.transform = t > tPl && (i % 10) >= 5 ? `translateX(${(16 * k * api.prog(t, tPl, tPl + 0.3, 'out')).toFixed(1)}px)` : ''; });
    api.tw(q(root, '.sc-pl .a'), t, api.K.pop(tP + 0.2, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.sc-pb .a'), t, api.K.pop(tPl, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.sc-u .a'), t, api.K.spring(tU - 0.1, 0.55, { o: 0, s: 0.2 }));
  };
});
