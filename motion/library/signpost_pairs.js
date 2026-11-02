/* @scene {"type":"signpost_pairs","tags":["choice","two kinds of discomfort","crossroads","pick your pain"],"layout":"signpost-center-two-boards","metaphor":"a wooden signpost at a crossroads whose two boards flip over to each new pair of discomforts: one points up the hill, one down into the fog","assets":["wooden signpost","flipping arrow boards","hill and fog"]} */
// {pairs:[{up:{label, icon, at}, down:{label, icon, at}}]}
RM.def('signpost_pairs', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const pairs = p.pairs || [], tu = pairs.map(x => api.T(x.up.at)), td = pairs.map(x => api.T(x.down.at));
  const px = L.cx, BW = 820 * k, BH = 240 * k;
  const scenery = `<svg width="${L.w}" height="${L.h}" viewBox="0 0 ${L.w} ${L.h}" style="position:absolute;left:${L.x0}px;top:${L.y0}px;overflow:visible">
      <path d="M0 ${L.h * 0.62} Q ${L.w * 0.35} ${L.h * 0.22} ${L.w * 0.75} ${L.h * 0.2} T ${L.w} ${L.h * 0.12} V ${L.h} H 0 Z" fill="var(--acc-soft)"/>
      <path d="M${L.w * 0.5} ${L.h} Q ${L.w * 0.55} ${L.h * 0.6} ${L.w * 0.85} ${L.h * 0.22}" fill="none" stroke="var(--paper)" stroke-width="${40 * k}" stroke-linecap="round" opacity=".9"/>
      ${[0, 1, 2].map(i => `<ellipse class="sp-fog" cx="${L.w * (0.15 + i * 0.3)}" cy="${L.h * 0.96}" rx="${260 * k}" ry="${70 * k}" fill="var(--paper)" opacity=".75"/>`).join('')}</svg>`;
  const board = (cls, dir, color) => api.at(px + (dir > 0 ? 60 : -60) * k, 0, `<div class="sp-bd" style="perspective:${1200 * k}px">
      <div class="sp-in" style="position:relative;width:${BW}px;height:${BH}px">
        ${pairs.map((x, i) => { const it = dir > 0 ? x.up : x.down;
          return `<div class="sp-face" data-i="${i}" style="position:absolute;inset:0;display:flex;align-items:center;gap:${20 * k}px;padding:0 ${44 * k}px;background:${color};color:var(--on-acc);
            clip-path:polygon(${dir > 0 ? `0 0, 88% 0, 100% 50%, 88% 100%, 0 100%` : `12% 0, 100% 0, 100% 100%, 12% 100%, 0 50%`});${dir < 0 ? `padding-left:${110 * k}px;` : ''}box-shadow:var(--sh);backface-visibility:hidden">
            ${api.icon(it.icon, 140 * k, 'var(--on-acc)')}<div class="big sp-lb" style="font-size:${66 * k}px;white-space:normal;line-height:1.02;flex:1;min-width:0">${R.esc(it.label)}</div></div>`; }).join('')}
      </div></div>`, { cls: cls, idle: 'sway float', amp: 1.4 });
  root.innerHTML = scenery +
    api.at(px, L.y(0.6), `<div style="width:${44 * k}px;height:${L.h * 0.95}px;border-radius:${14 * k}px;background:var(--c2)"></div>`, { cls: 'sp-pole' }) +
    board('sp-up', 1, 'var(--acc)') + board('sp-dn', -1, 'var(--bad)');
  q(root, '.sp-up').style.top = L.y(0.2) + 'px'; q(root, '.sp-dn').style.top = L.y(0.5) + 'px';
  qa(root, '.sp-up .sp-in, .sp-dn .sp-in').forEach(el => el.style.transformStyle = 'preserve-3d');
  qa(root, '.sp-lb').forEach(el => { let fs = 66 * k; while (fs > 26 && el.scrollHeight > BH * 0.86) { fs -= 2; el.style.fontSize = fs + 'px'; } });
  return t => {
    api.tw(q(root, '.sp-pole .a'), t, api.K.rise(api.start, 0.45, 400 * k));
    [['.sp-up', tu, 1], ['.sp-dn', td, -1]].forEach(([c, ts, dir]) => {
      const cur = ts.filter(x => t >= x - 0.05).length - 1;
      api.tw(q(root, c + ' .a'), t, [[ts[0] - 0.1, { o: 0, x: dir * 300 * k, r: dir * -10 }], [ts[0] + 0.35, { o: 1, x: 0, r: dir * -3 }, 'back']]);
      qa(root, c + ' .sp-face').forEach(f => {
        const i = +f.dataset.i, a = ts[i] - 0.05, flip = i === 0 ? 1 : api.prog(t, a, a + 0.4, 'back'), next = i + 1 < ts.length ? api.prog(t, ts[i + 1] - 0.05, ts[i + 1] + 0.2, 'in') : 0;
        f.style.transform = `rotateX(${(-90 * (1 - flip) + 90 * next).toFixed(1)}deg)`;
        f.style.opacity = (i <= cur && next < 1) ? 1 : 0;
      });
    });
    qa(root, '.sp-fog').forEach((e, i) => e.setAttribute('transform', `translate(${(40 * Math.sin(t * 0.8 + i * 2)).toFixed(1)} 0)`));
  };
});
