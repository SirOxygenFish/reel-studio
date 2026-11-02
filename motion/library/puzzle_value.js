/* @scene {"type":"puzzle_value","tags":["value","price is one piece","quality","trust","complete picture"],"layout":"two-by-two-puzzle-assembly","metaphor":"the full picture is a four-piece puzzle: quality, effect and trust fly in, and price clicks in as just one piece","assets":["jigsaw pieces","snap sparkle"]} */
// {pieces:[{label, at}], last:{label, at}, tag, tagAt}
RM.def('puzzle_value', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const ps = (p.pieces || []).concat(p.last ? [p.last] : []), ts = ps.map(x => api.T(x.at)), tT = p.tag ? api.T(p.tagAt) : 0;
  const S = 380 * k, cx = L.cx, cy = L.y(0.5);
  const cols = ['var(--acc)', 'var(--c1)', 'var(--c2)', 'var(--bad)'];
  // a 2x2 jigsaw: tab directions per piece (right / bottom edges bulge, left / top edges notch accordingly)
  const shape = (i) => { const c = i % 2, r = Math.floor(i / 2), s = 100, b = 22;
    const right = c === 0 ? `L${s} ${s * 0.35} C ${s + b} ${s * 0.3} ${s + b} ${s * 0.7} ${s} ${s * 0.65} L${s} ${s}` : `L${s} ${s}`;
    const bottom = r === 0 ? `L${s * 0.65} ${s} C ${s * 0.7} ${s + b} ${s * 0.3} ${s + b} ${s * 0.35} ${s} L0 ${s}` : `L0 ${s}`;
    const left = c === 1 ? `L0 ${s * 0.65} C ${b} ${s * 0.7} ${b} ${s * 0.3} 0 ${s * 0.35} L0 0` : `L0 0`;
    const topE = r === 1 ? `M0 0 L${s * 0.35} 0 C ${s * 0.3} ${b} ${s * 0.7} ${b} ${s * 0.65} 0 L${s} 0` : `M0 0 L${s} 0`;
    return `${topE} ${right} ${bottom} ${left} Z`; };
  root.innerHTML = ps.map((x, i) => api.at(cx + (i % 2 ? 0.5 : -0.5) * S, cy + (i < 2 ? -0.5 : 0.5) * S, `<div style="position:relative;width:${S}px;height:${S}px">
      <svg width="${S}" height="${S}" viewBox="0 0 100 100" overflow="visible" style="position:absolute;inset:0"><path d="${shape(i)}" fill="${cols[i % 4]}" stroke="var(--paper)" stroke-width="2.5"/></svg>
      <div class="big pz-l" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;font-size:${80 * k}px;color:var(--on-acc);white-space:normal;padding:${30 * k}px;word-break:keep-all">${R.esc(x.label)}</div></div>`, { cls: 'pz-p' })).join('') +
    `<div class="pz-glow" style="position:absolute;left:${cx - S * 1.15}px;top:${cy - S * 1.15}px;width:${S * 2.3}px;height:${S * 2.3}px;border-radius:50%;background:radial-gradient(closest-side,var(--c1x),transparent);opacity:0"></div>` +
    (p.tag ? api.at(cx, L.y(0.96), R.tag(p.tag, 66 * k, 'c1'), { cls: 'pz-t', idle: 'sway' }) : '');
  qa(root, '.pz-l').forEach(el => { let fs = 80 * k; while (fs > 26 && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)) { fs -= 2; el.style.fontSize = fs + 'px'; } });
  const last = ps.length - 1;
  return t => {
    qa(root, '.pz-p').forEach((e, i) => { const fx = (i % 2 ? 1 : -1) * 600 * k, fy = (i < 2 ? -1 : 1) * 500 * k;
      api.tw(q(e, '.a'), t, [[ts[i] - 0.15, { o: 0, x: fx, y: fy, r: (i % 2 ? 40 : -40), s: 0.8 }], [ts[i] + 0.35, { o: 1, x: 0, y: 0, r: 0, s: 1 }, 'back']].concat(i === last ? [[ts[i] + 0.45, { s: 1.08 }, 'out'], [ts[i] + 0.65, { s: 1 }, 'io']] : [])); });
    q(root, '.pz-glow').style.opacity = 0.9 * Math.sin(Math.PI * api.prog(t, ts[last] + 0.3, ts[last] + 1.3, 'lin'));
    if (p.tag) api.tw(q(root, '.pz-t .a'), t, api.K.slam(tT - 0.05, 0.4));
  };
});
