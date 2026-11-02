/* @scene {"type":"frame_ties","tags":["structure","holds together","30 percent","everywhere in the body"],"layout":"scaffold-center-tags-orbit","metaphor":"a loose scaffold of beams wobbles; ties wrap its joints one by one as body parts are named, and it pulls together and stands firm","assets":["scaffold beams","rope ties","percentage tag","part tags"]} */
// {pct, pctAt, parts:[{label, at}], togetherAt, together}
RM.def('frame_ties', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tP = api.T(p.pctAt ?? api.start), parts = p.parts || [], tp = parts.map(x => api.T(x.at)), tG = api.T(p.togetherAt);
  const S = 560 * k, cx = L.cx, cy = L.y(0.55);
  const nodes = [[-1, -1], [1, -1], [1, 1], [-1, 1], [0, -1.6], [0, 1.6]];
  root.innerHTML = `<svg class="ft-s" style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      ${[[0, 1], [1, 2], [2, 3], [3, 0], [0, 2], [1, 3], [0, 4], [1, 4], [2, 5], [3, 5]].map(([a, b], i) => `<line class="ft-b" data-a="${a}" data-b="${b}" stroke="var(--c2)" stroke-width="${22 * k}" stroke-linecap="round"/>`).join('')}
      ${nodes.map((_, i) => `<circle class="ft-tie" data-i="${i}" r="${30 * k}" fill="none" stroke="var(--acc)" stroke-width="${10 * k}"/>`).join('')}</svg>` +
    api.at(L.x(0.2), L.y(0.1), `<div class="big" style="font-size:${150 * k}px;color:var(--acc)">${R.esc(p.pct || '')}</div>`, { cls: 'ft-pct' }) +
    parts.map((x, i) => api.at(L.x([0.18, 0.82, 0.18, 0.82][i % 4]), L.y([0.36, 0.36, 0.84, 0.84][i % 4]), R.tag(x.label, 56 * k, ['', 'c1', 'paper', ''][i % 4]), { cls: 'ft-p', idle: 'sway' })).join('') +
    api.at(L.cx, L.y(0.98), R.tag(p.together || '', 62 * k, 'c1'), { cls: 'ft-g', idle: 'wobble' });
  const ties = qa(root, '.ft-tie'), beams = qa(root, '.ft-b');
  return t => {
    const tight = api.prog(t, tG - 0.1, tG + 0.6, 'back');
    const pos = nodes.map(([a, b], i) => { const loose = (1 - tight) * 26 * k; return [cx + a * S * 0.42 + loose * Math.sin(t * 3 + i * 1.7), cy + b * S * 0.36 + loose * Math.cos(t * 2.6 + i)]; });
    beams.forEach(l => { const A = pos[+l.dataset.a], B = pos[+l.dataset.b]; l.setAttribute('x1', A[0]); l.setAttribute('y1', A[1]); l.setAttribute('x2', B[0]); l.setAttribute('y2', B[1]); });
    q(root, '.ft-s').style.opacity = api.prog(t, api.start, api.start + 0.4, 'out');
    ties.forEach((c, i) => { c.setAttribute('cx', pos[i][0]); c.setAttribute('cy', pos[i][1]); const at = tp[Math.min(i, tp.length - 1)] ?? tG; c.style.opacity = t > (i < tp.length ? at : tG) ? 1 : 0; });
    api.tw(q(root, '.ft-pct .a'), t, api.K.slam(tP - 0.05, 0.4));
    qa(root, '.ft-p').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.pop(tp[i] - 0.05, 0.4, { o: 0, s: 0.3, r: i % 2 ? 6 : -6 })));
    api.tw(q(root, '.ft-g .a'), t, api.K.pop(tG, 0.4, { o: 0, s: 0.3 }));
  };
});
