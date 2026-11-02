/* @scene {"type":"blister_empty","tags":["magic pill","no pill","empty"],"layout":"tilted-pack-center-pockets-burst-open","metaphor":"a shiny foil pack: every pocket bursts open one after another and each one is empty","assets":["foil blister pack","burst foil flaps"]} */
// {magic, magicAt, no, noAt}
RM.def('blister_empty', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tM = api.T(p.magicAt), tN = api.T(p.noAt), tO = tM + 0.34;
  const cx = L.cx, cy = L.y(0.46), PW = 620 * k, PH = 740 * k, C = 2, N = 3, r = 104 * k, gx = 240 * k, gy = 225 * k;
  const pts = []; for (let j = 0; j < N; j++) for (let i = 0; i < C; i++) pts.push([(i - 0.5) * gx, (j - 1) * gy]);
  const flap = a => `<path class="be-f" d="M0 0 L${-r * 0.8} ${-r * 0.5} L${-r * 0.3} ${-r * 0.95} L${r * 0.3} ${-r * 0.75} L${r * 0.85} ${-r * 0.3} Z" fill="var(--c1x)" transform="rotate(${a})"/>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><g class="be-p">
      <rect x="${-PW / 2}" y="${-PH / 2}" width="${PW}" height="${PH}" rx="${46 * k}" fill="var(--c2)" stroke="var(--c1l)" stroke-width="${10 * k}"/>
      <path d="M${-PW * 0.42} ${-PH * 0.44} L${PW * 0.1} ${PH * 0.44}" stroke="var(--c1l)" stroke-width="${44 * k}" opacity=".14"/>
      ${pts.map(([x, y]) => `<g transform="translate(${x} ${y})"><circle r="${r}" fill="var(--bgDeep)" stroke="var(--c1l)" stroke-width="${7 * k}"/>
        <g class="be-c"><circle r="${r * 0.98}" fill="var(--c1x)"/><path d="M${-r * 0.55} ${-r * 0.2} A${r * 0.6} ${r * 0.6} 0 0 1 ${r * 0.1} ${-r * 0.6}" stroke="#fff" stroke-width="${12 * k}" fill="none" stroke-linecap="round"/></g>
        <g class="be-b">${[0, 120, 240].map(flap).join('')}</g></g>`).join('')}</g></svg>` +
    api.at(cx, L.y(0.06), R.tag(p.magic || '', 78 * k, 'c1'), { cls: 'be-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.92), R.tag(p.no || '', 170 * k, 'bad'), { cls: 'be-t2', idle: 'wobble' });
  const cs = qa(root, '.be-c'), bs = qa(root, '.be-b'), pk = q(root, '.be-p');
  const order = [0, 3, 4, 1, 5, 2];
  return t => {
    const inn = api.prog(t, api.start, api.start + 0.3, 'back'), hit = Math.exp(-Math.max(0, t - tN) * 7) * (t > tN ? 1 : 0);
    R.gx(pk, { y: (1 - inn) * 640 * k, r: -6 + 2 * Math.sin(t * 2.4) + 7 * hit * Math.sin((t - tN) * 40), s: 1 + 0.05 * hit, o: 1 }, cx, cy);
    order.forEach((n, i) => { const a = tO + i * 0.075, u = api.prog(t, a, a + 0.16, 'out');
      cs[n].style.opacity = u > 0 ? 0 : 1;
      bs[n].style.opacity = u > 0 ? 1 - api.prog(t, a + 0.2, a + 0.5, 'lin') * 0.25 : 0;
      bs[n].setAttribute('transform', `scale(${(0.5 + 0.5 * u).toFixed(3)})`); });
    api.tw(q(root, '.be-t1 .a'), t, api.K.pop(tM - 0.04, 0.26, { o: 0, s: 0.3, r: -5 }));
    api.tw(q(root, '.be-t2 .a'), t, api.K.slam(tN - 0.03, 0.3));
  };
});
