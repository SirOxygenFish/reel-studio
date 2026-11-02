/* @scene {"type":"boulder_burden","tags":["worry","burden","other people's failure","start","let go"],"layout":"figure-left-startline-right","metaphor":"a figure crushed by a boulder of someone else's failures that crumbles before anyone has even started","assets":["bent figure","boulder","empty start line","flag"]} */
// {dropAt, label:"...", labelAt, lineAt, crackAt}
RM.def('boulder_burden', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tD = api.T(p.dropAt), tLb = api.T(p.labelAt ?? p.dropAt), tLn = api.T(p.lineAt), tC = api.T(p.crackAt);
  const FW = 520 * k;
  // boulder: a lumpy round blob; on the crack it is replaced by three wedges that fly apart
  const rad = a => 150 + 18 * Math.sin(a * 3 + 1) + 12 * Math.sin(a * 5 + 2), pt = a => [(rad(a) * 1.15 * Math.cos(a)).toFixed(1), (rad(a) * 0.9 * Math.sin(a)).toFixed(1)];
  const arc = (a0, a1) => Array.from({ length: 13 }, (_, i) => pt(a0 + (a1 - a0) * i / 12).join(' ')).join(' L');
  const ROCK = `<path class="bb-whole" d="M${arc(0, 6.283)} Z" fill="var(--muted)" stroke="var(--ink)" stroke-width="8" stroke-linejoin="round"/>
      <path d="M-70 -70 Q-20 -110 40 -96" stroke="var(--c1l)" stroke-width="12" fill="none" stroke-linecap="round" opacity=".6" class="bb-shine"/>` +
    [[0.3, 2.4], [2.4, 4.4], [4.4, 6.583]].map(([a0, a1], i) => `<path class="bb-frag" data-i="${i}" d="M0 0 L${arc(a0, a1)} Z" fill="var(--muted)" stroke="var(--ink)" stroke-width="7" stroke-linejoin="round"/>`).join('') +
    `<path class="bb-crack" d="M 10 -120 L -10 -50 L 30 0 L 0 60 L 20 115" stroke="var(--ink)" stroke-width="9" fill="none" stroke-linecap="round"/>`;
  // figure: head + torso + legs, the torso bends at the hips (group transforms set per frame)
  const fig = `<svg width="${FW}" height="${FW * 1.5}" viewBox="-260 -520 520 780" overflow="visible">
      <ellipse cx="0" cy="252" rx="170" ry="18" fill="var(--hard-shadow)"/>
      <g class="bb-legs"><path class="bb-l1" d="M-30 40 L-50 140 L-40 245" stroke="var(--c2)" stroke-width="44" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        <path class="bb-l2" d="M30 40 L50 140 L40 245" stroke="var(--c2)" stroke-width="44" stroke-linecap="round" stroke-linejoin="round" fill="none"/></g>
      <g class="bb-top"><path d="M-70 40 Q-80 -150 0 -170 Q80 -150 70 40 Z" fill="var(--acc)"/>
        <path class="bb-arm" d="M-60 -120 Q-130 -40 -110 30" stroke="var(--acc)" stroke-width="36" stroke-linecap="round" fill="none"/>
        <circle cx="0" cy="-245" r="70" fill="var(--c1l)" stroke="var(--c2)" stroke-width="8"/>
        <path class="bb-mouth" d="M-26 -212 Q0 -226 26 -212" stroke="var(--ink)" stroke-width="8" fill="none" stroke-linecap="round"/>
        <circle cx="-24" cy="-252" r="8" fill="var(--ink)"/><circle cx="24" cy="-252" r="8" fill="var(--ink)"/>
        <g class="bb-rock" transform="translate(10 -400)">${ROCK}</g></g></svg>`;
  const line = `<svg width="${330 * k}" height="${420 * k}" viewBox="0 0 330 420" overflow="visible">
      <rect x="10" y="330" width="310" height="22" rx="8" fill="var(--paper)" stroke="var(--c2)" stroke-width="6"/>
      ${Array.from({ length: 6 }, (_, i) => `<rect x="${12 + i * 52}" y="332" width="26" height="18" fill="var(--c2)"/>`).join('')}
      <path d="M90 330 L90 70" stroke="var(--c2)" stroke-width="12" stroke-linecap="round"/>
      <path class="bb-flag" d="M96 76 Q170 50 240 82 Q190 112 240 150 Q170 120 96 146 Z" fill="var(--acc)"/>
      <path d="M190 300 l40 0 l18 30 l-76 0 z M250 300 l40 0 l18 30 l-76 0 z" fill="none" stroke="var(--line)" stroke-width="8" stroke-dasharray="12 10"/></svg>`;
  const fx = L.x(0.33), fy = L.y(0.6);
  root.innerHTML = api.at(fx, fy, fig, { cls: 'bb-fig' }) +
    api.at(L.cx, L.y(0.09), R.tag(p.label || '', 70 * k, 'bad'), { cls: 'bb-tag', idle: 'sway' }) +
    api.at(L.x(0.8), L.y(0.66), line, { cls: 'bb-line' });
  const frs = qa(root, '.bb-frag');
  return t => {
    api.tw(q(root, '.bb-fig .a'), t, api.K.rise(api.start, 0.45, 260 * k));
    const drop = api.prog(t, tD - 0.35, tD, 'in'), crack = api.prog(t, tC, tC + 0.6, 'in');
    const squash = (t >= tD ? Math.min(1, (t - tD) / 0.15) : 0) * (1 - api.prog(t, tC + 0.1, tC + 0.6, 'out'));
    // the boulder falls onto the back, the torso bends forward, the knees give
    q(root, '.bb-rock').setAttribute('transform', `translate(10 ${(-400 - 700 * (1 - drop) + 40 * squash).toFixed(1)})`);
    q(root, '.bb-top').setAttribute('transform', `translate(0 40) rotate(${(24 * squash + 2 * Math.sin(t * 3) * squash).toFixed(2)}) translate(0 -40) translate(0 ${(30 * squash).toFixed(1)})`);
    q(root, '.bb-l1').setAttribute('d', `M-30 ${40 + 30 * squash} L${-50 - 50 * squash} ${140 + 10 * squash} L-40 245`);
    q(root, '.bb-l2').setAttribute('d', `M30 ${40 + 30 * squash} L${50 + 50 * squash} ${140 + 10 * squash} L40 245`);
    q(root, '.bb-mouth').setAttribute('d', squash > 0.3 ? 'M-26 -206 Q0 -224 26 -206' : 'M-26 -214 Q0 -200 26 -214');
    q(root, '.bb-rock').style.opacity = t < tD - 0.36 ? 0 : 1;
    R.draw(q(root, '.bb-crack'), api.prog(t, tC - 0.3, tC, 'out'));
    frs.forEach((f, i) => {
      const dx = [-260, 240, -60][i], dy = [520, 480, 620][i], r = [-70, 80, 30][i];
      f.setAttribute('transform', `translate(${(dx * crack).toFixed(1)} ${(dy * crack * crack).toFixed(1)}) rotate(${(r * crack).toFixed(1)})`);
      f.style.opacity = 1 - api.prog(t, tC + 0.35, tC + 0.6, 'lin');
    });
    q(root, '.bb-crack').style.opacity = crack > 0.05 ? 0 : 1;
    q(root, '.bb-whole').style.opacity = crack > 0.01 ? 0 : 1; q(root, '.bb-shine').style.opacity = crack > 0.01 ? 0 : 0.6;
    frs.forEach(f => { if (crack <= 0.01) f.style.opacity = 0; });
    api.tw(q(root, '.bb-tag .a'), t, api.K.pop(tLb - 0.05, 0.45, { o: 0, s: 0.3, r: 16 }).concat([[tC + 0.1, {}], [tC + 0.5, { o: 0, y: 200 * k, r: 30 }, 'in']]));
    api.tw(q(root, '.bb-line .a'), t, api.K.slide(tLn - 0.05, 420 * k, 0.5));
    q(root, '.bb-flag').setAttribute('transform', `skewY(${(4 * Math.sin(t * 5)).toFixed(2)})`);
  };
});
