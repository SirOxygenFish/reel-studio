// One-time asset build: Open Peeps (CC0 art by Pablo Stanley; npm @opeepsfun/open-peeps, MIT code) -> assets/peeps/peeps.json
// Each part (bust body, hair, face, beard, accessory) becomes plain SVG markup with its colours turned into CSS classes
// (pp-skinColor, pp-topColor, pp-outlineColor, ...) so a theme can recolour characters. The Effigy layout (group offsets)
// is copied from the package so the runtime can compose busts with a separately animated head and swappable faces.
//   node tools/build_assets.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(ROOT, 'node_modules', '@opeepsfun', 'open-peeps', 'build');
const TMP = path.join(ROOT, '_build', 'peeps');

fs.rmSync(TMP, { recursive: true, force: true });
fs.cpSync(SRC, TMP, { recursive: true });
fs.writeFileSync(path.join(TMP, 'package.json'), '{"type":"module"}');   // the build is ESM in .js files

const React = (await import('react')).default;
const { renderToStaticMarkup } = await import('react-dom/server');

const PLACE = n => '#' + (0x01f001 + n * 7).toString(16).padStart(6, '0');   // unlikely real colours
async function part(dir, file) {
  const mod = await import(pathToFileURL(path.join(TMP, dir, file)).href);
  const cfg = Object.entries(mod).find(([k]) => k.endsWith('Config'))?.[1];
  const comp = mod.default || Object.values(mod).find(v => typeof v === 'function');
  const props = {}, map = {};
  (cfg?.props || []).forEach((p, i) => { props[p.name] = PLACE(i); map[PLACE(i).toLowerCase()] = p.name; });
  let svg = renderToStaticMarkup(React.createElement(comp, props));
  svg = svg.replace(/(fill|stroke)="(#[0-9a-fA-F]{6})"/g, (m, attr, col) =>
    map[col.toLowerCase()] ? `class="pp-${attr === 'fill' ? '' : 's-'}${map[col.toLowerCase()]}"` : m);
  return { svg, w: cfg?.width, h: cfg?.height, props: Object.keys(props) };
}
async function category(dir) {
  const out = {};
  for (const f of fs.readdirSync(path.join(TMP, dir)).filter(f => f.endsWith('.js') && f !== 'index.js')) {
    try { out[f.slice(0, -3)] = await part(dir, f); } catch (e) { console.log('skip', dir, f, e.message); }
  }
  return out;
}

// Effigy layout: group offsets + per-part fix-ups, read from the package source so they stay exact
const eff = fs.readFileSync(path.join(SRC, 'Effigy.js'), 'utf8');
const table = fn => {
  const body = eff.split(`var ${fn} = function`)[1].split('\n};')[0], m = {};
  for (const x of body.matchAll(/\.type === "(\w+)"\) \{\s*return React\.createElement\("g", \{ transform: '([^']+)' \}/g)) m[x[1]] = x[2];
  return m;
};
const grp = id => { const x = eff.match(new RegExp(`id: '${id}', transform: '([^']+)'`)); return x ? x[1] : ''; };
const vb = eff.match(/viewBox: '([^']+)'/)[1];

const peeps = {
  licence: 'Open Peeps by Pablo Stanley, CC0 1.0 (https://www.openpeeps.com). Extracted from npm @opeepsfun/open-peeps 1.0.6 (MIT).',
  viewBox: vb,
  groups: { Body: grp('Body'), Hair: grp('Hair'), Face: grp('Face'), Beard: grp('Beard'), Accessories: grp('Accessories') },
  fix: { head: table('createHead'), hair: table('createHair'), beard: table('createBeard'), accessory: table('createAccessory') },
  body: await category('body/effigy'),
  head: await category('head'),
  face: await category('face'),
  beard: await category('beard'),
  accessory: await category('accessory'),
};
fs.mkdirSync(path.join(ROOT, 'assets', 'peeps'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'assets', 'peeps', 'peeps.json'), JSON.stringify(peeps));
for (const k of ['body', 'head', 'face', 'beard', 'accessory']) console.log(k, Object.keys(peeps[k]).length);
console.log('fix', JSON.stringify(peeps.fix.head), Object.keys(peeps.fix.hair).length, 'hair fixes');
console.log('groups', JSON.stringify(peeps.groups));
