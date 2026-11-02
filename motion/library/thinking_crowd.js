/* @scene {"type":"thinking_crowd","tags":["most people","reflection","second thought","majority"],"layout":"rows-of-heads-grid","metaphor":"rows of faces: one by one most of them get a thinking bubble, a few stay blank","assets":["rows of simple heads","thought bubbles with question marks"]} */
// {mostAt, most, notAllAt, notAll, thinkAt, think}
RM.def('thinking_crowd', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tM = api.T(p.mostAt ?? api.start), tN = api.T(p.notAllAt ?? p.mostAt), tT = api.T(p.thinkAt);
  const C = 5, Rw = 4, cw = L.w / C, rh = L.h * 0.17, skip = [3, 11, 17];
  const head = (i) => `<svg width="${cw * 0.7}" height="${cw * 0.7}" viewBox="-60 -60 120 120" overflow="visible">
      <circle r="50" fill="${['var(--c1l)', 'var(--c1x)', 'var(--paper)'][i % 3]}" stroke="var(--c2)" stroke-width="6"/>
      <circle cx="-17" cy="-6" r="6" fill="var(--ink)"/><circle cx="17" cy="-6" r="6" fill="var(--ink)"/>
      <path class="tc-mo" d="M-16 22 H16" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"/></svg>`;
  let html = '';
  for (let r = 0; r < Rw; r++) for (let c = 0; c < C; c++) {
    const i = r * C + c, x = L.x0 + cw * (c + 0.5) + (r % 2 ? cw * 0.18 : -cw * 0.18), y = L.y(0.3) + r * rh;
    html += api.at(x, y, head(i), { cls: 'tc-h', idle: 'bob', amp: 0.4 }) +
      (skip.includes(i) ? '' : api.at(x + cw * 0.3, y - cw * 0.42, `<div class="bubble" style="font-size:${44 * k}px;padding:.1em .45em;font-family:var(--f-display);font-weight:900;color:var(--c1)">?</div>`, { cls: 'tc-b', idle: 'float' }));
  }
  root.innerHTML = html + api.at(L.x(0.3), L.y(0.06), R.tag(p.most || '', 66 * k, 'c1'), { cls: 'tc-t1', idle: 'sway' }) +
    api.at(L.x(0.76), L.y(0.12), R.tag(p.notAll || '', 52 * k, 'paper'), { cls: 'tc-t2', idle: 'sway' }) +
    api.at(L.cx, L.y(0.98), R.tag(p.think || '', 70 * k, ''), { cls: 'tc-t3', idle: 'wobble' });
  return t => {
    qa(root, '.tc-h').forEach((h, i) => api.tw(q(h, '.a'), t, api.K.pop(api.start + (i % 5) * 0.04 + Math.floor(i / 5) * 0.06, 0.35, { o: 0, s: 0.3 })));
    qa(root, '.tc-b').forEach((b, i) => api.tw(q(b, '.a'), t, api.K.pop(tT - 0.2 + i * 0.05, 0.35, { o: 0, s: 0, y: 30 * k })));
    qa(root, '.tc-mo').forEach(m => m.setAttribute('d', t > tT ? 'M-14 24 Q0 16 14 24' : 'M-16 22 H16'));
    api.tw(q(root, '.tc-t1 .a'), t, api.K.pop(tM, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.tc-t2 .a'), t, api.K.pop(tN, 0.4, { o: 0, s: 0.3, r: 8 }));
    api.tw(q(root, '.tc-t3 .a'), t, api.K.slam(tT - 0.05, 0.4));
  };
});
