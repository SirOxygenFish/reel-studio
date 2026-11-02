/* @scene {"type":"squeeze_press","tags":["discount","pressure","price cut","learned behaviour"],"layout":"vise-center-price-tag","metaphor":"each discount is one more turn of a vise: the price tag gets squeezed smaller and smaller","assets":["bench vise with handle","price tag being squeezed"]} */
// {discount, discountAt, squeezeAt, label, labelAt, turns}
RM.def('squeeze_press', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tD = api.T(p.discountAt ?? api.start), tS = api.T(p.squeezeAt), tL = api.T(p.labelAt ?? p.squeezeAt), n = p.turns || 3;
  const VW = 860 * k, cx = L.cx, cy = L.y(0.56);
  root.innerHTML = api.at(cx, cy + 210 * k, `<svg width="${VW}" height="${300 * k}" viewBox="-430 -40 860 300" overflow="visible">
        <rect x="-420" y="60" width="840" height="60" rx="16" fill="var(--c2)"/><rect x="-60" y="120" width="120" height="120" rx="12" fill="var(--c2)"/></svg>`, { cls: 'sp-base', content: false }) +
    api.at(0, 0, `<div style="width:${110 * k}px;height:${300 * k}px;border-radius:${16 * k}px;background:var(--muted);box-shadow:var(--sh)"></div>`, { cls: 'sp-jl', content: false }) +
    api.at(0, 0, `<div style="width:${110 * k}px;height:${300 * k}px;border-radius:${16 * k}px;background:var(--muted);box-shadow:var(--sh)"></div>`, { cls: 'sp-jr', content: false }) +
    api.at(0, 0, `<svg width="${340 * k}" height="${60 * k}" viewBox="0 0 340 60" overflow="visible"><rect x="0" y="18" width="300" height="24" rx="12" fill="var(--c2)"/><circle cx="310" cy="30" r="28" fill="var(--bad)"/></svg>`, { cls: 'sp-hd', content: false }) +
    api.at(cx, cy, `<div class="sp-tag" style="position:relative;display:flex;align-items:center;justify-content:center;width:${520 * k}px;height:${260 * k}px;background:var(--paper);border-radius:${30 * k}px ${110 * k}px ${110 * k}px ${30 * k}px;border:${10 * k}px solid var(--c1);box-shadow:var(--sh)">
        <div class="big sp-pct" style="font-size:${120 * k}px;color:var(--bad)">−%</div></div>`, { cls: 'sp-t' }) +
    api.at(L.x(0.3), L.y(0.08), R.tag(p.discount || '', 70 * k, 'bad'), { cls: 'sp-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.95), R.tag(p.label || '', 70 * k, 'c1'), { cls: 'sp-t2', idle: 'wobble' });
  return t => {
    const sq = api.prog(t, tS - 0.6, tS + 0.4 * n, 'io'), w = 1 - 0.5 * sq;     // the tag width shrinks with the squeeze
    const gap = 520 * k * w / 2 + 55 * k;
    q(root, '.sp-jl').style.left = (cx - gap) + 'px'; q(root, '.sp-jr').style.left = (cx + gap) + 'px'; q(root, '.sp-jl').style.top = q(root, '.sp-jr').style.top = cy + 'px';
    q(root, '.sp-hd').style.left = (cx + gap + 230 * k) + 'px'; q(root, '.sp-hd').style.top = (cy - 60 * k) + 'px';
    q(root, '.sp-hd .m').style.transform = `rotate(${(-sq * n * 360).toFixed(1)}deg)`; q(root, '.sp-hd .m').style.transformOrigin = '0 50%';
    q(root, '.sp-tag').style.width = (520 * k * w).toFixed(1) + 'px'; q(root, '.sp-pct').style.fontSize = (120 * k * (0.6 + 0.4 * w)).toFixed(1) + 'px';
    api.tw(q(root, '.sp-t .a'), t, api.K.pop(tD - 0.05, 0.4, { o: 0, s: 0.3 }));
    q(root, '.sp-t .i').style.transform = `translateX(${(sq > 0 && sq < 1 ? 4 * Math.sin(t * 40) : 0).toFixed(1)}px)`;
    api.tw(q(root, '.sp-base .a'), t, api.K.rise(api.start, 0.4, 200 * k));
    api.tw(q(root, '.sp-t1 .a'), t, api.K.pop(tD, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.sp-t2 .a'), t, api.K.slam(tL - 0.05, 0.4));
  };
});
