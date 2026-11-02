/* @scene {"type":"age_hill","tags":["losing it","after 25","every year less","age"],"layout":"hill-path-milestone-downhill","metaphor":"a figure walks a path up a hill to a milestone flag at 25, then the path tilts downhill while a level beside it drops a little every year","assets":["hill path","milestone flag","walking figure","shrinking level bar"]} */
// {num, losing, losingAt, age, ageAt, less, lessAt}
RM.def('age_hill', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tLo = api.T(p.losingAt ?? api.start), tA = api.T(p.ageAt), tLe = api.T(p.lessAt);
  const P = (u) => { const x = L.x(0.06 + 0.88 * u), y = u < 0.45 ? L.y(0.8) - (u / 0.45) * L.h * 0.4 : L.y(0.4) + ((u - 0.45) / 0.55) * L.h * 0.45; return [x, y]; };
  let d = ''; for (let i = 0; i <= 40; i++) { const [x, y] = P(i / 40); d += (i ? ' L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1); }
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><path d="${d} L${L.x(0.94)} ${L.y1} L${L.x(0.06)} ${L.y1} Z" fill="rgba(46,196,182,.12)"/>
      <path class="ah-p" d="${d}" fill="none" stroke="var(--c1)" stroke-width="${16 * k}" stroke-linecap="round"/></svg>` +
    api.at(P(0.45)[0], P(0.45)[1] - 110 * k, `<svg width="${150 * k}" height="${210 * k}" viewBox="0 0 75 105"><path d="M10 105 V8" stroke="var(--paper)" stroke-width="6"/><path d="M14 8 L70 22 L14 38 Z" fill="var(--acc)"/></svg>`, { cls: 'ah-f' }) +
    api.at(P(0.45)[0] + 120 * k, P(0.45)[1] - 230 * k, `<div class="big" style="font-size:${100 * k}px;color:var(--acc)">${R.esc(p.age || '')}</div>`, { cls: 'ah-a' }) +
    api.at(0, 0, `<svg width="${90 * k}" height="${150 * k}" viewBox="-30 -50 60 100"><circle cx="0" cy="-32" r="15" fill="var(--paper)"/><path d="M-20 50 Q-22 -6 0 -10 Q22 -6 20 50 Z" fill="var(--paper)"/></svg>`, { cls: 'ah-w' }) +
    api.at(L.x(0.86), L.y(0.2), `<div style="width:${70 * k}px;height:${300 * k}px;border-radius:${35 * k}px;border:${8 * k}px solid var(--c2);position:relative;overflow:hidden"><div class="ah-lv" style="position:absolute;left:0;right:0;bottom:0;height:90%;background:var(--c1)"></div></div>`, { cls: 'ah-bar' }) +
    (p.num ? api.at(L.x(0.1), L.y(0.08), `<div class="badge acc" style="font-size:${140 * k}px;font-family:var(--f-display);font-weight:900"><span style="font-size:.52em">${R.esc(p.num)}</span></div>`, { cls: 'ah-n' }) : '') +
    api.at(L.x(0.58), L.y(0.08), R.tag(p.losing || '', 64 * k, 'c1'), { cls: 'ah-t1', idle: 'sway' }) +
    api.at(L.x(0.35), L.y(0.97), R.tag(p.less || '', 54 * k, ''), { cls: 'ah-t2', idle: 'wobble' });
  return t => {
    R.draw(q(root, '.ah-p'), api.prog(t, api.start, api.start + 0.8, 'io'));
    const u = 0.45 * api.prog(t, api.start + 0.3, tA, 'io') + 0.5 * api.prog(t, tA + 0.3, api.end, 'lin'), [x, y] = P(u);
    const w = q(root, '.ah-w'); w.style.left = x + 'px'; w.style.top = (y - 70 * k - 8 * k * Math.abs(Math.sin(t * 8))) + 'px';
    api.tw(q(w, '.a'), t, api.K.pop(api.start + 0.2, 0.3, { o: 0, s: 0.3 }));
    api.tw(q(root, '.ah-f .a'), t, api.K.drop(tA - 0.2, 0.45, -200 * k));
    api.tw(q(root, '.ah-a .a'), t, api.K.slam(tA - 0.05, 0.4));
    q(root, '.ah-lv').style.height = (90 - 55 * api.prog(t, tA + 0.2, api.end, 'lin')).toFixed(1) + '%';
    api.tw(q(root, '.ah-bar .a'), t, api.K.pop(tA, 0.4, { o: 0, s: 0.4 }));
    if (p.num) api.tw(q(root, '.ah-n .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0 }));
    api.tw(q(root, '.ah-t1 .a'), t, api.K.pop(tLo, 0.4, { o: 0, s: 0.3, r: -6 }));
    api.tw(q(root, '.ah-t2 .a'), t, api.K.pop(tLe - 0.05, 0.4, { o: 0, s: 0.3, r: 6 }));
  };
});
