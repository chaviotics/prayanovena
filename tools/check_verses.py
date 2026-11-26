#!/usr/bin/env python3
"""Check a novena's Scripture (epigraph, closing verse, 9 days) word for word against the RSVCE chapter
files of github.com/andrewheekin/obsidian-holy-bible. Used by the spiritual-dryness thread, Nov 24 2026.

  python3 tools/check_verses.py novenas/<slug>/novena.json [/tmp/ohb]

Source: raw.githubusercontent.com and api.github.com/repos/... are NOT usable here (raw 404s on a guessed
path; the API refuses repos outside the session). What works is a sparse, blob-less git clone:
  git clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/andrewheekin/obsidian-holy-bible /tmp/ohb
  cd /tmp/ohb && git checkout -q HEAD -- "Holy Bible/<Testament>/<NN>, <Book title>/<Book> <ch>.md"
This script does that checkout for each chapter it needs (commit 9595b0c at the time of writing).
File pattern: "Holy Bible/{Old,New} Testament/<NN>, <Book title>/<Book> <ch>.md"; psalms are "Psalms <ch>.md".
Each line is "<verse> <text>"; the RSV-CE line comes first, then Latin and Greek lines with the same number.
Source quirks: "theLord" for small-caps LORD (normalized here), stray footnote letters glued into words
("hismhand", "Ioturn"), and paragraph-opening quotation marks of continuing speech (left off on the site).
Those show up as DIFF lines to eyeball; anything else is a real mismatch.
"""
import difflib, json, os, re, subprocess, sys

ALIASES = {"Psalm": "Psalms", "Song of Solomon": "Song of Solomon"}


def ensure_repo(root):
    if not os.path.isdir(os.path.join(root, ".git")):
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout",
                        "https://github.com/andrewheekin/obsidian-holy-bible", root], check=True)
    return subprocess.run(["git", "-C", root, "ls-tree", "-r", "--name-only", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.splitlines()


def chapter_file(root, tree, book, ch):
    name = f"{ALIASES.get(book, book)} {ch}.md"
    hits = [p for p in tree if p.endswith("/" + name)]
    if not hits:
        raise SystemExit(f"no chapter file for {book} {ch}")
    path = os.path.join(root, hits[0])
    if not os.path.exists(path):
        subprocess.run(["git", "-C", root, "checkout", "-q", "HEAD", "--", hits[0]], check=True)
    return path


def source_text(root, tree, ref):
    book, cv = ref.rsplit(" ", 1)
    ch, vv = cv.split(":")
    a, b = (vv.split("–") + [vv])[:2]          # en dash ranges, e.g. "Job 23:8–10"
    lines = open(chapter_file(root, tree, book, ch), encoding="utf-8").read().splitlines()
    out = []
    for v in range(int(a), int(b) + 1):
        line = next((l for l in lines if l.startswith(f"{v} ")), None)   # first match = RSV-CE line
        if line is None:
            raise SystemExit(f"{ref}: verse {v} not found")
        out.append(line[len(str(v)) + 1:].strip())
    s = " ".join(out).replace(" ", " ").replace("theLord", "the LORD")
    return re.sub(r"the LORD(?=[a-z])", "the LORD ", s)


def main():
    novena = json.load(open(sys.argv[1], encoding="utf-8"))
    root = sys.argv[2] if len(sys.argv) > 2 else "/tmp/ohb"
    tree = ensure_repo(root)
    items = [("epigraph", novena["epigraph"]), ("closing", novena["closingVerse"])]
    items += [(f"Day {i}", {"ref": d["ref"], "text": d["verse"]}) for i, d in enumerate(novena["days"], 1)]
    bad = 0
    for name, it in items:
        src = source_text(root, tree, it["ref"])
        txt = it["text"].replace(" / ", " ")
        if src == txt:
            print("OK  ", name, it["ref"])
            continue
        bad += 1
        print("DIFF", name, it["ref"])
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, src, txt).get_opcodes():
            if tag != "equal":
                print("    ", tag, repr(src[i1:i2]), "->", repr(txt[j1:j2]))
    allv = " ".join([novena["epigraph"]["text"], novena["closingVerse"]["text"]] + [d["verse"] for d in novena["days"]])
    arch = re.findall(r"\b(thee|thou|thy|thine|hast|didst|doth|art|wilt|shalt)\b", allv, re.I)
    print("archaic words:", arch or "none")
    print(f"{bad} DIFF line(s) to eyeball (footnote letters and continuing-speech quote marks are expected)")


if __name__ == "__main__":
    main()
