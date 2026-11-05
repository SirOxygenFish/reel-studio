/* Reel Studio tutorials: clean generic UI drawings (no logos, no copied icons) and a small action player.
   Every scene is a pure function of t, like all ReelsMotion scenes: frames render in parallel and out of order.
   A scene = a screen built from params + p.acts, a list of timed actions (seconds from the scene start):
     {t, move: key, d}       pointer (PC) or finger (phone) glides to the element data-k=key
     {t, click: key}         press + soft ripple on it            {t, toggle: key}   a switch slides on
     {t, show: key, d}       element rises in                     {t, hide: key, d}  element fades out
     {t, sel: key}           element gets the selected look       {t, scroll: key, y, d}  content scrolls up by y px
     {t, type: key, text, d} letters appear one by one            {t, ring: key, d}  a soft highlight ring around it
   p.caps = [[t, text], ...] the caption above the screen; p.step = the step number in its badge.
   Sound cues (soft ticks on clicks) are collected by scripts/tutorials.py from the same actions. */
(function () {
  const R = window.RMK, E = RM.E;
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const P = (t, a, d, ease = 'io') => (d <= 0 ? (t >= a ? 1 : 0) : E[ease](clamp((t - a) / d)));
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  const CSS = `
  .tut { position:absolute; inset:0; font-family:var(--f-body); color:var(--ink); }
  .tut .cap { position:absolute; display:flex; align-items:center; gap:.55em; background:var(--paper); border-radius:var(--r-l);
     box-shadow:var(--sh); padding:.5em .8em; font-family:var(--f-head); font-weight:800; line-height:1.18; color:var(--ink); }
  .tut .cap .badge { font-size:1.15em; width:1.6em; height:1.6em; background:var(--acc); color:var(--on-acc); font-weight:900; }
  .tut .cap .ctx { position:relative; flex:1; min-height:1.18em; }
  .tut .cap .ct { position:absolute; left:0; right:0; top:50%; transform:translateY(-50%); }
  .tut .stage { position:absolute; }
  .tut [data-k] { transform-origin:center; }
  /* desktop window */
  .win { position:absolute; inset:0; background:var(--paper); border-radius:22px; box-shadow:var(--sh); overflow:hidden; display:flex; flex-direction:column; }
  .win .bar { height:56px; flex:none; display:flex; align-items:center; gap:14px; padding:0 22px; background:var(--c1x); border-bottom:2px solid var(--line); }
  .win .bar .dot { width:16px; height:16px; border-radius:50%; background:var(--dim); flex:none; }
  .win .bar .wt { font-size:26px; font-weight:700; color:var(--muted); margin-left:10px; }
  .win .body { flex:1; display:flex; min-height:0; position:relative; }
  .tside { width:330px; flex:none; background:var(--c1x); border-right:2px solid var(--line); padding:22px 16px; display:flex; flex-direction:column; gap:10px; position:relative; }
  .item { font-size:29px; font-weight:600; color:var(--text); padding:12px 18px; border-radius:14px; display:flex; align-items:center; gap:14px; white-space:nowrap; }
  .item.sel, .item.on { background:var(--paper); box-shadow:0 2px 0 var(--line); color:var(--ink); font-weight:800; }
  .item .gl { width:30px; height:30px; flex:none; border-radius:9px; background:var(--c1l); }
  .tph { height:22px; border-radius:11px; background:var(--line); opacity:.55; }
  .main { flex:1; padding:34px 46px; position:relative; overflow:hidden; }
  .h1 { font-size:44px; font-weight:800; font-family:var(--f-head); color:var(--ink); }
  .h2 { font-size:34px; font-weight:800; font-family:var(--f-head); color:var(--ink); margin:30px 0 10px; }
  .row { display:flex; align-items:center; justify-content:space-between; gap:30px; padding:22px 26px; border-radius:18px; background:var(--c1x); margin:12px 0; }
  .row .rl { font-size:30px; font-weight:700; color:var(--ink); }
  .row .rd { font-size:22px; color:var(--muted); margin-top:4px; }
  .sw { width:92px; height:52px; flex:none; border-radius:26px; background:var(--dim); position:relative; }
  .sw .kn { position:absolute; left:6px; top:6px; width:40px; height:40px; border-radius:50%; background:var(--paper); box-shadow:0 2px 4px var(--hard-shadow); }
  .sw .onbg { position:absolute; inset:0; border-radius:26px; background:var(--good); opacity:0; }
  .tagoff { font-size:24px; font-weight:800; color:var(--bad); background:var(--paper); border:3px solid var(--bad); border-radius:12px; padding:4px 12px; white-space:nowrap; }
  .tbtn { display:inline-flex; align-items:center; justify-content:center; gap:12px; font-size:30px; font-weight:800; padding:16px 28px; border-radius:16px;
         background:var(--acc); color:var(--on-acc); white-space:nowrap; }
  .tbtn.ghost { background:var(--paper); color:var(--ink); border:3px solid var(--line); }
  .menu { position:absolute; background:var(--paper); border-radius:18px; box-shadow:var(--sh); border:2px solid var(--line); padding:10px; width:300px; }
  .menu .item { font-size:28px; }
  .user { display:flex; align-items:center; gap:14px; padding:12px 14px; border-radius:16px; font-size:28px; font-weight:700; color:var(--ink); }
  .user .av { width:50px; height:50px; border-radius:50%; background:var(--c1); color:var(--on-c1); display:flex; align-items:center; justify-content:center; font-weight:900; font-size:26px; flex:none; }
  .dlg { position:absolute; background:var(--paper); border-radius:20px; box-shadow:var(--sh); border:2px solid var(--line); padding:26px 30px; }
  .fold { display:flex; align-items:center; gap:18px; font-size:30px; font-weight:600; padding:12px 16px; border-radius:12px; color:var(--ink); }
  .fold .fi { width:46px; height:34px; border-radius:6px 6px 8px 8px; background:var(--acc2); flex:none; position:relative; }
  .fold .fi:before { content:''; position:absolute; left:0; top:-7px; width:20px; height:10px; border-radius:4px 4px 0 0; background:var(--acc2); }
  .fold.sel { background:var(--c1x); outline:3px solid var(--c1); }
  .chip { display:inline-flex; align-items:center; gap:12px; font-size:28px; font-weight:700; padding:12px 20px; border-radius:999px; background:var(--c1x); border:2px solid var(--line); color:var(--ink); }
  .compose { position:absolute; left:46px; right:46px; bottom:40px; border-radius:22px; border:3px solid var(--line); background:var(--paper); padding:22px 26px; }
  .compose .hint { font-size:28px; color:var(--muted); margin-bottom:18px; }
  .ptr { position:absolute; left:0; top:0; width:46px; height:60px; z-index:20; pointer-events:none; }
  .rip { position:absolute; width:90px; height:90px; margin:-45px 0 0 -45px; border-radius:50%; border:6px solid var(--acc); z-index:19; opacity:0; }
  .son1 { position:absolute; border:7px solid var(--acc); border-radius:20px; opacity:0; z-index:17; pointer-events:none; }
  .hlr { position:absolute; border:5px solid var(--acc); border-radius:20px; box-shadow:0 0 0 6px var(--acc-soft); z-index:18; opacity:0; pointer-events:none; }
  /* phone */
  .tphone { position:absolute; inset:0; border-radius:86px; background:var(--phone); padding:22px; box-shadow:var(--sh); }
  .tphone .scr { position:absolute; inset:22px; border-radius:66px; overflow:hidden; background:var(--paper); }
  .tphone .pill { position:absolute; left:50%; top:40px; width:150px; height:40px; margin-left:-75px; border-radius:20px; background:var(--phone); z-index:30; }
  .scrn { position:absolute; inset:0; padding:118px 34px 40px; display:flex; flex-direction:column; gap:22px; }
  .ptitle { font-size:52px; font-weight:800; font-family:var(--f-head); color:var(--ink); }
  .ptext { font-size:34px; color:var(--muted); line-height:1.3; }
  .pcard { background:var(--c1x); border-radius:28px; padding:26px 28px; font-size:36px; color:var(--ink); }
  .pbtn { display:flex; align-items:center; justify-content:center; font-size:40px; font-weight:800; padding:30px 20px; border-radius:26px;
          background:var(--acc); color:var(--on-acc); text-align:center; }
  .pbtn.ghost { background:var(--paper); color:var(--acc); border:4px solid var(--acc); }
  .sheet { position:absolute; left:0; right:0; bottom:0; background:var(--paper); border-radius:44px 44px 0 0; box-shadow:0 -6px 30px var(--hard-shadow);
           padding:34px 34px 60px; display:flex; flex-direction:column; gap:20px; z-index:12; }
  .sheet .grab { width:90px; height:10px; border-radius:5px; background:var(--line); margin:0 auto 6px; }
  .lrow { display:flex; align-items:center; gap:24px; font-size:38px; font-weight:600; color:var(--ink); padding:22px 24px; border-radius:22px; background:var(--c1x); }
  .lrow .gl { width:56px; height:56px; border-radius:14px; background:var(--c1l); flex:none; }
  .lrow.sel, .lrow.on { outline:4px solid var(--acc); }
  .safbar { position:absolute; left:0; right:0; bottom:0; height:150px; background:var(--c1x); border-top:2px solid var(--line);
            display:flex; align-items:center; justify-content:space-around; padding-bottom:24px; z-index:5; }
  .safbar .sg { width:58px; height:58px; border-radius:14px; background:var(--dim); opacity:.6; }
  .share { width:66px; height:76px; position:relative; }
  .share .bx { position:absolute; left:6px; right:6px; bottom:0; height:46px; border:6px solid var(--c1); border-top:0; border-radius:0 0 12px 12px; }
  .share .st { position:absolute; left:30px; top:4px; width:6px; height:48px; background:var(--c1); border-radius:3px; }
  .share .hd { position:absolute; left:19px; top:2px; width:28px; height:28px; border-left:6px solid var(--c1); border-top:6px solid var(--c1); transform:rotate(45deg); border-radius:3px 0 0 0; }
  .urlbar { position:absolute; left:34px; right:34px; top:96px; height:76px; border-radius:22px; background:var(--c1x); font-size:30px; color:var(--muted);
            display:flex; align-items:center; justify-content:center; z-index:5; }
  .grid { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:34px 22px; padding:150px 34px 0; }
  .app { display:flex; flex-direction:column; align-items:center; gap:12px; font-size:26px; font-weight:600; color:var(--ink); text-align:center; min-width:0; }
  .app .tph { width:80% !important; }
  .app .ai { width:116px; height:116px; border-radius:28px; background:var(--dim); opacity:.55; }
  .app .ai.me { opacity:1; background:var(--c1); display:flex; align-items:center; justify-content:center; }
  .app .ai.cl { opacity:1; background:var(--acc); display:flex; align-items:center; justify-content:center; }
  .bub { width:70px; height:54px; border-radius:22px; background:var(--paper); position:relative; }
  .bub:after { content:''; position:absolute; left:12px; bottom:-12px; border:12px solid transparent; border-top-color:var(--paper); border-left-color:var(--paper); }
  .reelic { width:66px; height:66px; border-radius:16px; border:7px solid var(--paper); position:relative; }
  .reelic:after { content:''; position:absolute; left:20px; top:13px; border-left:22px solid var(--paper); border-top:13px solid transparent; border-bottom:13px solid transparent; }
  .thumbs { display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; }
  .th { aspect-ratio:9/16; border-radius:10px; background:linear-gradient(160deg, var(--c1l), var(--c1)); position:relative; }
  .th.b { background:linear-gradient(160deg, var(--acc-soft), var(--acc2)); } .th.c { background:linear-gradient(160deg, var(--c1x), var(--disc-a)); }
  .th .du { position:absolute; right:10px; bottom:8px; font-size:22px; font-weight:700; color:var(--paper); }
  .th .ck { position:absolute; right:10px; top:10px; width:46px; height:46px; border-radius:50%; background:var(--acc); border:4px solid var(--paper); opacity:0;
            display:flex; align-items:center; justify-content:center; }
  .th .ck:after { content:''; width:16px; height:9px; border-left:5px solid var(--paper); border-bottom:5px solid var(--paper); transform:rotate(-45deg) translate(1px,-2px); }
  .th.sel .ck { opacity:1; }
  .th.newv { outline:8px solid var(--acc); }
  .bar2 { height:16px; border-radius:8px; background:var(--line); overflow:hidden; } .bar2 > div { height:100%; width:0; background:var(--good); }
  .tmsg { max-width:80%; font-size:36px; line-height:1.3; padding:22px 28px; border-radius:30px; }
  .tmsg.me { align-self:flex-end; background:var(--acc); color:var(--on-acc); border-bottom-right-radius:10px; }
  .tmsg.it { align-self:flex-start; background:var(--c1x); color:var(--ink); border-bottom-left-radius:10px; }
  .inp { position:absolute; left:30px; right:30px; bottom:40px; display:flex; align-items:center; gap:18px; background:var(--c1x); border-radius:40px; padding:18px 18px 18px 34px; font-size:38px; color:var(--ink); z-index:5; }
  .inp .tx { flex:1; min-height:48px; }
  .inp .go { width:76px; height:76px; border-radius:50%; background:var(--acc); flex:none; position:relative; }
  .inp .go:after { content:''; position:absolute; left:26px; top:22px; border-bottom:22px solid var(--paper); border-left:13px solid transparent; border-right:13px solid transparent; }
  .tabs { display:flex; gap:14px; } .tab { font-size:36px; font-weight:800; padding:14px 30px; border-radius:999px; background:var(--c1x); color:var(--muted); }
  .tab.sel, .tab.on { background:var(--ink); color:var(--paper); }
  .sess { display:flex; align-items:center; gap:22px; padding:26px 26px; border-radius:26px; background:var(--c1x); font-size:38px; font-weight:700; color:var(--ink); }
  .sess .pc { width:70px; height:50px; border-radius:8px; border:6px solid var(--c1); flex:none; position:relative; }
  .sess .pc:after { content:''; position:absolute; left:14px; right:14px; bottom:-18px; height:6px; background:var(--c1); border-radius:3px; }
  .sess .live { width:24px; height:24px; border-radius:50%; background:var(--good); flex:none; margin-left:auto; }
  .sess.sel, .sess.on { outline:4px solid var(--acc); }
  .banner { position:absolute; left:26px; right:26px; top:96px; z-index:25; background:var(--paper); border-radius:30px; box-shadow:var(--sh); padding:24px 28px;
            display:flex; align-items:center; gap:22px; font-size:34px; font-weight:800; color:var(--ink); }
  .banner .sq { width:70px; height:70px; border-radius:18px; background:var(--c1); flex:none; }
  .tick { width:62px; height:62px; border-radius:50%; background:var(--good); flex:none; position:relative; margin-left:auto; }
  .tick:after { content:''; position:absolute; left:18px; top:18px; width:22px; height:12px; border-left:6px solid var(--paper); border-bottom:6px solid var(--paper); transform:rotate(-45deg); }
  .act { background:var(--paper); border:3px solid var(--line); border-radius:24px; padding:24px 26px; font-size:36px; font-weight:800; color:var(--ink);
         display:flex; align-items:center; gap:20px; }
  .act .ag { width:58px; height:58px; border-radius:14px; flex:none; background:var(--c1); }
  .act .ag.b { background:var(--good); }
  .field { border-bottom:4px solid var(--c1); font-size:44px; font-weight:800; padding:10px 4px; min-height:74px; color:var(--ink); }
  .tend { position:absolute; display:flex; flex-direction:column; gap:26px; }
  .tend .er { display:flex; align-items:center; gap:28px; background:var(--paper); border-radius:26px; box-shadow:var(--sh); padding:26px 34px;
             font-family:var(--f-head); font-weight:800; color:var(--ink); }
  .tend .er .badge { background:var(--good); color:var(--paper); }
  .ttl { position:absolute; text-align:center; font-family:var(--f-display); font-weight:var(--w-display); color:var(--title-c); line-height:1.05; }
  .tsub { position:absolute; text-align:center; font-family:var(--f-head); font-weight:800; color:var(--title-2); line-height:1.2; }
  .sk { position:absolute; }
  `;
  if (!document.getElementById('tut-css')) {
    const s = document.createElement('style'); s.id = 'tut-css'; s.textContent = CSS; document.head.appendChild(s);
  }

  const W = () => RM.CFG.W, H = () => RM.CFG.H, wide = () => W() > H();

  // the frame every scene shares: caption card on top, the stage (screen drawing) below
  function frame(p, inner, o = {}) {
    const wd = wide();
    const cap = wd ? { l: 110, t: 46, w: W() - 220, fs: 50 } : { l: 56, t: 120, w: W() - 112, fs: 58 };
    const st = o.stage || (wd ? { l: 150, t: 236, w: W() - 300, h: H() - 236 - 44 } : { l: 180, t: 540, w: 720, h: 1340 });
    const caps = (p.caps || []).map(([t, s], i) => `<div class="ct" data-ci="${i}">${esc(s)}</div>`).join('');
    return `<div class="tut">` +
      (p.caps && p.caps.length ? `<div class="cap a" style="left:${cap.l}px;top:${cap.t}px;width:${cap.w}px;font-size:${cap.fs}px">` +
        (p.step ? `<div class="badge">${esc(p.step)}</div>` : '') + `<div class="ctx">${caps}</div></div>` : '') +
      `<div class="stage a" style="left:${st.l}px;top:${st.t}px;width:${st.w}px;height:${st.h}px">${inner}` +
      `<div class="son1"></div><div class="son1"></div><div class="son1"></div><div class="hlr"></div><div class="rip"></div>${o.pointer === false ? '' : wd ? POINTER : '<div class="rip fing round"></div>'}</div></div>`;
  }
  const POINTER = `<svg class="ptr" viewBox="0 0 46 60"><path d="M4 3 L4 47 L15 37 L23 56 L31 52 L23 34 L39 34 Z" fill="var(--ink)" stroke="var(--paper)" stroke-width="4" stroke-linejoin="round"/></svg>`;

  // the action player: everything below is recomputed from t alone
  function player(api, root, p, o = {}) {
    const q = s => root.querySelector(s), qa = s => [...root.querySelectorAll(s)];
    const stage = q('.stage'), acts = (p.acts || []).slice().sort((a, b) => a.t - b.t);
    const K = k => root.querySelector(`[data-k="${k}"]`);
    const ptr = q('.ptr'), fing = q('.rip.fing'), rip = q('.rip:not(.fing)'), hlr = q('.hlr'), sons = qa('.son1');
    const cts = qa('.cap .ct'), capT = (p.caps || []).map(c => c[0]);
    const cap = q('.cap'), ctx = q('.cap .ctx');
    if (cap && cts.length) {                                   // the card fits its longest caption: shrink the font a little, then size the box
      const maxH = wide() ? 2 * 1.18 : 4 * 1.18, minFs = wide() ? 46 : 54;
      let fs = parseFloat(cap.style.fontSize);
      const tallest = () => Math.max(...cts.map(c => c.offsetHeight));
      while (tallest() > maxH * fs + 2 && fs > minFs) cap.style.fontSize = (fs -= 1) + 'px';
      ctx.style.height = tallest() + 'px';
    }
    const home = o.home || (wide() ? [stage.offsetWidth * 0.62, stage.offsetHeight * 0.72] : [stage.offsetWidth * 0.7, stage.offsetHeight * 0.8]);
    // elements that rise in later start hidden
    const shows = {}, hides = {}, sels = {}, toggles = {}, scrolls = {}, types = {};
    for (const a of acts) {
      if (a.show) (shows[a.show] ||= []).push(a);
      if (a.hide) (hides[a.hide] ||= []).push(a);
      if (a.sel) (sels[a.sel] ||= []).push(a);
      if (a.toggle) (toggles[a.toggle] ||= []).push(a);
      if (a.scroll) (scrolls[a.scroll] ||= []).push(a);
      if (a.type) (types[a.type] ||= []).push(a);
    }
    function rel(el) {
      const s = stage.getBoundingClientRect(), r = el.getBoundingClientRect(), k = s.width / stage.offsetWidth || 1;
      return [(r.left - s.left) / k, (r.top - s.top) / k, r.width / k, r.height / k];
    }
    const centre = k => { const el = K(k); if (!el) return null; const [x, y, w, h] = rel(el); return [x + w / 2, y + h / 2]; };
    // pressed elements whose transform nothing else sets: reset every frame, or the press would compound frame after frame
    const pressOnly = [...new Set(acts.filter(a => a.click).map(a => a.click))].filter(k => !shows[k] && !hides[k] && !scrolls[k]).map(K).filter(Boolean);
    return function (tg) {
      const t = tg - api.start;                                   // the engine passes video time; actions are scene time
      // the screen never moves (text stays sharp); pulse rings grow out of the next thing to click instead, so a calm moment is never a frozen one
      const nx = acts.find(a => a.click && t < a.t + 0.35) || acts.filter(a => a.ring && t >= a.t - 0.01).pop() || acts.filter(a => a.click).pop();
      const tgt = nx && K(nx.click || nx.ring);
      sons.forEach((el, j) => {
        if (!tgt) { el.style.opacity = 0; return; }
        const [x, y, w, h] = rel(tgt), ph = ((t + j / 3) % 1.0), g = 10 + 85 * E.out(ph);
        Object.assign(el.style, { left: (x - g) + 'px', top: (y - g) + 'px', width: (w + 2 * g) + 'px', height: (h + 2 * g) + 'px',
                                  opacity: (0.8 * (1 - ph) * P(t, 0.2, 0.3)).toFixed(3), borderRadius: (16 + g) + 'px' });
      });
      // captions: one at a time, soft cross-fade
      cts.forEach((el, i) => {
        const a = capT[i], b = i + 1 < capT.length ? capT[i + 1] : 1e9;
        const op = P(t, a, 0.35) * (1 - P(t, b - 0.15, 0.3));
        el.style.opacity = op.toFixed(3); el.style.transform = `translateY(calc(-50% + ${((1 - P(t, a, 0.45, 'out')) * 26).toFixed(1)}px))`;
      });
      for (const [k, list] of Object.entries(scrolls)) {
        const el = K(k); if (!el) continue;
        let y = 0; for (const a of list) y += (a.y || 0) * P(t, a.t, a.d ?? 0.9);
        el.style.transform = `translateY(${(-y).toFixed(1)}px)`;
      }
      for (const k of new Set([...Object.keys(shows), ...Object.keys(hides)])) {
        const el = K(k); if (!el) continue;
        const sh = shows[k] || [], hd = hides[k] || [];
        let v = sh.length ? 0 : 1;
        for (const a of sh) v = Math.max(v, P(t, a.t, a.d ?? 0.4, 'out'));
        for (const a of hd) v = Math.min(v, 1 - P(t, a.t, a.d ?? 0.3));
        const rise = sh.length ? (1 - P(t, sh[0].t, (sh[0].d ?? 0.4) * 1.2, 'out')) : 0;
        el.style.opacity = v.toFixed(3);
        el.style.transform = (el.dataset.from === 'bottom' ? `translateY(${(rise * 100).toFixed(1)}%)` : `translateY(${(rise * 30).toFixed(1)}px)`) + (el.dataset.press ? '' : '');
        el.style.visibility = v < 0.01 ? 'hidden' : 'visible';
      }
      for (const [k, list] of Object.entries(sels)) { const el = K(k); if (el) el.classList.toggle('sel', list.some(a => t >= a.t)); }
      for (const [k, list] of Object.entries(toggles)) {
        const el = K(k); if (!el) continue;
        const u = Math.max(...list.map(a => P(t, a.t, 0.28, 'out')));
        el.querySelector('.kn').style.transform = `translateX(${(u * (el.offsetWidth - el.querySelector('.kn').offsetWidth - 12)).toFixed(1)}px)`;
        el.querySelector('.onbg').style.opacity = u.toFixed(3);
      }
      for (const [k, list] of Object.entries(types)) {
        const el = K(k); if (!el) continue;
        let s = '';
        for (const a of list) if (t >= a.t) { const n = Math.round(a.text.length * clamp((t - a.t) / (a.d ?? 0.08 * a.text.length))); s = a.text.slice(0, n); }
        el.textContent = s;
      }
      // presses: a quick scale dip on the clicked element
      pressOnly.forEach(el => { el.style.transform = ''; });
      for (const a of acts) if (a.click) {
        const el = K(a.click); if (!el) continue;
        const u = t - a.t;
        if (u >= -0.05 && u < 0.3) el.style.transform = (el.style.transform || '') + ` scale(${(1 - 0.05 * Math.sin(clamp(u / 0.25) * Math.PI)).toFixed(4)})`;
      }
      // pointer / finger path: from home, through every move target
      let pos = home.slice(), lastMove = -1;
      for (const a of acts) {
        if (!a.move || t < a.t) continue;
        const c = centre(a.move); if (!c) continue;
        const to = [c[0] + (a.dx || 0), c[1] + (a.dy || 0)];
        const u = P(t, a.t, a.d ?? 0.7, 'io');
        pos = [pos[0] + (to[0] - pos[0]) * u, pos[1] + (to[1] - pos[1]) * u]; lastMove = a.t;
      }
      const breathe = [6 * Math.sin(t * 1.3), 5 * Math.cos(t * 1.1)];             // a gentle drift: never fully still
      const px = pos[0] + breathe[0], py = pos[1] + breathe[1];
      const lastClick = acts.filter(a => a.click && t >= a.t - 0.02).pop();
      const cu = lastClick ? t - lastClick.t : 9;
      const press = cu >= 0 && cu < 0.25 ? 1 - 0.12 * Math.sin(cu / 0.25 * Math.PI) : 1;
      const vis = P(t, o.pointerIn ?? 0.15, 0.3) * (1 - P(t, o.pointerOut ?? 1e9, 0.3));
      if (ptr) {
        ptr.style.transform = `translate(${(px - 4).toFixed(1)}px, ${(py - 3).toFixed(1)}px) scale(${press.toFixed(3)})`;
        ptr.style.opacity = vis.toFixed(3);
      }
      if (fing) {                                                   // phone: a soft finger dot
        fing.style.left = px.toFixed(1) + 'px'; fing.style.top = py.toFixed(1) + 'px';
        fing.style.opacity = (vis * 0.55).toFixed(3); fing.style.transform = `scale(${(0.8 * press).toFixed(3)})`;
        fing.style.background = 'var(--acc-soft)';
      }
      if (rip) {
        if (cu >= 0 && cu < 0.6) {
          const c = centre(lastClick.click) || [px, py];
          rip.style.left = c[0].toFixed(1) + 'px'; rip.style.top = c[1].toFixed(1) + 'px';
          rip.style.opacity = (0.8 * (1 - cu / 0.6)).toFixed(3); rip.style.transform = `scale(${(0.5 + 1.3 * E.out(cu / 0.6)).toFixed(3)})`;
        } else rip.style.opacity = 0;
      }
      if (hlr) {                                                    // highlight ring: rises in, breathes, fades
        const a = acts.filter(x => x.ring && t >= x.t - 0.01).pop();
        if (a && t < a.t + (a.d ?? 2)) {
          const el = K(a.ring), [x, y, w, h] = rel(el), pad = 12;
          const v = P(t, a.t, 0.3) * (1 - P(t, a.t + (a.d ?? 2) - 0.3, 0.3)), br = 1 + 0.015 * Math.sin((t - a.t) * 5);
          Object.assign(hlr.style, { left: (x - pad) + 'px', top: (y - pad) + 'px', width: (w + 2 * pad) + 'px', height: (h + 2 * pad) + 'px',
                                     opacity: v.toFixed(3), transform: `scale(${br.toFixed(4)})` });
        } else hlr.style.opacity = 0;
      }
    };
  }

  const sw = (k, on) => `<div class="sw" data-k="${k}"><div class="onbg"></div><div class="kn round"></div></div>`;
  const win = (title, side, main) => `<div class="win"><div class="bar"><div class="dot round"></div><div class="dot round"></div><div class="dot round"></div><div class="wt">${esc(title)}</div></div>` +
    `<div class="body">${side}${main}</div></div>`;
  const phs = n => Array.from({ length: n }, (_, i) => `<div class="tph" style="width:${[78, 62, 70, 55, 66][i % 5]}%"></div>`).join('');

  // ---------- shared ----------
  RM.def('tut_title', (api, root) => {
    const p = api.p, wd = wide();
    const art = wd ? `<div class="sk a" style="left:${W() / 2 - 300}px;top:560px;width:600px;height:370px"><div class="win" style="border-radius:18px"><div class="bar"><div class="dot round"></div><div class="dot round"></div><div class="dot round"></div></div><div class="body"><div class="tside" style="width:150px"></div><div class="main">${phs(4).replace(/class="tph"/g, 'class="tph" data-ph')}</div></div></div></div>`
                   : `<div class="sk a" style="left:${W() / 2 - 210}px;top:900px;width:420px;height:850px"><div class="tphone" style="border-radius:60px;padding:16px"><div class="scr" style="inset:16px;border-radius:46px">${p.src ? `<img src="${p.src}" style="position:absolute;left:0;top:13%;width:100%">` : `<div class="scrn" style="padding-top:90px">${phs(5)}</div>`}</div><div class="pill" style="top:30px;width:110px;height:30px;margin-left:-55px"></div></div></div>`;
    root.innerHTML = `<div class="tut"><div class="ttl a" style="left:60px;right:60px;top:${wd ? 170 : 330}px;font-size:${wd ? 104 : 104}px">${esc(p.title)}</div>` +
      `<div class="tsub a" style="left:80px;right:80px;top:${wd ? 330 : 600}px;font-size:${wd ? 50 : 56}px">${esc(p.sub)}</div>${art}</div>`;   // the art itself is the tweened box (a full-width wrapper would rotate into a phantom box)
    const [tt, ts, ar] = root.querySelectorAll('.a');
    return tg => {
      const t = tg - api.start;
      api.tw(tt, t, api.K.rise(0.1, 0.6)); api.tw(ts, t, api.K.rise(0.45, 0.6));
      const u = P(t, 0.8, 1.3, 'out');                          // the art keeps rising until the step starts
      ar.style.opacity = u; ar.style.transform = `translate(${Math.round(12 * Math.sin(t * 0.9))}px, ${Math.round((1 - u) * 80 + 14 * Math.sin(t * 1.3))}px)`;   // whole pixels: the screen in the art stays sharp
    };
  });

  RM.def('tut_end', (api, root) => {
    const p = api.p, wd = wide(), rows = p.rows || [];
    const fs = wd ? 46 : 56, top = wd ? 250 : 520, left = wd ? 300 : 70, w = wd ? W() - 600 : W() - 140;
    root.innerHTML = `<div class="tut"><div class="ttl a" style="left:60px;right:60px;top:${wd ? 90 : 250}px;font-size:${wd ? 90 : 96}px">${esc(p.title)}</div>` +
      `<div class="tend" style="left:${left}px;top:${top}px;width:${w}px">` +
      rows.map((r, i) => `<div class="er a" style="font-size:${fs}px"><div class="badge">${i + 1}</div><div>${esc(r)}</div></div>`).join('') + `</div></div>`;
    const tt = root.querySelector('.ttl'), rs = [...root.querySelectorAll('.er')];
    return tg => {
      const t = tg - api.start;
      api.tw(tt, t, api.K.rise(0.05, 0.55));
      rs.forEach((r, i) => {
        const u = P(t, 0.35 + 0.28 * i, 0.5, 'out');
        r.style.opacity = u; r.style.transform = `translateX(${Math.round((1 - u) * 80)}px) translateY(${Math.round(4 * Math.sin(t * 1.4 + i))}px)`;
      });
    };
  });

  // ---------- Tutorial 1: the computer ----------
  RM.def('t1_app', (api, root) => {
    const p = api.p, L = p.labels;
    const side = `<div class="tside"><div class="item"><div class="gl"></div>${phs(1)}</div><div class="item"><div class="gl"></div>${phs(1)}</div>` +
      `<div class="item"><div class="gl"></div>${phs(1)}</div><div style="flex:1"></div>` +
      `<div class="menu" data-k="menu" style="left:16px;bottom:110px"><div class="item" data-k="settings">${esc(L.settings)}</div><div class="item">${phs(1)}</div><div class="item">${phs(1)}</div></div>` +
      `<div class="user" data-k="user"><div class="av round">${esc(L.initial)}</div>${esc(L.name)}</div></div>`;
    const main = `<div class="main"><div class="h1" style="opacity:.25">${phs(1)}</div><div style="height:30px"></div>${phs(5)}<div style="height:24px"></div>${phs(4)}</div>`;
    root.innerHTML = frame(p, win('Claude', side, main));
    return player(api, root, p);
  });

  RM.def('t1_settings', (api, root) => {
    const p = api.p, L = p.labels;
    const nav = L.nav.map(n => `<div class="item" ${n === L.code ? 'data-k="nav_code"' : ''}><div class="gl"></div>${esc(n)}</div>`).join('');
    const rows = L.toggles.map((n, i) => `<div class="row" data-k="row${i}"><div><div class="rl">${esc(n)}</div></div>` +
      `<div style="display:flex;align-items:center;gap:20px">${i === 1 ? `<div class="tagoff" data-k="off">${esc(L.leaveOff)}</div>` : ''}${sw('sw' + i)}</div></div>`).join('');
    const main = `<div class="main"><div data-k="page"><div class="h1">${esc(L.code)}</div>` +
      `<div class="h2" style="opacity:.6">${phs(1)}</div><div class="row"><div style="flex:1">${phs(2)}</div>${sw('x1')}</div><div class="row"><div style="flex:1">${phs(2)}</div>${sw('x2')}</div>` +
      `<div class="h2" data-k="rc">${esc(L.section)}</div><div data-k="rcrows">${rows}</div><div style="height:300px"></div></div></div>`;
    root.innerHTML = frame(p, win(L.settings, `<div class="tside">${nav}</div>`, main));
    return player(api, root, p);
  });

  RM.def('t1_session', (api, root) => {
    const p = api.p, L = p.labels;
    const side = `<div class="tside"><div class="tbtn" data-k="new" style="font-size:28px">+ ${esc(L.newSession)}</div><div style="height:8px"></div>` +
      `<div class="item"><div class="gl"></div>${phs(1)}</div><div class="item"><div class="gl"></div>${phs(1)}</div></div>`;
    const folders = L.folders.map(f => `<div class="fold" ${f === L.videos ? 'data-k="videos"' : ''}><div class="fi"></div>${esc(f)}</div>`).join('');
    const main = `<div class="main"><div class="h1" data-k="sessTitle" style="opacity:.25">${phs(1)}</div>` +
      `<div class="compose" data-k="compose"><div class="hint">${phs(1)}</div><div style="display:flex;gap:16px;align-items:center">` +
      `<div class="chip" data-k="choose"><div class="fold" style="padding:0;font-size:28px"><div class="fi" style="transform:scale(.7)"></div></div><span data-k="chiptext">${esc(L.choose)}</span></div>` +
      `<div class="chip" data-k="chosen" style="position:absolute;left:26px;bottom:22px"><div class="fold" style="padding:0;font-size:28px"><div class="fi" style="transform:scale(.7)"></div></div>${esc(L.reels)}</div></div></div>` +
      `<div class="dlg" data-k="dlg" style="left:120px;top:60px;width:760px">` +
      `<div class="h2" style="margin-top:0">${esc(L.choose)}</div><div data-k="list1">${folders}</div>` +
      `<div data-k="inside" style="margin:6px 0 0 48px"><div class="fold" data-k="reels"><div class="fi"></div>${esc(L.reels)}</div></div>` +
      `<div style="display:flex;justify-content:flex-end;margin-top:18px"><div class="tbtn" data-k="select">${esc(L.select)}</div></div></div></div>`;
    root.innerHTML = frame(p, win('Claude', side, main));
    return player(api, root, p);
  });

  // ---------- Tutorial 1 (1.2.0): the Code tab, every click ----------
  // Clean generic drawings laid out after the real Windows desktop app (layout and button positions only; nothing copied).
  const CSS3 = `
  .cw .bar { gap:10px; padding:0 18px; }
  .cw .gi { width:34px; height:34px; border-radius:9px; background:var(--dim); opacity:.45; flex:none; }
  .cw .tg { position:relative; display:flex; gap:4px; padding:4px; border-radius:12px; background:var(--line); margin-left:6px; flex:none; }
  .cw .tg .pill { position:absolute; top:4px; width:52px; height:42px; border-radius:9px; background:var(--paper); box-shadow:0 2px 0 var(--dim); }
  .cw .tg .ti { position:relative; z-index:1; width:52px; height:42px; display:flex; align-items:center; justify-content:center; color:var(--ink); }
  .mono { font-family:Consolas,"Cascadia Mono","DejaVu Sans Mono",monospace; font-weight:800; letter-spacing:-1px; }
  .bubi { width:26px; height:20px; border:3px solid var(--ink); border-radius:8px; position:relative; }
  .bubi:after { content:''; position:absolute; left:3px; bottom:-8px; border:5px solid transparent; border-top-color:var(--ink); border-left-color:var(--ink); }
  .cw .tip { position:absolute; left:250px; top:64px; z-index:16; background:var(--ink); color:var(--paper); font-size:28px; font-weight:700; padding:10px 18px; border-radius:12px;
             display:flex; gap:12px; align-items:center; white-space:nowrap; }
  .cw .wt2 { font-size:24px; font-weight:600; color:var(--muted); margin-left:18px; }
  .cw .plus2 { width:30px; text-align:center; font-weight:800; font-size:32px; flex:none; }
  .cw .gear { width:36px; height:36px; border-radius:50%; border:5px dotted var(--muted); margin-left:auto; flex:none; }
  .cbox { position:absolute; left:60px; right:60px; bottom:84px; min-height:78px; border-radius:20px; border:3px solid var(--line); background:var(--paper);
          display:flex; align-items:center; gap:18px; padding:12px 16px 12px 22px; }
  .cbox .pl { font-size:32px; font-weight:800; color:var(--muted); flex:none; }
  .cbox .hintx { font-size:26px; color:var(--muted); position:absolute; left:70px; top:50%; margin-top:-17px; white-space:nowrap; }
  .cbox .tx { flex:1; font-size:28px; font-weight:700; color:var(--ink); min-height:36px; }
  .cbox .pasted { position:absolute; left:70px; right:90px; top:12px; bottom:12px; font-size:24px; color:var(--ink); display:flex; flex-direction:column; justify-content:center; gap:8px; overflow:hidden; }
  .cbox .sendb { width:50px; height:50px; border-radius:50%; background:var(--acc); flex:none; position:relative; margin-left:auto; }
  .cbox .sendb:after { content:''; position:absolute; left:15px; top:13px; border-bottom:18px solid var(--paper); border-left:10px solid transparent; border-right:10px solid transparent; }
  .chips { position:absolute; left:60px; right:60px; bottom:18px; height:54px; display:flex; align-items:center; gap:14px; }
  .ch { display:inline-flex; align-items:center; gap:10px; font-size:25px; font-weight:700; color:var(--ink); padding:8px 14px; border-radius:10px; white-space:nowrap; }
  .ch .mut { color:var(--muted); font-weight:600; }
  .swap { display:inline-grid; } .swap > * { grid-area:1/1; }
  .cv { width:11px; height:11px; border-right:3px solid var(--muted); border-bottom:3px solid var(--muted); transform:rotate(45deg) translate(-3px,-3px); flex:none; }
  .cvr { width:11px; height:11px; border-right:3px solid var(--muted); border-bottom:3px solid var(--muted); transform:rotate(-45deg); flex:none; margin-left:8px; }
  .pci { width:30px; height:21px; border:3px solid var(--ink); border-radius:4px; flex:none; position:relative; margin-bottom:5px; }
  .pci:after { content:''; position:absolute; left:4px; right:4px; bottom:-9px; height:3px; background:var(--ink); }
  .fi2 { width:30px; height:22px; border:3px solid var(--ink); border-radius:3px 3px 5px 5px; flex:none; position:relative; }
  .fi2:before { content:''; position:absolute; left:-3px; top:-9px; width:12px; height:6px; border:3px solid var(--ink); border-bottom:0; border-radius:3px 3px 0 0; }
  .mn { position:absolute; background:var(--paper); border-radius:18px; box-shadow:var(--sh); border:2px solid var(--line); padding:10px; z-index:12; }
  .mi { display:flex; align-items:center; gap:14px; font-size:26px; font-weight:600; color:var(--ink); padding:10px 16px; border-radius:10px; white-space:nowrap; }
  .mi.sel { background:var(--c1x); }
  .mi .sb2 { font-size:21px; color:var(--muted); font-weight:500; margin-top:3px; white-space:normal; }
  .mi .val { margin-left:auto; color:var(--muted); font-size:23px; display:flex; align-items:center; }
  .mh { font-size:21px; font-weight:700; color:var(--muted); padding:10px 16px 4px; }
  .msep { height:2px; background:var(--line); margin:8px 6px; }
  .mfield { font-size:24px; color:var(--muted); padding:10px 16px; border-bottom:2px solid var(--line); margin-bottom:6px; }
  .ck { width:24px; height:13px; border-left:4px solid var(--c1); border-bottom:4px solid var(--c1); transform:rotate(-45deg) translate(2px,-3px); margin-left:auto; flex:none; }
  .tagp { font-size:18px; color:var(--muted); border:2px solid var(--line); border-radius:8px; padding:1px 8px; }
  .nfbox { display:inline-block; min-width:220px; border:3px solid var(--c1); border-radius:6px; padding:2px 10px; min-height:44px; }
  .gh .url { flex:1; max-width:1000px; height:38px; border-radius:19px; background:var(--paper); border:2px solid var(--line); font-size:22px; color:var(--muted);
             display:flex; align-items:center; padding:0 22px; margin-left:20px; white-space:nowrap; overflow:hidden; }
  .codeb { position:relative; margin-top:22px; border-radius:16px; background:var(--c1x); border:2px solid var(--line); padding:30px 34px; display:flex; flex-direction:column; gap:16px; }
  .codeb .l1 { font-size:24px; color:var(--ink); }
  .cpy { position:absolute; right:18px; top:16px; width:58px; height:58px; border-radius:12px; background:var(--paper); border:2px solid var(--line); }
  .cpy:before, .cpy:after { content:''; position:absolute; width:18px; height:22px; border:3px solid var(--ink); border-radius:4px; background:var(--paper); }
  .cpy:before { left:14px; top:12px; } .cpy:after { left:22px; top:20px; }
  .cptip { position:absolute; right:0; top:-54px; background:var(--ink); color:var(--paper); font-size:22px; font-weight:700; padding:6px 14px; border-radius:8px; white-space:nowrap; }
  .msgs { position:absolute; left:80px; right:80px; top:26px; display:flex; flex-direction:column; gap:20px; }
  .um { align-self:flex-end; max-width:70%; background:var(--c1x); border-radius:18px; padding:16px 22px; font-size:24px; color:var(--ink); display:flex; flex-direction:column; gap:10px; }
  .cm { display:flex; flex-direction:column; gap:10px; font-size:25px; color:var(--ink); max-width:80%; }
  .cm b { font-weight:800; }
  .permc { border:3px solid var(--line); border-radius:16px; padding:18px 22px; display:flex; flex-direction:column; gap:14px; background:var(--paper); max-width:80%; }
  .permc .cmd { font-size:22px; background:var(--c1x); border-radius:8px; padding:8px 14px; }
  .permc .btns { display:flex; gap:14px; }
  .sbtn { font-size:24px; font-weight:800; padding:10px 24px; border-radius:10px; background:var(--acc); color:var(--on-acc); }
  .sbtn.ghost { background:var(--paper); color:var(--ink); border:2px solid var(--line); }
  .okline { display:flex; align-items:center; gap:14px; font-size:25px; font-weight:700; color:var(--ink); }
  .okline .tk { width:34px; height:34px; border-radius:50%; background:var(--good); position:relative; flex:none; }
  .okline .tk:after { content:''; position:absolute; left:9px; top:9px; width:13px; height:7px; border-left:4px solid var(--paper); border-bottom:4px solid var(--paper); transform:rotate(-45deg); }
  `;
  if (!document.getElementById('tut-css3')) {
    const s = document.createElement('style'); s.id = 'tut-css3'; s.textContent = CSS3; document.head.appendChild(s);
  }
  const pick = (fin, a, b, ka, kb) => fin ? esc(b) : `<span class="swap"><span data-k="${ka}">${esc(a)}</span><span data-k="${kb}">${esc(b)}</span></span>`;

  // the Code tab window: o.mode 'chat' starts on the chat side (the toggle scene); o.st = choices already made; o.anim = the chip that changes here
  function codeWin(p, o = {}) {
    const L = p.labels, st = o.st || {}, an = o.anim || '';
    const codeIc = `<span class="mono" style="font-size:24px">&lt;/&gt;</span>`;
    const toggle = `<div class="tg">` + (o.mode === 'chat' ? `<div class="pill" data-k="pillA" style="left:4px"></div><div class="pill" data-k="pillB" style="left:60px"></div>`
                                                             : `<div class="pill" style="left:60px"></div>`) +
      `<div class="ti" data-k="tg_chat"><div class="bubi"></div></div><div class="ti" data-k="tg_code">${codeIc}</div></div>`;
    const bar = `<div class="bar"><div class="gi"></div><div class="gi"></div><div class="gi"></div><div class="gi"></div>${toggle}` +
      `<div class="wt2">${esc(o.title || L.newSession)}</div></div>`;
    const tip = o.tip ? `<div class="tip" data-k="tip">${codeIc}${esc(L.codeTab)}</div>` : '';
    const side = `<div class="tside"><div class="item" data-k="new"><span class="plus2">+</span>${esc(L.newBtn)}</div>` +
      `<div class="item"><div class="gl"></div>${esc(L.search)}</div><div class="item"><div class="gl"></div>${phs(1)}</div>` +
      (st.sess ? `<div style="height:20px"></div><div class="item sel"><div class="gl"></div>${esc(st.sess)}</div>` : `<div class="item"><div class="gl"></div>${phs(1)}</div>`) +
      `<div style="flex:1"></div><div class="user"><div class="av round">${esc(L.initial)}</div>${esc(L.name)}<div class="gear round"></div></div></div>`;
    const comp = `<div class="cbox" data-k="input"><div class="pl">+</div>` + (o.noHint ? '' : `<div class="hintx" data-k="hint">${esc(L.hint)}</div>`) +
      `<div class="tx" data-k="typed"></div>${o.pasted || ''}<div class="sendb round" data-k="send"></div></div>`;
    const chips = `<div class="chips"><div class="ch" data-k="env"><div class="pci"></div>${esc(L.env)}<span class="cv"></span></div>` +
      `<div class="ch" data-k="choose"><div class="fi2"></div>${an === 'folder' ? pick(false, L.choose, L.reels, 'chA', 'chB') : esc(st.folder ? L.reels : L.choose)}<span class="cv"></span></div>` +
      `<div style="flex:1"></div><div class="ch" data-k="model">${esc(L.model)} <span class="mut">${an === 'effort' ? pick(false, L.efforts[1], L.efforts[2], 'efA', 'efB') : esc(st.effort ? L.efforts[2] : L.efforts[1])}</span></div>` +
      `<div class="ch" data-k="perm">${an === 'perm' ? pick(false, L.perms[2][0], L.perms[0][0], 'pmA', 'pmB') : esc(st.perm ? L.perms[0][0] : L.perms[2][0])}</div></div>`;
    const codeLayer = `<div data-k="codelay" style="position:absolute;inset:0">${o.body || ''}${comp}${chips}</div>`;
    const chatLayer = o.mode === 'chat' ? `<div data-k="chatlay" style="position:absolute;inset:0;padding:60px 120px"><div class="h1" style="opacity:.3">${phs(1)}</div><div style="height:30px"></div>${phs(5)}` +
      `<div class="cbox" style="left:120px;right:120px"><div class="pl">+</div>${phs(1)}</div></div>` : '';
    const main = `<div class="main" style="padding:0">${chatLayer}${codeLayer}${o.menus || ''}</div>`;
    return `<div class="win cw">${bar}<div class="body">${side}${main}</div>${tip}</div>`;
  }

  RM.def('t1_code', (api, root) => {
    root.innerHTML = frame(api.p, codeWin(api.p, { mode: 'chat', tip: true }));
    return player(api, root, api.p);
  });

  RM.def('t1_new', (api, root) => {
    const L = api.p.labels;
    const menus = `<div class="mn" data-k="envmenu" style="left:50px;bottom:84px;width:360px"><div class="mi" data-k="env_pc"><div class="pci"></div>${esc(L.env)}<div class="ck"></div></div>` +
      `<div class="mi">${phs(1)}</div><div class="mi">${phs(1)}</div></div>`;
    root.innerHTML = frame(api.p, codeWin(api.p, { menus }));
    return player(api, root, api.p);
  });

  RM.def('t1_folder', (api, root) => {
    const L = api.p.labels;
    const fmenu = `<div class="mn" data-k="fmenu" style="left:250px;bottom:84px;width:380px"><div class="mfield">${esc(L.searchFolders)}</div>` +
      `<div class="mi">${esc(L.noFolder)}<div class="ck"></div></div><div class="mh">${esc(L.recent)}</div>` +
      `<div class="mi">${phs(1)}</div><div class="mi">${phs(1)}</div><div class="mi">${phs(1)}</div><div class="msep"></div>` +
      `<div class="mi" data-k="openf">${esc(L.openFolder)}</div></div>`;
    const folders = L.folders.map(f => `<div class="fold" style="font-size:27px;padding:8px 14px"><div class="fi"></div>${esc(f)}</div>`).join('');
    const dlg = `<div class="dlg" data-k="dlg" style="left:110px;top:24px;width:900px;padding:22px 28px">` +
      `<div style="display:flex;align-items:center;gap:20px"><div class="h2" style="margin:0;font-size:32px">${esc(L.dlgTitle)}</div><div style="flex:1"></div>` +
      `<div class="tbtn ghost" data-k="newf" style="font-size:25px;padding:10px 20px">+ ${esc(L.newFolder)}</div></div>` +
      `<div style="margin-top:14px">${folders}<div class="fold" data-k="nf" style="font-size:27px;padding:8px 14px"><div class="fi"></div><span class="nfbox" data-k="nfname"></span></div></div>` +
      `<div style="display:flex;justify-content:flex-end;margin-top:14px"><div class="tbtn" data-k="select" style="font-size:26px;padding:12px 26px">${esc(L.select)}</div></div></div>`;
    root.innerHTML = frame(api.p, codeWin(api.p, { anim: 'folder', menus: fmenu + dlg }));
    return player(api, root, api.p);
  });

  RM.def('t1_model', (api, root) => {
    const L = api.p.labels;
    const mm = `<div class="mn" data-k="mmenu" style="right:200px;bottom:84px;width:400px"><div class="mh">${esc(L.modelHdr)}</div>` +
      L.models.map((m, i) => `<div class="mi" ${i === 0 ? 'data-k="m_opus"' : ''}>${esc(m)}${i === 0 ? `<span class="tagp">${esc(L.preset)}</span><div class="ck"></div>` : ''}</div>`).join('') +
      `<div class="msep"></div><div class="mi" data-k="m_effort">${esc(L.effort)}<span class="val">${esc(L.efforts[1])}<span class="cvr"></span></span></div>` +
      `<div class="mi">${esc(L.moreModels)}<span class="val"><span class="cvr"></span></span></div></div>`;
    const em = `<div class="mn" data-k="emenu" style="right:612px;bottom:150px;width:380px"><div class="mh" style="padding-bottom:10px">${phs(2)}</div>` +
      L.efforts.map((e, i) => `<div class="mi" ${i === 2 ? 'data-k="e_high"' : ''}>${esc(e)}` +
        (i === 1 ? `<span class="tagp">${esc(L.recommended)}</span><div class="ck" data-k="ck_med"></div>` : i === 2 ? `<div class="ck" data-k="ck_high"></div>` : '') + `</div>`).join('') + `</div>`;
    root.innerHTML = frame(api.p, codeWin(api.p, { st: { folder: 1 }, anim: 'effort', menus: mm + em }));
    return player(api, root, api.p);
  });

  RM.def('t1_perm', (api, root) => {
    const L = api.p.labels;
    const pm = `<div class="mn" data-k="pmenu" style="right:40px;bottom:84px;width:500px"><div class="mh">${esc(L.permHdr)}</div>` +
      L.perms.map(([a, b], i) => `<div class="mi" ${i === 0 ? 'data-k="p_auto"' : ''}><div style="flex:1"><div>${esc(a)}</div><div class="sb2">${esc(b)}</div></div>` +
        (i === 0 ? `<div class="ck" data-k="ck_auto"></div>` : i === 2 ? `<div class="ck" data-k="ck_acc"></div>` : '') + `</div>`).join('') + `</div>`;
    root.innerHTML = frame(api.p, codeWin(api.p, { st: { folder: 1, effort: 1 }, anim: 'perm', menus: pm }));
    return player(api, root, api.p);
  });

  RM.def('t1_github', (api, root) => {
    const L = api.p.labels;
    const bar = `<div class="bar"><div class="gi" style="width:30px;height:30px;border-radius:8px"></div><div class="gi" style="width:30px;height:30px"></div><div class="url">${esc(L.ghUrl)}</div></div>`;
    const main = `<div class="main" style="padding:30px 120px"><div style="font-size:24px;color:var(--muted)">${esc(L.ghPath)}</div>` +
      `<div class="h1" style="margin-top:10px">${esc(L.promptTitle)}</div><div style="height:16px"></div>${phs(1)}` +
      `<div class="codeb" data-k="codebox"><div class="l1 mono" style="font-weight:600;letter-spacing:0">${esc(L.promptStart)}</div>${phs(6)}` +
      `<div class="cpy" data-k="copy"><div class="cptip" data-k="copied">${esc(L.copied)}</div></div></div></div>`;
    root.innerHTML = frame(api.p, `<div class="win cw gh">${bar}<div class="body">${main}</div></div>`);
    return player(api, root, api.p);
  });

  RM.def('t1_chat', (api, root) => {
    const p = api.p, L = p.labels, st = { folder: 1, effort: 1, perm: 1, sess: L.reels };
    const um = `<div class="um" data-k="umsg"><div>${esc(L.promptStart)}</div>${phs(2)}</div>`;
    let body;
    if (p.mode === 'install') {
      body = `<div class="msgs">${um}<div class="cm" data-k="reply"><div>${esc(L.r1)}</div>${phs(1)}</div>` +
        `<div class="permc" data-k="permcard"><div style="font-size:25px;font-weight:700">${esc(L.permAsk)}</div><div class="cmd mono" style="font-weight:600;letter-spacing:0">${esc(L.permCmd)}</div>` +
        `<div class="btns"><div class="sbtn" data-k="allow">${esc(L.allow)}</div><div class="sbtn ghost">${esc(L.deny)}</div></div></div>` +
        `<div class="cm" data-k="working"><div>${esc(L.working)}</div>${phs(1)}</div></div>`;
      const pasted = `<div class="pasted" data-k="pasted"><div>${esc(L.promptStart)}</div>${phs(1)}</div>`;
      root.innerHTML = frame(p, codeWin(p, { st, title: L.reels, body, pasted }));
    } else {
      body = `<div class="msgs"><div class="um"><div>${esc(L.promptStart)}</div>${phs(1)}</div><div class="cm">${phs(2)}</div>` +
        `<div class="cm" data-k="fin"><div><b>${esc(L.finished)}</b></div><div>${esc(L.finished2)}</div></div>` +
        `<div class="um" data-k="umsg2"><div class="mono" style="font-weight:600;letter-spacing:0">${esc(L.reloadCmd)}</div></div>` +
        `<div class="okline" data-k="reloaded"><div class="tk"></div>${esc(L.reloaded)}</div></div>`;
      root.innerHTML = frame(p, codeWin(p, { st, title: L.reels, body }));
    }
    return player(api, root, p);
  });

  // ---------- Tutorial 2: the iPhone ----------
  // One step = one screen and one tap. The phone is an iPhone 11 Pro screen in its own units (375 x 812 CSS px), scaled up once
  // and never moved, so text stays sharp. Page screens are real renders of the upload page (scripts/tutorials.py -> shots.mjs);
  // iOS screens are clean drawings laid out after real iOS 18 screenshots (no icons copied, no logos).
  const S2 = 1.92, PW = 375, PH = 812, BZ = 14;                  // scale, screen size, bezel (video px)
  const VIEW = [109, 619];                                         // page viewport: top and height inside the screen
  const CSS2 = `
  .p2 { position:absolute; background:var(--phone); border-radius:${39 * S2 + BZ}px; box-shadow:var(--sh); }
  .p2 .s2 { position:absolute; left:${BZ}px; top:${BZ}px; width:${PW}px; height:${PH}px; transform:scale(${S2}); transform-origin:0 0;
            border-radius:39px; overflow:hidden; background:#fff; font-family:-apple-system,"SF Pro Text","Inter","Segoe UI",Roboto,Arial,sans-serif; color:#111; }
  .s2 * { box-sizing:border-box; }
  .s2 .ab { position:absolute; }
  .s2 .sb { position:absolute; left:0; right:0; top:0; height:50px; font-size:15px; font-weight:600; }
  .s2 .sb .tm { position:absolute; left:30px; top:13px; }
  .s2 .sb .bk { position:absolute; left:18px; top:31px; font-size:11px; font-weight:600; }
  .s2 .sb .ind { position:absolute; right:22px; top:16px; display:flex; gap:5px; align-items:flex-end; }
  .s2 .sb .ind i { display:block; width:3px; background:currentColor; border-radius:1px; }
  .s2 .sb .bat { width:24px; height:12px; border:1.5px solid currentColor; border-radius:3px; margin-left:4px; position:relative; }
  .s2 .sb .bat:after { content:''; position:absolute; left:1.5px; top:1.5px; width:12px; height:6px; background:currentColor; border-radius:1px; }
  .s2 .blue { color:#0a7cff; }
  .s2 .topb { position:absolute; left:0; right:0; top:50px; height:59px; background:#f4f4f6; border-radius:12px 12px 0 0; border-bottom:.5px solid #d4d4d8; }
  .s2 .topb .dn { position:absolute; left:14px; top:20px; font-size:17px; color:#0a7cff; }
  .s2 .topb .host { position:absolute; left:0; right:0; top:19px; text-align:center; font-size:17px; font-weight:600; }
  .s2 .topb .ic { position:absolute; top:18px; width:22px; height:22px; border:2px solid #0a7cff; border-radius:5px; }
  .s2 .topb .ic.r { border-radius:50%; border-right-color:transparent; }
  .s2 .tool { position:absolute; left:0; right:0; top:728px; bottom:0; background:#f4f4f6; border-top:.5px solid #d4d4d8; }
  .s2 .chev { position:absolute; top:16px; width:14px; height:14px; border-left:2.5px solid #0a7cff; border-bottom:2.5px solid #0a7cff; transform:rotate(45deg); }
  .s2 .chev.f { transform:rotate(-135deg); border-color:#b9b9c0; }
  .s2 .shr { position:absolute; top:9px; width:24px; height:30px; }
  .s2 .shr .bx { position:absolute; left:0; right:0; bottom:0; height:18px; border:2.2px solid #0a7cff; border-top:0; border-radius:0 0 4px 4px; }
  .s2 .shr .bx:before, .s2 .shr .bx:after { content:''; position:absolute; top:-2px; width:5px; border-top:2.2px solid #0a7cff; }
  .s2 .shr .bx:before { left:-2px; } .s2 .shr .bx:after { right:-2px; }
  .s2 .shr .st { position:absolute; left:11px; top:0; width:2.2px; height:19px; background:#0a7cff; }
  .s2 .shr .hd { position:absolute; left:7px; top:1px; width:10px; height:10px; border-left:2.2px solid #0a7cff; border-top:2.2px solid #0a7cff; transform:rotate(45deg); }
  .s2 .cmp { position:absolute; top:12px; width:26px; height:26px; border:2.2px solid #0a7cff; border-radius:50%; }
  .s2 .cmp:after { content:''; position:absolute; left:9px; top:4px; width:4px; height:14px; background:#0a7cff; transform:rotate(45deg); border-radius:2px; }
  .s2 .homei { position:absolute; left:120px; width:135px; bottom:8px; height:5px; border-radius:3px; background:#111; }
  .s2 .shot { position:absolute; left:0; top:${VIEW[0]}px; width:${PW}px; height:${VIEW[1]}px; }
  .s2 .dim { position:absolute; inset:0; background:rgba(0,0,0,.32); }
  .s2 .sheet2 { position:absolute; left:0; right:0; bottom:0; background:#f2f2f7; border-radius:14px 14px 0 0; }
  .s2 .grp { background:#fff; border-radius:12px; margin:0 16px; overflow:hidden; }
  .s2 .grp .li { height:50px; display:flex; align-items:center; padding:0 16px; font-size:17px; border-top:.5px solid #d4d4d8; gap:12px; }
  .s2 .grp .li:first-child { border-top:0; }
  .s2 .grp .li .g { width:22px; height:22px; border:2px solid #111; border-radius:5px; margin-left:auto; flex:none; }
  .s2 .btn2 { position:absolute; display:flex; align-items:center; justify-content:center; gap:10px; background:#0a7cff; color:#fff; font-size:20px; font-weight:600; border-radius:12px; }
  .s2 .plus { width:22px; height:22px; border-radius:50%; background:#fff; position:relative; flex:none; }
  .s2 .plus:before, .s2 .plus:after { content:''; position:absolute; left:10px; top:5px; width:2.4px; height:12px; background:#0a7cff; }
  .s2 .plus:after { transform:rotate(90deg); }
  .s2 .card2 { position:absolute; border-radius:20px; background:linear-gradient(160deg,#ef8a83,#df5d58); color:#fff; }
  .s2 .acard { position:absolute; left:16px; right:16px; background:#f0f0f4; border-radius:16px; padding:12px 14px; font-size:19px; line-height:1.55; }
  .s2 .acard .v { color:#0a7cff; }
  .s2 .alert { position:absolute; left:52px; width:270px; background:rgba(242,242,246,.98); border-radius:14px; text-align:center; overflow:hidden; }
  .s2 .alert .at { padding:19px 16px 16px; font-size:17px; font-weight:600; line-height:1.3; }
  .s2 .alert .ab2 { height:44px; display:flex; align-items:center; justify-content:center; font-size:17px; color:#0a7cff; border-top:.5px solid #c8c8cc; }
  .s2 .wall { position:absolute; inset:0; background:linear-gradient(170deg,#d9e4f5 0%,#c7d5ee 45%,#e9d8cf 100%); }
  .s2 .apps { position:absolute; left:27px; right:27px; top:70px; display:grid; grid-template-columns:repeat(4,60px); justify-content:space-between; row-gap:28px; }
  .s2 .ap { display:flex; flex-direction:column; align-items:center; gap:6px; font-size:12px; color:#1d1d1f; }
  .s2 .ap .ii { width:60px; height:60px; border-radius:14px; }
  .s2 .bub2 { width:30px; height:23px; border-radius:9px; background:#fff; position:relative; }
  .s2 .bub2:after { content:''; position:absolute; left:5px; bottom:-6px; border:6px solid transparent; border-top-color:#fff; border-left-color:#fff; }
  .s2 .navh { position:absolute; left:0; right:0; top:50px; height:50px; display:flex; align-items:center; justify-content:space-between; padding:0 16px; font-size:17px; }
  .s2 .navh b { font-weight:600; position:absolute; left:0; right:0; text-align:center; pointer-events:none; }
  .s2 .grid3 { position:absolute; left:0; right:0; display:grid; grid-template-columns:repeat(3,1fr); gap:2px; }
  .s2 .tb { aspect-ratio:1; position:relative; }
  .s2 .tb .du { position:absolute; right:5px; bottom:4px; font-size:12px; font-weight:600; color:#fff; text-shadow:0 1px 2px rgba(0,0,0,.4); }
  .s2 .tb .ck { position:absolute; right:6px; bottom:22px; width:24px; height:24px; border-radius:50%; background:#0a7cff; border:2px solid #fff; display:none; }
  .s2 .tb .ck:after { content:''; position:absolute; left:6px; top:5px; width:8px; height:5px; border-left:2px solid #fff; border-bottom:2px solid #fff; transform:rotate(-45deg); }
  .s2 .tb.sel .ck { display:block; } .s2 .tb.sel:after { content:''; position:absolute; inset:0; background:rgba(255,255,255,.18); }
  .s2 .seg { display:flex; gap:8px; }
  .s2 .seg .sg2 { font-size:17px; font-weight:600; padding:8px 18px; border-radius:20px; background:#ececf0; color:#555; }
  .s2 .seg .sg2.on { background:#1d1d1f; color:#fff; }
  .s2 .row2 { position:absolute; left:16px; right:16px; height:64px; border-radius:14px; background:#f0f0f4; display:flex; align-items:center; gap:14px; padding:0 16px; font-size:18px; font-weight:600; }
  .s2 .row2 .pc { width:30px; height:21px; border:2.5px solid #2f5d9a; border-radius:3px; flex:none; }
  .s2 .row2 .live { width:11px; height:11px; border-radius:50%; background:#2fa84f; margin-left:auto; }
  .s2 .msg2 { position:absolute; max-width:250px; font-size:18px; line-height:1.35; padding:10px 14px; border-radius:18px; }
  .s2 .msg2.me { right:16px; background:var(--acc); color:var(--on-acc); }
  .s2 .msg2.it { left:16px; background:#f0f0f4; }
  .s2 .inp2 { position:absolute; left:12px; right:12px; top:${PH - 100}px; height:52px; border-radius:26px; background:#f0f0f4; display:flex; align-items:center; padding:0 6px 0 18px; font-size:18px; }
  .s2 .inp2 .tx { flex:1; } .s2 .inp2 .go { width:40px; height:40px; border-radius:50%; background:var(--acc); position:relative; flex:none; }
  .s2 .inp2 .go:after { content:''; position:absolute; left:13px; top:11px; border-bottom:14px solid #fff; border-left:7px solid transparent; border-right:7px solid transparent; }
  .s2 .mark { position:absolute; border:4px solid var(--acc); border-radius:14px; box-shadow:0 0 0 5px var(--acc-soft); z-index:40; }
  .s2 .fdot { position:absolute; width:40px; height:40px; margin:-20px 0 0 -20px; border-radius:50%; border:4px solid var(--acc); box-shadow:0 0 0 2px #fff; opacity:0; z-index:41; }
  .s2 .son { position:absolute; border:4px solid var(--acc); border-radius:16px; opacity:0; z-index:39; pointer-events:none; }
  .s2 .rip2 { position:absolute; width:46px; height:46px; margin:-23px 0 0 -23px; border-radius:50%; border:4px solid var(--acc); opacity:0; z-index:41; }
  .t2cap { position:absolute; left:56px; right:56px; top:40px; display:flex; align-items:center; gap:.5em; background:var(--paper); border-radius:var(--r-l);
           box-shadow:var(--sh); padding:.45em .75em; font-family:var(--f-head); font-weight:800; line-height:1.16; color:var(--ink); }
  .t2cap .badge { font-size:1.1em; width:1.6em; height:1.6em; background:var(--acc); color:var(--on-acc); font-weight:900; flex:none; }
  `;
  if (!document.getElementById('tut2-css')) {
    const s = document.createElement('style'); s.id = 'tut2-css'; s.textContent = CSS2; document.head.appendChild(s);
  }

  const status = (back, dark) => `<div class="sb" style="color:${dark ? '#fff' : '#111'}"><div class="tm">9:41</div>${back ? `<div class="bk">&#9664; ${esc(back)}</div>` : ''}` +
    `<div class="ind"><i style="height:4px"></i><i style="height:6px"></i><i style="height:8px"></i><i style="height:10px"></i><div class="bat"></div></div></div>`;
  const browser = (L, inner) => `<div class="ab" style="left:0;right:0;top:0;height:60px;background:#1c1c1e"></div>${status('', true)}` +
    `<div class="topb"><div class="dn">${esc(L.done)}</div><div class="host">${esc(L.pageHost)}</div><div class="ic" style="left:297px"></div><div class="ic r" style="left:338px"></div></div>` +
    `<div class="ab" style="left:0;top:${VIEW[0]}px;width:${PW}px;height:${VIEW[1]}px;background:#f6f4ef;overflow:hidden">${inner}</div>` +
    `<div class="tool"><div class="chev" style="left:24px"></div><div class="chev f" style="left:126px"></div><div class="shr" data-k="share" style="left:226px"><div class="bx"></div><div class="st"></div><div class="hd"></div></div>` +
    `<div class="cmp" style="left:330px"></div></div><div class="homei"></div>`;
  const shotImg = p => `<img class="shot" style="top:0" src="${p.src}">`;
  const thumbsGrid = (n, top) => `<div class="grid3" style="top:${top}px">` + Array.from({ length: n }, (_, i) =>
    `<div class="tb" data-k="th${i}" style="background:linear-gradient(${150 + i * 23}deg, hsl(${[205, 18, 160, 32, 225, 350, 190, 40, 260][i % 9]} 45% ${62 + (i % 3) * 6}%), hsl(${[220, 8, 140, 20, 240, 330, 200, 25, 280][i % 9]} 40% ${40 + (i % 2) * 8}%))">` +
    `<div class="ck"></div><div class="du">0:${String(12 + i * 7).slice(-2)}</div></div>`).join('') + `</div>`;

  // every screen the tutorial shows; data-k marks what can be tapped
  const SCREENS = {
    page: (p, L) => browser(L, shotImg(p)),
    file: (p, L) => browser(L, `<div class="ab" style="inset:0;background:#fff"></div>` +
      `<div class="ab" style="left:141px;top:110px;width:94px;height:122px;background:#fff;border:1.5px solid #c9c9ce;border-radius:4px 22px 4px 4px;box-shadow:0 2px 6px rgba(0,0,0,.08)">` +
      `<div class="ab" style="left:20px;top:34px;width:52px;height:52px;border-radius:12px;background:linear-gradient(135deg,#7aa7ff,#e98bb8 55%,#ffb86b)"></div></div>` +
      `<div class="ab" style="left:0;right:0;top:325px;text-align:center;font-size:22px">${esc(L.fileName)}</div>` +
      `<div class="ab" style="left:0;right:0;top:358px;text-align:center;font-size:17px;color:#8a8a8e">${esc(L.fileMeta)}</div>` +
      `<div class="ab blue" data-k="open" style="left:84px;width:207px;top:443px;height:32px;line-height:32px;text-align:center;font-size:20px;white-space:nowrap">${esc(L.openIn)}</div>` +
      `<div class="ab blue" style="left:0;right:0;top:482px;text-align:center;font-size:20px">${esc(L.more)}</div>`),
    import: (p, L) => `<div class="ab" style="inset:0;background:#1c1c1e"></div>${status(L.backApp, true)}` +
      `<div class="ab" style="left:0;right:0;top:54px;bottom:0;background:#fff;border-radius:12px 12px 0 0"></div>` +
      `<div class="ab blue" style="left:16px;top:70px;font-size:20px">${esc(L.cancel)}</div><div class="ab blue" style="right:16px;top:70px;font-size:20px">${esc(L.report)}</div>` +
      `<div class="ab" style="left:0;right:0;top:111px;text-align:center;font-size:31px;font-weight:700">SaveReel</div>` +
      `<div class="ab" style="left:0;right:0;top:161px;text-align:center;font-size:19px;color:#8a8a8e">${esc(L.shared)}</div>` +
      `<div class="card2" style="left:103px;top:376px;width:169px;height:120px"><div class="ab" style="left:13px;top:12px;width:20px;height:20px;border:2.5px solid #fff;border-radius:6px"></div>` +
      `<div class="ab" style="right:12px;top:12px;width:20px;height:20px;border-radius:50%;background:rgba(255,255,255,.35)"></div>` +
      `<div class="ab" style="left:12px;bottom:12px;font-size:19px;font-weight:700">SaveReel</div></div>` +
      `<div class="btn2" data-k="add" style="left:24px;top:691px;width:327px;height:55px"><div class="plus"></div>${esc(L.addShortcut)}</div><div class="homei"></div>`,
    editor: (p, L) => `<div class="ab" style="inset:0;background:#fff"></div>${status(L.backApp)}` +
      `<div class="ab" style="left:0;right:0;top:50px;height:40px;display:flex;align-items:center;justify-content:center;gap:9px;font-size:20px;font-weight:700">` +
      `<div style="width:24px;height:24px;border-radius:6px;background:linear-gradient(135deg,#ffd36b,#ff8f8f 50%,#8fb4ff)"></div>SaveReel<div style="width:20px;height:20px;border-radius:50%;background:#e5e5ea"></div></div>` +
      `<div class="ab blue" data-k="done" style="left:306px;top:47px;width:56px;height:36px;line-height:36px;text-align:center;font-size:20px;font-weight:700">${esc(L.done)}</div>` +
      L.editor.map((c, i) => `<div class="acard" style="top:${[100, 276, 390, 494][i]}px;${i > 1 ? 'left:32px;' : ''}">${c}</div>`).join('') +
      `<div class="ab" style="left:20px;right:20px;top:667px;height:48px;border-radius:12px;background:#ececf0;color:#8a8a8e;font-size:19px;display:flex;align-items:center;justify-content:center">${esc(L.searchActions)}</div>` +
      `<div class="homei"></div>`,
    share: (p, L) => browser(L, shotImg(p)) + `<div class="dim"></div><div class="sheet2" style="top:430px">` +
      `<div style="display:flex;align-items:center;gap:12px;padding:18px 16px 14px"><img src="${p.icon}" style="width:46px;height:46px;border-radius:11px">` +
      `<div><div style="font-size:16px;font-weight:600">Reel Studio</div><div style="font-size:14px;color:#8a8a8e">${esc(L.pageHost)}</div></div></div>` +
      `<div class="grp"><div class="li">${esc(L.copy)}<div class="g"></div></div><div class="li">${esc(L.favorites)}<div class="g"></div></div>` +
      `<div class="li" data-k="a2hs">${esc(L.addHome)}<div class="g"></div></div></div></div>`,
    a2hs: (p, L) => `<div class="ab" style="inset:0;background:#1c1c1e"></div>${status('', true)}<div class="ab" style="left:0;right:0;top:54px;bottom:0;background:#f2f2f7;border-radius:12px 12px 0 0"></div>` +
      `<div class="navh" style="top:56px"><span class="blue">${esc(L.cancel)}</span><b>${esc(L.addHome)}</b><span class="blue" data-k="add" style="font-weight:600;padding:6px 4px">${esc(L.add)}</span></div>` +
      `<div class="grp" style="position:absolute;left:0;right:0;top:130px;padding:14px;display:flex;gap:14px;align-items:center"><img src="${p.icon}" style="width:62px;height:62px;border-radius:14px">` +
      `<div style="flex:1;font-size:17px"><div style="border-bottom:.5px solid #d4d4d8;padding:6px 0 10px">Reel Studio</div><div style="color:#8a8a8e;font-size:15px;padding-top:8px">${esc(L.pageHost)}</div></div></div><div class="homei"></div>`,
    home: (p, L) => `<div class="wall"></div>${status()}<div class="apps">` +
      ['#f2b880', '#9cc8a8', '#8fb0e8', '#e89aa5', '#b7a3e6', '#f0d27a', '#86c9d6', '#c7c7cc'].map((c, i) =>
        `<div class="ap"><div class="ii" style="background:linear-gradient(160deg,${c},${c}cc)"></div>${esc(L.apps[i])}</div>`).join('') +
      `<div class="ap" data-k="claude"><div class="ii" style="background:var(--acc);display:flex;align-items:center;justify-content:center"><div class="bub2"></div></div>Claude</div>` +
      `<div class="ap" data-k="reel"><img class="ii" src="${p.icon}">Reel Studio</div></div><div class="homei"></div>`,
    picker: (p, L) => `<div class="ab" style="inset:0;background:#1c1c1e"></div>${status('', true)}<div class="ab" style="left:0;right:0;top:54px;bottom:0;background:#fff;border-radius:12px 12px 0 0"></div>` +
      `<div class="navh" style="top:58px"><span class="blue">${esc(L.cancel)}</span><b>${esc(L.photos)}</b><span class="blue" data-k="add" style="font-weight:600;padding:6px 4px;opacity:${p.picked ? 1 : .35}">${esc(L.add)}</span></div>` +
      `<div class="ab" data-k="recent" style="left:16px;top:116px;font-size:20px;font-weight:700">${esc(L.recent)}</div>` +
      thumbsGrid(12, 156) + `<div class="homei"></div>`,
    tabs: (p, L) => `<div class="ab" style="inset:0;background:#fff"></div>${status()}` +
      `<div class="ab" style="left:20px;top:62px;font-size:30px;font-weight:700">Claude</div>` +
      `<div class="ab seg" style="left:20px;top:116px"><div class="sg2 ${p.code ? '' : 'on'}">${esc(L.chat)}</div><div class="sg2 ${p.code ? 'on' : ''}" data-k="code">${esc(L.code)}</div></div>` +
      (p.code ? `<div class="row2" data-k="sess" style="top:176px"><div class="pc"></div>${esc(L.sessName)}<div class="live"></div></div>` +
                `<div class="ab" style="left:20px;top:256px;font-size:15px;color:#8a8a8e">${esc(L.sessNote)}</div>`
              : `<div class="ab" style="left:20px;right:20px;top:190px;font-size:18px;color:#8a8a8e;line-height:1.5">${esc(L.chatEmpty)}</div>`) + `<div class="homei"></div>`,
    chat: (p, L) => `<div class="ab" style="inset:0;background:#fff"></div>${status()}` +
      `<div class="navh"><span class="blue" style="font-size:22px">&#8249;</span><b>${esc(L.sessName)}</b><span></span></div>` +
      `<div class="msg2 me" data-k="mine" style="top:560px">${esc(L.command)}</div><div class="msg2 it" data-k="reply" style="top:625px">${esc(L.reply)}</div>` +
      `<div class="inp2"><div class="tx" data-k="typed"></div><div class="go" data-k="go"></div></div><div class="homei"></div>`,
    allow: (p, L) => `<div class="ab" style="inset:0;background:#f2f2f7"></div>${status()}` +
      `<div class="ab" style="left:20px;top:62px;font-size:30px;font-weight:700">SaveReel</div><div class="dim"></div>` +
      `<div class="alert" style="top:270px"><div class="at">${esc(L.allowTitle)}</div><div class="ab2">${esc(L.allowOnce)}</div>` +
      `<div class="ab2" data-k="always" style="font-weight:600">${esc(L.allowAlways)}</div><div class="ab2">${esc(L.dontAllow)}</div></div>`,
    photos: (p, L) => `<div class="ab" style="inset:0;background:#fff"></div>${status()}` +
      `<div class="ab" style="left:16px;top:58px;font-size:30px;font-weight:700">${esc(L.photos)}</div>` +
      thumbsGrid(15, 110).replace('data-k="th14"', 'data-k="newv"') + `<div class="homei"></div>`,
  };

  // a target box in screen units: a real button (from the page render's measured boxes) or a drawn element
  function target(root, scr, p, k) {
    if (p.rects && p.rects[k]) { const [x, y, w, h] = p.rects[k]; return [x, y + VIEW[0], w, h]; }
    const el = scr.querySelector(`[data-k="${k}"]`); if (!el) return null;
    const a = scr.getBoundingClientRect(), b = el.getBoundingClientRect(), k2 = a.width / PW;
    return [(b.left - a.left) / k2, (b.top - a.top) / k2, b.width / k2, b.height / k2];
  }

  RM.def('t2s', (api, root) => {
    const p = api.p, L = p.labels, dur = api.end - api.start;
    const ow = PW * S2 + 2 * BZ, oh = PH * S2 + 2 * BZ, left = (W() - ow) / 2, top = H() - 40 - oh;
    root.innerHTML = `<div class="tut"><div class="t2cap a" style="font-size:58px">${p.part ? `<div class="badge round">${esc(p.part)}</div>` : ''}<div class="ct">${esc(p.cap)}</div></div>` +
      `<div class="p2 a" style="left:${left}px;top:${top}px;width:${ow}px;height:${oh}px"><div class="s2">${SCREENS[p.screen](p, L)}` +
      `<div class="son"></div><div class="son"></div><div class="son"></div><div class="mark"></div><div class="rip2 round"></div><div class="fdot round"></div></div></div></div>`;
    const cap = root.querySelector('.t2cap'), ct = cap.querySelector('.ct');
    let fs = 58; while (ct.offsetHeight > 3 * 1.16 * fs + 2 && fs > 54) cap.style.fontSize = (fs -= 1) + 'px';
    const scr = root.querySelector('.s2'), sons = [...scr.querySelectorAll('.son')], mark = scr.querySelector('.mark'), dot = scr.querySelector('.fdot'), rip = scr.querySelector('.rip2');
    const taps = (p.taps || []).map(k => ({ k, box: target(root, scr, p, k) })).filter(x => x.box);
    const ring = p.ring ? target(root, scr, p, p.ring) : null;
    const tapT = p.tapAt != null ? [p.tapAt] : taps.map((_, i) => dur - 0.75 - (taps.length - 1 - i) * 0.7);   // the last tap 0.75 s before the next screen
    const typed = scr.querySelector('[data-k="typed"]'), mine = scr.querySelector('[data-k="mine"]'), reply = scr.querySelector('[data-k="reply"]');
    const sel = p.sel || [];
    (p.selected || []).forEach(x => { const el = scr.querySelector(`[data-k="${x}"]`); if (el) el.classList.add('sel'); });
    return tg => {
      const t = tg - api.start;
      // which tap is current: the marker sits on it from the start, the finger comes in and presses at its time
      let i = tapT.findIndex(x => t < x + 0.35); if (i < 0) i = taps.length - 1;
      const cur = taps[i] ? taps[i].box : ring;
      if (cur) {
        const pad = 6, br = 1 + 0.035 * Math.sin(t * 5.2);
        const v = P(t, 0.1, 0.25);
        Object.assign(mark.style, { left: (cur[0] - pad) + 'px', top: (cur[1] - pad) + 'px', width: (cur[2] + 2 * pad) + 'px', height: (cur[3] + 2 * pad) + 'px',
                                    opacity: v.toFixed(3), transform: `scale(${br.toFixed(4)})`, borderRadius: Math.min(16, cur[3] / 2 + pad) + 'px' });
      } else mark.style.opacity = 0;
      // sonar rings: keep growing out of the target, so the eye finds it and the frame is never frozen (the screen itself stays still)
      sons.forEach((el, j) => {
        if (!cur) { el.style.opacity = 0; return; }
        const ph = ((t + j / 3) % 1.0) / 1.0, g = 6 + 38 * E.out(ph);
        Object.assign(el.style, { left: (cur[0] - g) + 'px', top: (cur[1] - g) + 'px', width: (cur[2] + 2 * g) + 'px', height: (cur[3] + 2 * g) + 'px',
                                  opacity: (0.85 * (1 - ph) * P(t, 0.2, 0.3)).toFixed(3), borderRadius: Math.min(16, cur[3] / 2) + g + 'px' });
      });
      if (taps[i]) {
        const b = taps[i].box, cx = b[0] + b[2] / 2, cy = b[1] + b[3] / 2, tt = tapT[i];
        const inn = P(t, tt - 0.55, 0.25) * (1 - P(t, tt + 0.45, 0.25)), u = t - tt;   // a hollow ring just around the tap: the label stays readable
        const press = u >= 0 && u < 0.3 ? 1 - 0.18 * Math.sin(u / 0.3 * Math.PI) : 1;
        Object.assign(dot.style, { left: cx + 'px', top: cy + 'px', opacity: inn.toFixed(3), transform: `scale(${(press * (1.25 - 0.25 * inn)).toFixed(3)})` });
        if (u >= 0 && u < 0.6) { rip.style.left = cx + 'px'; rip.style.top = cy + 'px'; rip.style.opacity = (0.9 * (1 - u / 0.6)).toFixed(3); rip.style.transform = `scale(${(1 + 1.6 * E.out(u / 0.6)).toFixed(3)})`; }
        else rip.style.opacity = 0;
      } else { dot.style.opacity = 0; rip.style.opacity = 0; }
      // selections that follow taps (picker thumbnails)
      taps.forEach((x, j) => { if (sel.includes(x.k)) { const el = scr.querySelector(`[data-k="${x.k}"]`); if (el) el.classList.toggle('sel', t >= tapT[j]); } });
      if (typed) {                                                // the command is typed, sent, then answered
        const n = Math.round(L.command.length * clamp((t - 0.25) / 0.7)), sent = t >= tapT[0];
        typed.textContent = sent ? '' : L.command.slice(0, n);
        mine.style.opacity = P(t, tapT[0] + 0.05, 0.2).toFixed(3); reply.style.opacity = P(t, tapT[0] + 0.7, 0.3).toFixed(3);
      }
    };
  });

})();
