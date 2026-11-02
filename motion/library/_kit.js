/* ReelsMotion bespoke-scene kit (always loaded together with library scenes).
   Bespoke scenes (2026-10-27, the user): every Reel gets NEW scenes drawn for its own script (SVG illustrations, own
   layout, own motion). Each one lives in library/<type>.js with a one-line header the variety check reads:
     /* @scene {"type":"domino","tags":["collapse","chain"],"layout":"row-falling","metaphor":"domino line falling",
                "assets":["domino tiles"]} *\/
     RM.def('domino', (api, root) => { ...; return t => { ... } });
   Rules: pure function of t; elements appear on the word they show (no empty slots waiting); on-screen text = the speaker's own
   words only; colours only from theme tokens (var(--c1) etc.). Helpers below: window.RMK.
*/
(function () {
  'use strict';
  const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const q = (root, s) => root.querySelector(s), qa = (root, s) => Array.from(root.querySelectorAll(s));
  function fitFont(el, maxW, maxH, max, min = 22) {
    let fs = max; el.style.fontSize = fs + 'px';
    const over = () => el.getBoundingClientRect().width > maxW + 0.5 || (maxH && el.getBoundingClientRect().height > maxH + 0.5);
    while (fs > min && over()) { fs -= 2; el.style.fontSize = fs + 'px'; }
    return fs;
  }
  // an absolutely positioned full-box SVG layer in box pixels (0..L.w, 0..L.h); returns html
  const svg = (L, inner, cls = '') => `<svg class="rmk-svg ${cls}" width="${L.w}" height="${L.h}" viewBox="0 0 ${L.w} ${L.h}" overflow="visible" style="position:absolute;left:${L.x0}px;top:${L.y0}px">${inner}</svg>`;
  // stroke draw-on for <path>/<line>/<polyline> elements: u 0..1
  function draw(el, u) {
    if (!el) return;
    const len = el.__len || (el.__len = el.getTotalLength ? el.getTotalLength() : 1000);
    el.style.strokeDasharray = len; el.style.strokeDashoffset = (len * (1 - Math.max(0, Math.min(1, u)))).toFixed(1);
    el.style.visibility = u <= 0.001 ? 'hidden' : 'visible';
  }
  // SVG transform of a group around its own point (x, y): translate/rotate/scale + opacity, from an api.tw-style value
  function gx(el, v, ox = 0, oy = 0) {
    if (!el) return;
    el.setAttribute('transform', `translate(${(ox + (v.x || 0)).toFixed(2)} ${(oy + (v.y || 0)).toFixed(2)}) rotate(${(v.r || 0).toFixed(2)}) scale(${(v.s ?? 1).toFixed(4)})`);
    el.style.opacity = v.o ?? 1; el.style.visibility = (v.o ?? 1) <= 0.003 ? 'hidden' : 'visible';
  }
  // keyframe value without applying (same keys as api.tw)
  function kv(api, keys, t) { const d = document.createElement('div'); api.tw(d, t, keys);
    const m = /translate\(([-\d.]+)px,([-\d.]+)px\).*rotate\(([-\d.]+)deg\) scale\(([-\d.]+),/.exec(d.style.transform) || [];
    return { x: +m[1] || 0, y: +m[2] || 0, r: +m[3] || 0, s: m[4] === undefined ? 1 : +m[4], o: +d.style.opacity }; }
  // a tilted word tag (spoken words only); returns html for api.at
  const tag = (text, fs, cls = '') => `<div class="tag ${cls}" style="font-size:${fs}px">${esc(text)}</div>`;
  // seeded jitter for hand-drawn feel
  const jit = (seed, n = 1) => { let s = seed * 9301 + 49297; return Array.from({ length: n }, () => ((s = (s * 9301 + 49297) % 233280) / 233280) - 0.5); };
  // keep every placed element (api.at points) inside the safe box: measured once at build time, before any tween,
  // so tags and props can never be clipped by the frame edge (QC "outside frame")
  function keepIn(root, L, m = 14) {
    root.querySelectorAll(':scope > .pt').forEach(pt => {
      const a = pt.querySelector('.a'); if (!a) return;
      let r = a.getBoundingClientRect(); if (r.width < 2) return;
      if (r.width > L.w - 2 * m) {                                  // too wide (a long tag): shrink it to fit the box
        const c = a.querySelector('.i > *') || a; c.style.zoom = ((L.w - 2 * m) / r.width).toFixed(3); r = a.getBoundingClientRect();
      }
      let dx = 0, dy = 0;
      if (r.width > L.w - 2 * m) dx = L.cx - (r.left + r.right) / 2;
      else if (r.left < L.x0 + m) dx = L.x0 + m - r.left; else if (r.right > L.x1 - m) dx = L.x1 - m - r.right;
      if (r.bottom > L.y1 - 10) dy = L.y1 - 10 - r.bottom;   // leave room for the camera push-in else if (r.top < L.y0 - 30) dy = L.y0 - 30 - r.top;
      if (dx) pt.style.left = (parseFloat(pt.style.left) + dx).toFixed(1) + 'px';
      if (dy) pt.style.top = (parseFloat(pt.style.top) + dy).toFixed(1) + 'px';
    });
  }
  window.RMK = { esc, q, qa, fitFont, svg, draw, gx, kv, tag, jit, keepIn };
  // every library scene gets keepIn after it builds (stock scenes in scenes.js are registered before this file)
  const def0 = window.RM.def;
  window.RM.def = (name, fn) => def0(name, (api, root) => { const u = fn(api, root); keepIn(root, api.L); return u; });
})();
