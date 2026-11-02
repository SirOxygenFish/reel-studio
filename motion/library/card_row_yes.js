/* @scene {"type":"card_row_yes","tags":["statistics","rejections mean nothing","your yes","keep going"],"layout":"long-card-row-camera-pan","metaphor":"a long row of face-down cards: the first three flip to NO, then the view pans far down the row to where one flips to YES","assets":["playing-card row","NO and YES faces"]} */
// {no, yes, flipAt, nothingAt, nothing, panAt, yesAt}
RM.def('card_row_yes', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tF = api.T(p.flipAt ?? api.start), tN = api.T(p.nothingAt), tP = api.T(p.panAt), tY = api.T(p.yesAt), N = 24, YES = 21;
  const CW = 200 * k, CH = 300 * k, gap = 30 * k, y = L.y(0.5);
  const card = i => `<div style="perspective:${1200 * k}px"><div class="cr-c" style="position:relative;width:${CW}px;height:${CH}px;transform-style:preserve-3d">
      <div style="position:absolute;inset:0;border-radius:${18 * k}px;background:repeating-linear-gradient(45deg,var(--c1) 0 ${16 * k}px,var(--c2) ${16 * k}px ${32 * k}px);border:${8 * k}px solid var(--paper);box-shadow:var(--sh);backface-visibility:hidden"></div>
      <div style="position:absolute;inset:0;border-radius:${18 * k}px;background:var(--paper);border:${8 * k}px solid ${i === YES ? 'var(--good)' : 'var(--bad)'};display:flex;align-items:center;justify-content:center;transform:rotateY(180deg);backface-visibility:hidden">
        <div class="big" style="font-size:${66 * k}px;color:${i === YES ? 'var(--good)' : 'var(--bad)'}">${R.esc(i === YES ? p.yes || '' : p.no || '')}</div></div></div></div>`;
  root.innerHTML = `<div class="cr-track" style="position:absolute;left:0;top:0">${Array.from({ length: N }, (_, i) => api.at(L.x(0.18) + i * (CW + gap), y, card(i), { cls: 'cr-p', content: false })).join('')}</div>` +
    api.at(L.cx, L.y(0.08), R.tag(p.nothing || '', 60 * k, 'c1'), { cls: 'cr-t', idle: 'sway' });
  const cs = qa(root, '.cr-c'), track = q(root, '.cr-track'), dist = (YES - 1) * (CW + gap) - (L.cx - L.x(0.18)) + (CW + gap);
  return t => {
    const pan = api.prog(t, tP - 0.2, tY - 0.05, 'io');
    track.style.transform = `translateX(${(-dist * pan).toFixed(1)}px)`;
    cs.forEach((c, i) => { const at = i < 3 ? tF + i * 0.35 : i === YES ? tY : 1e9;
      c.style.transform = `rotateY(${(180 * api.prog(t, at, at + 0.45, 'back')).toFixed(1)}deg) translateY(${(i === YES && t > tY + 0.4 ? -20 * k * Math.abs(Math.sin((t - tY) * 5)) : 0).toFixed(1)}px)`; });
    qa(root, '.cr-p').forEach((pt, i) => api.tw(q(pt, '.a'), t, [[api.start + Math.min(i, 8) * 0.04, { o: 0, y: 60 * k }], [api.start + 0.3 + Math.min(i, 8) * 0.04, { o: 1, y: 0 }, 'back']]));
    api.tw(q(root, '.cr-t .a'), t, api.K.pop(tN - 0.05, 0.4, { o: 0, s: 0.3, r: -6 }));
  };
});
