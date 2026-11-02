/* @scene {"type":"no_stamps","tags":["rejection","three no","self judgement","conclusions"],"layout":"portrait-sheet-with-stamps","metaphor":"three red NO stamps slam onto a sketched self-portrait; the portrait shrinks and greys out: we draw conclusions about ourselves","assets":["sketched portrait sheet","rubber stamps","red stamp marks"]} */
// {tries, triesAt, stamps:[at...], stampText, self, selfAt}
RM.def('no_stamps', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const ts = (p.stamps || []).map(a => api.T(a)), tT = api.T(p.triesAt ?? api.start), tS = api.T(p.selfAt);
  const pos = [[0.3, 0.32, -14], [0.68, 0.46, 10], [0.4, 0.66, -6]];
  root.innerHTML = api.at(L.cx, L.y(0.5), `<div class="ns-sheet" style="width:${L.w * 0.78}px;height:${L.h * 0.84}px;background:var(--paper);box-shadow:var(--sh);border-radius:${12 * k}px;display:flex;align-items:center;justify-content:center">
        <svg width="${L.w * 0.5}" height="${L.w * 0.6}" viewBox="0 0 100 120"><circle cx="50" cy="40" r="24" fill="none" stroke="var(--c2)" stroke-width="3"/><path d="M14 118 Q16 70 50 68 Q84 70 86 118" fill="none" stroke="var(--c2)" stroke-width="3"/>
          <path d="M40 38 h4 M56 38 h4 M42 50 q8 5 16 0" stroke="var(--c2)" stroke-width="3" fill="none" stroke-linecap="round"/></svg></div>`, { cls: 'ns-p' }) +
    ts.map((_, i) => api.at(L.x(pos[i][0]), L.y(pos[i][1]), `<div class="big" style="font-size:${120 * k}px;color:var(--bad);border:${12 * k}px solid var(--bad);border-radius:${16 * k}px;padding:0 .2em;transform:rotate(${pos[i][2]}deg);opacity:.92">${R.esc(p.stampText || '')}</div>`, { cls: 'ns-s' })).join('') +
    api.at(L.x(0.3), L.y(0.05), R.tag(p.tries || '', 62 * k, 'c1'), { cls: 'ns-t1', idle: 'sway' }) +
    api.at(L.x(0.66), L.y(0.95), R.tag(p.self || '', 62 * k, ''), { cls: 'ns-t2', idle: 'wobble' });
  return t => {
    api.tw(q(root, '.ns-p .a'), t, api.K.rise(api.start, 0.45, 200 * k));
    qa(root, '.ns-s').forEach((s, i) => api.tw(q(s, '.a'), t, [[ts[i] - 0.12, { o: 0, s: 2.6, y: -80 * k }], [ts[i], { o: 1, s: 0.92, y: 0 }, 'in'], [ts[i] + 0.12, { s: 1 }, 'out']]));
    const g = api.prog(t, tS - 0.2, tS + 0.6, 'io');
    q(root, '.ns-sheet').style.filter = `grayscale(${g.toFixed(2)})`; q(root, '.ns-sheet svg').style.transform = `scale(${(1 - 0.3 * g).toFixed(3)})`;
    api.tw(q(root, '.ns-t1 .a'), t, api.K.pop(tT, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.ns-t2 .a'), t, api.K.pop(tS - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
