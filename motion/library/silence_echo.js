/* @scene {"type":"silence_echo","tags":["silence","patience","pause","self reflection"],"layout":"sound-wave-top-head-silhouette-bottom","metaphor":"the sound wave flattens into a calm line; in that silence a small voice lights up inside the customer's head","assets":["sound wave line","head silhouette in profile","inner speech bubble"]} */
// {patientAt, patient, quietAt, quiet, selfAt, self}
RM.def('silence_echo', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tP = api.T(p.patientAt ?? api.start), tQ = api.T(p.quietAt), tS = api.T(p.selfAt);
  const W = L.w, wy = L.y(0.22), N = 120;
  root.innerHTML = `<svg style="position:absolute;left:${L.x0}px;top:0;overflow:visible" width="1" height="1"><path class="se-w" fill="none" stroke="var(--c1)" stroke-width="${14 * k}" stroke-linecap="round" stroke-linejoin="round"/></svg>` +
    api.at(L.x(0.42), L.y(0.68), `<svg width="${520 * k}" height="${560 * k}" viewBox="0 0 260 280" overflow="visible">
        <path d="M60 280 V220 Q20 200 24 150 Q10 140 22 120 Q14 108 26 98 Q24 40 90 18 Q160 0 200 50 Q236 96 214 150 Q206 180 170 196 V280 Z" fill="var(--c2)"/>
        <circle class="se-glow" cx="130" cy="100" r="62" fill="var(--c1l)" opacity="0"/></svg>`, { cls: 'se-h', content: false }) +
    api.at(L.x(0.45), L.y(0.6), `<div class="bubble acc" style="font-size:${60 * k}px">${R.esc(p.self || '')}</div>`, { cls: 'se-b' }) +
    api.at(L.x(0.28), L.y(0.36), R.tag(p.patient || '', 58 * k, 'c1'), { cls: 'se-t1', idle: 'sway' }) +
    api.at(L.x(0.72), L.y(0.47), R.tag(p.quiet || '', 62 * k, ''), { cls: 'se-t2', idle: 'sway' });
  const wv = q(root, '.se-w');
  return t => {
    const amp = 140 * k * (1 - api.prog(t, tQ - 0.6, tQ + 0.4, 'io')) * api.prog(t, api.start, api.start + 0.4, 'out');
    let d = ''; for (let i = 0; i <= N; i++) { const x = W * i / N, a = Math.sin(i * 0.5 + t * 9) * Math.sin(i * 0.13 + t * 2.3) * Math.sin(Math.PI * i / N);
      d += (i ? ' L' : 'M') + x.toFixed(1) + ' ' + (wy + a * amp).toFixed(1); }
    wv.setAttribute('d', d);
    api.tw(q(root, '.se-h .a'), t, api.K.rise(api.start + 0.1, 0.45, 300 * k));
    q(root, '.se-glow').setAttribute('opacity', (0.9 * api.prog(t, tS - 0.3, tS + 0.2, 'out') * (0.8 + 0.2 * Math.sin(t * 5))).toFixed(2));
    api.tw(q(root, '.se-b .a'), t, api.K.spring(tS - 0.05, 0.55, { o: 0, s: 0.2 }));
    api.tw(q(root, '.se-t1 .a'), t, api.K.pop(tP, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.se-t2 .a'), t, api.K.pop(tQ - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
