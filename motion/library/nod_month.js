/* @scene {"type":"nod_month","tags":["agreement","no action","meeting","month passes","silent phone"],"layout":"window-top-person-behind-table","metaphor":"a person nods along at the table while days and nights race past the window and the phone on the table never moves","assets":["meeting table","window with sun and moon","nodding person (open peeps)","silent phone with zero badge"]} */
// {peep, nodFrom, nodTo, okTag, okAt, monthAt, monthTag, phoneAt, phoneTag}
RM.def('nod_month', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tN0 = api.T(p.nodFrom), tN1 = api.T(p.nodTo), tOk = api.T(p.okAt), tM = api.T(p.monthAt), tP = api.T(p.phoneAt);
  const peep = Object.assign({ body: 'Coffee', head: 'ShortOne', faces: { Smile: 0 } }, p.peep || {});
  const WW = 380 * k, WH = 300 * k;
  root.innerHTML =
    api.at(L.x(0.79), L.y(0.2), `<div class="nm-win" style="position:relative;width:${WW}px;height:${WH}px;border-radius:${26 * k}px;overflow:hidden;border:${16 * k}px solid var(--c2);box-shadow:var(--sh)">
        <div class="nm-sky" style="position:absolute;inset:0"></div>
        <div class="nm-sun" style="position:absolute;left:0;top:0">${api.icon('ph-fill:sun', 110 * k, 'var(--c1)')}</div>
        <div class="nm-moon" style="position:absolute;left:0;top:0">${api.icon('ph-fill:moon', 96 * k, 'var(--paper)')}</div>
        <div style="position:absolute;left:50%;top:0;bottom:0;width:${12 * k}px;margin-left:${-6 * k}px;background:var(--c2)"></div>
        <div style="position:absolute;top:50%;left:0;right:0;height:${12 * k}px;margin-top:${-6 * k}px;background:var(--c2)"></div></div>`, { cls: 'nm-w' }) +
    api.at(L.x(0.38), L.y(0.53), api.peep(Object.assign({ size: 600 * k }, peep)), { cls: 'nm-p' }) +
    api.at(L.cx, L.y(0.84), `<div style="width:${L.w * 0.98}px;height:${70 * k}px;border-radius:${20 * k}px;background:var(--c1);box-shadow:var(--sh)"></div>`, { cls: 'nm-t' }) +
    api.at(L.x(0.82), L.y(0.72), `<div style="position:relative">${api.icon('ph:phone', 210 * k, 'var(--c2)')}
        <div class="badge bad nm-z" style="position:absolute;right:${-34 * k}px;top:${-26 * k}px;font-size:${100 * k}px;font-family:var(--f-display);font-weight:900"><span style="font-size:.52em">0</span></div>
        <svg class="nm-web" width="${200 * k}" height="${200 * k}" viewBox="0 0 100 100" style="position:absolute;left:${-40 * k}px;top:${-50 * k}px;overflow:visible">
          <path d="M0 0 L60 50 M0 0 L30 70 M0 0 L70 20 M20 16 Q30 8 38 14 M14 26 Q30 22 40 34 M10 40 Q26 40 34 52" fill="none" stroke="var(--muted)" stroke-width="2.5"/></svg></div>`, { cls: 'nm-ph' }) +
    api.at(L.x(0.3), L.y(0.02), `<div style="display:flex;align-items:center;gap:${14 * k}px">${R.tag(p.okTag || '', 58 * k, 'good')}${api.icon('ph:check-circle', 90 * k, 'var(--good)')}</div>`, { cls: 'nm-ok', idle: 'sway' }) +
    api.at(L.x(0.72), L.y(0.37), R.tag(p.monthTag || '', 62 * k, 'c1'), { cls: 'nm-mt', idle: 'sway' }) +
    api.at(L.x(0.62), L.y(0.97), R.tag(p.phoneTag || '', 62 * k, 'bad'), { cls: 'nm-pt', idle: 'sway' });
  const pp = q(root, '.nm-p'), sky = q(root, '.nm-sky'), sun = q(root, '.nm-sun'), moon = q(root, '.nm-moon');
  return t => {
    api.tw(q(root, '.nm-w .a'), t, api.K.pop(api.start, 0.45, { o: 0, s: 0.4 }));
    api.tw(q(root, '.nm-t .a'), t, api.K.rise(api.start, 0.4, 200 * k));
    api.tw(q(pp, '.a'), t, api.K.rise(api.start + 0.1, 0.45, 260 * k));
    api.peepUpdate(pp, t, peep, []);
    const hd = q(pp, '.phd'); if (hd) { const nod = t > tN0 && t < tN1 + 0.2 ? 9 * Math.sin((t - tN0) * 12) : 0;
      hd.setAttribute('transform', `${hd.getAttribute('transform') || ''} rotate(${nod.toFixed(2)} 620 900)`); }
    // days and nights: slow at first, then a whole month races past
    const days = t < tM ? (t - api.start) * 0.15 : (tM - api.start) * 0.15 + 30 * api.prog(t, tM, tM + 1.6, 'io') + Math.max(0, t - tM - 1.6) * 0.15;
    const ph = days % 1, a = ph * Math.PI * 2, night = Math.max(0, -Math.sin(a));
    sky.style.background = `linear-gradient(180deg, ${night > 0.3 ? 'var(--c2)' : 'var(--acc-soft)'}, ${night > 0.3 ? 'var(--ink)' : 'var(--paper)'})`;
    const ox = WW / 2 - 55 * k + Math.cos(a + Math.PI) * WW * 0.38, oy = WH * 0.62 - Math.sin(a) * WH * 0.5;
    sun.style.transform = `translate(${ox.toFixed(1)}px,${oy.toFixed(1)}px)`; sun.style.opacity = Math.sin(a) > -0.05 ? 1 : 0;
    moon.style.transform = `translate(${(WW / 2 - 48 * k + Math.cos(a) * WW * 0.38).toFixed(1)}px,${(WH * 0.62 + Math.sin(a) * WH * 0.5).toFixed(1)}px)`; moon.style.opacity = Math.sin(a) < 0.05 ? 1 : 0;
    api.tw(q(root, '.nm-ok .a'), t, api.K.pop(tOk - 0.05, 0.4, { o: 0, s: 0.3, r: -10 }).concat([[tM - 0.2, {}], [tM + 0.1, { o: 0 }, 'lin']]));
    api.tw(q(root, '.nm-mt .a'), t, api.K.pop(tM, 0.4, { o: 0, s: 0.3, r: 10 }));
    api.tw(q(root, '.nm-ph .a'), t, api.K.drop(api.start + 0.3, 0.45, -300 * k));
    api.tw(q(root, '.nm-z'), t, api.K.pop(tP, 0.35, { o: 0, s: 0 }));
    R.draw(q(root, '.nm-web path'), api.prog(t, tM + 0.3, tM + 1.6, 'out'));
    q(root, '.nm-web').style.opacity = t > tM + 0.3 ? 1 : 0;
    api.tw(q(root, '.nm-pt .a'), t, api.K.pop(tP + 0.05, 0.4, { o: 0, s: 0.3, r: -8 }));
  };
});
