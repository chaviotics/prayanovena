#!/usr/bin/env python3
"""Make the 1200x630 link-preview images (og.jpg) for the library and each novena.

  python3 tools/og.py            # every novena + the library (site/og.jpg)
  python3 tools/og.py healing    # one novena -> novenas/healing/og.jpg
  python3 tools/og.py --html DIR # no Python Playwright? write the cards as HTML, then: node tools/og_render.js DIR

Run tools/build.py afterwards so the images are copied into site/.

Design for thumbnail size: chat apps show this image 300-500px wide, and WhatsApp
may crop it to a centered square. So the title is huge and stacked inside the
central 600px, and the two saint portraits sit at the edges, where a square crop
loses them harmlessly. No URL or small print: every app already shows the domain.

Portraits: novena.json may set "ogSaints": [left_id, right_id] so each saint faces
inward; otherwise the first and last saints are used.
"""
import asyncio, base64, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from shots import font_css as _ttf_css  # noqa: E402


def font_css():
    """the font package's TTFs when present, else the site's own woff2 files (same faces)"""
    css = _ttf_css()
    if css:
        return css
    d, out = os.path.join(ROOT, "site", "fonts"), []
    # weights as the site's fonts.css declares them (the italic is a single 500 face, as in the TTF set)
    for fam, st, w, f in [("Cormorant Garamond", "normal", "500 700", "cormorant-garamond.woff2"),
                          ("Cormorant Garamond", "italic", "500", "cormorant-garamond-italic.woff2"),
                          ("EB Garamond", "normal", "400 600", "eb-garamond.woff2"), ("EB Garamond", "italic", "400 600", "eb-garamond-italic-var.woff2")]:
        with open(os.path.join(d, f), "rb") as fh:
            out.append("@font-face{font-family:'%s';font-style:%s;font-weight:%s;src:url(data:font/woff2;base64,%s)}"
                       % (fam, st, w, base64.b64encode(fh.read()).decode()))
    return "".join(out)

# Colors: the site's Wine & Gold palette, on its cream page color (wine as a full background read too red)
CSS = """
*{box-sizing:border-box}html,body{margin:0}
body{width:1200px;height:630px;overflow:hidden;font-family:'Cormorant Garamond',Garamond,Georgia,serif;
  background:radial-gradient(ellipse 75% 95% at 50% 45%,#FFFDF9 0%,#FBF6EC 65%,#F3EADA 100%);color:#6E1F2B;
  border-top:14px solid #94702A}
.frame{position:absolute;inset:34px 22px 22px;border:2px solid #94702A;border-radius:6px}
.frame:after{content:"";position:absolute;inset:8px;border:1px solid rgba(148,112,42,.4);border-radius:3px}
.arch{position:absolute;top:100px;width:236px;height:430px;border-radius:118px 118px 8px 8px;overflow:hidden;
  border:4px solid #94702A;box-shadow:0 0 0 6px rgba(148,112,42,.14),0 12px 30px rgba(60,40,20,.28)}
.arch img{width:100%;height:100%;object-fit:cover}
.l{left:52px}.r{right:52px}
/* text column 520px wide: at least 44px of clear cream between the words and each arch */
.mid{position:absolute;left:340px;width:520px;top:0;bottom:0;display:flex;flex-direction:column;
  align-items:center;justify-content:center;text-align:center;padding:30px 0 34px}
.cross{line-height:0;margin-bottom:10px}.cross svg{display:block}
.pre{font-family:'EB Garamond',Georgia,serif;font-weight:600;font-size:34px;letter-spacing:.2em;
  text-transform:uppercase;color:#94702A;margin:6px 0 0}
h1{font-weight:700;font-size:150px;line-height:.9;margin:4px 0 0;letter-spacing:-.005em;color:#6E1F2B;max-width:520px;text-wrap:balance}
.rule{width:120px;height:2px;background:#94702A;margin:26px 0 20px}
.sub{font-style:italic;font-weight:600;font-size:44px;line-height:1.1;color:#4A3F38;margin:0;max-width:520px;white-space:nowrap}
.sub.wrap{white-space:normal;text-wrap:balance}
"""

# shrink the title until it fits the column in at most 2 lines and the stack clears the frame. The subtitle stays on one line, shrinking to 38px;
# a longer one wraps onto 2 balanced lines instead of getting tiny. Then shrink it more if the stack is too tall.
# Run after the web fonts load: measuring with the fallback font gives the wrong widths.
FIT = """async () => {
  await document.fonts.ready;
  const h = document.querySelector('h1'), mid = document.querySelector('.mid'), sub = document.querySelector('.sub');
  let s = 150;
  const lines = () => Math.round(h.getBoundingClientRect().height / (s * 0.9));
  while ((h.scrollWidth > 520 || lines() > 2) && s > 70) { s -= 4; h.style.fontSize = s + 'px'; }
  // keep the whole stack (mark to subtitle) clear of the gold frame: at least 24px inside it at top and bottom.
  // The mark gives way first (down to 92px), then the title.
  const svg = mid.querySelector('.cross svg');
  const top = () => mid.firstElementChild.getBoundingClientRect().top, bot = () => sub.getBoundingClientRect().bottom;
  let m = 124;
  while ((top() < 66 || bot() > 564) && (m > 92 || s > 70)) {
    if (m > 92) { m -= 8; svg.setAttribute('width', m); svg.setAttribute('height', m); }
    else { s -= 4; h.style.fontSize = s + 'px'; }
  }
  let t = 44;
  while (sub.scrollWidth > 520 && t > 38) { t -= 2; sub.style.fontSize = t + 'px'; }
  if (sub.scrollWidth > 520) { t = 42; sub.style.fontSize = t + 'px'; sub.classList.add('wrap'); }
  while (mid.scrollHeight > 630 && t > 32) { t -= 2; sub.style.fontSize = t + 'px'; }
}"""


def data(p):
    with open(p, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


# the site's icon (the "9 days" mark from tools/app_icons.py) without its cream tile, so the two never drift apart
from app_icons import LIGHT, mark  # noqa: E402
MARK = '<svg width="124" height="124" viewBox="0 0 64 64">%s</svg>' % mark(LIGHT)


def card_html(pre, title, sub, left, right):
    """left/right: (image path, CSS object-position)"""
    arch = lambda cls, img: '<div class="arch %s"><img src="%s" style="object-position:%s"></div>' % (cls, data(img[0]), img[1])
    return ("<html><head><meta charset='utf-8'><style>%s%s</style></head><body><div class='frame'></div>%s%s"
            "<div class='mid'><div class='cross'>%s</div>%s<h1>%s</h1><div class='rule'></div>"
            "<p class='sub'>%s</p></div></body></html>") % (
        font_css(), CSS, arch("l", left), arch("r", right), MARK,
        "<p class='pre'>%s</p>" % pre if pre else "", title, sub)


async def render(pairs):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome")
        pg = await b.new_page(viewport={"width": 1200, "height": 630})
        for htmlstr, out in pairs:
            await pg.set_content(htmlstr); await pg.evaluate(FIT); await pg.wait_for_timeout(200)
            await pg.screenshot(path=out, type="jpeg", quality=88)
            print("wrote", out)
        await b.close()


def portrait(base, slug, sid, focus):
    return (os.path.join(base, slug, "img", sid + ".jpg"), focus.get(sid, "50% 30%"))


# where each face sits in its 480x600 portrait, so the arch crop keeps it
FOCUS = {"joseph": "62% 30%", "jude": "45% 30%", "rita": "55% 30%",
         "raphael": "55% 20%", "bernadette": "60% 25%", "camillus": "60% 25%"}


def main():
    args = sys.argv[1:]
    html_dir = None
    if "--html" in args:
        k = args.index("--html"); html_dir = args[k + 1]; del args[k:k + 2]
    only = args[0] if args else None
    pairs, lib = [], {}
    base = os.path.join(ROOT, "novenas")
    for slug in sorted(os.listdir(base)):
        p = os.path.join(base, slug, "novena.json")
        if not os.path.exists(p):
            continue
        n = json.load(open(p, encoding="utf-8"))
        ids = n.get("ogSaints") or [n["saints"][0]["id"], n["saints"][-1]["id"]]
        if n.get("status") == "published":
            for sid in ids:
                lib[sid] = portrait(base, slug, sid, FOCUS)
        if only and slug != only:
            continue
        title = n["barTitle"]
        pre, word = ("Novena for", title[len("Novena for "):]) if title.startswith("Novena for ") else ("", title)
        sub = n["kicker"][0].upper() + n["kicker"][1:]
        pairs.append((card_html(pre, word, sub, portrait(base, slug, ids[0], FOCUS), portrait(base, slug, ids[1], FOCUS)),
                      os.path.join(base, slug, "og.jpg")))
    if not only:
        left = lib.get("joseph") or next(iter(lib.values()))
        right = lib.get("raphael") or list(lib.values())[-1]
        pairs.append((card_html("", "Pray a<br>Novena", "Catholic novenas for every intention", left, right),
                      os.path.join(ROOT, "site", "og.jpg")))
    if html_dir:
        os.makedirs(html_dir, exist_ok=True)
        jobs = []
        for i, (h, out) in enumerate(pairs):
            f = os.path.join(html_dir, "card%02d.html" % i)
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(h)
            jobs.append({"html": os.path.abspath(f), "out": os.path.abspath(out)})
        with open(os.path.join(html_dir, "jobs.json"), "w") as fh:
            json.dump({"fit": FIT, "jobs": jobs}, fh, indent=1)
        print("wrote", len(jobs), "cards to", html_dir, "- now run: node tools/og_render.js", html_dir)
        return
    asyncio.run(render(pairs))


if __name__ == "__main__":
    main()
