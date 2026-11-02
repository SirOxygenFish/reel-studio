/* @scene {"type":"paper_wall","tags":["circumstances","excuse","try","break through"],"layout":"brick-wall-full-tear","metaphor":"a solid-looking brick wall labelled 'the situation' turns out to be paper: a poke tears it open onto a sunny path","assets":["painted paper brick wall","poking finger","torn paper edges","sunny path"]} */
// {wall, wallAt, really, reallyAt, tearAt, try, tryAt}
RM.def('paper_wall', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tW = api.T(p.wallAt ?? api.start), tR = api.T(p.reallyAt), tT = api.T(p.tearAt), tY = api.T(p.tryAt ?? p.tearAt);
  const W = L.w, H = L.h * 0.86, ox = L.x0, oy = L.y0 + L.h * 0.06;
  const bricks = []; for (let r = 0; r < 9; r++) for (let c = -1; c < 7; c++) bricks.push(`<rect x="${(c + (r % 2) * 0.5) * W / 6 + 4}" y="${r * H / 9 + 4}" width="${W / 6 - 8}" height="${H / 9 - 8}" rx="6" fill="${(r * 3 + c) % 4 ? 'var(--c1)' : 'var(--bad)'}"/>`);
  const half = (side) => `<svg class="pw-h pw-${side}" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" style="position:absolute;left:${ox}px;top:${oy}px;overflow:visible">
      <clipPath id="pwc${side}"><path d="${side === 'l' ? `M0 0 H${W * 0.52} L${W * 0.46} ${H * 0.2} L${W * 0.56} ${H * 0.38} L${W * 0.44} ${H * 0.55} L${W * 0.55} ${H * 0.75} L${W * 0.47} ${H} H0 Z`
                                                        : `M${W} 0 H${W * 0.52} L${W * 0.46} ${H * 0.2} L${W * 0.56} ${H * 0.38} L${W * 0.44} ${H * 0.55} L${W * 0.55} ${H * 0.75} L${W * 0.47} ${H} H${W} Z`}"/></clipPath>
      <g clip-path="url(#pwc${side})"><rect width="${W}" height="${H}" fill="var(--c2)"/>${bricks.join('')}</g></svg>`;
  root.innerHTML = `<div style="position:absolute;left:${ox}px;top:${oy}px;width:${W}px;height:${H}px;border-radius:${30 * k}px;overflow:hidden;background:linear-gradient(180deg,var(--orb2),var(--c1x))">
      <div class="round" style="position:absolute;left:${W * 0.5 - 110 * k}px;top:${H * 0.12}px;width:${220 * k}px;height:${220 * k}px;background:radial-gradient(circle,var(--paper),var(--c1l))"></div>
      <div style="position:absolute;left:0;right:0;bottom:0;height:${H * 0.32}px;background:var(--acc-soft)"></div>
      <div style="position:absolute;left:${W * 0.38}px;bottom:0;width:${W * 0.24}px;height:${H * 0.32}px;background:var(--paper);clip-path:polygon(35% 0,65% 0,100% 100%,0 100%)"></div></div>` +
    half('l') + half('r') +
    api.at(L.cx, L.y(0.42), R.tag(p.wall || '', 84 * k, 'paper'), { cls: 'pw-w', idle: 'sway' }) +
    api.at(L.x(0.7), L.y(0.62), api.icon('ph-fill:hand-pointing', 200 * k, 'var(--c1l)'), { cls: 'pw-f' }) +
    api.at(L.x(0.3), L.y(0.8), R.tag(p.really || '', 74 * k, 'c1'), { cls: 'pw-r', idle: 'wobble' }) +
    api.at(L.cx, L.y(0.95), R.tag(p.try || '', 74 * k, ''), { cls: 'pw-y', idle: 'sway' });
  return t => {
    api.tw(q(root, '.pw-w .a'), t, api.K.slam(tW - 0.05, 0.4).concat([[tT - 0.05, {}], [tT + 0.3, { o: 0, s: 0.6 }, 'in']]));
    const poke = api.prog(t, tR, tR + 0.3, 'back');
    api.tw(q(root, '.pw-f .a'), t, [[tR - 0.3, { o: 0, x: 300 * k, r: -30 }], [tR, { o: 1, x: 0, r: -30 }, 'out'], [tR + 0.15, { x: -40 * k }, 'in'], [tR + 0.35, { x: 0 }, 'out'], [tT - 0.1, {}], [tT, { x: -60 * k }, 'in'], [tT + 0.3, { o: 0 }, 'lin']]);
    const tear = api.prog(t, tT, tT + 0.7, 'out'), wob = t > tR && t < tT ? 4 * Math.sin((t - tR) * 30) * Math.exp(-(t - tR) * 3) : 0;
    q(root, '.pw-l').style.transform = `translateX(${(-W * 0.62 * tear).toFixed(1)}px) rotate(${(-8 * tear + wob * 0.2).toFixed(2)}deg)`;
    q(root, '.pw-r').style.transform = `translateX(${(W * 0.62 * tear).toFixed(1)}px) rotate(${(8 * tear - wob * 0.2).toFixed(2)}deg)`;
    api.tw(q(root, '.pw-r .a'), t, api.K.pop(tR, 0.4, { o: 0, s: 0.3, r: -8 }).concat([[tT, {}], [tT + 0.3, { o: 0 }, 'lin']]));
    api.tw(q(root, '.pw-y .a'), t, api.K.pop(tY - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
