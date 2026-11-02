/* @scene {"type":"envelope_stream","tags":["attempts","pitches","investors","numbers game","100 tries"],"layout":"sender-left-stream-right-returns","metaphor":"five envelopes go out and all bounce back with a cross; then a stream of a hundred goes out and one or two come back with a tick","assets":["envelopes","cross and tick stamps","counter"]} */
// {hundred, hundredAt, fiveAt, five, noOneAt, noOne, manyAt}
RM.def('envelope_stream', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tH = api.T(p.hundredAt ?? api.start), t5 = api.T(p.fiveAt), tN = api.T(p.noOneAt), tM = api.T(p.manyAt ?? p.noOneAt);
  const env = (c) => `<svg width="${110 * k}" height="${76 * k}" viewBox="0 0 110 76"><rect x="2" y="2" width="106" height="72" rx="8" fill="var(--paper)" stroke="${c}" stroke-width="5"/><path d="M4 6 L55 44 L106 6" fill="none" stroke="${c}" stroke-width="5"/></svg>`;
  const N5 = 5, NM = 26, sx = L.x(0.12), sy = L.y(0.55);
  root.innerHTML = api.at(sx, sy, `<div class="badge c2" style="font-size:${180 * k}px">${api.icon('ph-fill:paper-plane-tilt', 100 * k)}</div>`, { cls: 'es-s', idle: 'bob wobble', amp: 1.6 }) +
    Array.from({ length: N5 }, (_, i) => api.at(0, 0, `<div style="position:relative">${env('var(--c2)')}<div class="es-x badge bad" style="position:absolute;right:${-20 * k}px;top:${-20 * k}px;font-size:${50 * k}px">${api.icon('ph-bold:x', 30 * k)}</div></div>`, { cls: 'es-5', content: false })).join('') +
    Array.from({ length: NM }, (_, i) => api.at(0, 0, `<div style="position:relative">${env(i === 9 || i === 20 ? 'var(--good)' : 'var(--c1)')}${i === 9 || i === 20 ? `<div class="badge good" style="position:absolute;right:${-20 * k}px;top:${-20 * k}px;font-size:${56 * k}px">${api.icon('ph-bold:check', 34 * k)}</div>` : ''}</div>`, { cls: 'es-m' + (i === 9 || i === 20 ? ' es-hit' : ''), content: false })).join('') +
    api.at(L.x(0.32), L.y(0.08), `<div class="big" style="font-size:${150 * k}px;color:var(--c2)">${R.esc(p.hundred || '')}</div>`, { cls: 'es-h' }) +
    api.at(L.x(0.68), L.y(0.2), R.tag(p.five || '', 62 * k, 'bad'), { cls: 'es-t5', idle: 'sway' }) +
    api.at(L.cx, L.y(0.95), R.tag(p.noOne || '', 58 * k, 'paper'), { cls: 'es-tn', idle: 'wobble' });
  const e5 = qa(root, '.es-5'), em = qa(root, '[class*="es-m"]');
  return t => {
    api.tw(q(root, '.es-s .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.es-h .a'), t, tH < t5 ? api.K.slam(tH - 0.05, 0.4).concat([[t5 - 0.2, {}], [t5, { o: 0.25, s: 0.7 }, 'lin'], [tM - 0.1, {}], [tM + 0.2, { o: 1, s: 1 }, 'back']]) : api.K.slam(tH - 0.05, 0.4));
    e5.forEach((e, i) => {      // five go out to the right and come back crossed
      const a = t5 + i * 0.18, u = api.prog(t, a, a + 0.6, 'out'), back = api.prog(t, a + 0.9, a + 1.5, 'in');
      e.style.left = (sx + (L.x(0.85) - sx) * u - (L.x(0.85) - sx) * back * 0.75 + (t < a ? 20 * k * Math.sin(t * 4 + i) : 0)) + 'px'; e.style.top = (sy - 200 * k + i * 90 * k) + 'px';
      api.tw(q(e, '.a'), t, [[a - 0.01, { o: 0 }], [a, { o: 1 }], [tM - 0.2, {}], [tM, { o: 0 }, 'lin']]);
      q(e, '.es-x').style.opacity = back > 0.05 ? 1 : 0;
    });
    em.forEach((e, i) => {      // the stream: many go out; only the hits come back
      const a = tM + i * 0.11, u = api.prog(t, a, a + 0.8, 'lin'), hit = e.classList.contains('es-hit');
      const back = hit ? api.prog(t, a + 1.0, a + 1.6, 'out') : 0;
      e.style.left = (sx + (L.x(1.05) - sx) * u - (L.x(1.05) - L.x(0.5)) * back) + 'px';
      e.style.top = (sy + Math.sin(i * 1.7) * 260 * k - 120 * k * back) + 'px';
      api.tw(q(e, '.a'), t, [[a - 0.01, { o: 0 }], [a, { o: 1 }]]);
    });
    api.tw(q(root, '.es-t5 .a'), t, api.K.pop(t5, 0.4, { o: 0, s: 0.3, r: 8 }).concat([[tM - 0.2, {}], [tM, { o: 0 }, 'lin']]));
    api.tw(q(root, '.es-tn .a'), t, api.K.pop(tN - 0.05, 0.4, { o: 0, s: 0.3, r: -8 }).concat([[tM - 0.2, {}], [tM, { o: 0 }, 'lin']]));
  };
});
