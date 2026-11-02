/* @scene {"type":"swipe_card","tags":["if it hurts","doctor first","not a blogger"],"layout":"card-stack-center-top-card-swiped-away","metaphor":"a stack of cards: the vertical-video card with a play button is flicked off the screen and the stethoscope card underneath stamps forward","assets":["card stack","play-button video card","stethoscope card"]} */
// {pain, painAt, first, firstAt, blog, blogAt, doc, docAt}
RM.def('swipe_card', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tP = api.T(p.painAt), tF = api.T(p.firstAt), tB = api.T(p.blogAt), tD = api.T(p.docAt);
  const cx = L.cx, cy = L.y(0.5), CW = 520 * k, CH = 660 * k;
  const card = (bg, inner, cls) => `<div class="${cls}" style="position:absolute;left:${cx - CW / 2}px;top:${cy - CH / 2}px;width:${CW}px;height:${CH}px;border-radius:${40 * k}px;background:${bg};box-shadow:var(--sh);display:flex;align-items:center;justify-content:center;flex-direction:column;gap:${30 * k}px">${inner}</div>`;
  root.innerHTML = card('var(--paper)', `<div style="line-height:0">${api.icon('ph-fill:stethoscope', 300 * k, 'var(--c2)')}</div>`, 'sc-d') +
    card('var(--c2)', `<svg width="${260 * k}" height="${260 * k}" viewBox="-50 -50 100 100"><circle r="44" fill="none" stroke="var(--c1l)" stroke-width="7"/><path d="M-14 -22 L24 0 L-14 22 Z" fill="var(--c1l)"/></svg>
      <div style="display:flex;gap:${26 * k}px"><div style="line-height:0">${api.icon('ph-fill:heart', 76 * k, 'var(--acc)')}</div><div style="line-height:0">${api.icon('ph-fill:chat-circle', 76 * k, 'var(--c1l)')}</div><div style="line-height:0">${api.icon('ph-fill:share-fat', 76 * k, 'var(--c1l)')}</div></div>`, 'sc-b') +
    api.at(cx, L.y(0.05), R.tag(p.pain || '', 92 * k, 'bad'), { cls: 'sc-t1', idle: 'wobble' }) +
    api.at(cx, L.y(0.05), R.tag(p.first || '', 80 * k, 'c1'), { cls: 'sc-t2', idle: 'sway' }) +
    api.at(cx, L.y(0.95), R.tag(p.blog || '', 84 * k, ''), { cls: 'sc-t3', idle: 'sway' }) +
    api.at(cx, L.y(0.95), R.tag(p.doc || '', 108 * k, 'c1'), { cls: 'sc-t4', idle: 'wobble' });
  const b = q(root, '.sc-b'), d = q(root, '.sc-d');
  return t => {
    const inn = api.prog(t, api.start, api.start + 0.26, 'back'), go = api.prog(t, tB + 0.08, tB + 0.42, 'in'), wig = api.prog(t, tB - 0.05, tB + 0.08, 'lin') * (1 - go);
    b.style.transform = `translate(${(-go * 1300 * k + 26 * k * Math.sin(t * 34) * wig).toFixed(1)}px,${((1 - inn) * 760 * k).toFixed(1)}px) rotate(${(-3 - go * 26).toFixed(2)}deg)`; b.style.visibility = go >= 1 ? 'hidden' : 'visible';
    const hit = api.prog(t, tD - 0.05, tD + 0.18, 'back'), sc = 0.92 + 0.08 * api.prog(t, tB + 0.2, tB + 0.5, 'out') + 0.1 * Math.exp(-Math.max(0, t - tD) * 7) * (t > tD ? 1 : 0);
    d.style.transform = `translateY(${((1 - inn) * 760 * k).toFixed(1)}px) rotate(${(3 * (1 - hit)).toFixed(2)}deg) scale(${sc.toFixed(3)})`;
    api.tw(q(root, '.sc-t1 .a'), t, api.K.pop(tP - 0.03, 0.24, { o: 0, s: 0.3 }).concat([[tF - 0.1, {}], [tF - 0.02, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.sc-t2 .a'), t, api.K.slam(tF - 0.02, 0.28));
    api.tw(q(root, '.sc-t3 .a'), t, api.K.pop(tB - 0.1, 0.24, { o: 0, s: 0.3, r: -4 }).concat([[tD - 0.12, {}], [tD - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.sc-t4 .a'), t, api.K.slam(tD - 0.03, 0.3));
  };
});
