/* @scene {"type":"toggle_switch","tags":["if it hurts","doctor first","not a blogger"],"layout":"huge-horizontal-toggle-center","metaphor":"one huge toggle switch: the knob tries the phone side, gets a cross, and snaps across to the stethoscope side","assets":["huge toggle switch","phone mark"]} */
// {pain, painAt, first, firstAt, blog, blogAt, doc, docAt}
RM.def('toggle_switch', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tP = api.T(p.painAt), tF = api.T(p.firstAt), tB = api.T(p.blogAt), tD = api.T(p.docAt), cx = L.cx, cy = L.y(0.5), TW = L.w * 0.92, TH = 340 * k, KR = 138 * k, xl = cx - TW / 2 + TH / 2, xr = cx + TW / 2 - TH / 2;
  root.innerHTML = `<div class="ts2-t" style="position:absolute;left:${cx - TW / 2}px;top:${cy - TH / 2}px;width:${TW}px;height:${TH}px;border-radius:${TH / 2}px;background:var(--c2);border:${10 * k}px solid var(--c1l);box-sizing:border-box"></div>
    <svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><circle class="ts2-k" cy="${cy}" r="${KR}" fill="var(--paper)"/></svg>` +
    api.at(xl, cy, `<svg width="${150 * k}" height="${150 * k}" viewBox="-50 -50 100 100"><rect x="-26" y="-44" width="52" height="88" rx="10" fill="var(--c1x)"/><path d="M-9 -14 L14 0 L-9 14 Z" fill="var(--c2)"/></svg>`, { cls: 'ts2-a' }) +
    api.at(xr, cy, api.icon('ph-fill:stethoscope', 170 * k, 'var(--c1x)'), { cls: 'ts2-d' }) +
    api.at(xl, cy, `<svg width="${260 * k}" height="${260 * k}" viewBox="-50 -50 100 100"><path d="M-36 -36 L36 36 M36 -36 L-36 36" stroke="var(--bad)" stroke-width="14" stroke-linecap="round"/></svg>`, { cls: 'ts2-x' }) +
    api.at(cx, L.y(0.14), R.tag(p.pain || '', 96 * k, 'bad'), { cls: 'ts2-t1', idle: 'wobble' }) +
    api.at(cx, L.y(0.14), R.tag(p.first || '', 86 * k, 'c1'), { cls: 'ts2-t2', idle: 'sway' }) +
    api.at(cx, L.y(0.84), R.tag(p.blog || '', 88 * k, ''), { cls: 'ts2-t3', idle: 'sway' }) +
    api.at(cx, L.y(0.84), R.tag(p.doc || '', 110 * k, 'c1'), { cls: 'ts2-t4', idle: 'wobble' });
  const ks = q(root, '.ts2-k'), tr = q(root, '.ts2-t');
  return t => {
    const a = api.prog(t, tF - 0.05, tF + 0.25, 'back'), b = api.prog(t, tB - 0.1, tB + 0.14, 'out'), c = api.prog(t, tD - 0.05, tD + 0.25, 'back'), pos = (a * (1 - b) + c * b);
    ks.setAttribute('cx', (xl + (xr - xl) * pos).toFixed(1)); ks.setAttribute('fill', t >= tD ? 'var(--acc)' : 'var(--paper)');
    tr.style.background = t >= tD + 0.05 ? 'var(--c1)' : 'var(--c2)'; tr.style.transform = `translateY(${((1 - api.prog(t, api.start, api.start + 0.26, 'back')) * 700 * k).toFixed(1)}px)`;
    api.tw(q(root, '.ts2-a .a'), t, api.K.pop(api.start + 0.12, 0.24, { o: 0, s: 0.3 })); api.tw(q(root, '.ts2-d .a'), t, api.K.pop(api.start + 0.18, 0.24, { o: 0, s: 0.3 }));
    api.tw(q(root, '.ts2-x .a'), t, api.K.slam(tB + 0.16, 0.26));
    api.tw(q(root, '.ts2-t1 .a'), t, api.K.pop(tP - 0.03, 0.24, { o: 0, s: 0.3 }).concat([[tF - 0.1, {}], [tF - 0.02, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.ts2-t2 .a'), t, api.K.slam(tF - 0.02, 0.28));
    api.tw(q(root, '.ts2-t3 .a'), t, api.K.pop(tB - 0.1, 0.24, { o: 0, s: 0.3, r: -4 }).concat([[tD - 0.12, {}], [tD - 0.03, { o: 0, s: 0.6 }, 'in']]));
    api.tw(q(root, '.ts2-t4 .a'), t, api.K.slam(tD - 0.03, 0.3));
  };
});
