/* @scene {"type":"glue_tube","tags":["glue","holds your body together","skin","joints","bones","tendons"],"layout":"tube-top-four-tiles-glued-in-a-cross","metaphor":"a glue tube squeezes a bead down a line and four tiles snap together along it as he names them","assets":["glue tube","glue bead","four tiles"]} */
// {glue, glueAt, items:[{t,at}]}
RM.def('glue_tube', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tG = api.T(p.glueAt), I = p.items.map(x => ({ t: x.t, at: api.T(x.at) })), cx = L.cx, cy = L.y(0.6), S = 300 * k, G = 18 * k;
  const pos = [[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([a, b]) => [cx + a * (S / 2 + G), cy + b * (S / 2 + G)]), COL = ['var(--c1)', 'var(--acc)', 'var(--c1x)', 'var(--c2)'], INK = ['var(--ink)', 'var(--ink)', 'var(--ink)', '#fff'];
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">
      <g class="gt-t" transform="translate(${cx} ${L.y(0.16)})"><path class="gt-b" d="M${-120 * k} ${-110 * k} H${120 * k} L${90 * k} ${60 * k} H${-90 * k} Z" fill="var(--paper)"/><rect x="${-40 * k}" y="${60 * k}" width="${80 * k}" height="${50 * k}" fill="var(--c1l)"/><path d="M${-22 * k} ${110 * k} H${22 * k} L0 ${160 * k} Z" fill="var(--c1l)"/></g>
      <path class="gt-g" d="M${cx} ${L.y(0.16) + 150 * k} V${cy + S + 2 * G} M${cx - S - 2 * G} ${cy} H${cx + S + 2 * G}" fill="none" stroke="var(--paper)" stroke-width="${26 * k}" stroke-linecap="round"/></svg>` +
    I.map((x, i) => api.at(pos[i][0], pos[i][1], `<div style="width:${S}px;height:${S}px;border-radius:${26 * k}px;background:${COL[i]};color:${INK[i]};display:flex;align-items:center;justify-content:center;font-family:var(--f-display);font-weight:800;font-size:${72 * k}px">${x.t}</div>`, { cls: 'gt-i' })).join('') +
    api.at(cx, L.y(0.04), R.tag(p.glue || '', 76 * k, 'c1'), { cls: 'gt-t1', idle: 'sway' });
  const g = q(root, '.gt-g'), b = q(root, '.gt-b'), is = qa(root, '.gt-i');
  return t => {
    R.draw(g, api.prog(t, tG, I[3].at + 0.2, 'lin'));
    b.setAttribute('transform', `scale(${(1 - 0.08 * Math.abs(Math.sin(t * 5)) * (t > tG ? 1 : 0)).toFixed(3)} 1)`);
    is.forEach((e, i) => { const sx = i % 2 ? 1 : -1, sy = i < 2 ? -1 : 1; api.tw(q(e, '.a'), t, [[I[i].at - 0.04, { o: 0, x: sx * 420 * k, y: sy * 320 * k, s: 0.8 }], [I[i].at + 0.26, { o: 1, x: 0, y: 0, s: 1 }, 'back']]); });
    api.tw(q(root, '.gt-t1 .a'), t, api.K.pop(tG - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
  };
});
