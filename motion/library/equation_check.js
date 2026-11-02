/* @scene {"type":"equation_check","tags":["math","percentage","check","proof"],"layout":"stacked-handwritten-equation","metaphor":"the numbers are written out like a sum on squared paper, underlined, and ticked: it adds up","assets":["squared paper","handwritten numbers","underline","tick"]} */
// {rows:[{text, at}], result:{text, at}, okAt}
RM.def('equation_check', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const rs = p.rows || [], tr = rs.map(r => api.T(r.at)), tRes = api.T(p.result.at), tOk = api.T(p.okAt ?? p.result.at);
  const PW = L.w * 0.94, PH = L.h * 0.86;
  root.innerHTML = api.at(L.cx, L.y(0.5), `<div style="width:${PW}px;height:${PH}px;border-radius:${24 * k}px;background:var(--paper);box-shadow:var(--sh);
        background-image:linear-gradient(var(--acc-soft) ${2 * k}px,transparent ${2 * k}px),linear-gradient(90deg,var(--acc-soft) ${2 * k}px,transparent ${2 * k}px);background-size:${54 * k}px ${54 * k}px"></div>`, { cls: 'eq-p', content: false }) +
    rs.map((r, i) => api.at(L.x(0.55), L.y(0.2 + i * 0.17), `<div class="big" style="font-size:${120 * k}px;color:var(--c2);text-align:right;min-width:${PW * 0.7}px">${R.esc(r.text)}</div>`, { cls: 'eq-r' })).join('') +
    `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><path class="eq-u" d="M${L.x(0.12)} ${L.y(0.2 + rs.length * 0.17 - 0.07)} H${L.x(0.92)}" stroke="var(--c2)" stroke-width="${10 * k}" stroke-linecap="round"/>
      <path class="eq-ok" d="M${L.x(0.1)} ${L.y(0.86)} l ${40 * k} ${44 * k} l ${90 * k} ${-110 * k}" fill="none" stroke="var(--good)" stroke-width="${22 * k}" stroke-linecap="round" stroke-linejoin="round"/></svg>` +
    api.at(L.x(0.55), L.y(0.2 + rs.length * 0.17 + 0.04), `<div class="big" style="font-size:${150 * k}px;color:var(--good);text-align:right;min-width:${PW * 0.7}px">${R.esc(p.result.text)}</div>`, { cls: 'eq-res' });
  return t => {
    api.tw(q(root, '.eq-p .a'), t, api.K.rise(api.start, 0.4, 200 * k));
    qa(root, '.eq-r').forEach((r, i) => api.tw(q(r, '.a'), t, [[tr[i] - 0.05, { o: 0, x: 80 * k }], [tr[i] + 0.3, { o: 1, x: 0 }, 'back']]));
    R.draw(q(root, '.eq-u'), api.prog(t, tRes - 0.3, tRes, 'out'));
    api.tw(q(root, '.eq-res .a'), t, api.K.slam(tRes - 0.05, 0.4));
    R.draw(q(root, '.eq-ok'), api.prog(t, tOk, tOk + 0.35, 'out'));
  };
});
