/* @scene {"type":"effort_lanes","tags":["same effort","progress","going in circles","forward"],"layout":"two-horizontal-lanes","metaphor":"two people sweat the same; the one in the top lane walks forward to a flag, the one below runs inside a hamster wheel","assets":["walking figure","hamster wheel","sweat drops","progress trail"]} */
// {sameAt, same, fwdAt, fwd, loopAt, loop}
RM.def('effort_lanes', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.sameAt ?? api.start), tF = api.T(p.fwdAt), tL = api.T(p.loopAt);
  const y1 = L.y(0.3), y2 = L.y(0.72), FS = 250 * k;
  const runner = (c) => `<svg width="${FS}" height="${FS * 1.4}" viewBox="-50 -120 100 140" overflow="visible">
      <circle cx="0" cy="-96" r="18" fill="${c}"/><path class="el-body" d="M0 -78 L0 -30" stroke="${c}" stroke-width="16" stroke-linecap="round"/>
      <path class="el-a1" d="M0 -66 L-22 -46" stroke="${c}" stroke-width="12" stroke-linecap="round"/><path class="el-a2" d="M0 -66 L22 -46" stroke="${c}" stroke-width="12" stroke-linecap="round"/>
      <path class="el-l1" d="M0 -30 L-14 0" stroke="${c}" stroke-width="14" stroke-linecap="round"/><path class="el-l2" d="M0 -30 L14 0" stroke="${c}" stroke-width="14" stroke-linecap="round"/>
      <path class="el-sw" d="M24 -112 q6 10 0 14 q-6 -4 0 -14 Z M34 -96 q5 8 0 11 q-5 -3 0 -11 Z" fill="var(--c1l)"/></svg>`;
  const wheel = `<svg width="${470 * k}" height="${470 * k}" viewBox="-110 -110 220 220" overflow="visible"><path d="M-60 100 L0 0 L60 100" stroke="var(--c2)" stroke-width="10" fill="none"/>
      <g class="el-wh"><circle r="96" fill="none" stroke="var(--c2)" stroke-width="10"/>${Array.from({ length: 16 }, (_, i) => { const a = i / 16 * 6.283; return `<path d="M${Math.cos(a) * 86} ${Math.sin(a) * 86} L${Math.cos(a) * 96} ${Math.sin(a) * 96}" stroke="var(--c2)" stroke-width="6"/>`; }).join('')}
      <path d="M0 0 L0 -96 M0 0 L83 48 M0 0 L-83 48" stroke="var(--c1l)" stroke-width="5"/></g></svg>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <path d="M${L.x0} ${y1 + FS * 0.6} H${L.x1}" stroke="var(--c1l)" stroke-width="${10 * k}" stroke-dasharray="${30 * k} ${18 * k}"/>
      <path class="el-trail" d="M${L.x(0.08)} ${y1 + FS * 0.6} H${L.x(0.8)}" stroke="var(--acc)" stroke-width="${16 * k}" stroke-linecap="round"/>
      <path d="M${L.x0} ${y2 + 235 * k} H${L.x1}" stroke="var(--c1l)" stroke-width="${10 * k}"/></svg>` +
    api.at(L.x(0.88), y1, `<svg width="${180 * k}" height="${235 * k}" viewBox="0 0 130 170"><path d="M14 165 V10" stroke="var(--c2)" stroke-width="12" stroke-linecap="round"/><path class="el-fl" d="M20 14 Q70 -4 124 22 Q86 42 124 66 Q70 48 20 66 Z" fill="var(--acc)"/></svg>`, { cls: 'el-flag' }) +
    api.at(L.x(0.5), y2, wheel, { cls: 'el-wheel' }) +
    api.at(L.x(0.1), y1, runner('var(--acc)'), { cls: 'el-r1' }) + api.at(L.x(0.5), y2 + 60 * k, runner('var(--bad)'), { cls: 'el-r2' }) +
    api.at(L.cx, L.y(0.02), R.tag(p.same || '', 64 * k, 'c1'), { cls: 'el-t0', idle: 'sway' }) +
    api.at(L.x(0.62), L.y(0.44), R.tag(p.fwd || '', 62 * k, ''), { cls: 'el-t1', idle: 'sway' }) +
    api.at(L.x(0.2), L.y(0.97), R.tag(p.loop || '', 62 * k, 'bad'), { cls: 'el-t2', idle: 'sway' });
  const r1 = q(root, '.el-r1');
  const legs = (g, ph) => { const s = Math.sin(ph); q(g, '.el-l1').setAttribute('d', `M0 -30 L${(-16 * s).toFixed(1)} 0`); q(g, '.el-l2').setAttribute('d', `M0 -30 L${(16 * s).toFixed(1)} 0`);
    q(g, '.el-a1').setAttribute('d', `M0 -66 L${(18 * s).toFixed(1)} -46`); q(g, '.el-a2').setAttribute('d', `M0 -66 L${(-18 * s).toFixed(1)} -46`); };
  return t => {
    const go = api.prog(t, tF - 0.2, api.end, 'lin');
    r1.style.left = (L.x(0.1) + (L.x(0.76) - L.x(0.1)) * go) + 'px';
    R.draw(q(root, '.el-trail'), go * 0.92);
    legs(r1, t * 11); legs(q(root, '.el-r2'), t * 15);
    q(root, '.el-wh').setAttribute('transform', `rotate(${(-t * 260).toFixed(1)})`);
    qa(root, '.el-sw').forEach((s, i) => s.style.opacity = t > tS ? 0.5 + 0.5 * Math.sin(t * 8 + i) : 0);
    api.tw(q(r1, '.a'), t, api.K.pop(api.start, 0.35, { o: 0, s: 0.3 }));
    api.tw(q(root, '.el-r2 .a'), t, api.K.pop(api.start + 0.1, 0.35, { o: 0, s: 0.3 }));
    api.tw(q(root, '.el-wheel .a'), t, api.K.pop(api.start + 0.05, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.el-flag .a'), t, api.K.drop(api.start + 0.2, 0.4, -200 * k));
    q(root, '.el-fl').setAttribute('transform', `skewY(${(5 * Math.sin(t * 5)).toFixed(2)})`);
    api.tw(q(root, '.el-t0 .a'), t, api.K.pop(tS - 0.05, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.el-t1 .a'), t, api.K.pop(tF - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
    api.tw(q(root, '.el-t2 .a'), t, api.K.pop(tL - 0.05, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
