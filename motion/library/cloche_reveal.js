/* @scene {"type":"cloche_reveal","tags":["real reason","hidden","reveal","listen"],"layout":"serving-dome-center","metaphor":"a silver serving dome lifts away and reveals the glowing real reason underneath","assets":["serving dome (cloche)","plate","glowing gem"]} */
// {liftAt, reason, reasonAt}
RM.def('cloche_reveal', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tL = api.T(p.liftAt), tR = api.T(p.reasonAt ?? p.liftAt), cx = L.cx, cy = L.y(0.6);
  root.innerHTML = api.at(cx, cy + 150 * k, `<svg width="${760 * k}" height="${120 * k}" viewBox="-380 -60 760 120"><ellipse rx="370" ry="50" fill="var(--paper)" stroke="var(--c2)" stroke-width="8"/><ellipse rx="280" ry="30" fill="none" stroke="var(--c1x)" stroke-width="6"/></svg>`, { cls: 'cr-pl', content: false }) +
    api.at(cx, cy + 40 * k, `<svg width="${300 * k}" height="${260 * k}" viewBox="-150 -130 300 260" overflow="visible"><path d="M0 -110 L90 -30 L0 110 L-90 -30 Z" fill="var(--acc)"/><path d="M0 -110 L40 -30 L0 110 L-40 -30 Z" fill="var(--acc-soft)" opacity=".6"/><path d="M-90 -30 H90" stroke="var(--paper)" stroke-width="5"/></svg>`, { cls: 'cr-gem', idle: 'float' }) +
    `<div class="cr-glow" style="position:absolute;left:${cx - 330 * k}px;top:${cy - 290 * k}px;width:${660 * k}px;height:${660 * k}px;border-radius:50%;background:radial-gradient(closest-side,var(--c1x),transparent);opacity:0"></div>` +
    api.at(cx, cy - 20 * k, `<svg width="${640 * k}" height="${420 * k}" viewBox="-320 -260 640 420" overflow="visible"><path d="M-300 140 Q-300 -200 0 -200 Q300 -200 300 140 Z" fill="var(--muted)"/>
        <path d="M-220 60 Q-210 -120 -40 -150" stroke="var(--paper)" stroke-width="18" fill="none" opacity=".5" stroke-linecap="round"/><rect x="-30" y="-250" width="60" height="50" rx="20" fill="var(--c2)"/><rect x="-320" y="130" width="640" height="30" rx="12" fill="var(--c2)"/></svg>`, { cls: 'cr-d' }) +
    api.at(cx, L.y(0.12), R.tag(p.reason || '', 74 * k, 'c1'), { cls: 'cr-t', idle: 'wobble' });
  return t => {
    api.tw(q(root, '.cr-pl .a'), t, api.K.rise(api.start, 0.4, 200 * k));
    api.tw(q(root, '.cr-d .a'), t, api.K.drop(api.start, 0.5, -500 * k).concat([[tL - 0.1, {}], [tL + 0.2, { y: 30 * k }, 'out'], [tL + 0.7, { y: -900 * k, r: -18, o: 0 }, 'in']]));
    q(root, '.cr-d .i').style.transform = `rotate(${(t > tL - 0.5 && t < tL ? 3 * Math.sin(t * 40) : 0).toFixed(1)}deg)`;
    api.tw(q(root, '.cr-gem .a'), t, [[tL, { o: 0, s: 0.6 }], [tL + 0.3, { o: 1, s: 1 }, 'back']]);
    q(root, '.cr-glow').style.opacity = 0.9 * api.prog(t, tL + 0.1, tL + 0.5, 'out') * (0.8 + 0.2 * Math.sin(t * 4));
    api.tw(q(root, '.cr-t .a'), t, api.K.slam(tR - 0.05, 0.4));
  };
});
