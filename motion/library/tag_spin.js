/* @scene {"type":"tag_spin","tags":["the question","low price","only thing","doubt"],"layout":"hanging-tag-center-string","metaphor":"a big price tag hangs on a string; as the question lands it spins round and shows its other side: only that?","assets":["hanging price tag","string and nail","sparkle"]} */
// {front, frontAt, back, spinAt, ask, askAt}
RM.def('tag_spin', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tF = api.T(p.frontAt ?? api.start), tS = api.T(p.spinAt), tA = p.ask ? api.T(p.askAt ?? p.spinAt) : 0;
  const TW = 700 * k, TH = 400 * k, cx = L.cx, top = L.y(0.08);
  const face = (txt, bg, fg, back) => `<div style="position:absolute;inset:0;backface-visibility:hidden;${back ? 'transform:rotateY(180deg);' : ''}background:${bg};color:${fg};
      clip-path:polygon(18% 0,100% 0,100% 100%,18% 100%,0 50%);border-radius:${20 * k}px;display:flex;align-items:center;justify-content:center;padding-left:${120 * k}px">
      <div class="big ts-l" style="font-size:${120 * k}px;white-space:normal;text-align:center;line-height:1">${R.esc(txt)}</div></div>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><path class="ts-str" stroke="var(--c2)" stroke-width="${8 * k}" fill="none"/></svg>` +
    api.at(cx, top, `<div class="round" style="width:${40 * k}px;height:${40 * k}px;background:var(--c2)"></div>`, { cls: 'ts-nail' }) +
    api.at(cx, L.y(0.55), `<div style="perspective:${1600 * k}px"><div class="ts-card" style="position:relative;width:${TW}px;height:${TH}px;transform-style:preserve-3d">
        ${face(p.front || '', 'var(--c1)', 'var(--on-c1)', false)}${face(p.back || '', 'var(--bad)', 'var(--on-bad)', true)}
        <div class="ts-hole" style="position:absolute;left:${60 * k}px;top:50%;width:${44 * k}px;height:${44 * k}px;margin-top:${-22 * k}px;border-radius:50%;background:var(--paper)"></div></div></div>`, { cls: 'ts-t' }) +
    (p.ask ? api.at(cx, L.y(0.95), R.tag(p.ask, 70 * k, 'c1'), { cls: 'ts-a', idle: 'sway' }) : '');
  R.qa(root, '.ts-l').forEach(el => { let fs = 120 * k; while (fs > 40 && (el.scrollHeight > TH * 0.9 || el.scrollWidth > TW * 0.78)) { fs -= 4; el.style.fontSize = fs + 'px'; } });
  const card = q(root, '.ts-card'), str = q(root, '.ts-str'), tpt = q(root, '.ts-t');
  return t => {
    api.tw(q(tpt, '.a'), t, api.K.drop(api.start + 0.1, 0.6, -600 * k));
    const fl = R.qa(root, '.ts-l')[0]; api.tw(fl, t, [[tF - 0.05, { o: 0, s: 0.6 }], [tF + 0.3, { o: 1, s: 1 }, 'back']]);
    api.tw(q(root, '.ts-nail .a'), t, api.K.pop(api.start, 0.3, { o: 0, s: 0 }));
    const sw = 6 * Math.sin(t * 1.8) * (1 - api.prog(t, tS, tS + 0.2, 'lin')) + 4 * Math.sin(t * 2.2);
    const spin = 180 * api.prog(t, tS - 0.05, tS + 0.9, 'back');
    q(root, '.ts-hole').style.opacity = spin > 90 ? 0 : 1;
    card.style.transform = `rotateY(${(spin + sw * 3).toFixed(1)}deg) rotateZ(${sw.toFixed(2)}deg)`;
    const r = tpt.querySelector('.a').getBoundingClientRect();
    str.setAttribute('d', `M${L.cx} ${top} L${(r.left + r.width * 0.15).toFixed(1)} ${(r.top + r.height / 2).toFixed(1)}`);
    str.style.opacity = r.width > 5 ? 1 : 0;
    if (p.ask) api.tw(q(root, '.ts-a .a'), t, api.K.pop(tA, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
