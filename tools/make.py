#!/usr/bin/env python3
"""Build and check one novena in one step, printing only what needs a look.

  python3 tools/make.py <slug>                 # verses, link preview, PDF + text check, site, artifact, screenshots, sheets
  python3 tools/make.py <slug> --skip og,pdf   # leave out steps (verses, og, pdf, shots) when their inputs didn't change
  python3 tools/make.py <slug> --fixes F.json  # first apply a reviewer's exact replacements, then build and check

Why: every step a thread takes re-reads its whole memory, and build.py alone prints 25+ lines. This runs the usual
sequence (skill sections 4, 6 and 7) and prints about 15 lines: each step's OK / WARN / FAIL with only its key lines.
Full output of each step is in out/make/<slug>/<step>.log; grep it only when a step fails.

Look at these afterwards, one image each, instead of single screenshots or PDF pages:
  out/make/<slug>/shots.jpg   phone screenshots, light row then dark row
  out/make/<slug>/pdf.jpg     every PDF page
  out/make/<slug>/art.jpg     the 9 day pictures (when the novena has art.json)
  novenas/<slug>/og.jpg       the link preview

Uses Python Playwright when installed, else Node Playwright (tools/og_render.js, tools/shots.js).
--fixes takes a JSON list of {"file": "novenas/<slug>/novena.json", "path": "days[4].more", "old": "...", "new": "...",
"why": "..."} ("path" optional). In a .json file, `old` is matched inside the string values (as the text reads, no JSON
escaping), restricted to `path` when given, and must occur exactly once; the file keeps its indentation. In any other
file, `old` must occur exactly once in the raw text. A fix that doesn't match is skipped and listed, never guessed.
Safe to re-run: a fix already applied is reported as such. Day paths are 0-based (Day 5 is days[4]); a fix whose path
finds nothing is applied where its text occurs once in the file, and says so.
If novena.json "credits" is still "" and out/brief/<slug>/credits.txt exists (the picture helper writes it), the line is
filled in. Apart from --fixes and that, it never changes novena.json, and it never commits or pushes.
On an unchanged novena, skip pdf and og: they rewrite the PDF and site files with new bytes.
"""
import glob, importlib.util, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
HAS_PY_PW = importlib.util.find_spec("playwright") is not None
HAS_CHROME = os.path.exists("/usr/bin/google-chrome")  # shots.py needs it; else tools/shots.js
STEPS = {"verses", "og", "pdf", "shots"}


def run(log, *cmd):
    """run a command from the repo root, append its output to log, return (exit code, output lines)"""
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (p.stdout + p.stderr).splitlines()
    with open(log, "a", encoding="utf-8") as f:
        f.write("$ " + " ".join(cmd) + "\n" + "\n".join(out) + "\n")
    return p.returncode, out


def report(step, code, keep, warn=False):
    status = "FAIL" if code else ("WARN" if warn else "OK")
    print("%-4s %-7s %s" % (status, step, keep[0] if keep else ""))
    for line in keep[1:]:
        print("             " + line)
    return status


def sheet(images, cols, width, out):
    """tile images into one JPEG, `cols` per row, each scaled to `width` px wide"""
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in images]
    if not ims:
        return None
    ims = [im.resize((width, round(im.height * width / im.width))) for im in ims]
    h = max(im.height for im in ims)
    rows = (len(ims) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * width + (cols - 1) * 8, rows * h + (rows - 1) * 8), "white")
    for i, im in enumerate(ims):
        canvas.paste(im, ((i % cols) * (width + 8), (i // cols) * (h + 8)))
    canvas.save(out, quality=82)
    return out


def applied(text, old, new):
    """new is there, and old is gone or every old sits inside a new"""
    return new in text and (old not in text or (old in new and text.count(new) * new.count(old) >= text.count(old)))


def apply_fixes(path):
    """apply a review's exact replacements; returns (applied, already applied, total, notes). Safe to run twice: a fix whose `new`
    text is already there (and whose `old` is gone or is part of `new`) counts as already applied."""
    import json
    fixes = json.load(open(path, encoding="utf-8"))
    bad = [i for i, fx in enumerate(fixes, 1) if not (isinstance(fx, dict) and {"file", "old", "new"} <= fx.keys() and fx["old"])]
    if bad:
        return 0, 0, len(fixes), ["nothing applied: entries %s need non-empty file, old and new" % bad]
    notes, done, already = [], 0, 0
    for i, fx in enumerate(fixes, 1):
        old, new, where = fx["old"], fx["new"], fx["file"] + (" " + fx["path"] if fx.get("path") else "")
        f = os.path.join(ROOT, fx["file"])
        if not os.path.exists(f):
            notes.append("#%d %s: no such file" % (i, fx["file"])); continue
        raw = open(f, encoding="utf-8").read()
        data, indent = None, None
        if f.endswith(".json"):
            data = json.loads(raw)
            indent = next((n for n in (1, 2, 4) if json.dumps(data, ensure_ascii=False, indent=n) == raw.rstrip("\n")), None)
        if data is None or indent is None:
            # plain text, or JSON in an unknown layout: replace in the raw text (JSON-escaped for a .json file)
            o, n = (json.dumps(old, ensure_ascii=False)[1:-1], json.dumps(new, ensure_ascii=False)[1:-1]) if data is not None else (old, new)
            if applied(raw, o, n):
                already += 1; notes.append("#%d %s: already applied" % (i, where)); continue
            if raw.count(o) != 1:
                notes.append("#%d %s: old text found %d times" % (i, where, raw.count(o))); continue
            open(f, "w", encoding="utf-8").write(raw.replace(o, n)); done += 1; continue
        strings = []  # (container, key, path) of every string value
        def walk(node, at):
            items = node.items() if isinstance(node, dict) else enumerate(node) if isinstance(node, list) else []
            for k, v in items:
                w = "%s.%s" % (at, k) if isinstance(node, dict) else "%s[%d]" % (at, k)
                if isinstance(v, str):
                    strings.append((node, k, w.lstrip(".")))
                else:
                    walk(v, w)
        walk(data, "")
        scope = [t for t in strings if t[2] == fx["path"]] if fx.get("path") else strings
        text = lambda ts: "\n".join(t[0][t[1]] for t in ts)
        moved = ""
        if fx.get("path") and old not in text(scope) and new not in text(scope):
            # wrong path (e.g. a 1-based day): look in the whole file instead, and say so
            scope, moved = strings, " (path %s had neither text; matched in the whole file)" % fx["path"]
        if applied(text(scope), old, new):
            already += 1; notes.append("#%d %s: already applied%s" % (i, where, moved)); continue
        hits = [t for t in scope if old in t[0][t[1]]]
        if moved and len(hits) == 1:
            moved = " (found at %s, not %s)" % (hits[0][2], fx["path"])
        if len(hits) != 1 or hits[0][0][hits[0][1]].count(old) != 1:
            n = sum(t[0][t[1]].count(old) for t in hits)
            notes.append("#%d %s: old text found %d times" % (i, where, n)); continue
        node, k, _ = hits[0]
        node[k] = node[k].replace(old, new)
        open(f, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=indent) + ("\n" if raw.endswith("\n") else ""))
        done += 1
        if moved:
            notes.append("#%d applied%s" % (i, moved))
    return done, already, len(fixes), notes


def json_credits(nj):
    import json
    return json.load(open(nj, encoding="utf-8")).get("credits")


def fill_credits(slug):
    """novena.json "credits" still empty and the picture helper wrote out/brief/<slug>/credits.txt: fill it in"""
    import json
    nj, ct = os.path.join(ROOT, "novenas", slug, "novena.json"), os.path.join(ROOT, "out", "brief", slug, "credits.txt")
    raw = open(nj, encoding="utf-8").read()
    data = json.loads(raw)
    if data.get("credits") or not os.path.exists(ct):
        return None
    indent = next((n for n in (1, 2, 4) if json.dumps(data, ensure_ascii=False, indent=n) == raw.rstrip("\n")), 1)
    data["credits"] = open(ct, encoding="utf-8").read().strip()
    open(nj, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=indent) + "\n")
    return "filled from out/brief/%s/credits.txt" % slug


def main(slug, skip, fixes=None):
    nj = os.path.join(ROOT, "novenas", slug, "novena.json")
    if not os.path.exists(nj):
        sys.exit("no novenas/%s/novena.json" % slug)
    out = os.path.join(ROOT, "out", "make", slug)
    os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(out, "*.log")):
        os.remove(f)
    log = lambda step: os.path.join(out, step + ".log")
    results, look = [], []

    if fixes:
        done, already, total, notes = apply_fixes(fixes)
        head = "applied %d of %d" % (done, total) + (", %d already in" % already if already else "")
        results.append(report("fixes", 0, [head] + notes, warn=done + already < total))
    filled = fill_credits(slug)
    if filled:
        results.append(report("credits", 0, [filled]))
    elif not json_credits(nj):
        results.append(report("credits", 0, ["novena.json has no image credits yet"], warn=True))

    if "verses" not in skip:
        code, lines = run(log("verses"), PY, "tools/check_verses.py", nj)
        diffs = [l for l in lines if l.startswith("DIFF") or l.startswith("     ")]
        tail = [l for l in lines if l.startswith("archaic") or "DIFF line(s)" in l]
        arch = any(l.startswith("archaic") and not l.endswith("none") for l in lines)
        keep = (tail[-1:] + diffs[:24] + tail[:-1]) or lines[-3:]
        if code and lines and lines[-1] not in keep:
            keep.append(lines[-1])  # the error, so a crash doesn't read as a verse mismatch
        results.append(report("verses", code, keep, warn=bool(diffs) or arch))

    if "og" not in skip:
        if HAS_PY_PW:
            code, lines = run(log("og"), PY, "tools/og.py", slug)
        else:
            d = os.path.join(out, "og-html")
            code, lines = run(log("og"), PY, "tools/og.py", "--html", d, slug)
            if not code:
                code, lines = run(log("og"), "node", "tools/og_render.js", d)
        results.append(report("og", code, ["novenas/%s/og.jpg" % slug] if not code else lines[-4:]))
        look.append("novenas/%s/og.jpg" % slug)

    pdf = os.path.join("novenas", slug, slug + "-novena.pdf")
    pdf_ok = True
    if "pdf" not in skip:
        code, lines = run(log("pdf"), PY, "tools/print_pdf.py", slug)
        keep = [l for l in lines if re.match(r"[a-z0-9]+: .*body", l) or l.startswith("NOTICE") or "rror" in l] or lines[-4:]
        if not code:
            c2, l2 = run(log("pdf"), PY, "tools/check_print.py", pdf, slug)
            code = code or c2
            keep += [l for l in l2 if l.startswith("pages:") or l.startswith("missing:")]
        missing = any(l.startswith("missing:") and "all text present" not in l for l in keep)
        results.append(report("pdf", code, keep, warn=missing))
        pdf_ok = not code

    code, lines = run(log("build"), PY, "tools/build.py")
    warns = list(dict.fromkeys(l for l in lines if "WARNING" in l or "rror" in l))
    if not code:
        c2, l2 = run(log("build"), PY, "tools/build.py", "--artifact", slug)
        code = code or c2
        art_line = [l for l in l2 if l.endswith("KB")]
    if len(warns) > 5:
        warns = warns[:5] + ["... %d more WARNING lines in out/make/%s/build.log" % (len(warns) - 5, slug)]
    results.append(report("build", code, (warns + (art_line if not code else [])) or lines[-4:], warn=bool(warns)))
    build_ok = not code

    if "shots" not in skip and build_ok:
        for f in glob.glob(os.path.join(ROOT, "out", "shots", slug + "_*.png")):
            os.remove(f)
        if HAS_PY_PW and HAS_CHROME:
            code, lines = run(log("shots"), PY, "tools/shots.py", slug)
        else:
            code, lines = run(log("shots"), "node", "tools/shots.js", slug)
        errs = [l for l in lines if "page errors" in l]
        shots = sorted(glob.glob(os.path.join(ROOT, "out", "shots", slug + "_light_*.png"))) + \
            sorted(glob.glob(os.path.join(ROOT, "out", "shots", slug + "_dark_*.png")))
        if not code and shots:
            n = len(shots) // 2 or 1
            sheet(shots, n, 260, os.path.join(out, "shots.jpg"))
            look.append("out/make/%s/shots.jpg" % slug)
        bad = any(not l.endswith("none") for l in errs)
        results.append(report("shots", code, errs or lines[-4:], warn=bad))

    if os.path.exists(os.path.join(ROOT, pdf)) and pdf_ok:
        for f in glob.glob(os.path.join(out, "page-*.png")):
            os.remove(f)
        subprocess.run(["pdftoppm", "-r", "50", "-png", pdf, os.path.join(out, "page")], cwd=ROOT)
        pages = sorted(glob.glob(os.path.join(out, "page-*.png")))
        if sheet(pages, 3, 420, os.path.join(out, "pdf.jpg")):
            look.append("out/make/%s/pdf.jpg" % slug)
    if os.path.exists(os.path.join(ROOT, "novenas", slug, "art.json")):
        code, _ = run(log("art"), PY, "tools/art.py", "sheet", slug, os.path.join(out, "art.jpg"))
        if not code:
            look.append("out/make/%s/art.jpg" % slug)

    print("look at:", ", ".join(look) or "nothing made")
    print("logs:   out/make/%s/<step>.log" % slug)
    return 1 if "FAIL" in results else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    opts = {}
    for flag in ("--skip", "--fixes"):
        if flag in args:
            k = args.index(flag)
            if k + 1 >= len(args) or args[k + 1].startswith("--"):
                sys.exit("%s needs a value\n\n%s" % (flag, __doc__))
            opts[flag] = args[k + 1]; del args[k:k + 2]
    skip = set(opts.get("--skip", "").split(",")) - {""}
    if skip - STEPS:
        sys.exit("unknown step(s) for --skip: %s (steps: %s)" % (", ".join(sorted(skip - STEPS)), ", ".join(sorted(STEPS))))
    fixes = opts.get("--fixes")
    if len(args) != 1 or args[0].startswith("-"):
        sys.exit(__doc__)
    sys.exit(main(args[0], skip, fixes))
