// ReelsMotion renderer: storyboard.json -> frames in pinned chrome-headless-shell (CDP over Node's built-in WebSocket,
// no npm at render time) -> ffmpeg. Parallel workers, each its own browser process and ffmpeg part.
//
//   node render.mjs <storyboard.json> --out out.mp4            full render (+ voice + subs.ass when the storyboard names them)
//   node render.mjs <storyboard.json> --preview 1.5,4,9        PNG stills -> <dir>/preview/
//   node render.mjs <storyboard.json> --out clip.mkv --alpha   transparent clip (ffv1 bgra), e.g. hybrid segments
//   options: --workers 6  --report report.json  --crf 18  --html-only
// Why chrome-headless-shell: a desktop browser's first launch on a fresh profile can hang forever in --screenshot mode and
// it updates under us. The pinned headless shell has no first-run UI, starts in ~0.3 s from any shell and never hangs.
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import zlib from 'node:zlib';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ENGINE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(ENGINE, '..');
const DATA = process.env.REEL_STUDIO_DATA || '';                 // the plugin data dir (set by reel-tool)
const ENVDIR = path.join(DATA, 'env');
const NM = process.env.RS_FONT_MODULES || path.join(ENVDIR, 'fonts', 'node_modules');   // @fontsource packages (setup)
const argv = process.argv.slice(2);
const opt = (k, d = null) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const flag = k => argv.includes(k);
const sbPath = path.resolve(argv[0]);
const DIR = path.dirname(sbPath);
const SB = JSON.parse(fs.readFileSync(sbPath, 'utf8'));
const rel = p => (p && !path.isAbsolute(p) ? path.join(DIR, p) : p);

export function findFfmpeg() {
  const ext = process.platform === 'win32' ? '.exe' : '';
  const c = [process.env.RS_FFMPEG, path.join(ENVDIR, 'ffmpeg', 'bin', 'ffmpeg' + ext)];
  return c.find(p => p && fs.existsSync(p)) || 'ffmpeg';
}
const FFMPEG = findFfmpeg();
function findBrowser() {
  if (process.env.RS_CHROME && fs.existsSync(process.env.RS_CHROME)) return process.env.RS_CHROME;
  const bin = path.join(ENVDIR, 'chrome');
  const v = fs.existsSync(bin) ? fs.readdirSync(bin).filter(d => d.startsWith('chs-')).sort().pop() : null;
  if (!v) throw new Error('chrome-headless-shell not found: run /reel-setup');
  const sub = fs.readdirSync(path.join(bin, v)).find(d => d.startsWith('chrome-headless-shell'));
  return path.join(bin, v, sub, process.platform === 'win32' ? 'chrome-headless-shell.exe' : 'chrome-headless-shell');
}

// ---------- page assembly ----------
function themeFile(name) {                                     // a brand profile in the data dir, a bundled theme, or a path
  const n = name || 'default';
  const c = [path.join(DATA, 'brands', n, 'theme.json'), path.join(ROOT, 'themes', n + '.json'), rel(n)];
  const f = c.find(p => p && fs.existsSync(p));
  if (!f) throw new Error('theme not found: ' + n);
  return f;
}
const theme = JSON.parse(fs.readFileSync(themeFile(SB.theme), 'utf8'));
const [W, H] = SB.size || [1080, 1920];
let words = [], total = SB.t1 || 0;
if (SB.words) {
  const wj = JSON.parse(fs.readFileSync(rel(SB.words), 'utf8'));
  const fix = SB.fix || (SB.edit && fs.existsSync(rel(SB.edit)) ? JSON.parse(fs.readFileSync(rel(SB.edit), 'utf8')).fix : {}) || {};
  words = (wj.words || wj).map((w, i) => [w[0], w[1], fix[i] || w[2]]);
  total = total || wj.total || words[words.length - 1][1] + 0.6;
}
const t0 = SB.t0 ?? 0, t1 = SB.t1 ?? total;
const box = SB.box || (H > 1500 ? [50, 196, 1030, 1205] : [40, 40, 1040, H - 40]);   // full: 35 px above the subtitle band (camera push-in margin)

const extraJs = (SB.extra_js || []).map(p => fs.readFileSync(rel(p), 'utf8'));
const scenesJs = fs.readFileSync(path.join(ENGINE, 'scenes.js'), 'utf8');
const sbText = JSON.stringify(SB) + scenesJs + extraJs.join('\n');

const BUNDLES = {};                                            // assets/icons/<style>.json.gz: { name: svg }, noto = iconify shape
const bundle = k => (BUNDLES[k] ??= JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(ROOT, 'assets', 'icons', k + '.json.gz'))).toString('utf8')));
function loadIcon(ref) {
  const [kind, name] = ref.split(':');
  if (kind === 'noto') {
    const N = bundle('noto'), ic = N.icons[name] || N.icons[N.aliases?.[name]?.parent];
    if (!ic) return null;
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ic.width || N.width || 128} ${ic.height || N.height || 128}">${ic.body}</svg>`;
  }
  return bundle(kind)[name] || null;
}
const icons = {}, MISSING = [];
for (const m of sbText.matchAll(/["'`]((?:ph|ph-fill|ph-bold|ph-reg|tb|tbf|noto):[a-z0-9-]+)["'`]/g)) {
  if (icons[m[1]]) continue;
  const svg = loadIcon(m[1]);
  if (svg) icons[m[1]] = svg; else MISSING.push(m[1]);
}
// a missing icon draws as an empty box in the Reel: stop here and say which (names as on phosphoricons.com / tabler.io)
if (MISSING.length) { console.error('icon not found: ' + MISSING.join(', ') + '. Pick existing names (reel-tool icon --find word).'); process.exit(2); }
const needPeeps = /"peep"|peep\(/.test(JSON.stringify(SB)) || /peep/.test(extraJs.join(''));
const peeps = needPeeps ? JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/peeps/peeps.json'), 'utf8')) : null;

function fontFaces() {
  let css = '';
  for (const [fam, f] of Object.entries(theme.fonts.files)) {
    const dir = path.join(NM, f.pkg);
    if (f.ttf) {                                               // a brand's own font file (brand wizard)
      for (const [w, file] of Object.entries(f.ttf)) css += `@font-face{font-family:'${fam}';font-weight:${w};src:url(${pathToFileURL(file).href})}`;
      continue;
    }
    for (const w of f.weights) {
      const p = path.join(dir, `${w}.css`);
      if (!fs.existsSync(p)) continue;
      css += fs.readFileSync(p, 'utf8').replace(/url\(\.\/files\/([^)]+)\)/g, (m, file) => `url(${pathToFileURL(path.join(dir, 'files', file)).href})`)
        .replace(/, url\([^)]+\.woff\) format\('woff'\)/g, '');
    }
  }
  return css;
}
function themeVars() {
  const c = theme.colors, f = theme.fonts, v = { '--W': W + 'px', '--H': H + 'px' };
  for (const [k, x] of Object.entries(c)) v['--' + k] = x;
  v['--f-display'] = `'${f.display.family}', 'Arial Black', sans-serif`; v['--w-display'] = f.display.weight;
  v['--f-head'] = `'${f.head.family}', Arial, sans-serif`; v['--f-body'] = `'${f.body.family}', Arial, sans-serif`; v['--w-body'] = f.body.weight;
  v['--r-s'] = theme.radius.s + 'px'; v['--r-m'] = theme.radius.m + 'px'; v['--r-l'] = theme.radius.l + 'px';
  v['--sh'] = theme.shadow; v['--grid-op'] = theme.grid; v['--orb'] = c.c1;
  v['--title-fs'] = theme.title.fs + 'px'; v['--title-top'] = theme.title.top + 'px'; v['--mark-top'] = (H > 1500 ? 150 : 14) + 'px';
  if (!c.substrip) v['--substrip'] = 'none';
  const alt = theme.alt ? 'section.scene.alt{' + Object.entries(theme.alt).map(([k, x]) => `--${k}:${x}`).join(';') + '}' : '';
  return ':root{' + Object.entries(v).map(([k, x]) => `${k}:${x}`).join(';') + '}' + alt;
}
// image paths in scenes ("src") are relative to the storyboard: make them absolute file URLs for the page in _build/
(function fixSrc(o) {
  if (Array.isArray(o)) o.forEach(fixSrc);
  else if (o && typeof o === 'object') for (const [k, v] of Object.entries(o)) {
    if (k === 'src' && typeof v === 'string' && !/^(https?|file|data):/.test(v)) o[k] = pathToFileURL(rel(v)).href;
    else fixSrc(v);
  }
})(SB.scenes);
const titleBottom = SB.title ? theme.title.top + theme.title.fs * 1.05 + theme.title.fs * 0.6 * (SB.title.lines.length - 1) + 40 : box[1];
const CFG = { W, H, fps: SB.fps || 30, t0, t1, box, titleBottom, words, theme, board: SB, icons, peeps, snap: SB.snap,
  alphaIn: SB.alpha?.in || null, alphaOut: SB.alpha?.out || null, tin: SB.tin };
const html = `<!doctype html><html><head><meta charset="utf-8"><style>${fontFaces()}\n${themeVars()}\n${fs.readFileSync(path.join(ENGINE, 'base.css'), 'utf8')}${SB.css ? '\n' + SB.css : ''}</style></head>
<body class="${SB.placeholders ? 'ph-on' : ''}"><div id="frame">
<div id="bg"><div class="bgl" id="bgA"></div><div class="bgl" id="bgB"></div><div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div><div id="sweep"></div><div id="grid"></div><div id="vig"></div></div>
<div id="world"><div id="stage"></div></div>
<div id="substrip"></div>
<canvas id="fx" width="${W}" height="${H}"></canvas>
<div id="title"></div>${theme.wordmark && !SB.noMark ? `<div id="mark">${theme.wordmark}</div>` : ''}
<div id="wipe" style="display:none"></div><div id="iris" style="display:none"></div>
<svg width="0" height="0" style="position:absolute"><filter id="mbxf" x="-20%" y="-5%" width="140%" height="110%"><feGaussianBlur id="mbx" stdDeviation="0 0"/></filter>
<filter id="mbyf" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur id="mby" stdDeviation="0 0"/></filter></svg>
</div>
<script>window.CFG=${JSON.stringify(CFG)};</script>
<script>${fs.readFileSync(path.join(ENGINE, 'runtime.js'), 'utf8')}</script>
<script>${scenesJs}</script>
${extraJs.map(j => `<script>${j}</script>`).join('\n')}
<script>RM_BOOT().catch(e => { window.__error = String(e && e.stack || e); });</script>
</body></html>`;
const BUILD = path.join(DIR, '_build');
fs.mkdirSync(BUILD, { recursive: true });
const page = path.join(BUILD, path.basename(sbPath, '.json') + '.html');
fs.writeFileSync(page, html);
if (flag('--html-only')) { console.log(page); process.exit(0); }

// ---------- browser workers ----------
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function startWorker(k) {
  const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'rm_prof_'));
  const exe = findBrowser();
  const proc = spawn(exe, ['--headless', '--remote-debugging-port=0', `--user-data-dir=${prof}`, '--no-first-run',
    '--no-default-browser-check', '--disable-extensions', '--mute-audio', '--hide-scrollbars', '--force-device-scale-factor=1',
    `--window-size=${W},${H}`, '--allow-file-access-from-files', '--disable-background-timer-throttling',
    '--disable-renderer-backgrounding', '--run-all-compositor-stages-before-draw', 'about:blank'],
    { detached: false, stdio: ['ignore', 'ignore', fs.openSync(path.join(BUILD, `browser_${k}.log`), 'a')] });
  let target, port = 0;
  for (let i = 0; i < 150 && !target; i++) {
    await sleep(100);
    try { port = port || +fs.readFileSync(path.join(prof, 'DevToolsActivePort'), 'utf8').split('\n')[0]; } catch {}
    if (port) try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(x => x.type === 'page'); } catch {}
  }
  if (!target) { proc.kill(); throw new Error('browser did not start: ' + exe); }
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let seq = 0; const waiting = new Map(), events = [];
  const fail = why => { for (const [, [, rej]] of waiting) rej(new Error(why)); waiting.clear(); };
  ws.onclose = () => fail(`browser ${k} disconnected (see _build/browser_${k}.log)`);
  ws.onerror = () => fail(`browser ${k} socket error`);
  proc.on('exit', c => fail(`browser ${k} exited (${c})`));
  ws.onmessage = m => {
    const d = JSON.parse(m.data);
    if (d.id && waiting.has(d.id)) { const [res, rej] = waiting.get(d.id); waiting.delete(d.id); d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result); }
    else if (d.method) events.push(d.method);
  };
  // every call has a deadline: a browser that stops answering is replaced, and rendering resumes at the same frame
  const send = (method, params = {}, ms = 30000) => new Promise((res, rej) => { const id = ++seq;
    const tm = setTimeout(() => { waiting.delete(id); rej(new Error(`browser ${k} did not answer ${method} in ${ms / 1000} s`)); }, ms);
    waiting.set(id, [v => { clearTimeout(tm); res(v); }, e => { clearTimeout(tm); rej(e); }]); ws.send(JSON.stringify({ id, method, params })); });
  const js = async expr => {
    const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  };
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  if (flag('--alpha')) await send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
  await send('Page.navigate', { url: pathToFileURL(page).href });
  for (let i = 0; i < 300; i++) { if (await js('!!(window.__ready || window.__error)').catch(() => false)) break; await sleep(100); }
  const err = await js('window.__error || null');
  if (err) throw new Error('page error: ' + err);
  const shot = async t => {
    const cc = await js(`(RM.seek(${t}), new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => r(RM.circleCheck())))))`);
    CIRCLES.n++; if (cc[0] > CIRCLES.max[0]) CIRCLES.max = [cc[0], +t.toFixed(3), cc[1]]; if (cc[0] > 0.02) CIRCLES.fails.push([+t.toFixed(3), cc[0], cc[1]]);
    return Buffer.from((await send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true, fromSurface: true })).data, 'base64');
  };
  const close = async () => { try { await send('Browser.close', {}, 3000); } catch {} ws.close(); await sleep(200); try { proc.kill(); } catch {}
    try { fs.rmSync(prof, { recursive: true, force: true }); } catch {} };
  return { shot, js, close };
}

function ff(args, opts = {}) { return spawn(FFMPEG, ['-hide_banner', '-loglevel', 'error', '-y', ...args], { stdio: ['pipe', 'inherit', 'inherit'], ...opts }); }
const done = p => new Promise((res, rej) => p.on('close', c => (c ? rej(new Error('ffmpeg exit ' + c)) : res())));

const FPS = CFG.fps;
const CIRCLES = { n: 0, max: [0, 0, ''], fails: [] };            // per-frame roundness of every circular element
const N = Math.round((t1 - t0) * FPS);
const t_0 = Date.now();

const prev = opt('--preview');
if (prev) {
  const w = await startWorker(0);
  try {
    fs.mkdirSync(path.join(DIR, 'preview'), { recursive: true });
    for (const t of prev.split(',').map(Number)) {
      fs.writeFileSync(path.join(DIR, 'preview', `t_${t.toFixed(2)}.png`), await w.shot(t));
    }
    console.log('scenes', JSON.stringify(await w.js('RM.scenes')));
  } finally { await w.close(); }
  console.log(`preview ${prev.split(',').length} stills in ${((Date.now() - t_0) / 1000).toFixed(1)} s -> ${path.join(DIR, 'preview')}`);
  process.exit(0);
}

const out = path.resolve(opt('--out', path.join(DIR, 'render.mp4')));
const alpha = flag('--alpha');
const nW = Math.max(1, Math.min(Number(opt('--workers', Math.max(2, Math.min(6, os.cpus().length / 2 - 1)))), Math.ceil(N / 30)));
const parts = [];
const ranges = Array.from({ length: nW }, (_, k) => [Math.floor(N * k / nW), Math.floor(N * (k + 1) / nW)]);
console.log(`render ${N} frames (${(t1 - t0).toFixed(2)} s) with ${nW} workers -> ${out}`);
let rendered = 0, EVENTS = [], SAMPLES = null;
await Promise.all(ranges.map(async ([a, b], k) => {
  const part = path.join(BUILD, `part_${k}.mkv`); parts[k] = part;
  const enc = alpha ? ['-c:v', 'ffv1', '-pix_fmt', 'bgra'] : ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '8', '-pix_fmt', 'yuv420p'];
  const p = ff(['-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-', ...enc, part]);
  const fin = done(p);
  p.stdin.on('error', () => {});                              // ffmpeg's own exit code reports the failure
  const closed = new Promise(r => p.once('close', r));
  let i = a, w = null;
  for (let attempt = 0; attempt < 6 && i < b; attempt++) {     // a crashed browser is replaced; rendering resumes at frame i
    try {
      w = await startWorker(k + attempt * 10);
      for (; i < b; i++) {
        const buf = await w.shot(t0 + i / FPS);
        if (!p.stdin.write(buf)) await Promise.race([new Promise(r => p.stdin.once('drain', r)), closed]);
        if (++rendered % 150 === 0) console.log(`  ${rendered}/${N} frames  ${((Date.now() - t_0) / 1000).toFixed(0)} s`);
      }
      if (k === 0) EVENTS = await w.js('RM.events()');
      if (k === 0 && opt('--report')) {                     // layout samples for qc.py
        const samples = [];
        for (let t = t0; t < t1; t += 0.25) samples.push([+t.toFixed(2), await w.js(`RM.report(${t})`)]);
        SAMPLES = { samples, scenes: await w.js('RM.scenes') };
      }
    } catch (e) {
      console.log(`  worker ${k}: ${e.message} at frame ${i}; restarting`);
    } finally { if (w) await w.close(); w = null; }
  }
  p.stdin.end();
  if (i < b) throw new Error(`worker ${k} failed at frame ${i}`);
  await fin;
}));

if (opt('--report') && SAMPLES) fs.writeFileSync(opt('--report'), JSON.stringify({ W, H, box, t0, t1, scenes: SAMPLES.scenes, samples: SAMPLES.samples,
  circles: { frames: CIRCLES.n, max: CIRCLES.max, fails: CIRCLES.fails.slice(0, 200), failCount: CIRCLES.fails.length } }));
console.log(`circle check: ${CIRCLES.n} frames, worst ${(CIRCLES.max[0] * 100).toFixed(2)} % ${CIRCLES.max[2] || ''}${CIRCLES.fails.length ? `  FAIL on ${CIRCLES.fails.length} frames` : '  ok'}`);
const list = path.join(BUILD, 'parts.txt');
fs.writeFileSync(list, parts.map(p => `file '${p.replace(/\\/g, '/').replace(/'/g, "'\\''")}'`).join('\n'));
if (alpha) {
  await done(ff(['-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out]));
} else {
  const fonts = path.join(BUILD, 'fonts'); fs.mkdirSync(fonts, { recursive: true });
  for (const f of (process.env.RS_SUB_FONTS || '').split(path.delimiter).filter(Boolean)) try { fs.copyFileSync(f, path.join(fonts, path.basename(f))); } catch {}
  const args = ['-f', 'concat', '-safe', '0', '-i', list];
  let audio = SB.voice ? rel(SB.voice) : null;
  if (audio && SB.sfx && EVENTS.length) {                    // synthesised whoosh/pop under the voice (the voice itself is untouched)
    const evf = path.join(BUILD, 'sfx_events.json'), mixed = path.join(BUILD, 'voice_sfx.wav');
    fs.writeFileSync(evf, JSON.stringify(EVENTS));
    const py = process.env.RS_PYTHON || 'python';
    const r = spawnSync(py, [path.join(ROOT, 'tools', 'sfx.py'), evf, audio, mixed, '--level', String(SB.sfxLevel ?? -22)], { stdio: 'inherit' });
    if (r.status === 0) audio = mixed; else console.log('sfx failed; voice only');
  }
  if (audio) args.push('-i', audio);
  const vf = SB.subs ? ['-vf', `ass='${path.relative(BUILD, rel(SB.subs)).replace(/\\/g, '/')}':fontsdir=fonts`] : [];
  args.push(...vf, '-map', '0:v');
  if (audio) args.push('-map', '1:a', '-c:a', 'aac', '-b:a', '192k');
  args.push('-t', (t1 - t0).toFixed(3), '-c:v', 'libx264', '-preset', 'medium', '-crf', opt('--crf', '18'), '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', '-metadata', 'comment=Reel Studio render', out);
  await done(ff(args, { cwd: BUILD }));
}
for (const p of parts) try { fs.unlinkSync(p); } catch {}
console.log(`done ${out}  ${((Date.now() - t_0) / 1000).toFixed(1)} s`);
