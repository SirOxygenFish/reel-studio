/* @scene {"type":"traffic_food","tags":["more real food","less sugar","junk"],"layout":"tall-traffic-light-center-three-lamps","metaphor":"a traffic light: the green lamp shows real food, then the red lamp shows sugar and junk","assets":["traffic light","food in the lamps"]} */
// {more, moreAt, less, lessAt, junk, junkAt}
RM.def('traffic_food', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tM = api.T(p.moreAt), tL = api.T(p.lessAt), tJ = api.T(p.junkAt), cx = L.cx, BW = 330 * k, r = 118 * k, ys = [L.y(0.26), L.y(0.5), L.y(0.74)], C = ['var(--bad)', 'var(--acc)', 'var(--good)'];
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <rect class="tf-h" x="${cx - BW / 2}" y="${L.y(0.13)}" width="${BW}" height="${L.y(0.74) - L.y(0.26) + 2 * r + 60 * k}" rx="${60 * k}" fill="var(--bgDeep)" stroke="var(--c1l)" stroke-width="${10 * k}"/>
      ${ys.map((y, i) => `<circle class="tf-g" cx="${cx}" cy="${y}" r="${r * 1.55}" fill="${C[i]}" opacity="0"/><circle class="tf-l" cx="${cx}" cy="${y}" r="${r}" fill="${C[i]}"/>`).join('')}</svg>` +
    api.at(cx, ys[2], api.icon('ph-fill:carrot', 150 * k, 'var(--ink)'), { cls: 'tf-i' }) + api.at(cx, ys[0], api.icon('ph-fill:cube', 140 * k, 'var(--ink)'), { cls: 'tf-i' }) +
    api.at(cx, L.y(0.04), R.tag(p.more || '', 78 * k, 'c1'), { cls: 'tf-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.04), R.tag(p.less || '', 84 * k, ''), { cls: 'tf-t2', idle: 'sway' }) +
    api.at(cx, L.y(0.95), R.tag(p.junk || '', 84 * k, 'bad'), { cls: 'tf-t3', idle: 'wobble' });
  const gs = qa(root, '.tf-g'), ls = qa(root, '.tf-l'), is = qa(root, '.tf-i'), h = q(root, '.tf-h');
  return t => {
    const on = [t >= tL ? 1 : 0, t < tM ? 1 : 0, t >= tM && t < tL ? 1 : 0];
    on.forEach((v, i) => { const pul = 0.3 + 0.12 * Math.sin(t * 8); gs[i].setAttribute('opacity', v ? pul.toFixed(3) : 0); ls[i].style.opacity = v ? 1 : 0.18; });
    api.tw(q(is[0], '.a'), t, api.K.spring(tM, 0.34).concat([[tL - 0.1, {}], [tL, { o: 0.15 }, 'lin']])); api.tw(q(is[1], '.a'), t, api.K.spring(tL, 0.34));
    h.style.transform = '';
    api.tw(q(root, '.tf-t1 .a'), t, api.K.pop(tM - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }).concat([[tL - 0.14, {}], [tL - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.tf-t2 .a'), t, api.K.slam(tL - 0.03, 0.3));
    api.tw(q(root, '.tf-t3 .a'), t, api.K.slam(tJ - 0.03, 0.3));
  };
});
