/* @scene {"type":"quit_bar","tags":["giving up too early","patience","give it time","mirror"],"layout":"progress-bar-mirror-walkaway","metaphor":"a progress bar barely starts; a figure checks a mirror after two weeks and walks away; then the bar keeps filling: give it time","assets":["progress bar","hand mirror","walking-away figure"]} */
// {weeks, weeksAt, mirrorAt, quit, quitAt, time, timeAt}
RM.def('quit_bar', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tW = api.T(p.weeksAt), tM = api.T(p.mirrorAt), tQ = api.T(p.quitAt), tT = api.T(p.timeAt);
  const BW = L.w * 0.86, bx = L.cx, by = L.y(0.3);
  root.innerHTML = api.at(bx, by, `<div style="width:${BW}px;height:${110 * k}px;border-radius:${55 * k}px;background:rgba(255,255,255,.1);border:${6 * k}px solid var(--c2);overflow:hidden"><div class="qb-f" style="height:100%;width:0;background:linear-gradient(90deg,var(--c1),var(--c1l))"></div></div>`, { cls: 'qb-b' }) +
    api.at(bx - BW / 2 + BW * 0.12, by - 100 * k, R.tag(p.weeks || '', 66 * k, ''), { cls: 'qb-w' }) +
    api.at(L.x(0.4), L.y(0.66), `<svg width="${280 * k}" height="${450 * k}" viewBox="-40 -64 80 128"><circle cx="0" cy="-42" r="18" fill="var(--paper)"/><path d="M-26 64 Q-28 -14 0 -18 Q28 -14 26 64 Z" fill="var(--paper)"/></svg>`, { cls: 'qb-fig' }) +
    api.at(L.x(0.66), L.y(0.56), `<svg width="${220 * k}" height="${400 * k}" viewBox="0 0 55 100"><ellipse cx="27" cy="30" rx="24" ry="28" fill="var(--c1x)" stroke="var(--c2)" stroke-width="5"/><rect x="22" y="56" width="10" height="40" rx="5" fill="var(--c2)"/></svg>`, { cls: 'qb-m' }) +
    api.at(L.x(0.4), L.y(0.94), R.tag(p.quit || '', 66 * k, 'bad'), { cls: 'qb-q', idle: 'wobble' }) +
    api.at(L.x(0.66), L.y(0.12), R.tag(p.time || '', 72 * k, 'c1'), { cls: 'qb-t', idle: 'sway' });
  const fig = q(root, '.qb-fig');
  return t => {
    api.tw(q(root, '.qb-b .a'), t, api.K.rise(api.start, 0.4, 100 * k));
    const fill = 12 * api.prog(t, api.start + 0.2, tW + 0.3, 'out') + 88 * api.prog(t, tT, api.end + 0.6, 'io');
    q(root, '.qb-f').style.width = fill.toFixed(1) + '%';
    api.tw(q(root, '.qb-w .a'), t, api.K.pop(tW - 0.05, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.qb-m .a'), t, api.K.pop(tM - 0.1, 0.4, { o: 0, s: 0.3 }).concat([[tQ + 0.4, {}], [tQ + 0.7, { o: 0, s: 0.5 }, 'in']]));
    const away = api.prog(t, tQ, tQ + 1.0, 'in');
    fig.style.left = (L.x(0.4) - L.w * 0.5 * away) + 'px';
    api.tw(q(fig, '.a'), t, api.K.pop(api.start + 0.2, 0.35, { o: 0, s: 0.3 }).concat([[tQ + 0.6, {}], [tQ + 1.0, { o: 0 }, 'lin']]));
    q(fig, '.i').style.transform = `scaleX(${t > tQ ? -1 : 1})`;
    api.tw(q(root, '.qb-q .a'), t, api.K.pop(tQ - 0.05, 0.4, { o: 0, s: 0.3, r: -6 }).concat([[tT - 0.2, {}], [tT, { o: 0 }, 'lin']]));
    api.tw(q(root, '.qb-t .a'), t, api.K.slam(tT - 0.05, 0.4));
  };
});
