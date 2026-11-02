/* @scene {"type":"cutout_obstacles","tags":["excuses","talent","contacts","luck","what stands between"],"layout":"figure-left-goal-right-walls-between","metaphor":"three cardboard walls (no talent, no contacts, no luck) pop up between you and your goal, then fold flat: they are not what stands in the way","assets":["cardboard walls","figure","goal star flag"]} */
// {walls:[{label, at}], flatAt}
RM.def('cutout_obstacles', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const ws = p.walls || [], tw = ws.map(w => api.T(w.at)), tF = api.T(p.flatAt ?? api.end - 1.2), gy = L.y(0.8);
  root.innerHTML = `<div style="position:absolute;left:${L.x0}px;top:${gy}px;width:${L.w}px;height:${16 * k}px;border-radius:${8 * k}px;background:var(--c2)"></div>` +
    api.at(L.x(0.08), gy - 120 * k, `<svg width="${150 * k}" height="${240 * k}" viewBox="-40 -64 80 128"><circle cx="0" cy="-42" r="18" fill="var(--acc)"/><path d="M-26 64 Q-28 -14 0 -18 Q28 -14 26 64 Z" fill="var(--acc)"/></svg>`, { cls: 'co-me' }) +
    api.at(L.x(0.93), gy - 150 * k, `<svg width="${150 * k}" height="${300 * k}" viewBox="0 0 75 150"><path d="M10 150 V10" stroke="var(--c2)" stroke-width="6"/><path d="M14 10 L70 26 L14 44 Z" fill="var(--bad)"/><path d="M40 70 l6 14 15 2 -11 10 3 15 -13 -7 -13 7 3 -15 -11 -10 15 -2 Z" fill="var(--c1)"/></svg>`, { cls: 'co-goal', idle: 'float' }) +
    ws.map((w, i) => api.at(L.x(0.3 + i * 0.22), gy, `<div class="co-w" style="width:${200 * k}px;height:${520 * k}px;background:repeating-linear-gradient(0deg,var(--c1l) 0 ${20 * k}px,var(--c1x) ${20 * k}px ${24 * k}px);border:${8 * k}px solid var(--c1);border-radius:${10 * k}px ${10 * k}px 0 0;transform-origin:50% 100%;display:flex;align-items:center;justify-content:center;box-shadow:var(--sh)">
        <div class="big" style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:${60 * k}px;color:var(--c2);white-space:nowrap">${R.esc(w.label)}</div></div>`, { cls: 'co-p' })).join('');
  qa(root, '.co-p').forEach(pt => { pt.style.top = (gy - 260 * k) + 'px'; });
  qa(root, '.co-w .big').forEach(el => { let fs = 60 * k; while (fs > 26 && el.getBoundingClientRect().height > 490 * k) { fs -= 2; el.style.fontSize = fs + 'px'; } });
  return t => {
    api.tw(q(root, '.co-me .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0.3 }));
    api.tw(q(root, '.co-goal .a'), t, api.K.pop(api.start + 0.15, 0.4, { o: 0, s: 0.3 }));
    qa(root, '.co-p').forEach((pt, i) => {
      const up = api.prog(t, tw[i] - 0.1, tw[i] + 0.35, 'back'), flat = api.prog(t, tF + i * 0.12, tF + 0.5 + i * 0.12, 'in');
      q(pt, '.co-w').style.transform = `scaleY(${Math.max(0.001, up).toFixed(3)}) rotateX(${(85 * flat).toFixed(1)}deg)`;
      api.tw(q(pt, '.a'), t, [[tw[i] - 0.1, { o: 0 }], [tw[i], { o: 1 }]]);
    });
    const go = api.prog(t, tF + 0.6, api.end - 0.1, 'io');
    q(root, '.co-me').style.left = (L.x(0.08) + (L.x(0.8) - L.x(0.08)) * go) + 'px';
    q(root, '.co-me .i').style.transform = `translateY(${(go > 0 && go < 1 ? -10 * k * Math.abs(Math.sin(t * 10)) : 0).toFixed(1)}px)`;
  };
});
