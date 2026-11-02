/* @scene {"type":"pin_note","tags":["one sentence","remember","script","answer"],"layout":"cork-board-single-note","metaphor":"one handwritten note gets pinned to a cork board: one sentence to remember","assets":["cork board","sticky note","push pin","scribble line"]} */
// {one, oneAt, remember, rememberAt}
RM.def('pin_note', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const t1 = api.T(p.oneAt ?? api.start), t2 = api.T(p.rememberAt);
  const BW = L.w * 0.96, BH = L.h * 0.74;
  root.innerHTML = api.at(L.cx, L.y(0.48), `<div style="width:${BW}px;height:${BH}px;border-radius:${30 * k}px;border:${22 * k}px solid var(--c2);background:radial-gradient(circle at 30% 30%,var(--c1l),var(--c1));box-shadow:var(--sh);position:relative;overflow:hidden">
        ${Array.from({ length: 60 }, (_, i) => `<div style="position:absolute;left:${(i * 41) % 100}%;top:${(i * 67) % 100}%;width:${10 * k}px;height:${10 * k}px;border-radius:50%;background:var(--c2);opacity:.25"></div>`).join('')}</div>`, { cls: 'pn-b', content: false }) +
    api.at(L.cx, L.y(0.5), `<div style="position:relative;width:${520 * k}px;height:${520 * k}px;background:var(--paper);box-shadow:0 ${24 * k}px ${40 * k}px var(--hard-shadow);transform:rotate(-3deg)">
        <svg width="${520 * k}" height="${520 * k}" viewBox="0 0 520 520" style="position:absolute;inset:0">${[150, 230, 310].map(y => `<path d="M60 ${y} H460" stroke="var(--acc-soft)" stroke-width="5"/>`).join('')}
          <path class="pn-s" d="M70 230 c 30 -40 60 30 90 0 s 60 -30 90 0 s 60 30 90 0 s 50 -20 90 0" fill="none" stroke="var(--ink)" stroke-width="12" stroke-linecap="round"/>
          <path class="pn-u" d="M80 270 H440" stroke="var(--bad)" stroke-width="10" stroke-linecap="round"/></svg>
        <div class="big" style="position:absolute;left:0;right:0;top:${60 * k}px;text-align:center;font-size:${110 * k}px;color:var(--bad)">1</div></div>`, { cls: 'pn-n' }) +
    api.at(L.cx, L.y(0.5) - 270 * k, `<svg width="${90 * k}" height="${120 * k}" viewBox="0 0 90 120" overflow="visible"><path d="M45 70 V118" stroke="var(--muted)" stroke-width="6" stroke-linecap="round"/><ellipse cx="45" cy="40" rx="40" ry="34" fill="var(--bad)"/><ellipse cx="34" cy="30" rx="10" ry="8" fill="var(--paper)" opacity=".6"/></svg>`, { cls: 'pn-p' }) +
    api.at(L.x(0.3), L.y(0.06), R.tag(p.one || '', 66 * k, 'c1'), { cls: 'pn-t1', idle: 'sway' }) +
    api.at(L.x(0.7), L.y(0.92), R.tag(p.remember || '', 72 * k, ''), { cls: 'pn-t2', idle: 'wobble' });
  return t => {
    api.tw(q(root, '.pn-b .a'), t, api.K.rise(api.start, 0.45, 300 * k));
    api.tw(q(root, '.pn-n .a'), t, [[t1 - 0.1, { o: 0, s: 1.6, r: 20, y: -300 * k }], [t1 + 0.3, { o: 1, s: 1, r: 0, y: 0 }, 'in'], [t1 + 0.45, { s: 1.03 }, 'out'], [t1 + 0.6, { s: 1 }, 'io']]);
    R.draw(q(root, '.pn-s'), api.prog(t, t1 + 0.3, t1 + 1.3, 'io'));
    R.draw(q(root, '.pn-u'), api.prog(t, t2, t2 + 0.4, 'out'));
    api.tw(q(root, '.pn-p .a'), t, [[t2 - 0.25, { o: 0, y: -260 * k, s: 1.4 }], [t2, { o: 1, y: 0, s: 1 }, 'in'], [t2 + 0.12, { s: 0.9 }, 'out'], [t2 + 0.25, { s: 1 }, 'io']]);
    api.tw(q(root, '.pn-t1 .a'), t, api.K.pop(t1, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.pn-t2 .a'), t, api.K.pop(t2 + 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
