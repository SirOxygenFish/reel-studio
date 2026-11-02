/* @scene {"type":"plan_scroll","tags":["plan","step by step","waited years","beginners","guide"],"layout":"wax-seal-then-vertical-scroll","metaphor":"a wax seal with the years waited, then a paper scroll unrolls with footsteps walking down it","assets":["wax seal","paper scroll","footprints"]} */
// {seal:"...", sealAt, sealLabel, unrollAt, stepsAt, stepsTag, forAt, forTag}
RM.def('plan_scroll', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tSe = api.T(p.sealAt ?? api.start), tU = api.T(p.unrollAt), tSt = api.T(p.stepsAt), tF = p.forTag ? api.T(p.forAt) : 0;
  const SW = 600 * k, SHmax = 760 * k, sx = L.cx, top = L.y(0.08);
  root.innerHTML =
    api.at(sx, top + SHmax / 2, `<div class="ps-paper" style="position:relative;width:${SW}px;height:${SHmax}px;overflow:hidden">
        <div style="position:absolute;inset:0 ${20 * k}px;background:linear-gradient(90deg,var(--c1x),var(--paper) 18%,var(--paper) 82%,var(--c1x));box-shadow:var(--sh)"></div>
        ${Array.from({ length: 6 }, (_, i) => `<div class="ps-fp" style="position:absolute;left:${(i % 2 ? 0.56 : 0.3) * SW}px;top:${(0.12 + i * 0.145) * SHmax}px;transform:rotate(${i % 2 ? 10 : -10}deg)">${api.icon('ph-fill:footprints', 110 * k, i % 2 ? 'var(--acc)' : 'var(--c1)')}</div>`).join('')}
      </div>`, { cls: 'ps-s' }) +
    api.at(sx, top, `<div style="width:${SW + 60 * k}px;height:${70 * k}px;border-radius:${35 * k}px;background:linear-gradient(180deg,var(--c1l),var(--c1),var(--c2));box-shadow:var(--sh)"></div>`, { cls: 'ps-r1' }) +
    api.at(sx, top, `<div style="width:${SW + 60 * k}px;height:${70 * k}px;border-radius:${35 * k}px;background:linear-gradient(180deg,var(--c1l),var(--c1),var(--c2));box-shadow:var(--sh)"></div>`, { cls: 'ps-r2' }) +
    api.at(L.x(0.78), L.y(0.3), `<div class="round" style="width:${260 * k}px;height:${260 * k}px;background:radial-gradient(circle at 35% 30%, var(--bad), var(--c2));display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:var(--sh);color:var(--on-bad)">
        <div class="big" style="font-size:${78 * k}px">${R.esc(p.seal || '')}</div>${p.sealLabel ? `<div class="label" style="font-size:${28 * k}px;color:var(--on-bad)">${R.esc(p.sealLabel)}</div>` : ''}</div>`, { cls: 'ps-seal', idle: 'wobble' }) +
    api.at(L.x(0.26), L.y(0.62), R.tag(p.stepsTag || '', 62 * k, 'c1'), { cls: 'ps-tg', idle: 'sway' }) +
    (p.forTag ? api.at(sx, L.y(0.97), R.tag(p.forTag, 60 * k, ''), { cls: 'ps-for', idle: 'sway' }) : '');
  const paper = q(root, '.ps-paper');
  return t => {
    api.tw(q(root, '.ps-seal .a'), t, [[tSe - 0.05, { o: 0, s: 2.6, r: -40 }], [tSe + 0.25, { o: 1, s: 0.92, r: -8 }, 'in'], [tSe + 0.4, { s: 1 }, 'back']]);
    const u = api.prog(t, tU - 0.1, tU + 0.8, 'io'), h = 70 * k + (SHmax - 70 * k) * u;
    paper.style.clipPath = `inset(0 0 ${(SHmax - h).toFixed(1)}px 0)`;
    api.tw(q(root, '.ps-s .a'), t, [[api.start, { o: 0 }], [tU - 0.1, { o: 0 }], [tU, { o: 1 }]]);
    api.tw(q(root, '.ps-r1 .a'), t, api.K.drop(api.start, 0.45, -300 * k));
    const r2 = q(root, '.ps-r2'); r2.style.top = (top + h - 35 * k + 35 * k) + 'px';
    api.tw(q(r2, '.a'), t, api.K.drop(api.start, 0.45, -300 * k));
    qa(root, '.ps-fp').forEach((e, i) => { const a = tSt + i * 0.22; api.tw(e, t, [[a - 0.01, { o: 0, s: 0.4 }], [a + 0.2, { o: 1, s: 1 }, 'back']]); e.style.transform += ` rotate(${i % 2 ? 10 : -10}deg)`; });
    api.tw(q(root, '.ps-tg .a'), t, api.K.pop(tSt - 0.05, 0.4, { o: 0, s: 0.3, r: -12 }));
    if (p.forTag) api.tw(q(root, '.ps-for .a'), t, api.K.pop(tF - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
