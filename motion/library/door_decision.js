/* @scene {"type":"door_decision","tags":["decision","choice","responsibility","door","not yours"],"layout":"door-frame-left","metaphor":"a door that only the other person can open; your pushing hand is crossed out","assets":["wooden door","light behind door","pushing hand"]} */
// {wobbleAt, openAt, tag:"...", tagAt, hand:"...", handAt}
RM.def('door_decision', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tW = api.T(p.wobbleAt ?? api.start + 0.3), tO = api.T(p.openAt), tTag = api.T(p.tagAt ?? p.openAt), tH = api.T(p.handAt);
  const DW = 400 * k, DH = 720 * k, x0 = L.x(0.36), y0 = L.y(0.58);
  const panels = `<svg width="${DW}" height="${DH}" viewBox="0 0 430 780" style="position:absolute;inset:0">
      <rect x="0" y="0" width="430" height="780" rx="14" fill="var(--c1)"/>
      ${[[40, 40, 350, 300], [40, 380, 160, 360], [230, 380, 160, 360]].map(([x, y, w, h]) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="18" fill="none" stroke="var(--c2)" stroke-width="12" opacity=".75"/>`).join('')}
      ${Array.from({ length: 7 }, (_, i) => `<path d="M${60 + i * 50} 60 q 10 120 -4 260" stroke="var(--c2)" stroke-width="3" fill="none" opacity=".25"/>`).join('')}
      <ellipse cx="372" cy="420" rx="26" ry="26" fill="var(--c1l)" stroke="var(--c2)" stroke-width="8"/></svg>`;
  root.innerHTML =
    api.at(x0, y0, `<div style="position:relative;width:${DW + 70 * k}px;height:${DH + 50 * k}px">
        <div style="position:absolute;left:${35 * k}px;top:${35 * k}px;width:${DW}px;height:${DH}px;border-radius:${10 * k}px;background:radial-gradient(70% 60% at 50% 55%, var(--paper) 0%, var(--c1x) 55%, var(--c1l) 100%)" class="dd-light"></div>
        <div class="dd-rays" style="position:absolute;left:${35 * k}px;top:${35 * k}px;width:${DW}px;height:${DH}px;overflow:hidden">${Array.from({ length: 6 }, (_, i) =>
          `<div style="position:absolute;left:50%;top:50%;width:${DW * 2}px;height:${36 * k}px;margin:${-18 * k}px 0 0 ${-DW}px;background:linear-gradient(90deg,transparent,var(--paper),transparent);transform:rotate(${i * 30}deg);opacity:.7"></div>`).join('')}</div>
        <div style="position:absolute;inset:0;border:${35 * k}px solid var(--c2);border-bottom:0;border-radius:${18 * k}px ${18 * k}px 0 0"></div>
        <div style="position:absolute;left:${35 * k}px;top:${35 * k}px;width:${DW}px;height:${DH}px;perspective:${1400 * k}px"><div class="dd-door" style="position:absolute;inset:0;transform-origin:0 50%;box-shadow:var(--sh)">${panels}</div></div>
      </div>`, { cls: 'dd-frame' }) +
    api.at(L.cx, L.y(0.1), R.tag(p.tag || '', 80 * k, ''), { cls: 'dd-tag', idle: 'sway' }) +
    api.at(L.x(0.8), L.y(0.68), `<div style="position:relative">${api.icon('ph:hand-palm', 210 * k, 'var(--c2)')}
        <div class="badge bad dd-x" style="position:absolute;right:${-30 * k}px;top:${-20 * k}px;font-size:${110 * k}px">${api.icon('ph-bold:x', 64 * k)}</div></div>`, { cls: 'dd-hand', idle: 'float' }) +
    api.at(L.x(0.79), L.y(0.9), `<div class="label" style="font-size:${50 * k}px;color:var(--bad)">${R.esc(p.hand || '')}</div>`, { cls: 'dd-hl' });
  return t => {
    api.tw(q(root, '.dd-frame .a'), t, api.K.rise(api.start, 0.5, 300 * k));
    const wob = t > tW && t < tO ? 3 * Math.sin((t - tW) * 22) * Math.exp(-(t - tW) * 3) : 0;
    const open = api.prog(t, tO, tO + 0.7, 'back');
    q(root, '.dd-door').style.transform = `rotateY(${(-74 * open + wob).toFixed(2)}deg)`;
    q(root, '.dd-rays').style.opacity = api.prog(t, tO + 0.1, tO + 0.6, 'out');
    q(root, '.dd-rays').style.transform = `rotate(${(t * 12).toFixed(1)}deg) scale(1.3)`;
    api.tw(q(root, '.dd-tag .a'), t, [[tTag, { o: 0, s: 0.3, r: 20, x: -80 * k }], [tTag + 0.45, { o: 1, s: 1, r: -6, x: 0 }, 'back']]);
    api.tw(q(root, '.dd-hand .a'), t, api.K.antic(tH - 0.15, 160 * k, 140 * k, 0.45).concat([[tH + 0.55, {}], [tH + 0.8, { x: 40 * k, y: 30 * k, r: 12 }, 'io']]));
    api.tw(q(root, '.dd-x'), t, api.K.pop(tH + 0.25, 0.35, { o: 0, s: 0 }));
    api.tw(q(root, '.dd-hl .a'), t, api.K.rise(tH + 0.05, 0.4, 60 * k));
  };
});
