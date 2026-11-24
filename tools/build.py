#!/usr/bin/env python3
"""Build the novena library.

  python3 tools/build.py                 # builds site/ (library + every published novena)
  python3 tools/build.py --artifact SLUG # one self-contained HTML file (images inlined) in out/

Each novena lives in novenas/<slug>/ as novena.json plus img/<id>.jpg (portrait, 480x600)
and img/<id>_face.jpg (round avatar, 112x112) for every saint and litany image.
"""
import base64, hashlib, html, json, os, re, shutil, sys

import datetime
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = "https://prayanovena.com"
ICON_DIRS = [os.path.join(ROOT, "tools", "icons")]
BASE_ICONS = ["logo", "cross", "sun", "moon", "text-aa", "check", "caret-down", "footprints", "hands-praying", "arrow-left", "book-open", "paper-plane-tilt", "printer"]
NUMWORD = {1: "The Intercessor", 2: "The 2 Intercessors", 3: "The 3 Intercessors"}
MARIAN_MEMORARE = ("Remember, O most gracious Virgin Mary, that never was it known that anyone who fled to your protection, "
                   "implored your help, or sought your intercession was left unaided. Inspired by this confidence, I fly unto you, "
                   "O Virgin of virgins, my Mother. To you do I come; before you I stand, sinful and sorrowful. O Mother of the Word "
                   "Incarnate, despise not my petitions, but in your mercy hear and answer me.")


GOOGLE_FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500'
                '&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">')
PAGE_TIMEOUT_MS = 4000  # how long a page waits for the network before showing the saved copy

# Library filters. Each novena.json names one "category"; a chip shows only when a published novena uses it.
CATEGORIES = [
    ("exams-school", "School & exams"),
    ("work-money", "Work & money"),
    ("healing", "Health & healing"),
    ("family", "Family"),
    ("love-friendship", "Love & friendship"),
    ("decisions-growth", "Wisdom & decisions"),
    ("spiritual-life", "Spiritual life"),
    ("travel", "Travel & abroad"),
    ("hard-times", "Hard times"),
    ("departed", "The departed"),
    ("seasons", "Seasons & feasts"),
]
CHIPS_MIN = 4    # show the filter chips once this many novenas are published
SEARCH_MIN = 10  # show the search box once this many are published (chips are enough below that)


def local_fonts(up):
    """the site's own copies of the fonts (site/fonts), so pages look right offline"""
    return ('<link rel="preload" href="{0}fonts/eb-garamond.woff2" as="font" type="font/woff2" crossorigin>\n'
            '<link rel="preload" href="{0}fonts/cormorant-garamond.woff2" as="font" type="font/woff2" crossorigin>\n'
            '<link rel="stylesheet" href="{0}fonts/fonts.css?v=2">').format(up)


def sw_register(up):
    """register the service worker, and say so once the library is saved on this device"""
    return ('<script>\nif ("serviceWorker" in navigator && window.isSecureContext){\n'
            '  try{ navigator.serviceWorker.register("%ssw.js").then(function(){ return navigator.serviceWorker.ready; })'
            '.then(function(){ var n = document.getElementById("offlineNote"); if (n) n.hidden = false; }).catch(function(){}); }catch(e){}\n}\n</script>') % up


RSV_NOTICE = ("Scripture quotations are from The Catholic Edition of the Revised Standard Version of the Bible, copyright © 1965, 1966 "
              "National Council of the Churches of Christ in the United States of America. Used by permission. All rights reserved worldwide.")
CCC_NOTICE = "Catechism quotations are from the <i>Catechism of the Catholic Church</i>, 2nd edition, © Libreria Editrice Vaticana."
FOOT_NAV = [("index.html", "All novenas"), ("about/index.html", "About"), ("privacy/index.html", "Privacy")]
# one footer for every page (styles in FOOTER_CSS): site links, the offline note, a can't-save warning (novena pages), credits, and a closing line
FOOTER_CSS = """
/* ---- site footer (shared by every page; built by tools/build.py) ---- */
.site-foot{margin-top:40px;border-top:1px solid var(--rule);text-align:center;color:var(--muted)}
.site-foot .wrap{padding-top:22px;padding-bottom:calc(56px + env(safe-area-inset-bottom))}
.foot-nav{display:flex;flex-wrap:wrap;justify-content:center;align-items:center;margin:0 0 8px}
.foot-nav a{display:inline-flex;align-items:center;min-height:44px;padding:0 12px;color:var(--wine);font-weight:600;font-size:calc(16px * var(--scale));text-underline-offset:3px}
.foot-nav a[aria-current="page"]{text-decoration:none;color:var(--muted)}
.foot-nav span{color:var(--rule-strong)}
.fnote{font-size:calc(13.5px * var(--scale));line-height:1.5;color:var(--muted);max-width:62ch;margin:0 auto 10px}
.fnote a{color:inherit;text-underline-offset:2px}
.fnote.warn{font-size:calc(15px * var(--scale));color:var(--ink)}
.fnote.credits{font-size:calc(13px * var(--scale))}
.amdg{display:flex;align-items:center;justify-content:center;gap:14px;margin:30px 0 0;font-family:var(--display);font-style:italic;font-weight:500;font-size:calc(20px * var(--scale));line-height:1.3;color:var(--wine)}
.amdg::before,.amdg::after{content:"";flex:none;width:32px;height:1px;background:var(--gold)}
"""


def site_footer(up, current=None, credits=(), store_id=False, scripture=True):
    """the footer every page shares. up: path to the site root; current: this page's FOOT_NAV href; credits: notes (HTML)"""
    links = []
    for href, label in FOOT_NAV:
        cur = ' aria-current="page"' if href == current else ""
        links.append('<a href="%s%s"%s>%s</a>' % (up, href, cur, label))
    notes = "".join('\n    <p class="fnote credits">%s</p>' % c for c in credits)
    return ('<footer class="site-foot">\n  <div class="wrap">\n'
            '    <nav class="foot-nav" aria-label="Site">%s</nav>\n'
            '%s'
            '    <p class="fnote" id="offlineNote" hidden>Saved on this device, so it opens even without signal.</p>%s\n'
            '%s'
            '    <p class="amdg">To God be the glory</p>\n'
            '  </div>\n</footer>') % ('<span aria-hidden="true">·</span>'.join(links), '    <p class="fnote warn" id="storeFoot" hidden></p>\n' if store_id else "", notes,
                                       '    <p class="fnote credits">%s</p>\n' % RSV_NOTICE if scripture else "")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def esc(t):
    return html.escape(t, quote=True)


def icon_symbol(name):
    if name == "logo":   # the 9 days mark, same source as the favicon; cross takes currentColor, ring the theme gold
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app_icons import ring, cross
        return ('<symbol id="i-logo" viewBox="0 0 64 64"><path fill="none" style="stroke:var(--gold,#94702A)" stroke-width="4" '
                'stroke-linecap="round" d="%s"/><path d="%s"/></symbol>' % (ring(), cross()))
    for d in ICON_DIRS:
        p = os.path.join(d, name + ".svg")
        if os.path.exists(p):
            body = re.search(r"<svg[^>]*>(.*)</svg>", read(p), re.S).group(1).strip()
            return '<symbol id="i-%s" viewBox="0 0 256 256">%s</symbol>' % (name, body)
    raise SystemExit("icon not found: " + name)


def sprite(names):
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n); out.append(icon_symbol(n))
    return '<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">' + "".join(out) + "</svg>"


def load_novenas():
    out = []
    base = os.path.join(ROOT, "novenas")
    for slug in sorted(os.listdir(base)):
        p = os.path.join(base, slug, "novena.json")
        if os.path.exists(p):
            n = json.loads(read(p))
            assert n["slug"] == slug, (slug, n["slug"])
            validate(n)
            out.append(n)
    out.sort(key=lambda n: n.get("order", 99))
    return out


def validate(n):
    req = ["slug", "storageKey", "category", "title", "barTitle", "barShort", "kicker", "card", "description", "epigraph",
           "closingVerse", "saints", "litany", "openingPrayer", "closingPrayer", "memorare", "tips", "icons", "credits", "days"]
    miss = [k for k in req if k not in n]
    assert not miss, (n.get("slug"), "missing", miss)
    assert n["category"] in dict(CATEGORIES), (n["slug"], "unknown category", n["category"])
    assert len(n["days"]) == 9 and len(n["icons"]) == 9, n["slug"]
    assert 1 <= len(n["saints"]) <= 3, n["slug"]
    for d in n["days"]:
        for k in ("title", "ref", "verse", "refl", "more", "prayer", "step"):
            assert d.get(k), (n["slug"], d.get("title"), k)
        assert "--" not in d["ref"] and "-" not in d["ref"].split(" ")[-1], ("use an en dash in refs", d["ref"])
    imgdir = os.path.join(ROOT, "novenas", n["slug"], "img")
    for s in n["saints"]:
        for f in (s["id"] + ".jpg", s["id"] + "_face.jpg"):
            assert os.path.exists(os.path.join(imgdir, f)), (n["slug"], "missing image", f)
    for l in n["litany"]:
        if l.get("img"):
            assert os.path.exists(os.path.join(imgdir, l["img"] + "_face.jpg")), (n["slug"], "missing face", l["img"])


def scripture(t):
    """escape, and show the divine name LORD in small caps as the RSV prints it"""
    return esc(t).replace("LORD", '<span class="sc">Lord</span>')


def saint_line(saints):
    # each name (and the "&" before the last) stays on one line; the line breaks only between names
    names = [esc(s["name"]) for s in saints]
    if len(names) > 1:
        names[-1] = "&amp; " + names[-1]
    names = ['<span class="nb">%s</span>' % x for x in names]
    if len(names) <= 2:
        return " ".join(names)
    return ", ".join(names[:-1]) + " " + names[-1]


def page(n, mode):
    """mode 'site' -> image files next to the page; mode 'artifact' -> inlined images, no library links."""
    slug = n["slug"]
    imgdir = os.path.join(ROOT, "novenas", slug, "img")

    def src(name):
        if mode == "artifact":
            with open(os.path.join(imgdir, name + ".jpg"), "rb") as f:
                return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
        return "img/%s.jpg" % name

    faces = "".join('<img src="%s" alt="">' % src(s["id"] + "_face") for s in n["saints"])
    litany = "\n".join(
        '          <p>%s%s, <span class="resp">pray for us.</span></p>' % (
            ('<img class="av" src="%s" alt="">' % src(l["img"] + "_face")) if l.get("img") else
            '<span class="av av-none" aria-hidden="true"><svg class="i" focusable="false"><use href="#i-cross"/></svg></span>', esc(l["text"]))
        for l in n["litany"])
    saints = "\n".join(
        '      <article class="saint"><img class="portrait" src="%s" alt="%s" width="92" height="115"><div><h3>%s</h3>'
        '<p class="meta">%s · %s</p><p class="pat">%s</p><p>%s</p></div></article>' % (
            src(s["id"]), esc(s["alt"]), esc(s["name"]), esc(s["dates"]), esc(s["feast"]), esc(s["patron"]), esc(s["bio"]))
        for s in n["saints"])
    tips = "\n".join('      <div class="tip"><h3>%s</h3><p>%s</p></div>' % (esc(t["h"]), t["p"]) for t in n["tips"])
    mem = n["memorare"]
    mem_text = MARIAN_MEMORARE if mem.get("to") == "Mary" and not mem.get("text") else mem["text"]
    mem_title = "Memorare" if mem.get("to") == "Mary" else "Memorare to " + mem["to"]
    how_mem = "<strong>Memorare</strong>" + ("" if mem.get("to") == "Mary" else " to " + esc(mem["to"]))

    url = "%s/%s/" % (SITE_URL, slug)
    if mode == "site":
        head = "\n".join([
            '<meta name="description" content="%s">' % esc(n["description"]),
            '<meta name="theme-color" content="#FFFDF9" media="(prefers-color-scheme: light)">',
            '<meta name="theme-color" content="#0E1524" media="(prefers-color-scheme: dark)">',
            '<meta property="og:type" content="website">',
            '<meta property="og:site_name" content="Pray a Novena">',
            '<meta property="og:url" content="%s">' % url,
            '<meta property="og:title" content="%s">' % esc(og_title(n)),
            '<meta property="og:description" content="%s">' % esc(n.get("ogDescription") or n["description"]),
            '<meta property="og:image" content="%sog.jpg?v=%s">' % (url, og_ver(os.path.join(ROOT, "novenas", slug, "og.jpg"))),
            '<meta property="og:image:alt" content="%s">' % esc(n["barTitle"] + ": " + n["kicker"]),
            '<meta property="og:image:type" content="image/jpeg">',
            '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
            '<meta name="twitter:card" content="summary_large_image">',
            '<link rel="canonical" href="%s">' % url,
            '<link rel="icon" href="../favicon.svg" type="image/svg+xml">',
            '<link rel="apple-touch-icon" href="../apple-touch-icon.png">',
            '<link rel="manifest" href="../manifest.webmanifest">',
            breadcrumbs(n["title"], url),
        ] + ([] if n.get("status") == "published" else ['<meta name="robots" content="noindex">']))
        back = ('    <a class="back" href="../index.html"><svg class="i" aria-hidden="true" focusable="false"><use href="#i-arrow-left"/></svg>'
                'All novenas</a>\n')
        title_tag = esc(og_title(n))  # the full title ("Novena for the Healing of the Sick | Pray a Novena") is what people search for
        back = ""  # the top bar reads "← All novenas › <title>" on every size, so the hero needs no back link of its own
        home = ('href="../index.html"', '<svg class="i back-ic" aria-hidden="true" focusable="false"><use href="#i-arrow-left"/></svg>')
    else:
        home = ('href="#top" aria-label="Back to top"', "")
        head, back, title_tag = "", "", esc(n["barTitle"])
        home = ('href="#top" aria-label="Back to top"', "")

    # a rubric for "N." wherever a prayer asks for a name, so nobody stumbles over it when praying aloud
    texts = [n["openingPrayer"], n["closingPrayer"]] + [d["prayer"] for d in n["days"]]
    name_rubric = " Where you see N., say the name of the person you are praying for." if any(re.search(r"\bN\.", t) for t in texts) else ""
    printing = print_link(n, mode)
    vals = {
        "TITLE_TAG": title_tag, "HEAD_META": head, "BAR_TITLE": esc(n["barTitle"]), "BAR_SHORT": esc(n["barShort"]),
        "BACK_LINK": back, "NAME_RUBRIC": name_rubric, "HOME_LABEL": "All novenas" if mode == "site" else "",
        "FOOTER": site_footer("../" if mode == "site" else SITE_URL + "/", credits=[n["credits"]], store_id=True), "FOOTER_CSS": FOOTER_CSS, "HOME_ATTRS": home[0], "HOME_ARROW": home[1], "KICKER": esc(n["kicker"]), "TITLE": esc(n["title"]),
        "SAINT_LINE": saint_line(n["saints"]), "EPI_TEXT": scripture(n["epigraph"]["text"]), "EPI_REF": esc(n["epigraph"]["ref"]),
        "FACES": faces, "DAY1_TITLE": esc(n["days"][0]["title"]),
        # Day 1 is written into the HTML (the script swaps in the chosen day), so search engines see a full day of prayer
        "DAY1_VERSE": verse_html(n["days"][0]["verse"]), "DAY1_REF": esc(n["days"][0]["ref"]), "DAY1_REFL": esc(n["days"][0]["refl"]),
        "DAY_LIST": "\n".join(
            '      <li><a href="#day-%d" data-day="%d"><span class="di" aria-hidden="true"><svg class="i" focusable="false"><use href="#i-%s"/></svg></span>'
            '<span class="dn">Day %d<span class="st"></span></span><span class="dt">%s</span><span class="dr">%s</span></a></li>' % (
                i, i, n["icons"][i - 1], i, esc(d["title"]), esc(d["ref"])) for i, d in enumerate(n["days"], 1)),
        "DAY1_MORE": esc(n["days"][0].get("more", "")), "DAY1_PRAYER": esc(n["days"][0]["prayer"]), "DAY1_STEP": esc(n["days"][0].get("step", "")), "OPENING_PRAYER": esc(n["openingPrayer"]),
        "INTENT_PH": esc(n.get("intentionPlaceholder", "Write the intention you are praying for.")),
        "LITANY": litany, "CLOSING_PRAYER": esc(n["closingPrayer"]), "MEMORARE_TITLE": esc(mem_title),
        "MEMORARE_TEXT": esc(mem_text), "HOW_MEMORARE": how_mem, "TIPS": tips,
        "SAINTS_HEAD": NUMWORD[len(n["saints"])], "SAINTS": saints, "CLOSE_TEXT": scripture(n["closingVerse"]["text"]),
        "CLOSE_REF": esc(n["closingVerse"]["ref"]),
        "ICONS": json.dumps(n["icons"]), "KEY": json.dumps(n["storageKey"] + ("-artifact" if mode == "artifact" else "")),
        "DAYS": json.dumps(n["days"], ensure_ascii=False),
        "SPRITE": sprite(BASE_ICONS + n["icons"]),
        "FONTS": local_fonts("../") if mode == "site" else GOOGLE_FONTS,
        "SW": sw_register("../") if mode == "site" else "",
        "SHARE": json.dumps(share(n), ensure_ascii=False),
        "PRINT_HOW": printing[0], "PRINT_SIDE": printing[1],
    }
    t = read(os.path.join(ROOT, "templates", "novena.html"))
    for k, v in vals.items():
        t = t.replace("{{%s}}" % k, v)
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", t)
    assert not left, left
    return t


def pdf_path(n):
    """the printable PDF made by tools/print_pdf.py (novenas/<slug>/<slug>-novena.pdf), or None; warns when it is out of date"""
    p = os.path.join(ROOT, "novenas", n["slug"], n["slug"] + "-novena.pdf")
    if not os.path.exists(p):
        return None
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from print_pdf import print_version, VERSIONS
    made = json.loads(read(VERSIONS)).get(n["slug"]) if os.path.exists(VERSIONS) else None
    if made != print_version(n["slug"]):
        print("WARNING: %s PDF is out of date; run python3 tools/print_pdf.py %s" % (n["slug"], n["slug"]))
    return p


def print_link(n, mode):
    """the "Print or download (PDF)" link: under How to pray, and in the desktop sidebar"""
    p = pdf_path(n)
    if not p:
        return "", ""
    name = os.path.basename(p)
    href = name if mode == "site" else "%s/%s/%s" % (SITE_URL, n["slug"], name)
    kb = os.path.getsize(p) // 1024
    how = ('    <p class="printrow"><a class="printlink" href="%s" type="application/pdf" target="_blank" rel="noopener"><svg class="i" aria-hidden="true" focusable="false">'
           '<use href="#i-printer"/></svg>Print or download (PDF)</a><span class="printmeta">4 pages, A4 · %d KB</span></p>' % (href, kb))
    # opens in a new tab: an installed (home-screen) app has no back button, so a PDF in the same view would trap the reader
    side = ('  <p class="side-pdf"><a class="printlink" href="%s" type="application/pdf" target="_blank" rel="noopener"><svg class="i" aria-hidden="true" focusable="false">'
            '<use href="#i-printer"/></svg>Print or download (PDF)</a></p>' % href)
    return how, side


def share(n):
    """what the Share button sends: the novena's public link (never the page's own address, so no day, intention
    or progress can ride along), its title and a short message"""
    return {"url": "%s/%s/" % (SITE_URL, n["slug"]), "title": n["title"],
            "text": "Sharing this novena with you: %s. 9 days of prayer, one day at a time." % n["title"]}


def og_title(n):
    """a fuller link-preview title: add the site name when it still fits in 60 characters"""
    t = n["title"] + " | Pray a Novena"
    return t if len(t) <= 60 else n["title"]


def og_ver(path):
    """short content hash, so chat apps fetch a changed og.jpg instead of their cached copy"""
    import hashlib
    if not os.path.exists(path):
        return "0"
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]


def verse_html(t):
    """a Scripture verse as the page script shows it (small-caps LORD, " / " starts a new poetry line), for the Day 1 text in the HTML"""
    h = scripture(t)
    parts = h.split(" / ")
    return "".join('<span class="ln">%s</span>' % l for l in parts) if len(parts) > 1 else h


def json_ld(data):
    """a schema.org block for search engines (data only: the CSP never runs it)"""
    return '<script type="application/ld+json">%s</script>' % json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def breadcrumbs(name, url):
    """Home > this page, so Google can show the site's name and path above the result"""
    return json_ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Pray a Novena", "item": SITE_URL + "/"},
        {"@type": "ListItem", "position": 2, "name": name, "item": url}]})


def last_changed(*paths):
    """YYYY-MM-DD of the last commit touching these paths (today when they have uncommitted changes), for the sitemap"""
    rel = [os.path.relpath(p, ROOT) for p in paths]
    try:
        if subprocess.run(["git", "status", "--porcelain", "--"] + rel, cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip():
            return datetime.date.today().isoformat()
        d = subprocess.run(["git", "log", "-1", "--format=%cs", "--"] + rel, cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        return d or datetime.date.today().isoformat()
    except (OSError, subprocess.CalledProcessError):
        return None


def build_seo(novenas, site):
    """site/sitemap.xml (published pages only), site/robots.txt pointing to it, site/_headers giving each PDF its page
    as canonical (so search results send people to the prayer page, which links the PDF), and site/_redirects
    sending the free netlify.app address to prayanovena.com (one address in search results)"""
    pub = [n for n in novenas if n.get("status") == "published"]
    nov = lambda n: os.path.join(ROOT, "novenas", n["slug"])
    tmpl = lambda name: os.path.join(ROOT, "templates", name)
    pages = [(SITE_URL + "/", last_changed(tmpl("library.html"), *[nov(n) for n in pub]))]
    pages += [("%s/%s/" % (SITE_URL, n["slug"]), last_changed(nov(n))) for n in pub]
    pages += [(SITE_URL + "/about/", last_changed(tmpl("about.html"), ABOUT_DIR)),
              (SITE_URL + "/privacy/", last_changed(tmpl("privacy.html")))]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in pages:
        xml.append("  <url><loc>%s</loc>%s</url>" % (loc, "<lastmod>%s</lastmod>" % mod if mod else ""))
    xml.append("</urlset>")
    with open(os.path.join(site, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(xml) + "\n")
    with open(os.path.join(site, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("# Pray a Novena: every page may be crawled.\nUser-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL)
    heads = ["# Made by tools/build.py (build_seo); netlify.toml holds the site-wide headers."]
    for n in pub:
        p = pdf_path(n)
        if p:
            heads += ["/%s/%s" % (n["slug"], os.path.basename(p)), '  Link: <%s/%s/>; rel="canonical"' % (SITE_URL, n["slug"])]
    with open(os.path.join(site, "_headers"), "w", encoding="utf-8") as f:
        f.write("\n".join(heads) + "\n")
    with open(os.path.join(site, "_redirects"), "w", encoding="utf-8") as f:
        f.write("# Made by tools/build.py (build_seo): the free Netlify address forwards to the real domain.\n"
                "https://prayanovena.netlify.app/* %s/:splat 301!\n" % SITE_URL)
    print("built sitemap.xml (%d pages), robots.txt, _headers, _redirects" % len(pages))


def search_text(n, title):
    """what the search box matches: title, card, saints, Marian title, category and keywords"""
    parts = [title, n["title"], n["card"], dict(CATEGORIES)[n["category"]]]
    parts += [x["name"] for x in n["saints"]] + [l["text"] for l in n["litany"]] + n.get("keywords", [])
    t = " ".join(parts).lower().replace("\u2019", "'")
    return re.sub(r"\s+", " ", t)


def library(novenas, search=None):
    t = read(os.path.join(ROOT, "templates", "library.html"))
    cards, icons = [], []
    pub = [n for n in novenas if n.get("status") == "published"]
    for n in pub:
        icons.append(n.get("icon", "cross"))
        faces = "".join('<img src="%s/img/%s_face.jpg" alt="" width="36" height="36">' % (n["slug"], s["id"]) for s in n["saints"])
        title = n.get("cardTitle") or re.sub(r"^Novena for (the )?", "", n["title"])
        names = ['<span class="nb">%s</span>' % esc(x["name"]) for x in n["saints"]]
        through = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " &amp;&nbsp;" + names[-1]
        blurb = re.sub(r"(\d) ", r"\1&nbsp;", esc(n["card"]))
        sl = n["slug"]
        cards.append(
            '<li class="card" data-key="%s" data-cat="%s" data-search="%s"><a href="%s/index.html" aria-labelledby="t-%s p-%s">'
            '<div class="top"><span class="ic" aria-hidden="true"><svg class="i"><use href="#i-%s"/></svg></span>'
            '<div class="faces" aria-hidden="true">%s</div></div>'
            '<h3 id="t-%s">%s</h3><p class="through">through %s</p>'
            '<p class="blurb">%s</p>'
            '<div class="foot"><p class="prog" id="p-%s"></p>'
            '<span class="go" aria-hidden="true"><span>Pray</span><svg class="i"><use href="#i-arrow-right"/></svg></span></div></a></li>' % (
                esc(n["storageKey"]), n["category"], esc(search_text(n, title)), sl, sl, sl, n.get("icon", "cross"), faces, sl, esc(title), through, blurb, sl))
    used = [n["category"] for n in pub]
    chips = ""
    if len(pub) >= CHIPS_MIN and len(set(used)) > 1:
        btn = '<button type="button" class="chip" data-cat="%s" aria-pressed="%s">%s<span class="n"><span class="sr">, </span>%d<span class="sr"> novenas</span></span></button>'
        chips = ('<div class="chips" id="chips" role="group" aria-label="Filter by intention">' + btn % ("all", "true", "All", len(pub))
                 + "".join(btn % (k, "false", esc(v), used.count(k)) for k, v in CATEGORIES if k in used) + "</div>")
    if search is None:
        search = len(pub) >= SEARCH_MIN
    box = ""
    if search:
        box = ('<div class="search" role="search"><svg class="i" aria-hidden="true" focusable="false"><use href="#i-magnifying-glass"/></svg>'
               '<label class="sr" for="q">Search novenas</label>'
               '<input id="q" type="search" placeholder="Search by intention or saint" autocomplete="off" enterkeyhint="search">'
               '<button type="button" class="clear" id="qClear" aria-label="Clear search" hidden><svg class="i" aria-hidden="true" focusable="false"><use href="#i-x"/></svg></button></div>')
    tools = ""
    if chips or box:
        tools = '<div class="filters">%s%s</div>\n  <p class="sr" id="filterStatus" role="status" aria-live="polite"></p>' % (box, chips)
    t = t.replace("{{FILTERS}}", tools)
    # WebSite tells Google the site's name ("Pray a Novena", not the domain) for search results
    t = t.replace("{{JSON_LD}}", json_ld({"@context": "https://schema.org", "@type": "WebSite", "name": "Pray a Novena",
                                          "alternateName": ["prayanovena.com", "Pray a Novena: Catholic novenas for every intention"],
                                          "url": SITE_URL + "/", "inLanguage": "en"}))
    t = t.replace("{{CARDS}}", "\n".join(cards))
    t = t.replace("{{OG_VER}}", og_ver(os.path.join(ROOT, "site", "og.jpg")))
    t = t.replace("{{FONTS}}", local_fonts("")).replace("{{SW}}", sw_register(""))
    t = t.replace("{{FOOTER_CSS}}", FOOTER_CSS).replace("{{FOOTER}}", site_footer("", current="index.html"))
    t = t.replace("{{SPRITE}}", sprite(["logo", "cross", "sun", "moon", "text-aa", "arrow-right", "hands-praying", "calendar-check", "church", "magnifying-glass", "x"] + icons))
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", t)
    assert not left, left
    return t


ABOUT_DIR = os.path.join(ROOT, "pages", "about")
ABOUT_IMAGES = ("Images: El Greco, <i>Pentecost</i>, Museo del Prado; Jean-François Millet, <i>The Angelus</i>, Musée d’Orsay; "
                "Hubert and Jan van Eyck, <i>Ghent Altarpiece</i>, St. Bavo’s Cathedral; Rembrandt, <i>The Apostle Paul</i>, "
                "Kunsthistorisches Museum, Vienna; Philippe de Champaigne, <i>Saint Augustine</i>, Los Angeles County Museum of Art; Carlo Crivelli, "
                "<i>Saint Thomas Aquinas</i>, National Gallery, London; Cristóbal Lozano, <i>Ecstasy of Saint Camillus de Lellis</i>; "
                "Placido Costanzi, <i>A Miracle of Saint Joseph of Cupertino</i>, Metropolitan Museum of Art; photograph of Bartolo Longo; El Greco, <i>Saint Peter in Tears</i>, Bowes Museum; "
                "Peter Paul Rubens, <i>Saint Ignatius of Loyola</i>, Norton Simon Museum; Sassoferrato, <i>The Virgin in Prayer</i>. "
                "Public domain, via Wikimedia Commons. Portrait of St. John Bosco via ius-sdb.com; painting of St. Dominic Savio via "
                "anastpaul.com (artists unknown).")


def about(novenas, mode="site"):
    """the About page: what a novena is, how to pray one, the saints. mode 'artifact' inlines images and links to the live site."""
    t = read(os.path.join(ROOT, "templates", "about.html"))
    pub = [n for n in novenas if n.get("status") == "published"]
    live = SITE_URL + "/"
    up = "../" if mode == "site" else live

    def img(rel):  # rel: path under site/ (about images are 'about/img/x.jpg')
        if mode == "artifact":
            src = os.path.join(ABOUT_DIR, "img", rel.split("/")[-1]) if rel.startswith("about/") else \
                os.path.join(ROOT, "novenas", rel.split("/")[0], "img", rel.split("/")[-1])
            with open(src, "rb") as f:
                return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
        return rel[len("about/"):] if rel.startswith("about/") else "../" + rel

    t = re.sub(r"\{\{IMG:([a-z0-9-]+)\}\}", lambda m: img("about/img/%s.jpg" % m.group(1)), t)

    # each saint once, with every novena that asks their prayers
    people, order = {}, []
    for n in pub:
        for s in n["saints"]:
            if s["id"] not in people:
                people[s["id"]] = {"s": s, "faceof": n["slug"], "novenas": []}; order.append(s["id"])
            people[s["id"]]["novenas"].append(n)

    def card_title(n):
        return n.get("cardTitle") or re.sub(r"^Novena for (the )?", "", n["title"])

    def pray(m):
        p = people.get(m.group(1))
        if not p:
            return ""
        n = p["novenas"][0]
        return ('<a class="pray" href="%s%s/index.html">Pray with him: %s<svg class="i" aria-hidden="true" focusable="false"><use href="#i-arrow-right"/></svg></a>'
                % (up, n["slug"], esc(card_title(n))))
    t = re.sub(r"\{\{PRAY:([a-z0-9-]+)\}\}", pray, t)

    rows = []
    for sid in order:
        p = people[sid]; s = p["s"]; first = p["novenas"][0]
        names = " · ".join(esc(card_title(n)) for n in p["novenas"])
        rows.append('      <li><a href="%s%s/index.html"><img src="%s" alt="" width="56" height="56" loading="lazy"><span><span class="nm">%s</span>'
                    '<span class="pt">%s</span><span class="nv">%s</span></span></a></li>' % (
                        up, first["slug"], img("%s/img/%s_face.jpg" % (p["faceof"], sid)), esc(s["name"] + ("" if re.search(r"\d", s["dates"]) else " the " + s["dates"])), esc(s["patron"]), names))
    t = t.replace("{{PEOPLE}}", "\n".join(rows))

    url = SITE_URL + "/about/"
    if mode == "site":
        head = "\n".join([
            '<meta property="og:type" content="website">',
            '<meta property="og:site_name" content="Pray a Novena">',
            '<meta property="og:url" content="%s">' % url,
            '<meta property="og:title" content="What is a novena? | Pray a Novena">',
            '<meta property="og:description" content="What a novena is, how to pray one, and why Catholics ask the saints to pray for us.">',
            '<meta property="og:image" content="%sog.jpg?v=%s">' % (live, og_ver(os.path.join(ROOT, "site", "og.jpg"))),
            '<meta property="og:image:alt" content="Pray a Novena: Catholic novenas for every intention">',
            '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
            '<meta name="twitter:card" content="summary_large_image">',
            '<link rel="canonical" href="%s">' % url,
            '<link rel="icon" href="../favicon.svg" type="image/svg+xml">',
            '<link rel="apple-touch-icon" href="../apple-touch-icon.png">',
            '<link rel="manifest" href="../manifest.webmanifest">',
            breadcrumbs("What is a novena?", url),
        ])
    else:
        head = ""
    t = t.replace("{{HEAD_META}}", head).replace("{{HOME_HREF}}", up + "index.html" if mode == "site" else live).replace("{{UP}}", up)
    t = t.replace("{{FONTS}}", local_fonts("../") if mode == "site" else GOOGLE_FONTS)
    t = t.replace("{{SW}}", sw_register("../") if mode == "site" else "")
    t = t.replace("{{FOOTER_CSS}}", FOOTER_CSS).replace("{{FOOTER}}", site_footer(up, current="about/index.html", credits=[ABOUT_IMAGES, CCC_NOTICE]))
    t = t.replace("{{SPRITE}}", sprite(["logo", "cross", "sun", "moon", "text-aa", "arrow-left", "arrow-right"]))
    left = re.findall(r"\{\{[A-Z0-9_:a-z-]+\}\}", t)
    assert not left, left
    return t


def build_about(novenas, site):
    d = os.path.join(site, "about")
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(os.path.join(d, "img"))
    for f in os.listdir(os.path.join(ABOUT_DIR, "img")):
        shutil.copy(os.path.join(ABOUT_DIR, "img", f), os.path.join(d, "img", f))
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(about(novenas))
    print("built about")


def privacy(mode="site"):
    """the privacy page: what is kept on the device, what is not collected, and a button to clear it all"""
    t = read(os.path.join(ROOT, "templates", "privacy.html"))
    up = "../" if mode == "site" else SITE_URL + "/"
    url = SITE_URL + "/privacy/"
    head = "\n".join([
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Pray a Novena">',
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:title" content="Privacy | Pray a Novena">',
        '<meta property="og:description" content="Your progress and intentions stay on your device. No accounts, ads or cookies.">',
        '<link rel="canonical" href="%s">' % url,
        '<link rel="icon" href="../favicon.svg" type="image/svg+xml">',
        '<link rel="apple-touch-icon" href="../apple-touch-icon.png">',
        '<link rel="manifest" href="../manifest.webmanifest">',
        breadcrumbs("Privacy", url),
    ]) if mode == "site" else ""
    t = t.replace("{{HEAD_META}}", head).replace("{{HOME_HREF}}", up + "index.html").replace("{{UP}}", up)
    t = t.replace("{{FONTS}}", local_fonts("../") if mode == "site" else GOOGLE_FONTS)
    t = t.replace("{{SW}}", sw_register("../") if mode == "site" else "")
    t = t.replace("{{FOOTER_CSS}}", FOOTER_CSS).replace("{{FOOTER}}", site_footer(up, current="privacy/index.html", scripture=False))
    t = t.replace("{{SPRITE}}", sprite(["logo", "cross", "sun", "moon", "text-aa", "arrow-left"]))
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", t)
    assert not left, left
    return t


def build_privacy(site):
    d = os.path.join(site, "privacy")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(privacy())
    print("built privacy")


def build_site(search=None):
    novenas = load_novenas()
    site = os.path.join(ROOT, "site")
    for n in novenas:
        d = os.path.join(site, n["slug"])
        if os.path.isdir(d):
            shutil.rmtree(d)
        if n.get("status") not in ("published", "draft"):
            continue
        os.makedirs(os.path.join(d, "img"))
        for f in os.listdir(os.path.join(ROOT, "novenas", n["slug"], "img")):
            shutil.copy(os.path.join(ROOT, "novenas", n["slug"], "img", f), os.path.join(d, "img", f))
        og = os.path.join(ROOT, "novenas", n["slug"], "og.jpg")
        if os.path.exists(og):
            shutil.copy(og, os.path.join(d, "og.jpg"))
        pdf = pdf_path(n)
        if pdf:
            shutil.copy(pdf, os.path.join(d, os.path.basename(pdf)))
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(page(n, "site"))
        print("built", n["slug"], n.get("status"))
    with open(os.path.join(site, "index.html"), "w", encoding="utf-8") as f:
        f.write(library(novenas, search))
    print("built library with", sum(1 for n in novenas if n.get("status") == "published"), "published novenas")
    build_about(novenas, site)
    build_privacy(site)
    build_seo(novenas, site)
    build_sw(site)


def build_sw(site):
    """site/sw.js: precache every page, image, font and icon (not the link-preview images or the PDFs, which a phone
    keeps only once someone opens one); the version is a hash of them"""
    files, h = [], hashlib.sha256()
    for d, _, fs in sorted(os.walk(site)):
        for f in sorted(fs):
            rel = os.path.relpath(os.path.join(d, f), site).replace(os.sep, "/")
            if f in ("sw.js", "og.png", "og.jpg", "_headers", "_redirects", "robots.txt", "sitemap.xml"):
                continue
            if f.endswith(".pdf"):  # not precached, but still part of the version so a new PDF reaches phones
                with open(os.path.join(d, f), "rb") as fh:
                    h.update(rel.encode() + fh.read())
                continue
            files.append(rel)
            with open(os.path.join(d, f), "rb") as fh:
                h.update(rel.encode() + fh.read())
            if f == "index.html":
                files.append(rel[:-len("index.html")] or "./")
    t = read(os.path.join(ROOT, "templates", "sw.js"))
    t = t.replace("{{VERSION}}", h.hexdigest()[:12]).replace("{{FILES}}", json.dumps(files)).replace("{{TIMEOUT}}", str(PAGE_TIMEOUT_MS))
    with open(os.path.join(site, "sw.js"), "w", encoding="utf-8") as f:
        f.write(t)
    print("built sw.js:", len(files), "files cached for offline use")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--artifact":
        n = [x for x in load_novenas() if x["slug"] == sys.argv[2]][0]
        os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
        p = os.path.join(ROOT, "out", n["slug"] + ".html")
        with open(p, "w", encoding="utf-8") as f:
            f.write(page(n, "artifact"))
        print(p, os.path.getsize(p) // 1024, "KB")
    else:
        # --search / --no-search force the library search box on or off (default: on from SEARCH_MIN novenas)
        build_site(True if "--search" in sys.argv else False if "--no-search" in sys.argv else None)
