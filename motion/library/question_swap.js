/* @scene {"type":"question_swap","tags":["mindset","better question","what if I fail","how many tries"],"layout":"index-card-crossed-then-replaced","metaphor":"the old question on an index card gets scribbled out and crumpled away; a new question card drops in its place","assets":["index cards","scribble-out lines","crumpled paper ball"]} */
// {old, oldAt, crossAt, neu, newAt}
RM.def('question_swap', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tO = api.T(p.oldAt ?? api.start), tX = api.T(p.crossAt), tN = api.T(p.newAt ?? p.crossAt);
  const card = (txt, c) => `<div class="card" style="width:${L.w * 0.88}px;min-height:${L.h * 0.34}px;padding:.5em .7em;display:flex;align-items:center;justify-content:center;text-align:center;font-family:var(--f-display);font-weight:900;font-size:${80 * k}px;line-height:1.1;color:${c};border-top:${22 * k}px solid ${c === 'var(--bad)' ? 'var(--bad)' : 'var(--acc)'}">${R.esc(txt)}</div>`;
  root.innerHTML = api.at(L.cx, L.y(0.3), `<div style="position:relative">${card(p.old || '', 'var(--muted)')}
        <svg class="qs-x" style="position:absolute;inset:0;overflow:visible" width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
          <path d="M5 30 Q 30 60 50 35 T 95 45 M8 55 Q 40 80 60 50 T 92 70" fill="none" stroke="var(--bad)" stroke-width="3" vector-effect="non-scaling-stroke" style="stroke-width:${14 * k}px" stroke-linecap="round"/></svg></div>`, { cls: 'qs-o' }) +
    api.at(L.x(0.86), L.y(0.12), `<div class="round" style="width:${110 * k}px;height:${110 * k}px;background:radial-gradient(circle at 35% 35%,var(--paper),var(--c1x));box-shadow:var(--sh)"></div>`, { cls: 'qs-ball' }) +
    api.at(L.cx, L.y(0.72), card(p.neu || '', 'var(--ink)'), { cls: 'qs-n' });
  return t => {
    api.tw(q(root, '.qs-o .a'), t, api.K.pop(tO - 0.05, 0.45, { o: 0, s: 0.4, r: -4 }).concat([[tX + 0.5, {}], [tX + 0.8, { s: 0.2, x: 330 * k, y: -250 * k, r: 200, o: 0 }, 'in']]));
    R.draw(q(root, '.qs-x path'), api.prog(t, tX - 0.05, tX + 0.45, 'io'));
    api.tw(q(root, '.qs-ball .a'), t, [[tX + 0.75, { o: 0, s: 0.3 }], [tX + 0.9, { o: 1, s: 1 }, 'back'], [tX + 1.4, { y: 700 * k, o: 0 }, 'in']]);
    api.tw(q(root, '.qs-n .a'), t, api.K.drop(tN - 0.1, 0.55, -500 * k));
  };
});
