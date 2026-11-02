/* @scene {"type":"pill_fizzle","tags":["no magic pill","no single fix","several things at once"],"layout":"big-tilted-capsule-center-wand-then-orbit","metaphor":"a wand sparkles over a giant capsule, the magic fizzles out and falls, the capsule splits and a few small things orbit at once","assets":["giant capsule","limp magic wand","falling sparkles","orbiting icon discs"]} */
// {noAt, pill, pillAt, few, fewAt, onceAt}
RM.def('pill_fizzle', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tN = api.T(p.noAt), tP = api.T(p.pillAt), tF = api.T(p.fewAt), tO = api.T(p.onceAt);
  const cx = L.cx, cy = L.y(0.5), W = 300 * k, r = 118 * k, ANG = -32;
  const half = (s, fill) => { const d = `M0 ${-r} H${s * (W - r)} A${r} ${r} 0 0 ${s > 0 ? 1 : 0} ${s * (W - r)} ${r} H0 Z`;
    return `<path d="${d}" fill="${fill}"/><path class="pf-dim" d="${d}" fill="var(--bgDeep)" opacity="0"/>
      <rect x="${s > 0 ? 30 * k : -(W - 60 * k)}" y="${-r * 0.62}" width="${W - 90 * k}" height="${22 * k}" rx="${11 * k}" fill="#fff" opacity=".4"/>`; };
  const star = s => `M0 ${-s} Q0 0 ${s} 0 Q0 0 0 ${s} Q0 0 ${-s} 0 Q0 0 0 ${-s} Z`;
  const SP = [[-160, 400, 44], [-120, 330, 28], [-75, 390, 52], [-30, 420, 30], [20, 380, 40], [70, 340, 26], [120, 400, 46], [165, 410, 30], [-95, 240, 22], [50, 250, 20]]
    .map(([a, d, s]) => ({ x: cx + Math.cos(a * Math.PI / 180) * d * k, y: cy + Math.sin(a * Math.PI / 180) * d * k, s: s * k }));
  const RAD = 320 * k, DS = 200 * k;
  const disc = (ic, c) => `<div style="width:${DS}px;height:${DS}px;border-radius:50%;background:var(--paper);display:flex;align-items:center;justify-content:center;box-shadow:var(--sh)">${ic}</div>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <ellipse class="pf-glow" cx="${cx}" cy="${cy}" rx="${430 * k}" ry="${300 * k}" fill="var(--acc)" opacity=".16"/>
      <g class="pf-l">${half(-1, 'var(--acc)')}</g><g class="pf-r">${half(1, 'var(--paper)')}</g>
      ${SP.map(s => `<path class="pf-s" d="${star(s.s)}" fill="var(--acc2)"/>`).join('')}
      <g class="pf-w"><rect x="${-14 * k}" y="${-4 * k}" width="${28 * k}" height="${330 * k}" rx="${14 * k}" fill="var(--paper)"/><rect x="${-14 * k}" y="${-4 * k}" width="${28 * k}" height="${90 * k}" rx="${14 * k}" fill="var(--c2)"/>
        <path d="${star(70 * k)}" transform="translate(0 ${345 * k})" fill="var(--acc)"/></g></svg>` +
    api.at(0, 0, disc(api.icon('ph:carrot', 130 * k, 'var(--acc)')), { cls: 'pf-o' }) +
    api.at(0, 0, disc(api.icon('ph:drop', 130 * k, 'var(--c2)')), { cls: 'pf-o' }) +
    api.at(0, 0, disc(api.icon('ph:person-simple-walk', 130 * k, 'var(--acc)')), { cls: 'pf-o' }) +
    api.at(0, 0, disc(api.icon('ph:egg', 130 * k, 'var(--c2)')), { cls: 'pf-o' }) +
    api.at(cx, L.y(0.07), R.tag(p.pill || '', 92 * k, 'c1'), { cls: 'pf-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.95), R.tag(p.few || '', 78 * k, ''), { cls: 'pf-t2', idle: 'wobble' });
  const sp = qa(root, '.pf-s'), os = qa(root, '.pf-o');
  return t => {
    const inn = api.prog(t, api.start, api.start + 0.4, 'back'), sc = 0.3 + 0.7 * inn, spl = api.prog(t, tF - 0.1, tF + 0.45, 'out'), bob = 8 * k * Math.sin(t * 2.4);
    const dead = api.prog(t, tN, tP + 0.3, 'out');
    const pos = s => { const a = ANG * Math.PI / 180, d = s * 230 * k * spl; return [cx + Math.cos(a) * d, cy + Math.sin(a) * d + bob]; };
    [['.pf-l', -1], ['.pf-r', 1]].forEach(([c, s]) => { const [x, y] = pos(s);
      q(root, c).setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${(ANG + s * 22 * spl).toFixed(2)}) scale(${(sc * (1 - 0.3 * spl)).toFixed(4)})`); });
    qa(root, '.pf-dim').forEach(e => e.setAttribute('opacity', (0.4 * dead * (1 - spl)).toFixed(3)));
    q(root, '.pf-glow').setAttribute('opacity', (0.16 * (1 - dead) + 0.1 * spl).toFixed(3));
    sp.forEach((e, i) => { const s = SP[i], u = Math.max(0, t - tN - i * 0.03), tw = 0.75 + 0.25 * Math.sin(t * 6 + i * 2);
      R.gx(e, { y: 1500 * k * u * u, r: t * 40 + i * 30, s: Math.max(0.01, api.prog(t, api.start + i * 0.03, api.start + 0.3 + i * 0.03, 'back') * tw * (1 - 0.5 * Math.min(1, u))), o: Math.max(0, 1 - u * 1.4) }, s.x, s.y); });
    const droop = api.prog(t, tN, tN + 0.5, 'out'), wr = (1 - droop) * (42 + 7 * Math.sin(t * 7)) + droop * 8;
    R.gx(q(root, '.pf-w'), { r: wr, y: 420 * k * api.prog(t, tF - 0.3, tF + 0.2, 'in'), s: 1, o: 1 - api.prog(t, tF - 0.2, tF + 0.2, 'lin') }, cx + 430 * k, cy - 470 * k);
    os.forEach((e, i) => { const a = i * Math.PI / 2 - Math.PI / 4 + (t - tF) * 0.55; e.style.left = (cx + Math.cos(a) * RAD) + 'px'; e.style.top = (cy + Math.sin(a) * RAD * 0.95) + 'px';
      api.tw(q(e, '.a'), t, api.K.pop(tF + i * 0.11, 0.4, { o: 0, s: 0 }).concat([[tO, { s: 1 }], [tO + 0.14, { s: 1.14 }, 'out'], [tO + 0.34, { s: 1 }, 'io']])); });
    api.tw(q(root, '.pf-t1 .a'), t, api.K.slam(tP - 0.1, 0.4));
    api.tw(q(root, '.pf-t2 .a'), t, api.K.pop(tF, 0.4, { o: 0, s: 0.3, r: 5 }));
  };
});
