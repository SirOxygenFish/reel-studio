/* @scene {"type":"spotlight_question","tags":["the question","price objection","spotlight","key words"],"layout":"stage-spotlight-text","metaphor":"his question appears word by word on a dark stage under a spotlight; the key words get circled and underlined","assets":["stage floor","spotlight cone","hand-drawn circle","underline"]} */
// {text, circle:[words], underline:[words]}
RM.def('spotlight_question', (api, root) => {
  const { p, L } = api, k = L.k, R = window.RMK, q = R.q, qa = R.qa;
  const text = p.text || '', wt = api.times(text, api.start, api.end), toks = text.split(/\s+/);
  const norm = s => s.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
  const circ = (p.circle || []).map(norm), und = (p.underline || []).map(norm);
  root.innerHTML = `<div class="sq-cone" style="position:absolute;left:${L.cx - L.w * 0.55}px;top:${L.y0 - 160 * k}px;width:${L.w * 1.1}px;height:${L.h * 1.05}px;
        background:radial-gradient(ellipse 60% 100% at 50% 0%, rgba(255,250,235,.32), transparent 72%);clip-path:polygon(40% 0,60% 0,100% 100%,0 100%)"></div>
      <div style="position:absolute;left:${L.x0}px;top:${L.y(0.86)}px;width:${L.w}px;height:${L.h * 0.14}px;border-radius:50%;background:radial-gradient(closest-side,rgba(255,250,235,.25),transparent)"></div>` +
    api.at(L.cx, L.y(0.45), `<div class="sq-txt" style="width:${L.w * 0.92}px;text-align:center;font-family:var(--f-display);font-weight:900;font-size:${96 * k}px;line-height:1.12;color:var(--text)">${toks.map((w, i) =>
        `<span class="sq-w${circ.includes(norm(w)) ? ' sq-c' : ''}${und.includes(norm(w)) ? ' sq-u' : ''}" style="display:inline-block;position:relative;margin:0 .12em">${R.esc(w)}</span>`).join(' ')}</div>`, { cls: 'sq-t' });
  const tx = q(root, '.sq-txt'); let fs = 96 * k; while (fs > 40 && tx.getBoundingClientRect().height > L.h * 0.7) { fs -= 3; tx.style.fontSize = fs + 'px'; }
  qa(root, '.sq-c').forEach(w => w.insertAdjacentHTML('beforeend', `<svg style="position:absolute;left:-12%;top:-22%;width:124%;height:144%;overflow:visible" viewBox="0 0 100 100" preserveAspectRatio="none"><path class="sq-cp" d="M50 4 C 90 2, 104 40, 96 64 C 88 92, 30 100, 10 80 C -6 62, 6 14, 56 8" fill="none" stroke="var(--bad)" stroke-width="5" vector-effect="non-scaling-stroke" stroke-linecap="round"/></svg>`));
  qa(root, '.sq-u').forEach(w => w.insertAdjacentHTML('beforeend', `<svg style="position:absolute;left:0;bottom:-14%;width:100%;height:20%;overflow:visible" viewBox="0 0 100 10" preserveAspectRatio="none"><path class="sq-up" d="M0 5 Q 50 10 100 3" fill="none" stroke="var(--acc)" stroke-width="7" vector-effect="non-scaling-stroke" stroke-linecap="round"/></svg>`));
  const ws = qa(root, '.sq-w');
  return t => {
    q(root, '.sq-cone').style.opacity = (0.6 + 0.4 * api.prog(t, api.start, api.start + 0.4, 'out')) * (0.9 + 0.1 * Math.sin(t * 3));
    ws.forEach((w, i) => {
      api.tw(w, t, [[wt[i] - 0.06, { o: 0.12, y: 30 * k }], [wt[i] + 0.2, { o: 1, y: 0 }, 'back']]);
      const c = q(w, '.sq-cp'); if (c) R.draw(c, api.prog(t, wt[i] + 0.15, wt[i] + 0.6, 'io'));
      const u = q(w, '.sq-up'); if (u) R.draw(u, api.prog(t, wt[i] + 0.1, wt[i] + 0.45, 'out'));
    });
  };
});
