/* @scene {"type":"key_unlock","tags":["one question","objection","unlock","price"],"layout":"padlock-center-key-from-left","metaphor":"the objection is a padlock; one question is the key that turns and pops it open","assets":["padlock","key","question banner"]} */
// {lock, keyAt, turnAt, question}
RM.def('key_unlock', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tK = api.T(p.keyAt ?? api.start), tT = api.T(p.turnAt), cx = L.cx, cy = L.y(0.62);
  const lock = `<svg width="${440 * k}" height="${520 * k}" viewBox="-110 -150 220 260" overflow="visible">
      <path class="ku-sh" d="M-60 -20 V-80 A60 60 0 0 1 60 -80 V-20" fill="none" stroke="var(--muted)" stroke-width="26"/>
      <rect x="-100" y="-30" width="200" height="140" rx="26" fill="var(--c1)"/><circle cx="0" cy="30" r="20" fill="var(--c2)"/><rect x="-7" y="30" width="14" height="40" rx="6" fill="var(--c2)"/></svg>`;
  const key = `<svg width="${420 * k}" height="${150 * k}" viewBox="0 -50 300 100" overflow="visible"><ellipse cx="40" cy="0" rx="38" ry="38" fill="var(--acc)"/><ellipse cx="40" cy="0" rx="16" ry="16" fill="var(--paper)"/>
      <rect x="74" y="-10" width="210" height="20" rx="8" fill="var(--acc)"/><rect x="220" y="10" width="20" height="26" fill="var(--acc)"/><rect x="254" y="10" width="20" height="18" fill="var(--acc)"/></svg>`;
  root.innerHTML = api.at(cx, cy, lock, { cls: 'ku-l' }) +
    api.at(cx, cy + 40 * k, `<div class="big" style="font-size:${74 * k}px;color:var(--on-c1)">${R.esc(p.lock || '')}</div>`, { cls: 'ku-lt' }) +
    api.at(0, 0, key, { cls: 'ku-k' }) +
    api.at(L.cx, L.y(0.12), `<div class="card ku-q" style="width:${L.w * 0.94}px;padding:.35em .6em;text-align:center;font-family:var(--f-display);font-weight:900;font-size:${64 * k}px;line-height:1.1">${R.esc(p.question || '')}</div>`, { cls: 'ku-qq', idle: 'float', amp: 0.4 });
  const kk = q(root, '.ku-k');
  return t => {
    api.tw(q(root, '.ku-l .a'), t, api.K.drop(api.start, 0.5, -400 * k).concat([[tT + 0.3, {}], [tT + 0.45, { s: 1.06 }, 'out'], [tT + 0.6, { s: 1 }, 'io']]));
    api.tw(q(root, '.ku-lt .a'), t, api.K.pop(api.start + 0.3, 0.4, { o: 0, s: 0.3 }));
    const ins = api.prog(t, tK - 0.1, tK + 0.6, 'io');
    kk.style.left = (L.x(-0.1) + (cx - 170 * k - L.x(-0.1)) * ins) + 'px'; kk.style.top = (cy + 30 * k) + 'px';
    api.tw(q(kk, '.a'), t, [[tK - 0.15, { o: 0 }], [tK, { o: 1 }]]);
    q(kk, '.m').style.transform = `rotateX(${(80 * api.prog(t, tT - 0.1, tT + 0.25, 'io')).toFixed(1)}deg)`;
    q(root, '.ku-sh').setAttribute('transform', `translate(${(36 * api.prog(t, tT + 0.2, tT + 0.45, 'back')).toFixed(1)} ${(-40 * api.prog(t, tT + 0.15, tT + 0.4, 'back')).toFixed(1)})`);
    api.tw(q(root, '.ku-qq .a'), t, api.K.pop(tK, 0.45, { o: 0, s: 0.4, y: -60 * k }));
  };
});
