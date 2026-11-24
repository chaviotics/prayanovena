// Print the HTML made by tools/print_pdf.py to PDF with Chromium (Node Playwright). Run through print_pdf.py.
//   node tools/print_render.js out/print/jobs.json
// Fails (exit 1) when a PDF runs past the page limit, so a too-long novena never ships quietly.
const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const { max, jobs } = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage();
  let bad = 0; const results = [];
  for (const j of jobs) {
    await page.goto('file://' + j.html, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    await page.emulateMedia({ media: 'print' });
    // page 1 must hold everything up to the Scripture notice; if it runs over, the notice would spill onto page 2
    const overflow = () => page.evaluate(([w, h]) => {
      const p1 = document.querySelector('.p1');
      if (!p1) return 0;  // the compact layout flows freely (print_pdf.py checks the notice is on page 1)
      document.body.style.width = w;  // measure at the printed column width
      const probe = document.createElement('div');
      probe.style.height = h; document.body.appendChild(probe);
      const limit = probe.getBoundingClientRect().height; probe.remove();
      const over = Math.round(p1.getBoundingClientRect().height - limit);
      document.body.style.width = '';
      return over;
    }, [j.width, j.page1]);
    const opts = { preferCSSPageSize: true, printBackground: true, tagged: true, outline: false };
    const count = (buf) => (buf.toString('latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
    let limit = max, note = '';
    if (j.fit) {
      // the largest type scale --k (1 = 10pt body) that keeps the PDF within fit.pages; if even the smallest won't fit, try fit.fallback
      // a scale "fits" when page 1 holds its part and the whole PDF is within the target page count
      const at = async (k) => {
        await page.evaluate((k) => document.documentElement.style.setProperty('--k', k), k);
        return (await overflow()) > 1 ? 99 : count(await page.pdf(opts));
      };
      let target = j.fit.pages, lo = j.fit.lo, hi = j.fit.hi;
      if (await at(j.fit.lo) > target && j.fit.fallback) target = j.fit.fallback;
      // fewer pages first, but only while the type stays at least fit.fewerLo (e.g. 3 or 4 pages at 9pt or more, else 5)
      for (const t of j.fit.fewer || []) if (await at(j.fit.fewerLo) <= t) { target = t; lo = j.fit.fewerLo; break; }
      if (await at(hi) <= target) lo = hi;
      else for (let i = 0; i < 9; i++) { const mid = (lo + hi) / 2; if (await at(mid) <= target) lo = mid; else hi = mid; }
      await at(lo);
      limit = target; note = `  body ${(10 * lo).toFixed(2)}pt`; j.k = lo;
      if (j.fit.portraits) {  // then let the saints' portraits on page 1 take up its spare room (up to fit.portraits times their size)
        const spare = () => page.evaluate(([w, h]) => {
          const p1 = document.querySelector('.p1'); const mh = p1.style.minHeight;
          p1.style.minHeight = '0'; document.body.style.width = w;
          const probe = document.createElement('div'); probe.style.height = h; document.body.appendChild(probe);
          const room = probe.getBoundingClientRect().height - p1.getBoundingClientRect().height; probe.remove();
          p1.style.minHeight = mh; document.body.style.width = '';
          return room;
        }, [j.width, j.page1]);
        const ps = async (x) => { await page.evaluate((x) => document.documentElement.style.setProperty('--ps', x), x); return spare(); };
        let a = 1, b = j.fit.portraits;
        if (await ps(b) >= 0) a = b;
        else for (let i = 0; i < 8; i++) { const m = (a + b) / 2; if (await ps(m) >= 0) a = m; else b = m; }
        await ps(a); j.ps = a; note += `  portraits x${a.toFixed(2)}`;
        if (j.fit.page1Zoom) {  // then the rest of page 1's room makes everything on it larger (title, prayers, pictures)
          const z = async (x) => { await page.evaluate((x) => document.documentElement.style.setProperty('--z1', x), x); return spare(); };
          let c = 1, d = j.fit.page1Zoom;
          if (await z(d) >= 0) c = d;
          else for (let i = 0; i < 8; i++) { const m = (c + d) / 2; if (await z(m) >= 0) c = m; else d = m; }
          await z(c); note += `  page 1 x${c.toFixed(3)}`;
        }
      }
      if (j.fit.grow) {  // then as many Graces lines as still fit in the page count (the box closes the last page)
        const gl = async (n) => { await page.evaluate((n) => document.documentElement.style.setProperty('--gl', n), n); return count(await page.pdf(opts)); };
        // count every line that would fit (j.gl: print_pdf.py prefers the arrangement that leaves the most room, i.e. the
        // fewest gaps on the other pages), then draw at most fit.growMax so a roomy last page simply ends in white space
        let a = 3, b = 41;
        if (await gl(a) > target) { await gl(a); } else {
          while (b - a > 1) { const m = (a + b) >> 1; if (await gl(m) <= target) a = m; else b = m; }
          j.gl = a; const n = Math.min(a, j.fit.growMax || a);
          await gl(n); note += `  ${n} Graces lines (room for ${a})`;
        }
      }
    }
    await page.pdf({ path: j.pdf, ...opts });
    const pages = count(fs.readFileSync(j.pdf));
    const over = await overflow();
    const ok = pages <= limit && over <= 1;
    if (over > 1) console.log(`PAGE 1 runs ${over}px over: shorten the credits or the "Alongside prayer" tip`);
    if (!ok) bad++;
    results.push({ pdf: j.pdf, ok, pages, k: j.k || 1, gl: j.gl || 0 });
    console.log(`${ok ? 'ok  ' : 'LONG'} ${pages} pages  ${(fs.statSync(j.pdf).size / 1024).toFixed(0)} KB${note}  ${j.pdf}`);
  }
  await browser.close();
  if (process.argv[3]) fs.writeFileSync(process.argv[3], JSON.stringify(results));
  process.exit(bad ? 1 : 0);
})();
