/* @scene {"type":"options_fan","tags":["ask questions","options","second opinion","informed choice"],"layout":"question-marks-then-card-fan-then-two-bubbles","metaphor":"question marks bubble up, a hand of option cards fans open, and a second speech bubble joins the first: ask, learn your options, get a second opinion","assets":["question-mark bubbles","fanned cards","two speech bubbles"]} */
// {ask:{label, at}, options:{label, at, n}, second:{label, at}}
RM.def('options_fan', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tA = api.T(p.ask.at), tO = api.T(p.options.at), tS = api.T(p.second.at), N = p.options.n || 5, cx = L.cx, cy = L.y(0.55);
  root.innerHTML = [0, 1, 2, 3].map(i => api.at(L.x(0.18 + i * 0.22), L.y(0.3 + (i % 2) * 0.08), `<div class="round" style="width:${130 * k}px;height:${130 * k}px;background:var(--acc);display:flex;align-items:center;justify-content:center;font-family:var(--f-display);font-weight:900;font-size:${90 * k}px;color:var(--ink)">?</div>`, { cls: 'of-q', idle: 'float' })).join('') +
    Array.from({ length: N }, (_, i) => api.at(cx, cy + 120 * k, `<div class="of-c" style="width:${230 * k}px;height:${330 * k}px;border-radius:${22 * k}px;background:var(--paper);border:${8 * k}px solid ${['var(--c1)', 'var(--c2)', 'var(--acc)'][i % 3]};box-shadow:var(--sh);transform-origin:50% 120%;display:flex;align-items:flex-start;justify-content:center;padding-top:${30 * k}px">
        <div class="big" style="font-size:${80 * k}px;color:${['var(--c1)', 'var(--c2)', 'var(--acc)'][i % 3]}">${i + 1}</div></div>`, { cls: 'of-cp' })).join('') +
    api.at(L.x(0.32), L.y(0.42), `<div class="bubble" style="font-size:${110 * k}px;padding:.2em .6em;color:var(--c2)">1</div>`, { cls: 'of-b1' }) +
    api.at(L.x(0.68), L.y(0.42), `<div class="bubble acc r" style="font-size:${110 * k}px;padding:.2em .6em">2</div>`, { cls: 'of-b2' }) +
    api.at(L.x(0.3), L.y(0.06), R.tag(p.ask.label, 60 * k, ''), { cls: 'of-t1', idle: 'sway' }) +
    api.at(L.x(0.7), L.y(0.97), R.tag(p.options.label, 56 * k, 'c1'), { cls: 'of-t2', idle: 'sway' }) +
    api.at(L.cx, L.y(0.16), R.tag(p.second.label, 58 * k, 'paper'), { cls: 'of-t3', idle: 'wobble' });
  return t => {
    qa(root, '.of-q').forEach((e, i) => api.tw(q(e, '.a'), t, api.K.pop(tA + i * 0.12, 0.35, { o: 0, s: 0, y: 60 * k }).concat([[tO - 0.2, {}], [tO + 0.1, { o: 0, y: -80 * k }, 'in']])));
    const fan = api.prog(t, tO, tO + 0.6, 'back');
    qa(root, '.of-cp').forEach((e, i) => { const a = (i - (N - 1) / 2) * 16 * fan;
      api.tw(q(e, '.a'), t, [[tO - 0.1, { o: 0, y: 200 * k }], [tO + 0.2, { o: 1, y: 0 }, 'out'], [tS - 0.2, {}], [tS + 0.15, { o: 0.25, s: 0.85 }, 'lin']]);
      q(e, '.of-c').style.transform = `rotate(${a.toFixed(1)}deg)`; });
    api.tw(q(root, '.of-b1 .a'), t, api.K.pop(tS - 0.1, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.of-b2 .a'), t, api.K.pop(tS + 0.25, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.of-t1 .a'), t, api.K.pop(tA, 0.4, { o: 0, s: 0.3, r: -6 }).concat([[tS - 0.2, {}], [tS, { o: 0 }, 'lin']]));
    api.tw(q(root, '.of-t2 .a'), t, api.K.pop(tO + 0.1, 0.4, { o: 0, s: 0.3, r: 6 }).concat([[tS - 0.2, {}], [tS, { o: 0 }, 'lin']]));
    api.tw(q(root, '.of-t3 .a'), t, api.K.slam(tS, 0.4));
  };
});
