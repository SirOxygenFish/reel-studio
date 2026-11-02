/* @scene {"type":"slot_blank","tags":["magic pill","no pill","luck"],"layout":"slot-machine-three-windows-lever-right","metaphor":"a slot machine spins capsules in three windows, the lever drops and all three reels stop on blanks","assets":["slot machine","spinning capsule reels","lever"]} */
// {magic, magicAt, no, noAt}
RM.def('slot_blank', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tM = api.T(p.magicAt), tN = api.T(p.noAt), cx = L.x(0.46), cy = L.y(0.5), MW = 760 * k, MH = 470 * k, WW = 196 * k, WH = 300 * k, id = 'sl' + Math.round(api.start * 100);
  const wx = i => cx + (i - 1) * (WW + 28 * k), cap = `<g><rect x="${-34 * k}" y="${-70 * k}" width="${68 * k}" height="${140 * k}" rx="${34 * k}" fill="var(--c1)"/><path d="M${-34 * k} 0 V${36 * k} A${34 * k} ${34 * k} 0 0 0 ${34 * k} ${36 * k} V0 Z" fill="var(--acc)"/></g>`;
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <defs>${[0, 1, 2].map(i => `<clipPath id="${id}${i}"><rect x="${wx(i) - WW / 2}" y="${cy - WH / 2}" width="${WW}" height="${WH}" rx="${20 * k}"/></clipPath>`).join('')}</defs>
      <rect x="${cx - MW / 2}" y="${cy - MH / 2}" width="${MW}" height="${MH}" rx="${50 * k}" fill="var(--c2)" stroke="var(--c1l)" stroke-width="${10 * k}"/>
      ${[0, 1, 2].map(i => `<rect x="${wx(i) - WW / 2}" y="${cy - WH / 2}" width="${WW}" height="${WH}" rx="${20 * k}" fill="var(--paper)"/><g clip-path="url(#${id}${i})"><g class="sb2-r">${[-1, 0, 1, 2].map(j => `<g transform="translate(${wx(i)} ${cy + j * 240 * k})">${cap}</g>`).join('')}</g></g><rect class="sb2-d" x="${wx(i) - 54 * k}" y="${cy - 9 * k}" width="${108 * k}" height="${18 * k}" rx="${9 * k}" fill="var(--c2)"/>`).join('')}
      <line class="sb2-a" x1="${cx + MW / 2 + 16 * k}" y1="${cy}" stroke="var(--c1l)" stroke-width="${22 * k}" stroke-linecap="round"/><circle class="sb2-k" r="${44 * k}" fill="var(--acc)"/></svg>` +
    api.at(L.cx, L.y(0.08), R.tag(p.magic || '', 78 * k, 'c1'), { cls: 'sb2-t1', idle: 'sway' }) +
    api.at(L.cx, L.y(0.9), R.tag(p.no || '', 160 * k, 'bad'), { cls: 'sb2-t2', idle: 'wobble' });
  const rs = qa(root, '.sb2-r'), ds = qa(root, '.sb2-d'), a = q(root, '.sb2-a'), kn = q(root, '.sb2-k');
  return t => {
    const stop = i => tN - 0.3 + i * 0.15;
    rs.forEach((e, i) => { const on = t < stop(i), y = ((t - api.start) * 1500 * k) % (240 * k); e.setAttribute('transform', `translate(0 ${y.toFixed(1)})`); e.style.visibility = on ? 'visible' : 'hidden'; ds[i].style.visibility = on ? 'hidden' : 'visible'; });
    const pull = api.prog(t, tM - 0.12, tM + 0.08, 'in') - api.prog(t, tM + 0.25, tM + 0.5, 'out'), ang = (-58 + 116 * pull) * Math.PI / 180, x = cx + MW / 2 + 16 * k + Math.cos(ang) * 130 * k, y = cy + Math.sin(ang) * 190 * k;
    a.setAttribute('x2', x.toFixed(1)); a.setAttribute('y2', y.toFixed(1)); kn.setAttribute('cx', x.toFixed(1)); kn.setAttribute('cy', y.toFixed(1));
    api.tw(q(root, '.sb2-t1 .a'), t, api.K.pop(tM - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
    api.tw(q(root, '.sb2-t2 .a'), t, api.K.slam(tN - 0.03, 0.3));
  };
});
