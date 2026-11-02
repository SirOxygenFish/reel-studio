/* @scene {"type":"mixed_studies","tags":["small studies","mixed results","not a replacement","neutral"],"layout":"paper-stack-left-dial-right-not-equal","metaphor":"a small stack of study papers, a needle that wobbles between low and high (mixed), and a not-equal sign between the glass and the doctor's bag","assets":["paper stack","wobbling dial","not-equal sign"]} */
// {studies:{label, at}, mixed:{label, at}, notRepl:{label, at}}
RM.def('mixed_studies', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.studies.at), tM = api.T(p.mixed.at), tN = api.T(p.notRepl.at);
  const dial = `<svg width="${520 * k}" height="${320 * k}" viewBox="-110 -100 220 130" overflow="visible">
      <path d="M-90 0 A90 90 0 0 1 90 0" fill="none" stroke="var(--muted)" stroke-width="22"/><path d="M-90 0 A90 90 0 0 1 -30 -85" fill="none" stroke="var(--bad)" stroke-width="22"/><path d="M30 -85 A90 90 0 0 1 90 0" fill="none" stroke="var(--good)" stroke-width="22"/>
      <g class="ms-n"><path d="M0 0 L0 -78" stroke="var(--paper)" stroke-width="8" stroke-linecap="round"/></g><circle r="14" fill="var(--paper)"/></svg>`;
  root.innerHTML = [0, 1, 2].map(i => api.at(L.x(0.25) + i * 16 * k, L.y(0.3) - i * 18 * k, `<div style="width:${320 * k}px;height:${420 * k}px;border-radius:${12 * k}px;background:var(--paper);box-shadow:var(--sh);padding:${30 * k}px ${24 * k}px;display:flex;flex-direction:column;gap:${18 * k}px">
        ${[0.9, 0.7, 0.85, 0.5].map(w => `<div style="height:${14 * k}px;width:${w * 100}%;border-radius:${7 * k}px;background:var(--c1l)"></div>`).join('')}
        <svg viewBox="0 0 100 40" style="width:100%"><path d="M5 35 L25 20 L45 28 L65 10 L95 18" fill="none" stroke="var(--c2)" stroke-width="5"/></svg></div>`, { cls: 'ms-p' })).join('') +
    api.at(L.x(0.73), L.y(0.28), dial, { cls: 'ms-d' }) +
    api.at(L.x(0.27), L.y(0.63), R.tag(p.studies.label, 58 * k, ''), { cls: 'ms-t1', idle: 'sway' }) +
    api.at(L.x(0.72), L.y(0.47), R.tag(p.mixed.label, 60 * k, 'c1'), { cls: 'ms-t2', idle: 'sway' }) +
    api.at(L.cx, L.y(0.8), `<div style="display:flex;align-items:center;gap:${30 * k}px">${api.icon('ph:drop', 190 * k, 'var(--c1)')}<div class="big" style="font-size:${220 * k}px;color:var(--bad)">≠</div>${api.icon('ph:first-aid-kit', 190 * k, 'var(--c2)')}</div>`, { cls: 'ms-ne' }) +
    api.at(L.cx, L.y(0.98), R.tag(p.notRepl.label, 50 * k, 'paper'), { cls: 'ms-t3', idle: 'wobble' });
  return t => {
    qa(root, '.ms-p').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.drop(tS - 0.1 + i * 0.12, 0.45, -300 * k)));
    api.tw(q(root, '.ms-d .a'), t, api.K.pop(tM - 0.2, 0.4, { o: 0, s: 0.3 }));
    const ang = t < tM ? -70 : 55 * Math.sin((t - tM) * 3.1) * (0.6 + 0.4 * Math.cos((t - tM) * 1.3));
    q(root, '.ms-n').setAttribute('transform', `rotate(${ang.toFixed(1)})`);
    api.tw(q(root, '.ms-t1 .a'), t, api.K.pop(tS + 0.2, 0.4, { o: 0, s: 0.3, r: -6 }));
    api.tw(q(root, '.ms-t2 .a'), t, api.K.pop(tM, 0.4, { o: 0, s: 0.3, r: 6 }));
    api.tw(q(root, '.ms-ne .a'), t, api.K.slam(tN - 0.05, 0.4));
    api.tw(q(root, '.ms-t3 .a'), t, api.K.pop(tN + 0.2, 0.4, { o: 0, s: 0.3, r: -4 }));
  };
});
