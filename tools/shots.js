// Node Playwright twin of tools/shots.py, for workspaces with Node Playwright but no Python Playwright (the cloud).
// Same shots, same names: out/shots/<slug>_<light|dark>_<n><part>.png (390x844 at 2x).
//   node tools/shots.js <slug>     one novena: top, Day 1, a poetry day, Day 9, litany, saints, close
//   node tools/shots.js            library home page
// The site self-hosts its fonts, so nothing is injected. Prints page errors, or "none".
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), http = require('http');
const ROOT = path.join(__dirname, '..'), SITE = path.join(ROOT, 'site'), OUT = path.join(ROOT, 'out', 'shots');
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2',
  '.webmanifest': 'application/manifest+json', '.pdf': 'application/pdf' };

(async () => {
  const slug = process.argv[2] || '';
  fs.mkdirSync(OUT, { recursive: true });
  const srv = http.createServer((req, res) => {
    let p;
    try { p = path.join(SITE, decodeURIComponent(req.url.split('?')[0])); } catch (e) { p = ''; }
    if (!p.startsWith(SITE)) { res.writeHead(404); res.end(); return; }
    if (p.endsWith('/')) p = path.join(p, 'index.html');
    fs.readFile(p, (err, data) => {
      if (err) { res.writeHead(404); res.end(); return; }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' }); res.end(data);
    });
  }).listen(0, '127.0.0.1');
  await new Promise(r => srv.once('listening', r));
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const errs = [];
  let poetry = null;
  if (slug) {
    const n = JSON.parse(fs.readFileSync(path.join(ROOT, 'novenas', slug, 'novena.json'), 'utf8'));
    const i = n.days.findIndex(d => d.verse.includes(' / '));
    poetry = i >= 0 ? i + 1 : null;
  }
  const b = await chromium.launch();
  for (const scheme of ['light', 'dark']) {
    const pg = await b.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, colorScheme: scheme });
    pg.on('pageerror', e => errs.push(String(e)));
    await pg.goto(base + (slug ? slug + '/' : '')); await pg.waitForTimeout(700);
    const tag = (slug || 'library') + '_' + scheme, shot = (label, full) => pg.screenshot({ path: path.join(OUT, `${tag}_${label}.png`), fullPage: !!full });
    await shot('0top');
    if (!slug) {
      await pg.evaluate("document.querySelector('.cards').scrollIntoView({block:'start'}); window.scrollBy(0,-70)");
      await pg.waitForTimeout(200); await shot('1cards'); await shot('full', true);
      continue;
    }
    for (const [label, day] of [['1day1', 1], ['2poetry', poetry], ['3day9', 9]]) {
      if (!day) continue;
      await pg.evaluate(`document.querySelectorAll('#track button')[${day - 1}].click()`);
      await pg.evaluate("document.getElementById('dTitle').scrollIntoView({block:'start'}); window.scrollBy(0,-110)");
      await pg.waitForTimeout(250); await shot(label);
    }
    for (const [label, sel] of [['4litany', '.litany'], ['5saints', '.saints'], ['6close', '.close']]) {
      await pg.evaluate(`document.querySelector('${sel}').scrollIntoView({block:'start'}); window.scrollBy(0,-90)`);
      await pg.waitForTimeout(250); await shot(label);
    }
  }
  await b.close(); srv.close();
  console.log('shots in', OUT, '| page errors:', errs.length ? errs.join('; ') : 'none');
})();
