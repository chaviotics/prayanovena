#!/usr/bin/env python3
"""Fill a copy of the print template Doc with a novena's content, keeping every style.

  python3 tools/print_fill.py <read_doc.json> <tabId> <slug> [--images-base URL] > requests.json

<read_doc.json> is a saved Google Docs read of the COPY (the read_doc tool result; a {"content": ...}
wrapper is fine). The script prints {"revisionId": ..., "requests": [...]} — send the requests with
update_doc and writeControl.requiredRevisionId = revisionId. Requests run bottom-up, so one batch is enough.

What it replaces: page-1 kicker, title (2 lines), subtitle, epigraph, intercessor heading and cards
(portraits from --images-base, default the live site), the "Alongside prayer" tip, the Memorare wording,
the daily prayers (opening, litany, closing, Memorare), and for each day: icon, title, verse, ref,
reflection (paragraph 1 only), prayer and step; then the closing verse and the image credits
(at the bottom of page 1, under the Scripture notice).
It also clears the manual layout fixes (page breaks before days, extra space after steps) so the
layout can be re-checked from scratch.

Optional novena.json fields used only here:
  "printTitle":   ["Novena for Relief from Debt", "and Financial Hardship"]   (2 lines)
  "printClosing": ["first line of the closing verse,", "second line."]
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_URL = "https://images.weserv.nl/?url=api.iconify.design/ph/{}.svg%3Fcolor%3D%252394702A%26height%3D96&output=png"
MARIAN_MEMORARE = ("Remember, O most gracious Virgin Mary, that never was it known that anyone who fled to your protection, "
                   "implored your help, or sought your intercession was left unaided. Inspired by this confidence, I fly unto you, "
                   "O Virgin of virgins, my Mother. To you do I come; before you I stand, sinful and sorrowful. O Mother of the Word "
                   "Incarnate, despise not my petitions, but in your mercy hear and answer me.")
NUMWORD = {1: "The Intercessor", 2: "The 2 Intercessors", 3: "The 3 Intercessors"}


def u16(s):
    return len(s.encode("utf-16-le")) // 2


def plain(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h)).replace(" ", " ")


def segments(h):
    """credits HTML -> [(text, italic)]"""
    out = []
    for part in re.split(r"(<em>.*?</em>)", h):
        if not part:
            continue
        it = part.startswith("<em>")
        out.append((plain(part), it))
    return out


def split_two(text):
    """split a line of text into two roughly equal lines at a comma (preferred) or a space"""
    mid = len(text) / 2
    cands = [m.end() for m in re.finditer(r",\s", text)] or [m.start() for m in re.finditer(r"\s", text)]
    cut = min(cands, key=lambda c: abs(c - mid))
    return text[:cut].rstrip(), text[cut:].lstrip()


def saint_line(saints):
    names = [s["name"] for s in saints]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " & " + names[-1]


class Doc:
    def __init__(self, path, tab):
        d = json.load(open(path, encoding="utf-8"))
        d = d.get("content", d)
        self.rev = d["revisionId"]
        t = [x for x in d["tabs"] if x["tabProperties"]["tabId"] == tab][0]
        self.dt = t["documentTab"]
        self.io = self.dt.get("inlineObjects", {})
        self.top = []      # top-level body items in order
        self.paras = []    # every paragraph, tables included, in order
        for el in self.dt["body"]["content"]:
            self.top.append(el)
            self._walk(el)

    def _walk(self, el):
        if "paragraph" in el:
            self.paras.append(el)
        elif "table" in el:
            for r in el["table"]["tableRows"]:
                for c in r["tableCells"]:
                    for x in c["content"]:
                        self._walk(x)

    @staticmethod
    def text(p):
        return "".join(e["textRun"]["content"] if "textRun" in e else "￼" for e in p["paragraph"]["elements"])

    def find(self, prefix, start=0):
        for i, p in enumerate(self.paras):
            if p["startIndex"] >= start and self.text(p).startswith(prefix):
                return i, p
        raise SystemExit("paragraph not found: %r" % prefix)

    def runs(self, p):
        return [e for e in p["paragraph"]["elements"] if "textRun" in e]

    def tables(self):
        return [el for el in self.top if "table" in el]


def main():
    args = sys.argv[1:]
    base = None
    if "--images-base" in args:
        k = args.index("--images-base"); base = args[k + 1]; del args[k:k + 2]
    path, tab, slug = args
    n = json.load(open(os.path.join(ROOT, "novenas", slug, "novena.json"), encoding="utf-8"))
    base = (base or "https://prayanovena.com/%s/img" % slug).rstrip("/")
    D = Doc(path, tab)
    T = lambda r: {"startIndex": r[0], "endIndex": r[1], "tabId": tab}
    groups = []  # (sortkey, [requests]) — applied in descending sortkey order

    def replace(a, b, new, extra=None):
        """replace [a,b) (b excludes the paragraph's final newline) with new text, keeping a's style"""
        reqs = []
        if new:
            reqs.append({"insertText": {"location": {"index": a, "tabId": tab}, "text": new}})
        L = u16(new)
        if b > a:
            reqs.append({"deleteContentRange": {"range": T((a + L, b + L))}})
        if extra:
            reqs += extra(a, L)
        groups.append((a, reqs))

    def whole(p, new, extra=None):
        replace(p["startIndex"], p["endIndex"] - 1, new, extra)

    def run_span(p, k):
        r = D.runs(p)[k]
        end = r["endIndex"] - (1 if r["textRun"]["content"].endswith("\n") else 0)
        return r["startIndex"], end

    STYLE_KEYS = ("bold", "italic", "underline", "smallCaps", "foregroundColor", "fontSize", "weightedFontFamily")

    def replace_run(p, k, new):
        """replace run k's text; a run after the first would inherit the previous run's style, so restate its own"""
        r = D.runs(p)[k]
        a, b = run_span(p, k)
        if k == 0:
            return replace(a, b, new)
        st = r["textRun"].get("textStyle", {})
        style = {key: st.get(key, False) for key in STYLE_KEYS if key in st or key in ("bold", "italic", "smallCaps")}
        fields = ",".join(style)
        replace(a, b, new, lambda a0, L: [{"updateTextStyle": {"range": T((a0, a0 + L)), "textStyle": style, "fields": fields}}])

    def swap_image(p, uri, height):
        for e in p["paragraph"]["elements"]:
            if "inlineObjectElement" in e:
                o = D.io[e["inlineObjectElement"]["inlineObjectId"]]["inlineObjectProperties"]["embeddedObject"]
                h0, w0 = o["size"]["height"]["magnitude"], o["size"]["width"]["magnitude"]
                i = e["startIndex"]
                size = {"height": {"magnitude": height, "unit": "PT"},
                        "width": {"magnitude": round(w0 * height / h0, 2) if height != h0 else w0, "unit": "PT"}}
                return [{"deleteContentRange": {"range": T((i, i + 1))}},
                        {"insertInlineImage": {"location": {"index": i, "tabId": tab}, "uri": uri, "objectSize": size}}], i
        raise SystemExit("no image in paragraph")

    saints = n["saints"]
    assert len(saints) == 3, "print_fill handles 3 saints; delete table columns by hand for fewer"

    # ---------- page 1 ----------
    kick = D.paras[1]  # the line under the cross
    whole(kick, n["kicker"].upper())
    t1, t2 = n.get("printTitle") or split_two(n["title"])
    whole(D.paras[2], t1)
    whole(D.paras[3], t2)
    _, sub = D.find("through the intercession of")
    whole(sub, "through the intercession of " + saint_line(saints))
    def sc_lord(text, offset):
        """small caps for LORD and GOD (written as Lord, God), as the NABRE prints the divine name"""
        def f(a, L):
            reqs = [{"updateTextStyle": {"range": T((a, a + L)), "textStyle": {"smallCaps": False}, "fields": "smallCaps"}}]
            for m in re.finditer("LORD|GOD", text):
                s0 = a + offset + u16(text[:m.start()])
                reqs.append({"updateTextStyle": {"range": T((s0, s0 + len(m.group()))), "textStyle": {"smallCaps": True}, "fields": "smallCaps"}})
            return reqs
        return f

    _, epi = D.find("“")
    et = n["epigraph"]["text"].replace(" / ", "\u000b")  # NABRE poetry lines keep their breaks (soft line breaks)
    whole(epi, "“" + et.replace("LORD", "Lord").replace("GOD", "God") + "”", sc_lord(et, 1))
    ei = D.paras.index(epi)
    whole(D.paras[ei + 1], n["epigraph"]["ref"].upper())
    _, ih = D.find("The 3 Intercessors")
    whole(ih, NUMWORD[len(saints)])

    cards = D.tables()[0]["table"]["tableRows"][0]["tableCells"]
    for s, cell in zip(saints, cards):
        ps = [x for x in cell["content"] if "paragraph" in x]
        img, name, meta, pat, bio = ps[:5]
        whole(bio, s["bio"]); whole(pat, s["patron"]); whole(meta, s["dates"] + " · " + s["feast"]); whole(name, s["name"])
        reqs, i = swap_image(img, "%s/%s.jpg" % (base, s["id"]), 120)
        reqs[1]["insertInlineImage"]["objectSize"]["width"]["magnitude"] = 96  # portraits are 480x600 (4:5)
        groups.append((i, reqs))

    # how-to: Memorare wording, "Alongside prayer" tip
    mem = n["memorare"]
    _, how4 = D.find("Pray the Closing Prayer")
    for r in D.runs(how4):
        if r["textRun"]["content"].startswith("Memorare"):
            replace_run(how4, D.runs(how4).index(r), "Memorare" if mem.get("to") == "Mary" else "Memorare to " + mem["to"])
    _, along = D.find("ALONGSIDE PRAYER")
    tip = [t for t in n["tips"] if t["h"].lower().startswith("alongside")][0]
    whole(D.paras[D.paras.index(along) + 1], plain(tip["p"]))

    # ---------- daily prayers ----------
    _, dp = D.find("Daily Prayers")
    _, op = D.find("Heavenly Father", start=dp["startIndex"])
    a, b = run_span(op, 0)
    replace(a, b, n["openingPrayer"] + " ")

    _, cp_head = D.find("Closing Prayer", start=op["startIndex"])
    ci = D.paras.index(cp_head)
    lit = []
    j = ci + 1
    while D.text(D.paras[j]).rstrip("\n").endswith("pray for us."):
        lit.append(D.paras[j]); j += 1
    closing = D.paras[j]
    a, b = run_span(closing, 0)
    replace(a, b, n["closingPrayer"] + " ")
    want = [l["text"] + ", " for l in n["litany"]]
    for p, txt in zip(lit, want):
        a, b = run_span(p, 0); replace(a, b, txt)
    if len(want) < len(lit):
        for p in lit[len(want):]:
            groups.append((p["startIndex"], [{"deleteContentRange": {"range": T((p["startIndex"], p["endIndex"]))}}]))
    elif len(want) > len(lit):
        last = lit[-1]; at = last["endIndex"]
        reqs = []
        add = "".join(t + "pray for us.\n" for t in want[len(lit):])
        reqs.append({"insertText": {"location": {"index": at, "tabId": tab}, "text": add}})
        pos = at
        for t in want[len(lit):]:
            reqs.append({"updateTextStyle": {"range": T((pos, pos + u16(t))), "textStyle": {"italic": False, "foregroundColor": {"color": {"rgbColor": {"red": 0.16470589, "green": 0.14509805, "blue": 0.12941177}}}}, "fields": "italic,foregroundColor"}})
            pos += u16(t) + u16("pray for us.\n")
        groups.append((at, reqs))

    _, mlabel = D.find("MEMORARE", start=closing["startIndex"])
    whole(mlabel, "MEMORARE" if mem.get("to") == "Mary" else ("MEMORARE TO " + mem["to"]).upper())
    mtext = D.paras[D.paras.index(mlabel) + 1]
    a, b = run_span(mtext, 0)
    replace(a, b, (MARIAN_MEMORARE if mem.get("to") == "Mary" and not mem.get("text") else mem["text"]) + " ")

    # ---------- the nine days ----------
    heads = [p for p in D.paras if re.match(r"￼\s+DAY \d", D.text(p))]
    assert len(heads) == 9, len(heads)
    for k, (hp, d) in enumerate(zip(heads, n["days"])):
        i = D.paras.index(hp)
        title, verse, ref, refl, pray, prayer, step = D.paras[i + 1:i + 8]
        assert D.text(pray).startswith("PRAY") and D.text(step).startswith("TODAY"), k
        # step text (run 2), keep the label run
        replace_run(step, 1, d["step"])
        # prayer (run 1), keep the soft break and "(Name your intention.) Amen."
        a, b = run_span(prayer, 0); replace(a, b, d["prayer"])
        whole(refl, d["refl"])
        a, b = run_span(ref, 0); replace(a, b, d["ref"].upper())
        lines = d["verse"].replace("LORD", "Lord").replace("GOD", "God").split(" / ")
        vt = "".join(("" if j == 0 else ("\u000b " if j % 2 else "\u000b")) + l for j, l in enumerate(lines))

        def vstyle(a, L, vt=vt, orig=d["verse"]):
            reqs = [{"updateTextStyle": {"range": T((a, a + L)), "textStyle": {"smallCaps": False, "italic": True}, "fields": "smallCaps,italic"}}]
            src = orig.split(" / ")
            pos = a
            for j, l in enumerate(src):
                if j:
                    pos += 2 if j % 2 else 1
                for m in re.finditer("LORD|GOD", l):
                    s0 = pos + u16(l[:m.start()])
                    reqs.append({"updateTextStyle": {"range": T((s0, s0 + len(m.group()))), "textStyle": {"smallCaps": True}, "fields": "smallCaps"}})
                pos += u16(l)
            return reqs
        whole(verse, vt, vstyle)
        whole(title, d["title"])
        reqs, ii = swap_image(hp, ICON_URL.format(n["icons"][k]), 13)
        # one-character ranges: a paragraph style applies to every paragraph the range touches
        reqs.append({"updateParagraphStyle": {"range": T((hp["startIndex"] + 1, hp["startIndex"] + 2)), "paragraphStyle": {"pageBreakBefore": False}, "fields": "pageBreakBefore"}})
        reqs.append({"updateParagraphStyle": {"range": T((step["startIndex"], step["startIndex"] + 1)), "paragraphStyle": {"spaceBelow": {"magnitude": 2, "unit": "PT"}}, "fields": "spaceBelow"}})
        groups.append((ii, reqs))

    # ---------- closing verse and credits ----------
    _, c1 = D.find("“", start=heads[-1]["startIndex"])
    c2 = D.paras[D.paras.index(c1) + 1]
    cite = D.paras[D.paras.index(c1) + 2]
    l1, l2 = n.get("printClosing") or split_two(n["closingVerse"]["text"])
    replace_run(c1, 1, l1)
    whole(c2, l2 + "”")
    whole(cite, n["closingVerse"]["ref"].upper())
    _, cred = D.find("Images")  # image credits sit at the bottom of page 1 (older copies: at the end)
    segs = segments(n["credits"])
    txt = "".join(s for s, _ in segs)

    def cstyle(a, L, segs=segs):
        reqs = [{"updateTextStyle": {"range": T((a, a + L)), "textStyle": {"italic": False}, "fields": "italic"}}]
        pos = a
        for s, it in segs:
            if it:
                reqs.append({"updateTextStyle": {"range": T((pos, pos + u16(s))), "textStyle": {"italic": True}, "fields": "italic"}})
            pos += u16(s)
        return reqs
    whole(cred, txt, cstyle)

    groups.sort(key=lambda g: -g[0])
    reqs = [r for _, rs in groups for r in rs]
    json.dump({"revisionId": D.rev, "requests": reqs}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
