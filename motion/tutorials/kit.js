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
      `<div class="hlr"></div><div class="rip"></div>${o.pointer === false ? '' : wd ? POINTER : '<div class="rip fing round"></div>'}</div></div>`;
  }
  const POINTER = `<svg class="ptr" viewBox="0 0 46 60"><path d="M4 3 L4 47 L15 37 L23 56 L31 52 L23 34 L39 34 Z" fill="var(--ink)" stroke="var(--paper)" stroke-width="4" stroke-linejoin="round"/></svg>`;

  // the action player: everything below is recomputed from t alone
  function player(api, root, p, o = {}) {
    const q = s => root.querySelector(s), qa = s => [...root.querySelectorAll(s)];
    const stage = q('.stage'), acts = (p.acts || []).slice().sort((a, b) => a.t - b.t);
    const K = k => root.querySelector(`[data-k="${k}"]`);
    const ptr = q('.ptr'), fing = q('.rip.fing'), rip = q('.rip:not(.fing)'), hlr = q('.hlr');
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
      // the whole screen drifts slowly by a few pixels, so a calm moment is never a frozen one
      stage.style.transform = `translate(${(12 * Math.sin(t * 0.7 + 0.6)).toFixed(2)}px, ${(9 * Math.sin(t * 0.85)).toFixed(2)}px)`;
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
                   : `<div class="sk a" style="left:${W() / 2 - 210}px;top:900px;width:420px;height:850px"><div class="tphone" style="border-radius:60px;padding:16px"><div class="scr" style="inset:16px;border-radius:46px"><div class="scrn" style="padding-top:90px">${phs(5)}</div></div><div class="pill" style="top:30px;width:110px;height:30px;margin-left:-55px"></div></div></div>`;
    root.innerHTML = `<div class="tut"><div class="ttl a" style="left:60px;right:60px;top:${wd ? 170 : 330}px;font-size:${wd ? 104 : 104}px">${esc(p.title)}</div>` +
      `<div class="tsub a" style="left:80px;right:80px;top:${wd ? 330 : 600}px;font-size:${wd ? 50 : 56}px">${esc(p.sub)}</div>${art}</div>`;   // the art itself is the tweened box (a full-width wrapper would rotate into a phantom box)
    const [tt, ts, ar] = root.querySelectorAll('.a');
    return tg => {
      const t = tg - api.start;
      api.tw(tt, t, api.K.rise(0.1, 0.6)); api.tw(ts, t, api.K.rise(0.45, 0.6));
      const u = P(t, 0.7, 0.8, 'out');
      ar.style.opacity = u; ar.style.transform = `translateY(${((1 - u) * 60 + 10 * Math.sin(t * 1.2)).toFixed(1)}px) rotate(${(0.6 * Math.sin(t * 0.8)).toFixed(3)}deg)`;
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
        r.style.opacity = u; r.style.transform = `translateX(${((1 - u) * 80).toFixed(1)}px) translateY(${(4 * Math.sin(t * 1.4 + i)).toFixed(1)}px)`;
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

  // ---------- Tutorial 2: the iPhone ----------
  const phone = inner => `<div class="tphone"><div class="scr">${inner}</div><div class="pill"></div></div>`;
  const thumbs = (n, sel = [], cls = '') => Array.from({ length: n }, (_, i) =>
    `<div class="th ${['', 'b', 'c'][i % 3]} ${cls}" ${sel.includes(i) ? `data-k="th${i}"` : ''}><div class="ck round"></div><div class="du">0:${String(12 + i * 7).slice(-2)}</div></div>`).join('');

  RM.def('t2_link', (api, root) => {
    const p = api.p, L = p.labels;
    const scr = `<div class="urlbar">${esc(L.linkHost)}</div><div class="scrn" style="padding-top:220px">` +
      `<div class="pcard" data-k="link" style="display:flex;align-items:center;gap:24px"><div class="act" style="padding:0;border:0;background:none"><div class="ag"></div></div><div><b>SaveReel</b><div class="ptext">${esc(L.linkHost)}</div></div></div>` +
      `${phs(3)}</div>` +
      `<div class="sheet" data-k="sheet" data-from="bottom"><div class="grab"></div><div style="display:flex;align-items:center;gap:26px"><div class="act" style="padding:0;border:0;background:none"><div class="ag" style="width:110px;height:110px;border-radius:26px"></div></div>` +
      `<div class="ptitle">SaveReel</div></div><div class="ptext">${esc(L.actionsShort)}</div><div class="pbtn" data-k="add">${esc(L.addShortcut)}</div></div>` +
      `<div class="banner" data-k="done"><div class="sq"></div>SaveReel<div class="tick round"></div></div>`;
    root.innerHTML = frame(p, phone(scr));
    return player(api, root, p);
  });

  RM.def('t2_build', (api, root) => {
    const p = api.p, L = p.labels;
    const scr = `<div class="scrn"><div class="ptext">${esc(L.shortcutsApp)}</div><div class="field" data-k="name"></div>` +
      `<div class="act" data-k="a1"><div class="ag"></div>${esc(L.getContents)}</div>` +
      `<div class="act" data-k="a2"><div class="ag b"></div>${esc(L.saveToAlbum)}</div></div>`;
    root.innerHTML = frame(p, phone(scr));
    return player(api, root, p);
  });

  RM.def('t2_home', (api, root) => {
    const p = api.p, L = p.labels;
    const page = `<div class="urlbar">${esc(L.pageHost)}</div><div class="scrn" style="padding-top:210px"><div class="ptitle">${esc(L.pageTitle)}</div>` +
      `<div class="pbtn">${esc(L.choose)}</div><div class="pcard"><b>${esc(L.finished)}</b><div class="ptext">${phs(1)}</div></div></div>` +
      `<div class="safbar"><div class="sg"></div><div class="sg"></div><div class="share" data-k="share"><div class="bx"></div><div class="st"></div><div class="hd"></div></div><div class="sg"></div><div class="sg"></div></div>` +
      `<div class="sheet" data-k="sheet" data-from="bottom"><div class="grab"></div><div class="ptext" style="text-align:center">${esc(L.share)}</div>` +
      `<div class="lrow"><div class="gl"></div>${phs(1)}</div><div class="lrow" data-k="a2hs"><div class="gl"></div>${esc(L.addHome)}</div><div class="lrow"><div class="gl"></div>${phs(1)}</div></div>` +
      `<div class="sheet" data-k="confirm" data-from="bottom" style="top:110px;border-radius:44px"><div style="display:flex;justify-content:flex-end"><div class="pbtn ghost" data-k="addbtn" style="padding:14px 34px;font-size:36px">${esc(L.add)}</div></div>` +
      `<div style="display:flex;align-items:center;gap:26px"><div class="ai me" style="width:120px;height:120px;border-radius:28px;background:var(--c1);display:flex;align-items:center;justify-content:center"><div class="reelic"></div></div>` +
      `<div class="field" style="flex:1">Reel Studio</div></div></div>` +
      `<div data-k="homegrid" style="position:absolute;inset:0;background:var(--c1x);z-index:20"><div class="grid">` +
      Array.from({ length: 11 }, () => `<div class="app"><div class="ai"></div>${phs(1)}</div>`).join('') +
      `<div class="app" data-k="icon"><div class="ai me"><div class="reelic"></div></div>Reel Studio</div></div></div>`;
    root.innerHTML = frame(p, phone(page));
    return player(api, root, p);
  });

  RM.def('t2_upload', (api, root) => {
    const p = api.p, L = p.labels;
    const page = `<div class="scrn" style="padding-top:150px"><div class="ptitle">${esc(L.pageTitle)}</div>` +
      `<div class="pbtn" data-k="choose">${esc(L.choose)}</div>` +
      `<div data-k="files" style="display:flex;flex-direction:column;gap:16px">` +
      [0, 1].map(i => `<div class="pcard" style="padding:18px 24px"><b>IMG_${4021 + i}.MOV</b><div class="bar2" style="margin-top:12px"><div data-k="bar${i}"></div></div></div>`).join('') +
      `<div class="pbtn" data-k="send">${esc(L.send)}</div></div>` +
      `<div class="pcard" data-k="done" style="background:var(--good);color:var(--paper);text-align:center;font-weight:800;font-size:44px">${esc(L.done)}</div></div>` +
      `<div class="sheet" data-k="picker" data-from="bottom" style="top:150px;padding:30px 24px"><div class="grab"></div>` +
      `<div class="ptitle" style="font-size:44px" data-k="recent">${esc(L.recent)}</div><div class="ptext" style="font-size:30px">${esc(L.recentNote)}</div>` +
      `<div class="thumbs">${thumbs(6, [1, 3])}</div><div class="pbtn" data-k="pickdone" style="padding:22px">${esc(L.pickDone)}</div></div>`;
    root.innerHTML = frame(p, phone(page));
    const upd = player(api, root, p);
    const bars = [0, 1].map(i => root.querySelector(`[data-k="bar${i}"]`));
    return tg => {
      upd(tg);
      const t = tg - api.start;
      bars.forEach((b, i) => { b.style.width = (100 * P(t, (p.barAt || 4.3) + i * 0.9, 1.1, 'io')).toFixed(1) + '%'; });
    };
  });

  RM.def('t2_claude', (api, root) => {
    const p = api.p, L = p.labels;
    const scr = `<div data-k="homegrid" style="position:absolute;inset:0;background:var(--c1x);z-index:20"><div class="grid">` +
      Array.from({ length: 6 }, () => `<div class="app"><div class="ai"></div>${phs(1)}</div>`).join('') +
      `<div class="app" data-k="appicon"><div class="ai cl"><div class="bub"></div></div>Claude</div>` +
      Array.from({ length: 5 }, () => `<div class="app"><div class="ai"></div>${phs(1)}</div>`).join('') + `</div></div>` +
      `<div class="scrn" style="padding-top:130px"><div class="tabs"><div class="tab">${esc(L.chat)}</div><div class="tab" data-k="code">Code</div></div>` +
      `<div class="sess" data-k="sess"><div class="pc"></div>Reels<div class="live round"></div></div><div class="sess" style="opacity:.5"><div class="pc"></div>${phs(1)}</div></div>` +
      `<div data-k="chat" style="position:absolute;inset:0;background:var(--paper);z-index:15"><div class="scrn" style="padding-top:130px">` +
      `<div class="ptitle" style="font-size:42px">Reels</div><div style="flex:1"></div>` +
      `<div class="tmsg me" data-k="mine"><span>${esc(L.command)}</span></div><div class="tmsg it" data-k="reply">${esc(L.reply)}</div><div style="height:150px"></div></div>` +
      `<div class="inp"><div class="tx" data-k="typed"></div><div class="go round" data-k="go"></div></div></div>`;
    root.innerHTML = frame(p, phone(scr));
    return player(api, root, p);
  });

  RM.def('t2_gallery', (api, root) => {
    const p = api.p, L = p.labels;
    const scr = `<div class="scrn" style="padding-top:150px"><div class="ptitle">${esc(L.finished)}</div>` +
      `<div class="pcard" style="display:flex;align-items:center;gap:20px"><div style="flex:1"><b>${esc(L.reelName)}</b><div class="ptext">${phs(1)}</div></div>` +
      `<div class="pbtn" data-k="gallery" style="padding:20px 26px;font-size:34px">${esc(L.gallery)}</div></div>${phs(3)}</div>` +
      `<div class="banner" data-k="run"><div class="sq"></div>SaveReel<div class="tick round"></div></div>` +
      `<div data-k="photos" style="position:absolute;inset:0;background:var(--paper);z-index:20"><div class="scrn" style="padding-top:130px;gap:16px">` +
      `<div class="ptitle">${esc(L.photos)}</div><div class="thumbs"><div class="th newv" data-k="newv"><div class="du">0:41</div></div>${thumbs(11)}</div></div></div>`;
    root.innerHTML = frame(p, phone(scr));
    return player(api, root, p);
  });
})();
