/* @scene {"type":"ai_scout","tags":["ai","assistant","research","trends","viral"],"layout":"robot-left-tile-wall-right","metaphor":"a friendly robot helper sweeps a magnifier over a wall of short videos and lifts out the one that took off","assets":["robot helper","wall of video tiles","magnifier","rising tile"]} */
// {name, nameAt, badge:"...", badgeAt, scanAt, hitAt, hit, hitTag}
RM.def('ai_scout', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tN = api.T(p.nameAt ?? api.start), tB = api.T(p.badgeAt), tS = api.T(p.scanAt), tH = api.T(p.hitAt), hit = p.hit ?? 4;
  const RW = 420 * k;
  const robot = `<svg width="${RW}" height="${RW * 1.3}" viewBox="-160 -230 320 416" overflow="visible">
      <path d="M0 -150 V-190" stroke="var(--c2)" stroke-width="10"/><circle class="ai-led" cx="0" cy="-200" r="16" fill="var(--bad)"/>
      <rect x="-130" y="-150" width="260" height="190" rx="60" fill="var(--paper)" stroke="var(--c2)" stroke-width="10"/>
      <rect x="-96" y="-110" width="192" height="100" rx="40" fill="var(--ink)"/>
      <g class="ai-eyes"><ellipse cx="-44" cy="-60" rx="20" ry="24" fill="var(--acc-soft)"/><ellipse cx="44" cy="-60" rx="20" ry="24" fill="var(--acc-soft)"/></g>
      <rect x="-150" y="-80" width="24" height="70" rx="10" fill="var(--c1)"/><rect x="126" y="-80" width="24" height="70" rx="10" fill="var(--c1)"/>
      <rect x="-100" y="56" width="200" height="130" rx="40" fill="var(--c1)"/>
      <text class="ai-txt" x="0" y="146" text-anchor="middle" style="font-family:var(--f-display);font-weight:900;font-size:78px" fill="var(--paper)">${R.esc(p.badge || '')}</text></svg>`;
  const TS = 170 * k, gx0 = L.x(0.68), gy0 = L.y(0.5);
  const tiles = Array.from({ length: 9 }, (_, i) => {
    const c = i % 3, r = Math.floor(i / 3);
    return api.at(gx0 + (c - 1) * (TS + 24 * k), gy0 + (r - 1) * (TS * 1.5 + 24 * k), `<div style="width:${TS}px;height:${TS * 1.5}px;border-radius:${22 * k}px;background:${i % 2 ? 'var(--c1l)' : 'var(--acc-soft)'};display:flex;align-items:center;justify-content:center;box-shadow:var(--sh)">
        <svg width="${TS * 0.36}" height="${TS * 0.36}" viewBox="0 0 10 10"><path d="M2 1 L9 5 L2 9 Z" fill="${i === hit ? 'var(--bad)' : 'var(--paper)'}"/></svg></div>`, { cls: 'ai-tile' + (i === hit ? ' ai-hit' : '') });
  }).join('');
  root.innerHTML = tiles +
    api.at(gx0 + ((hit % 3) - 1) * (TS + 24 * k) + TS * 0.55, gy0 + (Math.floor(hit / 3) - 1) * (TS * 1.5 + 24 * k) - TS * 0.95, `<div class="badge good" style="font-size:${120 * k}px">${api.icon('ph-bold:trend-up', 70 * k)}</div>`, { cls: 'ai-up' }) +
    api.at(0, 0, api.icon('ph:magnifying-glass', 230 * k, 'var(--c2)'), { cls: 'ai-mag' }) +
    api.at(L.cx, L.y(0.55), robot, { cls: 'ai-rb', idle: 'float' }) +
    api.at(L.cx, L.y(0.08), R.tag(p.name || '', 66 * k, 'c1'), { cls: 'ai-nm', idle: 'sway' }) +
    (p.hitTag ? api.at(gx0, L.y(0.97), R.tag(p.hitTag, 58 * k, 'bad'), { cls: 'ai-ht', idle: 'sway' }) : '');
  const rb = q(root, '.ai-rb'), tl = qa(root, '[class*="ai-tile"]');
  return t => {
    const mv = api.prog(t, tS - 0.2, tS + 0.4, 'io');
    rb.style.left = (L.cx + (L.x(0.2) - L.cx) * mv) + 'px'; rb.style.top = (L.y(0.55) + (L.y(0.62) - L.y(0.55)) * mv) + 'px';
    api.tw(q(rb, '.a'), t, api.K.spring(api.start, 0.6, { o: 0, s: 0.3, y: 200 * k }).concat([[tS - 0.2, {}], [tS + 0.4, { s: 0.62 }, 'io']]));
    q(root, '.ai-led').style.opacity = 0.5 + 0.5 * Math.sin(t * 9);
    q(root, '.ai-eyes').setAttribute('transform', `translate(${(t > tS ? 14 : 6 * Math.sin(t * 1.3)).toFixed(1)} 0) scale(1 ${(Math.sin(t * 2.7) > 0.97 ? 0.1 : 1)})`);
    api.tw(q(root, '.ai-txt'), t, [[tB - 0.05, { o: 0 }], [tB + 0.1, { o: 1 }]]);
    api.tw(q(root, '.ai-nm .a'), t, api.K.pop(tN, 0.4, { o: 0, s: 0.3, r: -10 }));
    tl.forEach((e, i) => {
      const isHit = e.classList.contains('ai-hit');
      const keys = api.K.pop(tS - 0.1 + i * 0.05, 0.35, { o: 0, s: 0.4 });
      if (isHit) keys.push([tH - 0.05, {}], [tH + 0.4, { s: 1.35, y: -60 * k }, 'back']);
      else keys.push([tH - 0.05, {}], [tH + 0.3, { o: 0.45, s: 0.92 }, 'out']);
      api.tw(q(e, '.a'), t, keys); if (isHit) e.style.zIndex = t > tH ? 5 : '';
    });
    // magnifier sweeps the wall row by row, then parks on the winner
    const m = q(root, '.ai-mag'), su = api.prog(t, tS + 0.3, tH - 0.05, 'lin');
    const path = [[0, 0], [2, 0], [2, 1], [0, 1], [0, 2], [2, 2]], seg = Math.min(4.999, su * 5), j = Math.floor(seg), f = seg - j;
    let cc = path[j][0] + (path[j + 1][0] - path[j][0]) * f, rr = path[j][1] + (path[j + 1][1] - path[j][1]) * f;
    const hu = api.prog(t, tH - 0.05, tH + 0.35, 'io'); cc += ((hit % 3) - cc) * hu; rr += (Math.floor(hit / 3) - rr) * hu;
    m.style.left = (gx0 + (cc - 1) * (TS + 24 * k) + 40 * k) + 'px'; m.style.top = (gy0 + (rr - 1) * (TS * 1.5 + 24 * k) + 40 * k) + 'px';
    api.tw(q(m, '.a'), t, [[tS + 0.1, { o: 0, s: 0.4 }], [tS + 0.4, { o: 1, s: 1 }, 'back'], [tH + 0.3, {}], [tH + 0.6, { o: 0, s: 1.4 }, 'in']]);
    api.tw(q(root, '.ai-up .a'), t, api.K.pop(tH + 0.15, 0.4, { o: 0, s: 0, y: 80 * k }));
    if (p.hitTag) api.tw(q(root, '.ai-ht .a'), t, api.K.pop(tH + 0.1, 0.4, { o: 0, s: 0.3, r: 10 }));
  };
});
