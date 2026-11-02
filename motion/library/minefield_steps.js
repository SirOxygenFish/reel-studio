/* @scene {"type":"minefield_steps","tags":["learn from others","mistakes","mentors","safe path"],"layout":"top-down-field-path-up","metaphor":"a field with craters where others stepped wrong; follow the footprints of those who crossed it before","assets":["field with craters","warning flags","footprint trail","tip numeral"]} */
// {num, errAt, err, followAt, follow, cheapAt, cheap}
RM.def('minefield_steps', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tE = api.T(p.errAt), tF = api.T(p.followAt), tC = p.cheap ? api.T(p.cheapAt) : 0;
  const craters = [[0.2, 0.3], [0.75, 0.22], [0.36, 0.55], [0.8, 0.6], [0.18, 0.78], [0.62, 0.86], [0.55, 0.36]];
  const path = [[0.5, 0.98], [0.42, 0.88], [0.5, 0.76], [0.6, 0.68], [0.55, 0.56], [0.46, 0.45], [0.38, 0.35], [0.42, 0.22], [0.5, 0.12]];
  root.innerHTML = `<div style="position:absolute;left:${L.x0}px;top:${L.y0}px;width:${L.w}px;height:${L.h}px;border-radius:${50 * k}px;background:var(--acc-soft);overflow:hidden">
      ${Array.from({ length: 40 }, (_, i) => `<div style="position:absolute;left:${(i * 37) % 100}%;top:${(i * 53) % 100}%;width:${20 * k}px;height:${8 * k}px;border-radius:4px;background:var(--acc);opacity:.35;transform:rotate(${(i * 47) % 90 - 45}deg)"></div>`).join('')}</div>` +
    craters.map(([x, y], i) => api.at(L.x(x), L.y(y), `<div style="position:relative;width:${150 * k}px;height:${90 * k}px">
        <div style="position:absolute;inset:0;border-radius:50%;background:radial-gradient(closest-side,var(--c2),var(--c1) 70%,transparent)"></div>
        <div style="position:absolute;left:55%;bottom:40%;width:${6 * k}px;height:${90 * k}px;background:var(--ink)"></div>
        <div style="position:absolute;left:calc(55% + ${6 * k}px);bottom:calc(40% + ${50 * k}px);width:${56 * k}px;height:${40 * k}px;background:var(--bad);clip-path:polygon(0 0,100% 50%,0 100%)"></div></div>`, { cls: 'mf-c' })).join('') +
    path.map(([x, y], i) => api.at(L.x(x), L.y(y), api.icon('ph-fill:footprints', 86 * k, 'var(--c2)'), { cls: 'mf-s' })).join('') +
    api.at(L.x(0.9), L.y(0.2), `<div class="badge acc" style="font-size:${150 * k}px;font-family:var(--f-display);font-weight:900"><span style="font-size:.52em">${R.esc(p.num || '')}</span></div>`, { cls: 'mf-n' }) +
    api.at(L.x(0.4), L.y(0.05), R.tag(p.err || '', 62 * k, 'bad'), { cls: 'mf-t1', idle: 'sway' }) +
    api.at(L.x(0.3), L.y(0.95), R.tag(p.follow || '', 58 * k, ''), { cls: 'mf-t2', idle: 'sway' }) +
    (p.cheap ? api.at(L.x(0.72), L.y(0.46), R.tag(p.cheap, 70 * k, 'c1'), { cls: 'mf-t3', idle: 'wobble' }) : '');
  qa(root, '.mf-s').forEach((s, i) => { if (i + 1 < path.length) { const a = Math.atan2(path[i + 1][1] - path[i][1], (path[i + 1][0] - path[i][0]) * L.w / L.h) * 57.3 + 90; q(s, '.m').style.transform = `rotate(${a.toFixed(0)}deg)`; } });
  return t => {
    qa(root, '.mf-c').forEach((c, i) => api.tw(q(c, '.a'), t, api.K.pop(tE - 0.1 + i * 0.08, 0.35, { o: 0, s: 0.2 })));
    qa(root, '.mf-s').forEach((s, i) => api.tw(q(s, '.a'), t, [[tF + i * 0.12, { o: 0, s: 0.4 }], [tF + i * 0.12 + 0.2, { o: 1, s: 1 }, 'back']]));
    api.tw(q(root, '.mf-n .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0 }));
    api.tw(q(root, '.mf-t1 .a'), t, api.K.pop(tE + 0.1, 0.4, { o: 0, s: 0.3, r: 8 }));
    api.tw(q(root, '.mf-t2 .a'), t, api.K.pop(tF + 0.1, 0.4, { o: 0, s: 0.3, r: -8 }));
    if (p.cheap) api.tw(q(root, '.mf-t3 .a'), t, api.K.slam(tC - 0.05, 0.4));
  };
});
