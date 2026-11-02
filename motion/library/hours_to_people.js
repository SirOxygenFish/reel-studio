/* @scene {"type":"hours_to_people","tags":["time saved","ai","scripts","editing","invest in people"],"layout":"two-props-then-clock-burst","metaphor":"a script writes itself and a film strip gets cut; then a clock's hours fly off and become people","assets":["self-writing script page","film strip with scissors","clock face","hour marks turning into people"]} */
// {script:{label, at}, film:{label, at}, clockAt, clockTag, clockTagAt, peopleAt, people, peopleTagAt}
RM.def('hours_to_people', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tSc = api.T(p.script.at), tFi = api.T(p.film.at), tCl = api.T(p.clockAt), tCt = api.T(p.clockTagAt ?? p.clockAt), tPe = api.T(p.peopleAt), tPt = api.T(p.peopleTagAt ?? p.peopleAt);
  const page = `<svg width="${300 * k}" height="${390 * k}" viewBox="0 0 300 390"><path d="M10 10 H230 L290 70 V380 H10 Z" fill="var(--paper)" stroke="var(--c2)" stroke-width="8"/><path d="M230 10 V70 H290" fill="var(--c1x)" stroke="var(--c2)" stroke-width="8"/>
      ${Array.from({ length: 7 }, (_, i) => `<path class="hp-ln" d="M40 ${110 + i * 38} H${i % 3 === 2 ? 170 : 250}" stroke="${i === 0 ? 'var(--c1)' : 'var(--muted)'}" stroke-width="${i === 0 ? 14 : 9}" stroke-linecap="round"/>`).join('')}</svg>`;
  const film = `<svg width="${430 * k}" height="${200 * k}" viewBox="0 0 430 200" overflow="visible"><g class="hp-fl"><rect x="0" y="20" width="200" height="160" rx="10" fill="var(--c2)"/><g class="hp-fr"><rect x="220" y="20" width="200" height="160" rx="10" fill="var(--c2)"/></g></g>
      ${[0, 1, 2, 3].map(i => `<rect x="${18 + i * 100}" y="58" width="76" height="84" rx="8" fill="${i % 2 ? 'var(--acc-soft)' : 'var(--c1l)'}"/>`).join('')}
      ${Array.from({ length: 8 }, (_, i) => `<rect x="${14 + i * 52}" y="28" width="24" height="16" rx="4" fill="var(--paper)"/><rect x="${14 + i * 52}" y="156" width="24" height="16" rx="4" fill="var(--paper)"/>`).join('')}</svg>`;
  const CR = 300 * k;
  const clock = `<svg width="${CR * 2}" height="${CR * 2}" viewBox="-150 -150 300 300" overflow="visible"><circle r="140" fill="var(--paper)" stroke="var(--c2)" stroke-width="12"/>
      <path class="hp-h" d="M0 0 V-70" stroke="var(--ink)" stroke-width="12" stroke-linecap="round"/><path class="hp-m" d="M0 0 V-108" stroke="var(--c1)" stroke-width="8" stroke-linecap="round"/><circle r="12" fill="var(--ink)"/></svg>`;
  const ticks = Array.from({ length: 12 }, (_, i) => api.at(0, 0, `<div class="hp-tk" style="width:${16 * k}px;height:${40 * k}px;border-radius:${8 * k}px;background:var(--c2)"></div>`, { cls: 'hp-t' })).join('');
  const ppl = Array.from({ length: 12 }, (_, i) => api.at(0, 0, api.icon(i % 4 === 0 ? 'ph-fill:user-circle' : 'ph-fill:user', 110 * k, ['var(--acc)', 'var(--c1)', 'var(--c2)'][i % 3]), { cls: 'hp-p', idle: 'bob' })).join('');
  root.innerHTML = api.at(L.x(0.27), L.y(0.36), page, { cls: 'hp-pg', idle: 'float' }) + api.at(L.x(0.27), L.y(0.74), R.tag(p.script.label, 56 * k, 'c1'), { cls: 'hp-st', idle: 'sway' }) +
    api.at(L.x(0.73), L.y(0.36), film, { cls: 'hp-fm', idle: 'float' }) + api.at(L.x(0.78), L.y(0.2), api.icon('ph:scissors', 150 * k, 'var(--bad)'), { cls: 'hp-sc' }) +
    api.at(L.x(0.73), L.y(0.74), R.tag(p.film.label, 56 * k, ''), { cls: 'hp-ft', idle: 'sway' }) +
    api.at(L.cx, L.y(0.42), clock, { cls: 'hp-ck' }) + ticks + ppl +
    api.at(L.cx, L.y(0.06), R.tag(p.clockTag || '', 68 * k, 'bad'), { cls: 'hp-ct', idle: 'sway' }) +
    api.at(L.cx, L.y(0.97), R.tag(p.people || '', 76 * k, ''), { cls: 'hp-pt', idle: 'wobble' });
  const tks = qa(root, '.hp-t'), pps = qa(root, '.hp-p'), cx = L.cx, cy = L.y(0.42);
  return t => {
    const away = [[tCl - 0.25, {}], [tCl + 0.1, { o: 0, s: 0.5 }, 'in']];
    api.tw(q(root, '.hp-pg .a'), t, api.K.antic(tSc - 0.1, -200 * k, 0, 0.45).concat(away));
    qa(root, '.hp-ln').forEach((e, i) => R.draw(e, api.prog(t, tSc + 0.1 + i * 0.16, tSc + 0.26 + i * 0.16, 'out')));
    api.tw(q(root, '.hp-st .a'), t, api.K.pop(tSc + 0.2, 0.4, { o: 0, s: 0.3 }).concat(away));
    api.tw(q(root, '.hp-fm .a'), t, api.K.antic(tFi - 0.1, 200 * k, 0, 0.45).concat(away));
    const cut = api.prog(t, tFi + 0.6, tFi + 0.9, 'back');
    q(root, '.hp-fr').setAttribute('transform', `translate(${(30 * cut).toFixed(1)} ${(-14 * cut).toFixed(1)}) rotate(${(8 * cut).toFixed(1)} 220 100)`);
    api.tw(q(root, '.hp-sc .a'), t, [[tFi + 0.2, { o: 0, x: 160 * k, r: 30 }], [tFi + 0.6, { o: 1, x: -60 * k, r: -10 }, 'io'], [tFi + 0.75, { r: 18 }, 'io']].concat(away));
    api.tw(q(root, '.hp-ft .a'), t, api.K.pop(tFi + 0.3, 0.4, { o: 0, s: 0.3 }).concat(away));
    api.tw(q(root, '.hp-ck .a'), t, api.K.spring(tCl - 0.05, 0.6, { o: 0, s: 0.2 }).concat([[tPe - 0.1, {}], [tPe + 0.3, { s: 0.55, o: 0.0 }, 'in']]));
    const spin = Math.max(0, t - tCl) * 1500 * (1 - 0.5 * api.prog(t, tPe - 0.5, tPe, 'lin'));
    q(root, '.hp-h').setAttribute('transform', `rotate(${(spin / 12).toFixed(1)})`); q(root, '.hp-m').setAttribute('transform', `rotate(${spin.toFixed(1)})`);
    api.tw(q(root, '.hp-ct .a'), t, api.K.pop(tCt, 0.4, { o: 0, s: 0.3, r: -10 }).concat([[tPe - 0.1, {}], [tPe + 0.2, { o: 0 }, 'lin']]));
    tks.forEach((e, i) => {      // hour marks: on the dial, then they fly out and become people
      const a = i / 12 * 6.283, fly = api.prog(t, tPe + i * 0.03, tPe + 0.45 + i * 0.03, 'io');
      const px = cx + Math.cos(a - 1.571) * CR * 0.78, py = cy + Math.sin(a - 1.571) * CR * 0.78;
      const qx = L.x(0.1 + 0.8 * ((i % 6) / 5)), qy = L.y(i < 6 ? 0.52 : 0.78);
      e.style.left = (px + (qx - px) * fly) + 'px'; e.style.top = (py + (qy - py) * fly) + 'px';
      api.tw(q(e, '.a'), t, [[tCl, { o: 0, r: i * 30 }], [tCl + 0.2, { o: 1, r: i * 30 }], [tPe + i * 0.03 + 0.35, { o: 1, r: i * 30 + 180 }, 'io'], [tPe + i * 0.03 + 0.45, { o: 0 }, 'lin']]);
      const pp = pps[i]; pp.style.left = qx + 'px'; pp.style.top = qy + 'px';
      api.tw(q(pp, '.a'), t, api.K.pop(tPe + 0.4 + i * 0.03, 0.4, { o: 0, s: 0.2 }));
    });
    api.tw(q(root, '.hp-pt .a'), t, api.K.slam(tPt - 0.05, 0.4));
  };
});
