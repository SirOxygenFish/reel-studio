/* @scene {"type":"megaphone_bounce","tags":["convincing","pushing","not listening","arguments"],"layout":"megaphone-left-person-right","metaphor":"arguments blasted through a megaphone bounce off a person with crossed arms who feels unheard","assets":["megaphone","sound arcs","arms-crossed figure","bouncing word pills"]} */
// {blast, blastAt, unheard, unheardAt}
RM.def('megaphone_bounce', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tB = api.T(p.blastAt ?? api.start), tU = api.T(p.unheardAt);
  const my = L.y(0.5);
  root.innerHTML = api.at(L.x(0.2), my, `<svg width="${300 * k}" height="${260 * k}" viewBox="-20 -110 300 220" overflow="visible">
        <path d="M0 -40 L180 -100 L180 100 L0 40 Z" fill="var(--c1)"/><rect x="-20" y="-46" width="40" height="92" rx="12" fill="var(--c2)"/>
        <path d="M40 40 L60 100" stroke="var(--c2)" stroke-width="26" stroke-linecap="round"/><ellipse cx="180" cy="0" rx="24" ry="100" fill="var(--c2)"/></svg>`, { cls: 'mb-m' }) +
    [0, 1, 2].map(i => `<svg class="mb-arc" style="position:absolute;left:${L.x(0.36) + i * 60 * k}px;top:${my - (90 + i * 40) * k}px;overflow:visible" width="${60 * k}" height="${(180 + i * 80) * k}" viewBox="0 0 60 ${180 + i * 80}"><path d="M10 10 Q 50 ${(180 + i * 80) / 2} 10 ${170 + i * 80}" fill="none" stroke="var(--c1l)" stroke-width="10" stroke-linecap="round"/></svg>`).join('') +
    api.at(L.x(0.8), L.y(0.58), `<svg width="${300 * k}" height="${480 * k}" viewBox="-90 -150 180 290" overflow="visible">
        <circle cx="0" cy="-100" r="40" fill="var(--c1l)" stroke="var(--c2)" stroke-width="6"/><path d="M-16 -104 h10 M6 -104 h10" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"/><path d="M-14 -78 Q0 -86 14 -78" stroke="var(--ink)" stroke-width="5" fill="none"/>
        <path d="M-60 140 Q-66 -40 0 -46 Q66 -40 60 140 Z" fill="var(--muted)"/><path d="M-56 10 Q0 50 56 0 M-56 30 Q0 -10 56 30" stroke="var(--c2)" stroke-width="22" fill="none" stroke-linecap="round"/></svg>`, { cls: 'mb-p' }) +
    [0, 1, 2, 3].map(i => api.at(0, 0, `<div class="tag ${i % 2 ? 'c1' : 'paper'}" style="font-size:${42 * k}px">${R.esc(p.blast || '')}</div>`, { cls: 'mb-w' })).join('') +
    api.at(L.x(0.3), L.y(0.08), R.tag(p.blast || '', 66 * k, 'c1'), { cls: 'mb-t1', idle: 'sway' }) +
    api.at(L.x(0.7), L.y(0.95), R.tag(p.unheard || '', 66 * k, 'bad'), { cls: 'mb-t2', idle: 'wobble' });
  return t => {
    api.tw(q(root, '.mb-m .a'), t, api.K.pop(api.start, 0.4, { o: 0, s: 0.3, r: -10 }));
    q(root, '.mb-m .i').style.transform = `translateX(${(t > tB ? -6 * Math.abs(Math.sin(t * 16)) : 0).toFixed(1)}px)`;
    api.tw(q(root, '.mb-p .a'), t, api.K.pop(api.start + 0.15, 0.4, { o: 0, s: 0.3 }));
    qa(root, '.mb-arc').forEach((a, i) => { const c = ((t - tB) * 2 - i * 0.3) % 1; a.style.opacity = t > tB ? Math.max(0, 1 - c) : 0; a.style.transform = `translateX(${(c * 80 * k).toFixed(1)}px)`; });
    qa(root, '.mb-w').forEach((w, i) => {      // word pills fly at the person and bounce back off
      const a0 = tB + 0.2 + i * 0.45, u = Math.max(0, t - a0);
      const fly = Math.min(1, u / 0.5), back = Math.max(0, u - 0.5);
      const x = L.x(0.38) + (L.x(0.66) - L.x(0.38)) * fly - back * 500 * k, y = L.y(0.38 + i * 0.07) - (back > 0 ? 240 * k * back - 300 * k * back * back : 0);
      w.style.left = x + 'px'; w.style.top = y + 'px';
      api.tw(q(w, '.a'), t, [[a0 - 0.01, { o: 0 }], [a0, { o: 1 }], [a0 + 0.5, { r: 0 }], [a0 + 1.1, { o: 0, r: -60 }, 'in']]);
    });
    api.tw(q(root, '.mb-t1 .a'), t, api.K.pop(tB, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.mb-t2 .a'), t, api.K.slam(tU - 0.05, 0.4));
  };
});
