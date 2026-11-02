/* @scene {"type":"sleep_window","tags":["sleep","night","small study","before bed"],"layout":"night-window-bed-wake-markers","metaphor":"a bedroom at night through a window: before bed a cup, then wake-up marks over the night get fewer, with a small-study note","assets":["night window with moon","bed","wake-up marks","study note"]} */
// {study, studyAt, bedAt, bed, lessAt, less}
RM.def('sleep_window', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.studyAt), tB = api.T(p.bedAt), tL = api.T(p.lessAt);
  root.innerHTML = api.at(L.x(0.72), L.y(0.22), `<div style="position:relative;width:${360 * k}px;height:${300 * k}px;border-radius:${24 * k}px;border:${16 * k}px solid var(--c2);background:linear-gradient(180deg,#0a1830,#163055);overflow:hidden">
        <div class="round" style="position:absolute;right:${50 * k}px;top:${40 * k}px;width:${90 * k}px;height:${90 * k}px;background:var(--acc-soft);box-shadow:0 0 ${40 * k}px var(--acc-soft)"></div>
        ${[[30, 50], [120, 140], [70, 200], [200, 90]].map(([x, y], i) => `<div class="sw-star" style="position:absolute;left:${x * k}px;top:${y * k}px;width:${10 * k}px;height:${10 * k}px;border-radius:50%;background:var(--paper)"></div>`).join('')}
        <div style="position:absolute;left:50%;top:0;bottom:0;width:${10 * k}px;margin-left:${-5 * k}px;background:var(--c2)"></div></div>`, { cls: 'sw-w' }) +
    api.at(L.x(0.45), L.y(0.72), `<svg width="${720 * k}" height="${320 * k}" viewBox="0 0 360 160"><rect x="10" y="60" width="340" height="60" rx="16" fill="var(--c2)"/><rect x="10" y="20" width="40" height="130" rx="12" fill="var(--c2)"/>
        <rect x="56" y="40" width="80" height="34" rx="16" fill="var(--paper)"/><path d="M120 62 H340 V86 H120 Z" fill="var(--c1)"/><path d="M14 150 v10 M346 150 v10" stroke="var(--c2)" stroke-width="10"/></svg>`, { cls: 'sw-bed' }) +
    api.at(L.x(0.12), L.y(0.58), api.icon('ph:coffee', 120 * k, 'var(--acc)'), { cls: 'sw-cup' }) +
    [0, 1, 2, 3, 4].map(i => api.at(L.x(0.25 + i * 0.12), L.y(0.47), `<div class="badge bad" style="font-size:${70 * k}px">${api.icon('ph-bold:eye', 40 * k)}</div>`, { cls: 'sw-wk' })).join('') +
    api.at(L.x(0.3), L.y(0.12), `<div class="card" style="padding:.3em .6em;font-size:${44 * k}px;font-family:var(--f-head);font-weight:800;color:var(--ink);display:flex;align-items:center;gap:${12 * k}px">${api.icon('ph:file-text', 60 * k, 'var(--c2)')}${R.esc(p.study || '')}</div>`, { cls: 'sw-st' }) +
    api.at(L.x(0.3), L.y(0.33), R.tag(p.bed || '', 52 * k, ''), { cls: 'sw-t1', idle: 'sway' }) +
    api.at(L.x(0.66), L.y(0.97), R.tag(p.less || '', 60 * k, 'c1'), { cls: 'sw-t2', idle: 'wobble' });
  const wk = qa(root, '.sw-wk');
  return t => {
    api.tw(q(root, '.sw-w .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0.4 }));
    qa(root, '.sw-star').forEach((s, i) => s.style.opacity = (0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i))).toFixed(2));
    api.tw(q(root, '.sw-bed .a'), t, api.K.rise(api.start + 0.1, 0.45, 200 * k));
    api.tw(q(root, '.sw-st .a'), t, api.K.pop(tS - 0.05, 0.4, { o: 0, s: 0.4 }));
    api.tw(q(root, '.sw-cup .a'), t, api.K.pop(tB - 0.1, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.sw-t1 .a'), t, api.K.pop(tB, 0.4, { o: 0, s: 0.3, r: -6 }));
    wk.forEach((w, i) => { const show = api.start + 0.3 + i * 0.12, keep = i < 2; api.tw(q(w, '.a'), t, [[show, { o: 0, s: 0 }], [show + 0.3, { o: 1, s: 1 }, 'back']].concat(keep ? [] : [[tL - 0.05 + i * 0.08, {}], [tL + 0.25 + i * 0.08, { o: 0, s: 0.3 }, 'in']])); });
    api.tw(q(root, '.sw-t2 .a'), t, api.K.slam(tL, 0.4));
  };
});
