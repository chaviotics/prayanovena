#!/usr/bin/env python3
"""Make the printable PDF of each novena from its novena.json (same words as the app, so they never drift apart).

  python3 tools/print_pdf.py                 # every published novena -> novenas/<slug>/<slug>-novena.pdf
  python3 tools/print_pdf.py healing         # one novena
  python3 tools/print_pdf.py healing --size folio --out out/print   # try another paper size somewhere else

Run it after changing a novena's words (or templates/print.html), then tools/build.py, which copies each PDF
next to its page and links it ("Print or download (PDF)"). build.py warns when a PDF is older than its novena.json.

How: templates/print.html is filled here, then tools/print_render.js (Node Playwright, Chromium) prints it.
Chromium keeps day headings with their text and the Graces box in one piece, so no hand fixes are needed.
The render fails if a PDF runs past MAX_PAGES. Print gets each day's `refl` only; `more` stays in the app.

Paper: A4 (Chav's choice, 2026-11-21). folio (long bond 8.5 x 13 in, the Google Docs size) and letter also work.
"""
import argparse, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402
from build import esc, scripture, saint_line, NUMWORD, MARIAN_MEMORARE, RSV_NOTICE  # noqa: E402
from app_icons import ring, cross  # noqa: E402

ROOT = build.ROOT
MAX_PAGES = 4
SIZES = {  # width, height, top margin, body size, page 1 content height (page minus margins, so the notice sits at the foot)
    "folio": ("8.5in", "13in", "0.5in", "10pt", "11.86in"),
    "a4": ("210mm", "297mm", "0.45in", "9.2pt", "10.6in"),
    "letter": ("8.5in", "11in", "0.42in", "9.4pt", "9.94in"),
}
SIZE_CSS = {  # shorter pages: tighter page 1 so the notice still fits at its foot
    "a4": ".saint img{width:76pt;height:95pt}h2{margin:10pt 0 6pt}.top h1{font-size:28pt}.top .mark{width:26pt;height:26pt}.saint{font-size:8.7pt}.intent .lines div{height:20pt}",
    "letter": ".saint img{width:72pt;height:90pt}h2{margin:9pt 0 6pt}.top h1{font-size:28pt}.intent .lines div{height:19pt}",
}


VERSIONS = os.path.join(ROOT, "novenas", "print_versions.json")  # what each PDF was made from (checked by build.py)


def print_version(slug):
    """hash of everything a PDF is made from, so build.py can tell when it needs remaking"""
    import hashlib
    h = hashlib.sha256()
    for p in (os.path.join(ROOT, "novenas", slug, "novena.json"), os.path.join(ROOT, "templates", "print.html"), os.path.abspath(__file__)):
        h.update(open(p, "rb").read())
    return h.hexdigest()[:12]


def fonts_css():
    d = os.path.join(ROOT, "tools", "print_fonts")
    css = open(os.path.join(d, "fonts.css"), encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.sub(r"url\(([^)]+)\)", lambda m: "url(file://%s/%s)" % (d, m.group(1)), css)


def icon(name):
    p = os.path.join(ROOT, "tools", "icons", name + ".svg")
    body = re.search(r"<svg[^>]*>(.*)</svg>", open(p, encoding="utf-8").read(), re.S).group(1).strip()
    return '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">%s</svg>' % body


def rich(h):
    """tip HTML from novena.json: keep italics for responses, drop links (paper has no links) but keep their words"""
    h = re.sub(r'<span class="resp">(.*?)</span>', r'<em>\1</em>', h)
    h = re.sub(r"<a [^>]*>(.*?)</a>", r"\1", h)
    return h


def verse(v):
    lines = v.split(" / ")
    if len(lines) == 1:
        return scripture(v)
    return "<br>".join(('<span class="in">%s</span>' % scripture(l)) if i % 2 else scripture(l) for i, l in enumerate(lines))


def split_two(text):
    mid = len(text) / 2
    cands = [m.end() for m in re.finditer(r",\s", text)] or [m.start() for m in re.finditer(r"\s", text)]
    cut = min(cands, key=lambda c: abs(c - mid))
    return text[:cut].rstrip(), text[cut:].lstrip()


LAYOUTS = {  # template, and how the type is sized (None: fixed sizes; else the largest --k that fits `pages`)
    "classic": ("print.html", None),
    "full": ("print-full.html", {"pages": 4, "lo": 0.9, "hi": 1.3, "width": "186mm", "page1": "273mm"}),
    "compact": ("print-compact.html", {"pages": 3, "lo": 0.84, "hi": 1.1, "fallback": 4}),
    "flow": ("print-flow.html", {"pages": 4, "lo": 0.8, "hi": 1.2}),
    "flow2": ("print-flow2.html", {"pages": 4, "lo": 0.8, "hi": 1.2}),
    "flow3": ("print-flow3.html", {"pages": 4, "lo": 0.8, "hi": 1.2}),
    "flow4": ("print-flow4.html", {"pages": 4, "lo": 0.8, "hi": 1.2}),  # flow3 with Today's step as an outlined callout
}
SITE_LAYOUT = "flow4"  # the one linked on the site ("Easy flow 3" with the Today’s step callout, chosen 2026-11-22)


def card_spread(count):
    """Ways to put `count` cards, at most 2 a row, at the foot of pages 2-4: filling pages 2 then 3, or 2 then 4."""
    out = []
    for order in ((0, 1, 2), (0, 2, 1)):
        per, left = [0, 0, 0], count
        for i in order:
            per[i] = min(2, left); left -= per[i]
        if tuple(per) not in out:
            out.append(tuple(per))
    return out


def fill(n, size, layout="classic", tips_at="end", saints_at=(2, 2, 0), notes_page=4):
    slug = n["slug"]
    img = os.path.join(ROOT, "novenas", slug, "img")
    w, h, top, body, p1h = SIZES[size]
    saints = "\n".join(
        '  <div class="saint"><img src="file://%s/%s.jpg" alt=""><div><h3>%s</h3><p class="meta">%s · %s</p>'
        '<p class="pat">%s</p><p>%s</p></div></div>' % (img, s["id"], esc(s["name"]), esc(s["dates"]), esc(s["feast"]),
                                                  esc(s["patron"]), esc(s["bio"])) for s in n["saints"])
    tie = (lambda s: s) if layout not in ("flow3", "flow4") else (lambda s: re.sub(r" (\S+)$", "\u00a0\\1", s))  # keep the last 2 words together
    if layout in ("flow2", "flow3", "flow4"):  # page 1 has only the essentials; each story goes to a day page
        saints = "\n".join(
            '  <div class="saint"><img src="file://%s/%s.jpg" alt=""><h3>%s</h3><p class="meta">%s</p><p class="meta">%s</p>'
            '<p class="pat">%s</p></div>' % (img, s["id"], esc(s["name"]), esc(s["dates"]), esc(s["feast"]), esc(s["patron"]))
            for s in n["saints"])
    tips = "\n".join('    <p class="cap">%s</p><p class="tip">%s</p>' % (esc(t["h"]), rich(t["p"])) for t in n["tips"])
    litany = "\n".join('      <p>%s, <span class="resp">pray for us.</span></p>' % esc(l["text"]) for l in n["litany"])
    mem = n["memorare"]
    days = []
    for k, d in enumerate(n["days"]):
        if layout == "compact":  # number, title and Done box on one line
            days.append(
                '    <article class="day"><div class="dhead"><div class="dnum">%s<span class="n">DAY %d</span><h3>%s</h3><span class="box"></span></div>'
                '<p class="verse">%s</p><p class="cap ref">%s</p></div>'
                '<p>%s</p><div class="pblock"><p class="cap label">Pray</p><p>%s <span class="amen">(Name your intention.) Amen.</span></p>'
                '<p class="step"><span class="cap">Today’s step</span>%s</p></div></article>' % (
                    icon(n["icons"][k]), k + 1, esc(d["title"]), verse(d["verse"]), esc(d["ref"]), esc(d["refl"]),
                    esc(d["prayer"]), esc(d["step"])))
            continue
        days.append(
            '    <article class="day"><div class="dhead"><div class="dnum">%s DAY %d <span class="box"></span><span class="done">Done</span></div>'
            '<h3>%s</h3><p class="verse">%s</p><p class="cap ref">%s</p></div>'
            '<p>%s</p><div class="pblock"><p class="cap label">Pray</p><p>%s <span class="amen">(Name your intention.) Amen.</span></p>'
            '<p class="step"><span class="cap">Today’s step</span>%s</p></div></article>' % (
                icon(n["icons"][k]), k + 1, esc(d["title"]), verse(d["verse"]), esc(d["ref"]), esc(d["refl"]),
                esc(d["prayer"]), esc(d["step"])))
    day_pages, flow_tips = "", ""
    if layout in ("flow", "flow2", "flow3", "flow4"):  # 3 days a page; each day a band: Scripture and reflection | prayer and step
        bands = []
        for k, d in enumerate(n["days"]):
            bands.append(
                '  <article class="day"><div class="dhead">%s<span class="n">%s %d</span><h3>%s</h3>'
                '<span class="done"><span class="box"></span>Done</span></div><div class="dbody">'
                '<div>%s<p class="verse">%s</p><p class="cap ref">%s</p><p>%s</p></div>'
                '<div><p class="cap label">Pray</p><p>%s <span class="amen">(Name your intention.) Amen.</span></p>'
                '<p class="step"><span class="cap">Today’s step</span>%s</p></div></div></article>' % (
                    icon(n["icons"][k]), "Day" if layout in ("flow2", "flow3", "flow4") else "DAY", k + 1, esc(d["title"]),
                    '<p class="cap label">Scripture &amp; Reflection</p>' if layout in ("flow2", "flow3", "flow4") else "",
                    verse(d["verse"]), esc(d["ref"]), tie(esc(d["refl"])), esc(d["prayer"]), tie(esc(d["step"]))))
            if layout in ("flow3", "flow4"):
                bands[-1] = bands[-1].replace("intention.) Amen.", "intention.)\u00a0Amen.")
            if layout == "flow4":  # never break "(Name your intention.) Amen." across lines
                bands[-1] = bands[-1].replace('<span class="amen">(Name', '<span class="amen nowrap">(Name')
                # the verse and its reference sit together inside a gold bar, like Today's step
                bands[-1] = re.sub(r'(<p class="verse">.*?</p><p class="cap ref">.*?</p>)', r'<div class="scrip">\1</div>', bands[-1], count=1)
            if layout == "flow4":  # Today's step as an outlined callout with a walking-figure icon (not one of the day icons): the bar now means Scripture only
                bands[-1] = re.sub(r'<p class="step"><span class="cap">Today’s step</span>(.*?)</p>',
                                   lambda m: '<div class="step call">%s<p><span class="cap">Today’s step</span>%s</p></div>' % (icon("person-simple-walk"), m.group(1)),
                                   bands[-1], count=1)
        c1f, c2f = n.get("printClosing") or split_two(n["closingVerse"]["text"])
        end = ('  <div class="endrow"><div class="graces"><p class="cap">Graces I have noticed</p>'
               '<p class="hint">Small mercies, open doors, moments of peace: write them down and give thanks.</p>'
               '<div class="lines"><div></div><div></div><div></div></div></div>'
               '<div class="closing"><p>“%s</p><p>%s”</p><p class="cap">%s</p></div></div>' % (
                   scripture(c1f), scripture(c2f), esc(n["closingVerse"]["ref"])))
        tips = "\n".join('      <div><p class="cap">%s</p><p>%s</p></div>' % (esc(t["h"]), rich(t["p"])) for t in n["tips"])
        flow_tips = '    <div class="tips">\n%s\n    </div>' % tips
        if tips_at == "end" and layout == "flow":
            end = flow_tips.replace("tips", "tips last", 1) + "\n" + end
            flow_tips = ""
        if layout in ("flow2", "flow3", "flow4"):
            # the saints' stories and the closing verse are "cards", 2 to a row, at the foot of the day pages;
            # saints_at says how many cards go on each of pages 2, 3 and 4. Page 4 ends with the Graces box, full width.
            cards = ['<div class="story"><img src="file://%s/%s.jpg" alt=""><div><p class="cap">Meet your intercessor</p><h3>%s</h3><p>%s</p></div></div>' % (
                img, s["id"], esc(s["name"]), tie(esc(s["bio"]))) for s in n["saints"]]
            cards.append('<div class="vcard"><p>“%s</p><p>%s”</p><p class="cap">%s</p></div>' % (
                scripture(c1f), scripture(c2f), esc(n["closingVerse"]["ref"])))
            if sum(saints_at) != len(cards):
                saints_at = card_spread(len(cards))[0]
            per, at = [], 0
            for c in saints_at:
                per.append(cards[at:at + c]); at += c
            orn = ('  <div class="orn"><svg viewBox="0 0 64 64" aria-hidden="true"><path fill="none" stroke="#94702A" stroke-width="4" '
                   'stroke-linecap="round" d="%s"/><path fill="currentColor" d="%s"/></svg></div>' % (ring(), cross()))
            graces = ('  <div class="graces"><p class="cap">Graces I have noticed</p>'
                      '<p class="hint">Small mercies, open doors, moments of peace: write them down and give thanks.</p>'
                      '<div class="lines"><div class="in"><div class="stack">%s</div></div></div></div>' % ('<div></div>' * 16))  # plain ruled lines, stacked from the bottom
            notes = '  <div class="notes"><p>%s</p><p>%s</p></div>' % (esc(RSV_NOTICE), n["credits"])
            for i in range(3):
                foot = (orn + '\n  <aside class="meet%s">%s</aside>' % (" one" if len(per[i]) == 1 else "", "".join(per[i]))) if per[i] else (orn if i < 2 else "")
                day_pages += ('<section class="dpage%s"><div class="runhead"><b>The 9 Days · Days %d to %d</b>'
                              '<span>Opening and Closing Prayers are on page 1</span></div>\n%s\n%s\n%s</section>\n' % (
                                  " last" if i == 2 else "", 3 * i + 1, 3 * i + 3, "\n".join(bands[3 * i:3 * i + 3]), foot,
                                  (graces if i == 2 else "") + ("\n" + notes if i + 2 == notes_page else "")))
        for i in range(3 if layout == "flow" else 0):
            day_pages += ('<section class="dpage"><div class="runhead"><b>The 9 Days · Days %d to %d</b>'
                          '<span>Opening and Closing Prayers are on page 1</span></div>\n%s\n%s</section>\n' % (
                              3 * i + 1, 3 * i + 3, "\n".join(bands[3 * i:3 * i + 3]), end if i == 2 else ""))
        tips = "\n".join('      <div><p class="cap">%s</p><p>%s</p></div>' % (esc(t["h"]), rich(t["p"])) for t in n["tips"])
    t1, t2 = n.get("printTitle") or split_two(n["title"])
    c1, c2 = n.get("printClosing") or split_two(n["closingVerse"]["text"])
    vals = {
        "FONTS": fonts_css(), "PAGE_W": w, "PAGE_H": h, "MARGIN_TOP": top, "BODY_PT": body, "PAGE1_H": p1h, "SIZE_CSS": SIZE_CSS.get(size, ""), "SLUG": slug,
        "TITLE": esc(n["title"]), "TITLE1": esc(t1), "TITLE2": esc(t2), "KICKER": esc(n["kicker"]),
        "RING": ring(), "CROSS": cross(),
        "SAINT_LINE": saint_line(n["saints"]), "EPI_TEXT": scripture(n["epigraph"]["text"]), "EPI_REF": esc(n["epigraph"]["ref"]),
        "SAINTS_HEAD": NUMWORD[len(n["saints"])], "SAINT_COUNT": str(len(n["saints"])), "SAINTS": saints,
        "HOW_MEMORARE": "<strong>Memorare</strong>" + ("" if mem.get("to") == "Mary" else " to " + esc(mem["to"])),
        "TIPS": tips, "RSV_NOTICE": esc(RSV_NOTICE), "CREDITS": n["credits"],
        "OPENING_PRAYER": esc(n["openingPrayer"]), "LITANY": litany, "CLOSING_PRAYER": esc(n["closingPrayer"]),
        "MEMORARE_TITLE": "Memorare" if mem.get("to") == "Mary" else "Memorare to " + esc(mem["to"]),
        "MEMORARE_TEXT": esc(MARIAN_MEMORARE if mem.get("to") == "Mary" and not mem.get("text") else mem["text"]),
        "TIP_COLS": str(min(len(n["tips"]), 3)), "DAYS": "\n".join(days), "DAY_PAGES": day_pages, "FLOW_TIPS": flow_tips, "CLOSE1": scripture(c1), "CLOSE2": scripture(c2), "CLOSE_REF": esc(n["closingVerse"]["ref"]),
    }
    t = open(os.path.join(ROOT, "templates", LAYOUTS[layout][0]), encoding="utf-8").read()
    for k, v in vals.items():
        t = t.replace("{{%s}}" % k, v)
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", t)
    assert not left, left
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--size", default="a4", choices=SIZES)
    ap.add_argument("--out", help="write PDFs here (as <slug>-<layout>.pdf) instead of novenas/<slug>/")
    ap.add_argument("--layout", default=SITE_LAYOUT, choices=LAYOUTS)
    ap.add_argument("--notes-page", type=int, choices=(3, 4), help="flow2-4: force the page whose foot holds the Scripture notice and image credits (default: 4; flow4 picks 3 or 4 per novena)")
    a = ap.parse_args()
    novenas = [n for n in build.load_novenas() if n.get("status") == "published" or n["slug"] in a.slugs]
    if a.slugs:
        novenas = [n for n in novenas if n["slug"] in a.slugs]
    work = os.path.join(ROOT, "out", "print")
    os.makedirs(work, exist_ok=True)
    jobs = []
    for n in novenas:
        src = os.path.join(work, "%s-%s-%s.html" % (n["slug"], a.layout, a.size))
        open(src, "w", encoding="utf-8").write(fill(n, a.size, a.layout))
        dest_dir = os.path.abspath(a.out) if a.out else os.path.join(ROOT, "novenas", n["slug"])
        os.makedirs(dest_dir, exist_ok=True)
        w, p1h = SIZES[a.size][0], SIZES[a.size][4]
        fit = LAYOUTS[a.layout][1] or {}
        jobs.append({"width": fit.get("width", "calc(%s - 1.2in)" % w), "page1": fit.get("page1", p1h), "html": src, "title": n["title"],
                     "fit": LAYOUTS[a.layout][1], "check_page1": a.layout != "classic",
                     "pdf": os.path.join(dest_dir, ("%s-%s.pdf" % (n["slug"], a.layout)) if a.out else "%s-novena.pdf" % n["slug"])})
    # some layouts try a few arrangements of each novena and keep the one that allows the largest type:
    # flow puts the tips on the last page or on page 1; flow2 tries ways of spreading the saints' stories over pages 2-4
    variants = {"flow": [("tips on the last page", {}), ("tips on page 1", {"tips_at": "p1"})]}
    def options(n):
        if a.layout not in ("flow2", "flow3", "flow4"):
            return variants.get(a.layout, [("", {})])
        # flow4: the footnotes go at the foot of page 3 or page 4, whichever lets the novena use the larger type
        pages = [a.notes_page] if a.notes_page else ([4, 3] if a.layout == "flow4" else [4])
        return [("cards on pages %s, footnotes on page %d" % (", ".join(str(i + 2) for i, c in enumerate(v) for _ in range(c)), np),
                 {"saints_at": v, "notes_page": np})
                for np in pages for v in card_spread(len(n["saints"]) + 1)]
    groups = []
    for n, j in zip(novenas, list(jobs)):
        g = []
        for i, (label, kw) in enumerate(options(n)):
            if i == 0:
                if kw:
                    open(j["html"], "w", encoding="utf-8").write(fill(n, a.size, a.layout, **kw))
                g.append((label, j)); continue
            src = j["html"].replace(".html", "-v%d.html" % i)
            open(src, "w", encoding="utf-8").write(fill(n, a.size, a.layout, **kw))
            alt = dict(j, html=src, pdf=j["pdf"].replace(".pdf", "-v%d.pdf" % i))
            jobs.append(alt); g.append((label, alt))
        groups.append(g)
    jobfile = os.path.join(work, "jobs.json")
    json.dump({"max": MAX_PAGES, "jobs": jobs}, open(jobfile, "w"))
    resfile = os.path.join(work, "results.json")
    code = subprocess.call(["node", os.path.join(ROOT, "tools", "print_render.js"), jobfile, resfile])
    if any(len(g) > 1 for g in groups):
        res = {r["pdf"]: r for r in json.load(open(resfile))}
        code = 0
        for g in groups:
            main_job = g[0][1]
            best = max(g, key=lambda lj: (res[lj[1]["pdf"]]["ok"], res[lj[1]["pdf"]]["k"]))  # ties keep the first
            for label, j in g:
                if j is best[1] and j is not main_job:
                    os.replace(j["pdf"], main_job["pdf"])
                elif j is not main_job and os.path.exists(j["pdf"]):
                    os.remove(j["pdf"])
            r = res[best[1]["pdf"]]
            code |= 0 if r["ok"] else 1
            print("%s: %s, body %.2fpt  %s" % (a.layout, best[0], 10 * r["k"], os.path.basename(main_job["pdf"])))
        jobs = [g[0][1] for g in groups]
    for j in jobs:  # the Scripture notice and image credits belong on page 1 (flow2: at the foot of the last page)
        pg = ["-f", "3", "-l", "4"] if a.layout in ("flow2", "flow3", "flow4") else ["-f", "1", "-l", "1"]
        p1 = subprocess.run(["pdftotext", *pg, j["pdf"], "-"], capture_output=True, text=True).stdout
        if "Scripture quotations" not in p1.replace("\n", " "):
            print("NOTICE: the Scripture notice is not where it belongs in", j["pdf"]); code = 1
    if code == 0 and not a.out and a.size == "a4" and a.layout == SITE_LAYOUT:
        vers = json.load(open(VERSIONS)) if os.path.exists(VERSIONS) else {}
        for n in novenas:
            vers[n["slug"]] = print_version(n["slug"])
        json.dump(vers, open(VERSIONS, "w"), indent=1, sort_keys=True)
        open(VERSIONS, "a").write("\n")
    sys.exit(code)


if __name__ == "__main__":
    main()
