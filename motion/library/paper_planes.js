/* @scene {"type":"paper_planes","tags":["follow up","three messages","timing","customer care"],"layout":"curved-timeline-planes-to-house","metaphor":"three paper planes take off from a timeline at day 3, week 2 and month 1, each carrying a short question to the customer's house","assets":["paper planes","customer house","curved timeline with stops","message cards"]} */
// {three, threeAt, stops:[{when, whenAt, msg, msgAt}]}
RM.def('paper_planes', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const st = p.stops || [], tw = st.map(s => api.T(s.whenAt)), tm = st.map(s => api.T(s.msgAt ?? s.whenAt)), t3 = api.T(p.threeAt ?? api.start);
  const hx = L.x(0.78), hy = L.y(0.2), base = L.y(0.92);
  const sx = i => L.x(0.14 + i * 0.27);
  const house = `<svg width="${360 * k}" height="${346 * k}" viewBox="0 0 260 250"><path d="M20 120 L130 20 L240 120 Z" fill="var(--bad)"/><rect x="45" y="110" width="170" height="130" fill="var(--paper)" stroke="var(--c2)" stroke-width="8"/>
      <rect x="110" y="160" width="44" height="80" fill="var(--c1)"/><rect x="60" y="135" width="40" height="36" fill="var(--acc-soft)"/><rect x="160" y="135" width="40" height="36" fill="var(--acc-soft)"/></svg>`;
  const plane = `<svg width="${190 * k}" height="${132 * k}" viewBox="0 0 130 90" overflow="visible"><path d="M0 40 L130 0 L60 90 L50 55 Z" fill="var(--paper)" stroke="var(--c2)" stroke-width="5" stroke-linejoin="round"/><path d="M50 55 L130 0" stroke="var(--c2)" stroke-width="4"/></svg>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><path class="pp-line" d="M${L.x(0.04)} ${base} H${L.x(0.96)}" stroke="var(--c1l)" stroke-width="${12 * k}" stroke-linecap="round"/>
      ${st.map((s, i) => `<path class="pp-arc" d="M${sx(i)} ${base - 40 * k} Q ${(sx(i) + hx) / 2} ${hy - 240 * k} ${hx} ${hy}" fill="none" stroke="var(--c1l)" stroke-width="${6 * k}" stroke-dasharray="${14 * k} ${12 * k}"/>`).join('')}</svg>` +
    api.at(hx, hy, house, { cls: 'pp-h', idle: 'float', amp: 0.5 }) +
    st.map((s, i) => api.at(sx(i), base, `<div class="badge ${['acc', 'c2', 'bad'][i % 3]}" style="font-size:${70 * k}px"></div>`, { cls: 'pp-dot' }) +
      api.at(0, 0, plane, { cls: 'pp-pl' }) +
      api.at(L.x(0.36), L.y(0.38 + i * 0.17), `<div class="card" style="padding:.25em .7em .35em;border-left:${16 * k}px solid ${['var(--acc)', 'var(--c1)', 'var(--bad)'][i % 3]}">
        <div class="label" style="font-size:${36 * k}px;color:var(--muted)">${R.esc(s.when)}</div><div class="big" style="font-size:${66 * k}px;color:var(--ink)">${R.esc(s.msg)}</div></div>`, { cls: 'pp-m', idle: 'sway' })).join('') +
    api.at(L.x(0.26), L.y(0.08), `<div class="big" style="font-size:${120 * k}px;color:var(--c1l)">${R.esc(p.three || '')}</div>`, { cls: 'pp-3' });
  const pls = qa(root, '.pp-pl'), arcs = qa(root, '.pp-arc');
  return t => {
    R.draw(q(root, '.pp-line'), api.prog(t, api.start, api.start + 0.6, 'io'));
    api.tw(q(root, '.pp-h .a'), t, api.K.pop(api.start + 0.2, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.pp-3 .a'), t, api.K.slam(t3 - 0.05, 0.4));
    qa(root, '.pp-dot').forEach((d, i) => api.tw(q(d, '.a'), t, api.K.pop(tw[i] - 0.05, 0.35, { o: 0, s: 0 })));
    pls.forEach((pl, i) => {
      const a = arcs[i], u = api.prog(t, tm[i] - 0.1, tm[i] + 0.8, 'io'), len = a.getTotalLength(), pt = a.getPointAtLength(len * u), p2 = a.getPointAtLength(Math.min(len, len * u + 2));
      pl.style.left = pt.x + 'px'; pl.style.top = pt.y + 'px'; q(pl, '.m').style.transform = `rotate(${(Math.atan2(p2.y - pt.y, p2.x - pt.x) * 57.3 + 17).toFixed(1)}deg)`;
      api.tw(q(pl, '.a'), t, [[tm[i] - 0.15, { o: 0, s: 0.4 }], [tm[i], { o: 1, s: 1 }], [tm[i] + 0.75, { o: 1 }], [tm[i] + 0.9, { o: 0, s: 0.5 }, 'in']]);
      R.draw(a, api.prog(t, tm[i] - 0.1, tm[i] + 0.8, 'io'));
    });
    qa(root, '.pp-m').forEach((m, i) => api.tw(q(m, '.a'), t, api.K.pop(tm[i] + 0.05, 0.4, { o: 0, s: 0.3, x: -100 * k })));
  };
});
