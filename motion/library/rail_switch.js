/* @scene {"type":"rail_switch","tags":["same situation","change","decision","loop","habit"],"layout":"top-down-track-loop-branch","metaphor":"a train circles the same loop of track; thinking alone cannot move the switch, a decision pulls the lever and it leaves on a new line","assets":["train","loop track with branch","switch lever","brain"]} */
// {differentAt, different, headAt, head, decideAt, decide}
RM.def('rail_switch', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tDf = api.T(p.differentAt), tH = api.T(p.headAt), tD = api.T(p.decideAt), tX = tD + 0.3;
  const cx = L.x(0.38), cy = L.y(0.52), r = 330 * k, w = 3.4;                 // loop centre, radius, angular speed
  const bx1 = L.x(0.97), by1 = L.y(0.1);
  const ties = Array.from({ length: 36 }, (_, i) => { const a = i / 36 * 6.283; return `<path d="M${cx + Math.cos(a) * (r - 34 * k)} ${cy + Math.sin(a) * (r - 34 * k)} L${cx + Math.cos(a) * (r + 34 * k)} ${cy + Math.sin(a) * (r + 34 * k)}" stroke="var(--c1)" stroke-width="${14 * k}"/>`; }).join('');
  const branch = `M${cx + r} ${cy} C ${cx + r} ${cy - r * 0.8} ${bx1 - 200 * k} ${by1 + 60 * k} ${bx1} ${by1}`;
  root.innerHTML = `<svg width="${L.W || 1080}" height="${1920}" style="position:absolute;left:0;top:0;overflow:visible">
      ${ties}<circle cx="${cx}" cy="${cy}" r="${r - 20 * k}" fill="none" stroke="var(--c1l)" stroke-width="${10 * k}"/><circle cx="${cx}" cy="${cy}" r="${r + 20 * k}" fill="none" stroke="var(--c1l)" stroke-width="${10 * k}"/>
      <path class="rs-br" d="${branch}" fill="none" stroke="var(--acc)" stroke-width="${46 * k}" stroke-linecap="round" opacity=".9"/>
      <path class="rs-br2" d="${branch}" fill="none" stroke="var(--paper)" stroke-width="${10 * k}" stroke-dasharray="${24 * k} ${20 * k}"/></svg>` +
    api.at(0, 0, `<div style="width:${190 * k}px;height:${108 * k}px;border-radius:${30 * k}px;background:var(--bad);box-shadow:var(--sh);position:relative">
        <div style="position:absolute;right:${12 * k}px;top:${16 * k}px;width:${44 * k}px;height:${54 * k}px;border-radius:${10 * k}px;background:var(--paper)"></div></div>`, { cls: 'rs-tr' }) +
    api.at(L.x(0.84), L.y(0.74), `<svg width="${200 * k}" height="${325 * k}" viewBox="-80 -200 160 260" overflow="visible"><rect x="-70" y="20" width="140" height="40" rx="14" fill="var(--c2)"/>
        <g class="rs-lev"><path d="M0 30 L0 -150" stroke="var(--ink)" stroke-width="16" stroke-linecap="round"/><circle cx="0" cy="-160" r="30" fill="var(--bad)"/></g></svg>`, { cls: 'rs-l' }) +
    api.at(L.x(0.62), L.y(0.8), api.icon('ph:brain', 190 * k, 'var(--c1l)'), { cls: 'rs-brain', idle: 'float' }) +
    api.at(L.x(0.95), L.y(0.68), api.icon('ph:hand-grabbing', 170 * k, 'var(--c1l)'), { cls: 'rs-hand' }) +
    api.at(L.x(0.3), L.y(0.08), R.tag(p.different || '', 64 * k, 'c1'), { cls: 'rs-t1', idle: 'sway' }) +
    api.at(L.x(0.4), L.y(0.97), R.tag(p.head || '', 58 * k, 'bad'), { cls: 'rs-t2', idle: 'sway' }) +
    api.at(L.x(0.66), L.y(0.36), R.tag(p.decide || '', 86 * k, ''), { cls: 'rs-t3', idle: 'wobble' });
  const tr = q(root, '.rs-tr'), br = q(root, '.rs-br'), blen = br.getTotalLength();
  return t => {
    R.draw(br, api.prog(t, tDf - 0.1, tDf + 0.6, 'io')); R.draw(q(root, '.rs-br2'), api.prog(t, tDf - 0.1, tDf + 0.6, 'io'));
    let x, y, ang;
    if (t < tX) { const a = w * (t - tX); x = cx + Math.cos(a) * r; y = cy + Math.sin(a) * r; ang = a * 57.3 + 90; }
    else { const d = Math.min(blen, (t - tX) * 900 * k * (1 + (t - tX))), pt = br.getPointAtLength(d), p2 = br.getPointAtLength(Math.min(blen, d + 2));
      x = pt.x; y = pt.y; ang = Math.atan2(p2.y - pt.y, p2.x - pt.x) * 57.3; }
    tr.style.left = x.toFixed(1) + 'px'; tr.style.top = y.toFixed(1) + 'px';
    q(tr, '.m').style.transform = `rotate(${ang.toFixed(1)}deg)`;
    api.tw(q(tr, '.a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0.3 }));
    const shake = t > tH && t < tH + 0.8 ? 6 * Math.sin((t - tH) * 40) : 0, pull = api.prog(t, tD, tD + 0.3, 'back');
    q(root, '.rs-lev').setAttribute('transform', `rotate(${(-28 + 56 * pull + shake).toFixed(1)})`);
    api.tw(q(root, '.rs-l .a'), t, api.K.rise(api.start + 0.2, 0.4, 200 * k));
    api.tw(q(root, '.rs-brain .a'), t, api.K.pop(tH - 0.05, 0.4, { o: 0, s: 0.3 }).concat([[tD - 0.2, {}], [tD + 0.1, { o: 0.35 }, 'lin']]));
    api.tw(q(root, '.rs-hand .a'), t, [[tD - 0.25, { o: 0, x: 140 * k }], [tD, { o: 1, x: 0 }, 'out'], [tD + 0.3, { x: -40 * k, r: -14 }, 'back']]);
    api.tw(q(root, '.rs-t1 .a'), t, api.K.pop(tDf - 0.05, 0.4, { o: 0, s: 0.3, r: -10 }));
    api.tw(q(root, '.rs-t2 .a'), t, api.K.pop(tH - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
    api.tw(q(root, '.rs-t3 .a'), t, api.K.slam(tD - 0.05, 0.4));
  };
});
