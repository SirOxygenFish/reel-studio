// Dev-time only: packs the MIT/Apache icon sets into small gzipped JSON bundles shipped in the plugin
// (node tools/build_icons.mjs <dir with @phosphor-icons/core and @tabler/icons> <noto-icons.json>).
// { "<name>": "<svg ...>" } per style; Noto keeps the iconify shape, without flags and skin-tone variants.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const OUT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'assets', 'icons');
const [nm, notoFile] = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });
const pack = (name, obj) => {
  const gz = zlib.gzipSync(JSON.stringify(obj), { level: 9 });
  fs.writeFileSync(path.join(OUT, name + '.json.gz'), gz);
  console.log(name, Object.keys(obj.icons || obj).length, 'icons', (gz.length / 1024).toFixed(0), 'KB');
};
const dir = (d, strip) => Object.fromEntries(fs.readdirSync(d).filter(f => f.endsWith('.svg')).map(f =>
  [f.slice(0, -4).replace(strip, ''), fs.readFileSync(path.join(d, f), 'utf8').replace(/<!--[\s\S]*?-->/g, '').replace(/\s+/g, ' ').trim()]));
const ph = path.join(nm, '@phosphor-icons/core/assets');
pack('ph', dir(path.join(ph, 'duotone'), /-duotone$/));
pack('ph-fill', dir(path.join(ph, 'fill'), /-fill$/));
pack('ph-bold', dir(path.join(ph, 'bold'), /-bold$/));
pack('ph-reg', dir(path.join(ph, 'regular'), /$^/));
pack('tb', dir(path.join(nm, '@tabler/icons/icons/outline'), /$^/));
pack('tbf', dir(path.join(nm, '@tabler/icons/icons/filled'), /$^/));
const N = JSON.parse(fs.readFileSync(notoFile, 'utf8'));
const keep = k => !/^flag-|-(light|medium|medium-light|medium-dark|dark)-skin-tone/.test(k);
const icons = Object.fromEntries(Object.entries(N.icons).filter(([k]) => keep(k)));
const aliases = Object.fromEntries(Object.entries(N.aliases || {}).filter(([k, v]) => keep(k) && icons[v.parent]));
pack('noto', { width: N.width, height: N.height, icons, aliases });
