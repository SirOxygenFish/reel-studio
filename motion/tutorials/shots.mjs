// Real screenshots of the upload page for Tutorial 2: iPhone 11 Pro size (375 CSS px wide, 3x), the Safari viewport only
// (status bar and Safari bars are drawn by kit.js around it). Run by scripts/tutorials.py against a scratch copy of the page.
//   node shots.mjs <page url with ?k=> <lang> <out dir> <ready dir> <sample.mp4> <reel title> <clip1> <clip2>
// Writes <state>.png for: install, page, chosen, sent, ready, and rects.json with the boxes (CSS px) of the buttons tapped.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';

const [URL0, LANG, OUT, READY, SAMPLE, TITLE, ...CLIPS] = process.argv.slice(2);
const VW = 375, VH = 619, DPR = 3;          // 812 minus the status and address bars (109) and the toolbar (84), as measured on an iPhone 11 Pro
const UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
const ENVDIR = path.join(process.env.REEL_STUDIO_DATA || '', 'env');
const sleep = ms => new Promise(r => setTimeout(r, ms));

function findBrowser() {
  if (process.env.RS_CHROME && fs.existsSync(process.env.RS_CHROME)) return process.env.RS_CHROME;
  const bin = path.join(ENVDIR, 'chrome');
  const v = fs.existsSync(bin) ? fs.readdirSync(bin).filter(d => d.startsWith('chs-')).sort().pop() : null;
  if (!v) throw new Error('chrome-headless-shell not found: run /reel-setup');
  const sub = fs.readdirSync(path.join(bin, v)).find(d => d.startsWith('chrome-headless-shell'));
  return path.join(bin, v, sub, process.platform === 'win32' ? 'chrome-headless-shell.exe' : 'chrome-headless-shell');
}

const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'rs_shots_'));
const proc = spawn(findBrowser(), ['--headless', '--remote-debugging-port=0', `--user-data-dir=${prof}`, '--no-first-run', '--hide-scrollbars',
  '--no-default-browser-check', '--disable-extensions', '--mute-audio', `--window-size=${VW},${VH}`, 'about:blank'], { stdio: 'ignore' });
const kill = () => { try { proc.kill(); } catch {} };
const watchdog = setTimeout(() => { console.error('shots: no progress in 120 s'); kill(); process.exit(2); }, 120000);
let target, port = 0;
for (let i = 0; i < 150 && !target; i++) {
  await sleep(100);
  try { port = port || +fs.readFileSync(path.join(prof, 'DevToolsActivePort'), 'utf8').split('\n')[0]; } catch {}
  if (port) try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(x => x.type === 'page'); } catch {}
}
if (!target) { kill(); throw new Error('browser did not start'); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let seq = 0; const waiting = new Map();
ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && waiting.has(d.id)) { const [res, rej] = waiting.get(d.id); waiting.delete(d.id); d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result); } };
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; waiting.set(id, [res, rej]); ws.send(JSON.stringify({ id, method, params })); });
const js = async expr => {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};
const until = async (expr, ms = 30000) => { for (let i = 0; i < ms / 100; i++) { if (await js(expr).catch(() => false)) return; await sleep(100); } throw new Error('timed out: ' + expr); };

await send('Page.enable'); await send('Runtime.enable'); await send('DOM.enable');
await send('Emulation.setDeviceMetricsOverride', { width: VW, height: VH, deviceScaleFactor: DPR, mobile: true });
await send('Emulation.setUserAgentOverride', { userAgent: UA, platform: 'iPhone' });
await send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });

const open = async () => {
  await send('Page.navigate', { url: URL0 });
  await until(`document.readyState === 'complete' && !!document.getElementById('readyList') && document.getElementById('readyList').textContent.trim().length > 0`);
  await js(`document.fonts.ready.then(() => true)`); await sleep(300);
};
const box = sel => js(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) return null; const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(v => Math.round(v * 10) / 10); })()`);
const rects = {};
async function shot(name, keys) {
  await sleep(250);
  const r = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(OUT, name + '.png'), Buffer.from(r.data, 'base64'));
  rects[name] = {};
  for (const [k, sel] of Object.entries(keys)) { rects[name][k] = await box(sel); if (!rects[name][k]) throw new Error(`no ${sel} in ${name}`); }
  console.log('shot', name);
}
const scrollTo = sel => js(`(() => { const r = document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect(); window.scrollBy(0, Math.max(0, r.bottom - ${VH} + 24)); return true; })()`);

fs.mkdirSync(OUT, { recursive: true });
// a first visit in the viewer's language, SaveReel not added yet
await open();
await js(`localStorage.setItem('lang', ${JSON.stringify(LANG)}); localStorage.removeItem('savereel'); true`);
await open();
await shot('install', { install: '#installBtn', added: '#installDone' });
await js(`document.getElementById('installDone').click(), true`);
await js(`window.scrollTo(0, 0), true`);
await shot('page', { choose: 'label[for=files]', howto: '#howto' });
// two clips picked (real files: the page shows their real names and sizes)
const doc = await send('DOM.getDocument');
const inp = await send('DOM.querySelector', { nodeId: doc.root.nodeId, selector: '#files' });
await send('DOM.setFileInputFiles', { nodeId: inp.nodeId, files: CLIPS });
await until(`!document.getElementById('chosen').hidden`);
await scrollTo('#send');
await shot('chosen', { send: '#send' });
await js(`document.getElementById('send').click(), true`);
await until(`!document.getElementById('done').hidden`, 60000);
await js(`window.scrollTo(0, 0), true`); await scrollTo('#done');
await shot('sent', { done: '#done' });
// the finished Reel appears in the list
const dst = path.join(READY, TITLE + '.mp4');
if (!fs.existsSync(dst)) fs.copyFileSync(SAMPLE, dst);
const when = new Date(); when.setHours(14, 20, 0, 0); fs.utimesSync(dst, when, when);
await open();
await shot('ready', { gallery: '.ready .dl' });
fs.writeFileSync(path.join(OUT, 'rects.json'), JSON.stringify({ viewport: [VW, VH], dpr: DPR, shots: rects }, null, 1));
clearTimeout(watchdog);
ws.close(); kill();
try { fs.rmSync(prof, { recursive: true, force: true }); } catch {}
process.exit(0);
