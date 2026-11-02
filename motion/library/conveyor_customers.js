/* @scene {"type":"conveyor_customers","tags":["sell and forget","next customer","no follow up","churn"],"layout":"conveyor-belt-bottom-seller-right","metaphor":"customers ride a conveyor belt; the seller stamps each one 'sold' and already looks for the next, while the earlier ones drop off the end","assets":["conveyor belt with rollers","customer figures","rubber stamp","seller figure"]} */
// {silent, silentAt, next, nextAt}
RM.def('conveyor_customers', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const tS = api.T(p.silentAt ?? api.start), tN = api.T(p.nextAt), N = 6, by = L.y(0.72), speed = 260 * k;
  const fig = c => `<svg width="${110 * k}" height="${170 * k}" viewBox="-40 -60 80 124"><circle cx="0" cy="-38" r="18" fill="${c}"/><path d="M-26 60 Q-28 -10 0 -14 Q28 -10 26 60 Z" fill="${c}"/><path d="M14 0 h24 l-4 30 h-18 z" fill="var(--acc)"/></svg>`;
  root.innerHTML = `<div style="position:absolute;left:${L.x0 - 20 * k}px;top:${by}px;width:${L.w * 0.86}px;height:${70 * k}px;border-radius:${35 * k}px;background:var(--c2)"></div>` +
    Array.from({ length: 12 }, (_, i) => `<div class="cc-roll" style="position:absolute;left:${L.x0 + i * L.w * 0.072}px;top:${by + 10 * k}px;width:${50 * k}px;height:${50 * k}px;border-radius:50%;background:var(--muted);border:${6 * k}px dashed var(--c1l)"></div>`).join('') +
    Array.from({ length: N }, (_, i) => api.at(0, 0, `<div style="position:relative">${fig(['var(--c1)', 'var(--bad)', 'var(--c1l)'][i % 3])}<div class="cc-st" style="position:absolute;left:${-30 * k}px;top:${20 * k}px;font-family:var(--f-display);font-weight:900;font-size:${30 * k}px;color:var(--bad);border:${4 * k}px solid var(--bad);padding:0 ${6 * k}px;transform:rotate(-14deg);opacity:0">✓</div></div>`, { cls: 'cc-f' })).join('') +
    api.at(L.x(0.88), L.y(0.5), `<svg width="${220 * k}" height="${360 * k}" viewBox="-60 -110 120 200" overflow="visible"><circle cx="0" cy="-80" r="28" fill="var(--c1l)" stroke="var(--c2)" stroke-width="5"/>
        <path d="M-42 90 Q-46 -36 0 -42 Q46 -36 42 90 Z" fill="var(--acc)"/><g class="cc-arm"><path d="M-30 -20 L-80 10" stroke="var(--acc)" stroke-width="18" stroke-linecap="round"/><rect x="-104" y="0" width="40" height="34" rx="6" fill="var(--bad)"/></g></svg>`, { cls: 'cc-sel' }) +
    api.at(L.x(0.3), L.y(0.12), R.tag(p.silent || '', 62 * k, 'bad'), { cls: 'cc-t1', idle: 'sway' }) +
    api.at(L.x(0.66), L.y(0.26), R.tag(p.next || '', 64 * k, 'c1'), { cls: 'cc-t2', idle: 'wobble' });
  const fs = qa(root, '.cc-f'), span = L.w * 0.86, endX = L.x0 - 20 * k + span;
  return t => {
    const run = (t - api.start) * speed;
    qa(root, '.cc-roll').forEach(r => r.style.transform = `rotate(${(run * 1.2) % 360}deg)`);
    fs.forEach((f, i) => {
      const x = endX - ((run + i * span / N) % span), drop = x > endX - 60 * k ? 0 : 0;
      const along = (run + i * span / N) % span, xx = L.x0 + span - 20 * k - along;      // they move right-to-left towards the seller? no: left-to-right
      const px = L.x0 - 20 * k + along, fall = Math.max(0, px - (endX - 40 * k)) / (60 * k);
      f.style.left = px + 'px'; f.style.top = (by - 85 * k + 400 * k * fall * fall) + 'px';
      api.tw(q(f, '.a'), t, [[api.start + i * 0.05, { o: 0 }], [api.start + 0.3 + i * 0.05, { o: 1 }]]);
      q(f, '.cc-st').style.opacity = px > L.x(0.62) ? 1 : 0;
      q(f, '.i').style.transform = `rotate(${(fall * 60).toFixed(1)}deg)`;
    });
    q(root, '.cc-arm').setAttribute('transform', `rotate(${(14 * Math.max(0, Math.sin(t * 6))).toFixed(1)} -30 -20)`);
    api.tw(q(root, '.cc-sel .a'), t, api.K.pop(api.start + 0.1, 0.4, { o: 0, s: 0.3 }));
    q(root, '.cc-sel .i').style.transform = `scaleX(${t > tN ? -1 : 1})`;
    api.tw(q(root, '.cc-t1 .a'), t, api.K.pop(tS, 0.4, { o: 0, s: 0.3, r: -8 }));
    api.tw(q(root, '.cc-t2 .a'), t, api.K.pop(tN - 0.05, 0.4, { o: 0, s: 0.3, r: 8 }));
  };
});
