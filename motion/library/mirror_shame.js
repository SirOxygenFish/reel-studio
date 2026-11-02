/* @scene {"type":"mirror_shame","tags":["self question","is it me","shame","reflection"],"layout":"standing-mirror-center","metaphor":"a standing mirror: the reflection first matches you, then turns away and hides its face: is it me, or my shame?","assets":["standing oval mirror","reflection figure hiding face"]} */
// {askAt, me, meAt, shame, shameAt}
RM.def('mirror_shame', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tA = api.T(p.askAt ?? api.start), tM = api.T(p.meAt), tS = api.T(p.shameAt);
  const MW = 480 * k, MH = 720 * k;
  const person = (hide) => `<svg width="${MW * 0.6}" height="${MH * 0.7}" viewBox="-90 -130 180 260" overflow="visible">
      <circle cx="0" cy="-80" r="40" fill="var(--c1l)" stroke="var(--c2)" stroke-width="6"/><path d="M-60 130 Q-64 -24 0 -30 Q64 -24 60 130 Z" fill="var(--acc)"/>
      ${hide ? `<path d="M-50 10 Q-40 -60 -10 -84 M50 10 Q40 -60 10 -84" stroke="var(--acc)" stroke-width="24" fill="none" stroke-linecap="round"/><ellipse cx="0" cy="-86" rx="34" ry="22" fill="var(--c1l)" stroke="var(--c2)" stroke-width="5"/>`
             : `<circle cx="-14" cy="-86" r="6" fill="var(--ink)"/><circle cx="14" cy="-86" r="6" fill="var(--ink)"/><path d="M-14 -64 Q0 -56 14 -64" stroke="var(--ink)" stroke-width="5" fill="none"/>`}</svg>`;
  root.innerHTML = api.at(L.cx, L.y(0.5), `<div style="position:relative;width:${MW}px;height:${MH}px">
        <div style="position:absolute;inset:0;border-radius:50%;background:var(--c2);box-shadow:var(--sh)"></div>
        <div style="position:absolute;inset:${24 * k}px;border-radius:50%;overflow:hidden;background:linear-gradient(160deg,var(--acc-soft),var(--paper) 50%,var(--c1x))">
          <div class="ms-a" style="position:absolute;left:50%;bottom:-${20 * k}px;transform:translateX(-50%)">${person(false)}</div>
          <div class="ms-b" style="position:absolute;left:50%;bottom:-${20 * k}px;transform:translateX(-50%);opacity:0">${person(true)}</div>
          <div class="ms-gl" style="position:absolute;top:-20%;left:-60%;width:40%;height:140%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.7),transparent);transform:rotate(20deg)"></div></div>
        <div style="position:absolute;left:50%;bottom:-${110 * k}px;width:${24 * k}px;height:${120 * k}px;margin-left:-${12 * k}px;background:var(--c2)"></div></div>`, { cls: 'ms-m' }) +
    api.at(L.x(0.2), L.y(0.1), R.tag(p.me || '', 72 * k, 'c1'), { cls: 'ms-t1', idle: 'sway' }) +
    api.at(L.x(0.75), L.y(0.92), R.tag(p.shame || '', 76 * k, 'bad'), { cls: 'ms-t2', idle: 'wobble' });
  return t => {
    api.tw(q(root, '.ms-m .a'), t, api.K.spring(api.start, 0.6, { o: 0, s: 0.3, y: 200 * k }));
    const sw = api.prog(t, tS - 0.1, tS + 0.35, 'io');
    q(root, '.ms-a').style.opacity = 1 - sw; q(root, '.ms-b').style.opacity = sw;
    q(root, '.ms-gl').style.left = (-60 + 180 * ((t - api.start) * 0.5 % 1)) + '%';
    api.tw(q(root, '.ms-t1 .a'), t, api.K.pop(tM - 0.05, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.ms-t2 .a'), t, api.K.slam(tS - 0.05, 0.4));
  };
});
