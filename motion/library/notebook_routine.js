/* @scene {"type":"notebook_routine","tags":["routine","daily","notes","follow up","contacts"],"layout":"open-notebook-spread","metaphor":"an open notebook filling in day by day: tally marks of talks, written names, then a call after the purchase","assets":["spiral notebook","handwriting scribbles","tally marks","phone and shopping bag"]} */
// {day:"...", dayAt, talk:{label, at}, note:{label, at}, call:{label, at}, bagAt}
RM.def('notebook_routine', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tD = api.T(p.dayAt ?? api.start), tT = api.T(p.talk.at), tN = api.T(p.note.at), tC = api.T(p.call.at), tBag = api.T(p.bagAt ?? p.call.at);
  const NW = 940 * k, NH = 640 * k;
  const tally0 = 0;
  const tally = Array.from({ length: 5 }, (_, i) => i < 4 ? `<path class="nr-ta" d="M${80 + i * 34} 250 l -6 110" stroke="var(--ink)" stroke-width="9" stroke-linecap="round"/>`
                                                          : `<path class="nr-ta" d="M60 330 L 210 270" stroke="var(--ink)" stroke-width="9" stroke-linecap="round"/>`).join('');
  const scrib = [0, 1, 2, 3].map(i => `<path class="nr-sc" d="M${520} ${180 + i * 80} c 30 -30 50 20 80 -6 s 40 -24 70 4 s 50 18 80 -10 s 40 20 70 0" fill="none" stroke="var(--c2)" stroke-width="8" stroke-linecap="round"/>
      <path class="nr-ck" d="M${860} ${168 + i * 80} l 14 16 l 28 -32" fill="none" stroke="var(--good)" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>`).join('');
  const book = `<svg width="${NW}" height="${NH}" viewBox="0 0 940 640" overflow="visible">
      <rect x="10" y="20" width="920" height="600" rx="26" fill="var(--c2)"/>
      <path d="M30 30 H460 V600 H40 Q30 600 30 590 Z" fill="var(--paper)"/><path d="M480 30 H910 V590 Q910 600 900 600 H480 Z" fill="var(--paper)"/>
      ${Array.from({ length: 9 }, (_, i) => `<path d="M60 ${120 + i * 54} H430 M510 ${120 + i * 54} H880" stroke="var(--acc-soft)" stroke-width="4"/>`).join('')}
      ${Array.from({ length: 11 }, (_, i) => `<ellipse cx="470" cy="${60 + i * 52}" rx="22" ry="11" fill="none" stroke="var(--muted)" stroke-width="7"/>`).join('')}
      <rect class="nr-day" x="60" y="56" width="250" height="56" rx="14" fill="var(--acc)"/>
      ${tally}${scrib}</svg>`;
  root.innerHTML = api.at(L.cx, L.y(0.4), book, { cls: 'nr-b' }) +
    api.at(L.cx - 470 * k + 185 * k, L.y(0.4) - 320 * k + 84 * k, `<div class="big nr-dtt" style="font-size:${44 * k}px;color:var(--on-acc)">${R.esc(p.day || '')}</div>`, { cls: 'nr-dt' }) +
    [0, 1, 2].map(i => api.at(L.x(0.12 + i * 0.12), L.y(0.53), api.icon('ph:chat-circle-dots', 92 * k, 'var(--c1)'), { cls: 'nr-bub', idle: 'bob' })).join('') +
    api.at(L.x(0.26), L.y(0.68), R.tag(p.talk.label, 60 * k, 'c1'), { cls: 'nr-t1', idle: 'sway' }) +
    api.at(L.x(0.74), L.y(0.68), R.tag(p.note.label, 56 * k, ''), { cls: 'nr-t2', idle: 'sway' }) +
    api.at(L.x(0.3), L.y(0.86), `<div class="badge c2" style="font-size:${150 * k}px">${api.icon('ph-fill:phone-call', 86 * k)}</div>`, { cls: 'nr-ph' }) +
    api.at(L.x(0.52), L.y(0.86), api.icon('ph:shopping-bag', 150 * k, 'var(--c1)'), { cls: 'nr-bag', idle: 'float' }) +
    api.at(L.x(0.78), L.y(0.86), R.tag(p.call.label, 54 * k, 'c1'), { cls: 'nr-t3', idle: 'sway' });
  R.fitFont(q(root, '.nr-dtt'), 230 * k, 50 * k, 44 * k, 20);
  return t => {
    api.tw(q(root, '.nr-b .a'), t, api.K.rise(api.start, 0.5, 260 * k).concat([[tC - 0.2, {}], [tC + 0.2, { y: -40 * k, s: 0.94 }, 'io']]));
    const dd = q(root, '.nr-day'); dd.style.opacity = api.prog(t, tD, tD + 0.3, 'out');
    api.tw(q(root, '.nr-dt .a'), t, api.K.pop(tD + 0.05, 0.35, { o: 0, s: 0.5 }).concat([[tC - 0.2, {}], [tC + 0.2, { y: -40 * k }, 'io']]));
    qa(root, '.nr-ta').forEach((e, i) => R.draw(e, api.prog(t, tT + i * 0.16, tT + i * 0.16 + 0.18, 'out')));
    qa(root, '.nr-bub').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.pop(tT + 0.1 + i * 0.15, 0.35, { o: 0, s: 0.2 }).concat([[tC - 0.2, {}], [tC + 0.1, { o: 0 }, 'lin']])));
    api.tw(q(root, '.nr-t1 .a'), t, api.K.pop(tT + 0.2, 0.4, { o: 0, s: 0.3, r: -10 }).concat([[tN + 0.1, {}], [tN + 0.35, { o: 0, s: 0.7 }, 'in']]));
    qa(root, '.nr-sc').forEach((e, i) => R.draw(e, api.prog(t, tN + i * 0.3, tN + i * 0.3 + 0.35, 'io')));
    qa(root, '.nr-ck').forEach((e, i) => R.draw(e, api.prog(t, tN + i * 0.3 + 0.3, tN + i * 0.3 + 0.45, 'out')));
    api.tw(q(root, '.nr-t2 .a'), t, api.K.pop(tN + 0.3, 0.4, { o: 0, s: 0.3, r: 10 }).concat([[tC - 0.2, {}], [tC + 0.1, { o: 0 }, 'lin']]));
    const ring = t > tC + 0.3 ? 9 * Math.sin((t - tC) * 40) * Math.max(0, 1 - (t - tC - 0.3) / 1.5) : 0;
    api.tw(q(root, '.nr-ph .a'), t, api.K.spring(tC, 0.55, { o: 0, s: 0.2 }).map(x => [x[0], Object.assign({}, x[1]), x[2]]));
    q(root, '.nr-ph .i').style.transform = `rotate(${ring.toFixed(1)}deg)`;
    api.tw(q(root, '.nr-bag .a'), t, api.K.drop(tBag - 0.1, 0.45, -300 * k));
    api.tw(q(root, '.nr-t3 .a'), t, api.K.pop(tC + 0.25, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
