#!/usr/bin/env python3
"""Check that a print PDF contains every day's text from novena.json, and report the page count.

  python3 tools/check_print.py <exported.pdf> <slug>

Works for the Google Docs export and for tools/print_pdf.py's PDFs (text in content order, footer dropped).
Compares with whitespace, soft breaks and indents removed, so line wrapping doesn't matter.
Needs pdftotext (poppler-utils) and pypdf.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    return re.sub(r"[\s ​­]+", "", s).lower().replace("ﬁ", "fi").replace("ﬂ", "fl")


def main(pdf, slug):
    import pypdf
    pages = len(pypdf.PdfReader(pdf).pages)
    txt = subprocess.run(["pdftotext", "-raw", "-f", "1", "-l", str(min(pages, 5)), pdf, "-"], capture_output=True, text=True).stdout
    # drop the running footer of the site PDFs (tools/print_pdf.py), which can fall inside text that crosses a page
    txt = re.sub(r"(?m)^\f?(Page \d+ of \d+|Pray a Novena · prayanovena\.com/\S*|The 9 Days|Opening and Closing Prayers are on page 1)$", "", txt)
    T = norm(txt)
    n = json.load(open(os.path.join(ROOT, "novenas", slug, "novena.json"), encoding="utf-8"))
    miss = []
    for i, d in enumerate(n["days"], 1):
        for k in ("title", "ref", "verse", "refl", "more", "prayer", "step"):  # `more` is printed since 2026-11-24 (flow6)
            if k not in d:
                continue
            v = d[k].replace(" / ", " ") if k == "verse" else d[k]
            if norm(v) not in T:
                miss.append("day %d %s: %s" % (i, k, v[:60]))
    for k in ("openingPrayer", "closingPrayer"):
        if norm(n[k]) not in T:
            miss.append(k)
    for k in ("epigraph", "closingVerse"):
        if norm(n[k]["text"].replace(" / ", " ")) not in T:
            miss.append(k)
    for s in n["saints"]:
        if norm(s["bio"]) not in T:
            miss.append("bio " + s["name"])
    print("pages:", pages, "(OK)" if pages <= 5 else "(TOO LONG: max 5)")
    print("missing:", miss or "nothing — all text present in pages 1-%d" % min(pages, 5))
    return 0 if pages <= 5 and not miss else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
