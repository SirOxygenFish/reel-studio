/* @scene {"type":"hub_split","tags":["break it down","building blocks","skin","tendons","joints","muscles"],"layout":"central-block-explodes-into-small-blocks-four-corner-labels","metaphor":"one big block shatters into small building blocks in the middle, then streams of blocks travel to each of the four places he names","assets":["shattering block","block streams to four corners"]} */
// {down, downAt, blocks, blocksAt, items:[{t,at}]}
RM.def('hub_split', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tD = api.T(p.downAt), tB = api.T(p.blocksAt), I = p.items.map(c => ({ t: c.t, tt: api.T(c.at) })), cx = L.cx, cy = L.y(0.5), S = 56 * k, Nn = 16, B = 300 * k;
  const C = [[L.x(0.2), L.y(0.14)], [L.x(0.8), L.y(0.14)], [L.x(0.2), L.y(0.86)], [L.x(0.8), L.y(0.86)]];
  root.innerHTML = `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><rect class="hs-b" x="${-B / 2}" y="${-B / 2}" width="${B}" height="${B}" rx="${30 * k}" fill="var(--paper)"/>
      ${Array.from({ length: Nn }, (_, i) => `<rect class="hs-s" x="${-S / 2}" y="${-S / 2}" width="${S}" height="${S}" rx="${10 * k}" fill="${i % 2 ? 'var(--c1)' : 'var(--acc)'}"/>`).join('')}</svg>` +
    I.map((c, i) => api.at(C[i][0], C[i][1], R.tag(c.t, 76 * k, 'paper'), { cls: 'hs-c' })).join('') +
    api.at(cx, L.y(0.5) - 280 * k, R.tag(p.down || '', 74 * k, 'c1'), { cls: 'hs-t1', idle: 'sway' }) +
    api.at(cx, L.y(0.5) + 280 * k, R.tag(p.blocks || '', 74 * k, ''), { cls: 'hs-t2', idle: 'sway' });
  const b = q(root, '.hs-b'), ss = qa(root, '.hs-s'), cs = qa(root, '.hs-c');
  return t => {
    const bo = t < tD + 0.15; R.gx(b, { s: api.prog(t, api.start, api.start + 0.26, 'back') * (1 + 0.06 * Math.sin(t * 16) * api.prog(t, tD - 0.3, tD, 'lin')), o: bo ? 1 : 0, r: 3 * Math.sin(t * 2) }, cx, cy);
    ss.forEach((e, i) => { const a = (i / Nn) * 2 * Math.PI, sp = api.prog(t, tD + 0.1, tD + 0.45, 'back'), g = i % 4, c = I[g], j = i >> 2, go = api.prog(t, c.tt + j * 0.06, c.tt + j * 0.06 + 0.4, 'in'); const hx = cx + Math.cos(a) * 170 * k * (1 + 0.1 * Math.sin(t * 2 + i)), hy = cy + Math.sin(a) * 120 * k, x = hx + (C[g][0] - hx) * go, y = hy + (C[g][1] - hy) * go;
      R.gx(e, { s: go >= 1 ? 0.01 : 1, r: t * 60 + i * 30, o: sp > 0 && go < 1 ? 1 : 0 }, x, y); });
    cs.forEach((e, i) => api.tw(q(e, '.a'), t, api.K.pop(I[i].tt - 0.03, 0.26, { o: 0, s: 0.3 })));
    api.tw(q(root, '.hs-t1 .a'), t, api.K.pop(tD - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }).concat([[I[0].tt - 0.14, {}], [I[0].tt - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.hs-t2 .a'), t, api.K.pop(tB - 0.04, 0.26, { o: 0, s: 0.3, r: 4 }).concat([[I[2].tt - 0.14, {}], [I[2].tt - 0.03, { o: 0, s: 0.6 }, 'in']]));
  };
});
