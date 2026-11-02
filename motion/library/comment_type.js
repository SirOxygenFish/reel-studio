/* @scene {"type":"comment_type","tags":["write in the comments","call to action"],"layout":"single-comment-field-center-letters-typed","metaphor":"one big comment field: her keyword types itself letter by letter, the send arrow fills and a paper plane flies off","assets":["comment field","typing caret","paper plane"]} */
// {write, writeAt, word, wordAt}
RM.def('comment_type', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q;
  const tW = api.T(p.writeAt), tK = api.T(p.wordAt), w = p.word || '', cx = L.cx, cy = L.y(0.5), FW = L.w * 0.94, FH = 230 * k;
  const dur = Math.min(0.5, 0.06 * w.length), tE = tK + dur;
  root.innerHTML = `<div class="ct-f" style="position:absolute;left:${cx - FW / 2}px;top:${cy - FH / 2}px;width:${FW}px;height:${FH}px;border-radius:${FH / 2}px;background:var(--paper);box-shadow:var(--sh)">
      <div class="ct-x" style="position:absolute;left:${64 * k}px;top:50%;transform:translateY(-50%);font-family:var(--f-display);font-weight:800;font-size:${96 * k}px;color:var(--ink);white-space:nowrap"></div>
      <div class="ct-c" style="position:absolute;top:22%;height:56%;width:${8 * k}px;background:var(--acc)"></div>
      <div class="ct-b" style="position:absolute;right:${28 * k}px;top:50%;margin-top:${-85 * k}px;width:${170 * k}px;height:${170 * k}px;border-radius:50%;background:var(--c2)"></div></div>` +
    api.at(cx + FW / 2 - 113 * k, cy, api.icon('ph-fill:paper-plane-tilt', 110 * k, 'var(--paper)'), { cls: 'ct-p' }) +
    api.at(cx, L.y(0.2), R.tag(p.write || '', 76 * k, 'c1'), { cls: 'ct-t', idle: 'sway' });
  const x = q(root, '.ct-x'), c = q(root, '.ct-c'), b = q(root, '.ct-b'), f = q(root, '.ct-f'), pl = q(root, '.ct-p');
  return t => {
    const inn = api.prog(t, api.start, api.start + 0.24, 'back'); f.style.transform = `translateY(${((1 - inn) * 500 * k).toFixed(1)}px) scale(${(0.9 + 0.1 * inn).toFixed(3)})`;
    const n = Math.round(api.clamp((t - tK) / dur, 0, 1) * w.length); if (x.textContent.length !== n) x.textContent = w.slice(0, n);
    c.style.left = (64 * k + x.getBoundingClientRect().width / (f.getBoundingClientRect().width / FW || 1) + 8 * k) + 'px'; c.style.opacity = Math.sin(t * 12) > -0.3 ? 1 : 0.15;
    b.style.background = t >= tE ? 'var(--acc)' : 'var(--c2)';
    const go = api.prog(t, tE + 0.1, tE + 0.5, 'in'); api.tw(q(pl, '.a'), t, api.K.pop(api.start + 0.12, 0.24, { o: 0, s: 0.3 }));
    q(pl, '.i').style.transform = `translate(${(go * 900 * k).toFixed(1)}px,${(-go * 620 * k).toFixed(1)}px) rotate(${(go * 20).toFixed(1)}deg)`;
    api.tw(q(root, '.ct-t .a'), t, api.K.pop(tW - 0.04, 0.26, { o: 0, s: 0.3, r: -4 }));
  };
});
