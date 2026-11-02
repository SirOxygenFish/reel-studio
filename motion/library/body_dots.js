/* @scene {"type":"body_dots","tags":["everywhere in your body","blood vessels","tendons","ligaments","bones"],"layout":"tall-body-outline-center-dots-light-with-labels-both-sides","metaphor":"a plain body outline: a dot lights up with a line to its label for each place he names","assets":["plain body outline","label lines"]} */
// {items:[{t,at,x,y}]}
RM.def('body_dots', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const I = p.items.map(c => ({ ...c, tt: api.T(c.at) })), S = 660 * k, cx = L.cx, cy = L.y(0.5), pt = c => [cx + c.x * S * 0.4, cy + c.y * S * 0.5];
  root.innerHTML = api.at(cx, cy, api.icon('ph-fill:person-arms-spread', S, 'var(--c2)'), { cls: 'bd-f' }) +
    `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1">${I.map(() => `<line class="bd-l" stroke="var(--c1l)" stroke-width="${6 * k}"/><circle class="bd-r" fill="none" stroke="var(--acc)" stroke-width="${8 * k}"/><circle class="bd-d" r="${20 * k}" fill="var(--acc)"/>`).join('')}</svg>` +
    I.map(c => api.at(L.x(c.x < 0 ? 0.2 : 0.8), cy + c.y * S * 0.7, R.tag(c.t, 54 * k, 'paper'), { cls: 'bd-t' })).join('');
  const ls = qa(root, '.bd-l'), rs = qa(root, '.bd-r'), ds = qa(root, '.bd-d'), ts = qa(root, '.bd-t');
  return t => {
    api.tw(q(root, '.bd-f .a'), t, api.K.rise(api.start, 0.3, 300 * k));
    I.forEach((c, i) => { const [x, y] = pt(c), u = api.prog(t, c.tt - 0.05, c.tt + 0.2, 'back'), on = u > 0, tx = L.x(c.x < 0 ? 0.2 : 0.8), ty = cy + c.y * S * 0.7, a = (t - c.tt) * 2.4;
      ds[i].setAttribute('cx', x); ds[i].setAttribute('cy', y); ds[i].style.visibility = on ? 'visible' : 'hidden';
      ls[i].setAttribute('x1', x); ls[i].setAttribute('y1', y); ls[i].setAttribute('x2', x + (tx - x) * Math.min(1, u)); ls[i].setAttribute('y2', y + (ty - y) * Math.min(1, u)); ls[i].style.visibility = on ? 'visible' : 'hidden';
      rs[i].setAttribute('cx', x); rs[i].setAttribute('cy', y); rs[i].setAttribute('r', ((20 + 30 * (a % 1)) * k).toFixed(1)); rs[i].style.opacity = on ? (1 - a % 1).toFixed(3) : 0;
      api.tw(q(ts[i], '.a'), t, api.K.pop(c.tt - 0.02, 0.26, { o: 0, s: 0.3 })); });
  };
});
