#!/usr/bin/env python3
"""The day pictures in the app's Scripture & Reflection step (app only: never in the printable PDF).

Each novena may have novenas/<slug>/art.json:
  {"days": [ {day 1}, ..., {day 9} ]}      (null for a day left plain, which should be rare)
  a day = {
    "file":   Wikimedia Commons file name (public domain only),
    "width":  the Commons thumbnail width to download (500, 960, 1280 or 1920), or 0 for the original file when it is
              narrower than the size you need
    "crop":   [left, top, right, bottom] of the day picture as fractions (0-1) of the downloaded image, 4:3,
    "kind":   "scene" | "names" | "saint" | "practice" | "stretch"   (see skill/SKILL.md, Day pictures),
    "artist", "title", "year" (may be ""), "place" (museum, may be ""),
    "passage": for a stretch only, the passage the picture shows, e.g. "Acts 12" (shown in the caption),
    "alt":    what the picture shows, for screen readers (one plain sentence),
    "look":   the line after the reflection: "Look again at ... ?" about something visible in the day picture,
    "license": why it is public domain (for images.md)
  }

Commands:
  python3 tools/art.py fetch <slug>     download each day's source to .cache/art/ (curl; skips files already there)
  python3 tools/art.py make <slug>      crop + resize into novenas/<slug>/art/day<N>.jpg (720x540) and day<N>_full.jpg
                                        (at most 900 wide, 1200 tall), and write novenas/<slug>/art/images.md
  python3 tools/art.py sheet <slug> <out.jpg>   contact sheet of the 9 day pictures, to check the crops by eye
  python3 tools/art.py meta "File name.jpg"     Commons metadata (artist, date, license, credit), to fill in art.json

Wikimedia rate-limits fast: space Commons API calls 4-5 s apart. Python's urllib gets 403 from upload.wikimedia.org,
so downloads use curl; API thumbnail URLs point at thumb.wikimedia.org (blocked here), so we build upload.* paths.
"""
import hashlib, json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "art")
UA = "pray-a-novena-build/1.0 (static site; public-domain art)"
KINDS = ("scene", "names", "saint", "practice", "stretch")
DAY_W, DAY_H, FULL_W, FULL_H = 720, 540, 900, 1200

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wm_images import thumb  # noqa: E402


def original(name):
    name = name.replace(" ", "_")
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    import urllib.parse
    return "https://upload.wikimedia.org/wikipedia/commons/%s/%s/%s" % (h[0], h[:2], urllib.parse.quote(name))


def load(slug):
    p = os.path.join(ROOT, "novenas", slug, "art.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def check(slug, art):
    """the rules build.py enforces; returns the list of days (None for plain days)"""
    days = art["days"]
    assert len(days) == 9, (slug, "art.json needs 9 days (null for a plain day)")
    for i, a in enumerate(days, 1):
        if a is None:
            continue
        assert isinstance(a.get("width"), int), (slug, "day", i, "width")
        for k in ("file", "crop", "kind", "artist", "title", "alt", "look", "license"):
            assert a.get(k) not in (None, ""), (slug, "day", i, "art missing", k)
        assert a["kind"] in KINDS, (slug, "day", i, "unknown kind", a["kind"])
        assert a["kind"] != "stretch" or a.get("passage"), (slug, "day", i, "a stretch must name its passage")
        l, t, r, b = a["crop"]
        assert 0 <= l < r <= 1 and 0 <= t < b <= 1, (slug, "day", i, "crop must be fractions")
        assert a["look"].startswith("Look again at ") and a["look"].endswith("?"), (slug, "day", i, "look line")
        for f in ("day%d.jpg" % i, "day%d_full.jpg" % i):
            assert os.path.exists(os.path.join(ROOT, "novenas", slug, "art", f)), (slug, "missing", f, "run tools/art.py make")
    return days


def src_path(a):
    h = hashlib.md5(("%s|%d" % (a["file"], a["width"])).encode()).hexdigest()[:10]
    return os.path.join(CACHE, "%s.jpg" % h)


def fetch(slug):
    os.makedirs(CACHE, exist_ok=True)
    for i, a in enumerate(load(slug)["days"], 1):
        if not a:
            continue
        p = src_path(a)
        if os.path.exists(p) and os.path.getsize(p) > 10000:
            print("day", i, "cached"); continue
        url = thumb(a["file"], a["width"]) if a["width"] else original(a["file"])
        code = subprocess.run(["curl", "-s", "-o", p, "-w", "%{http_code}", "-A", UA, url], capture_output=True, text=True).stdout
        print("day", i, code, a["file"])
        if code != "200":
            if os.path.exists(p):
                os.remove(p)
            print("  failed: try another width (Commons serves 330, 500, 960, 1280, 1920) or wait for the rate limit")
        time.sleep(3)


def make(slug):
    from PIL import Image
    out = os.path.join(ROOT, "novenas", slug, "art")
    os.makedirs(out, exist_ok=True)
    rows = []
    for i, a in enumerate(load(slug)["days"], 1):
        if not a:
            continue
        im = Image.open(src_path(a)).convert("RGB")
        W, H = im.size
        l, t, r, b = a["crop"]
        box = (round(l * W), round(t * H), round(r * W), round(b * H))
        ratio = (box[2] - box[0]) / (box[3] - box[1])
        assert abs(ratio - 4 / 3) < 0.03, (slug, "day", i, "crop is not 4:3", round(ratio, 3))
        im.crop(box).resize((DAY_W, DAY_H), Image.LANCZOS).save(
            os.path.join(out, "day%d.jpg" % i), "JPEG", quality=78, optimize=True, progressive=True)
        k = min(1, FULL_W / W, FULL_H / H)  # the whole picture: at most 900 wide and 1200 tall (tall paintings)
        im.resize((round(W * k), round(H * k)), Image.LANCZOS).save(
            os.path.join(out, "day%d_full.jpg" % i), "JPEG", quality=80, optimize=True, progressive=True)
        kb = [os.path.getsize(os.path.join(out, f)) // 1024 for f in ("day%d.jpg" % i, "day%d_full.jpg" % i)]
        print("day", i, "%d KB + %d KB" % tuple(kb), a["artist"], "-", a["title"])
        work = "%s, *%s*%s%s%s" % (a["artist"], a["title"], ", " + a["year"] if a.get("year") else "",
                                    ", " + a["place"] if a.get("place") else "", " (%s)" % a["passage"] if a.get("passage") else "")
        rows.append("| day%d.jpg, day%d_full.jpg | Day %d (%s) | %s. Commons `%s`, %s; day crop %s | %s |" % (
            i, i, i, a["kind"], work, a["file"], ("%dpx thumbnail" % a["width"]) if a["width"] else "original file", [round(x, 3) for x in a["crop"]], a["license"]))
    with open(os.path.join(out, "images.md"), "w", encoding="utf-8") as f:
        f.write("# Day pictures (app only, all public domain)\n\nMade by `tools/art.py make %s` from `novenas/%s/art.json`.\n\n"
                "| Files | Used for | Work | Why public domain |\n|---|---|---|---|\n" % (slug, slug) + "\n".join(rows) + "\n")


def sheet(slug, dest):
    from PIL import Image
    s = Image.new("RGB", (3 * 360 + 20, 3 * 270 + 20), "white")
    for i in range(1, 10):
        p = os.path.join(ROOT, "novenas", slug, "art", "day%d.jpg" % i)
        if os.path.exists(p):
            s.paste(Image.open(p).resize((360, 270)), (((i - 1) % 3) * 370, ((i - 1) // 3) * 280))
    s.save(dest, quality=80)
    print(dest)


def meta(name):
    q = ["curl", "-s", "-G", "https://commons.wikimedia.org/w/api.php", "-A", UA,
         "--data-urlencode", "action=query", "--data-urlencode", "titles=File:" + name, "--data-urlencode", "prop=imageinfo",
         "--data-urlencode", "iiprop=extmetadata|size", "--data-urlencode", "format=json"]
    r = subprocess.run(q, capture_output=True, text=True).stdout
    try:
        page = list(json.loads(r)["query"]["pages"].values())[0]
    except Exception:
        print("no answer (rate limit?): wait 5 s and try again"); return
    info = page.get("imageinfo", [{}])[0]
    m = info.get("extmetadata", {})
    print("size", info.get("width"), "x", info.get("height"))
    for k in ("ObjectName", "Artist", "DateTimeOriginal", "ImageDescription", "Credit", "LicenseShortName", "UsageTerms"):
        v = re.sub(r"<[^>]+>", "", m.get(k, {}).get("value", "")).strip()
        print("%s: %s" % (k, re.sub(r"\s+", " ", v)[:300]))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "fetch":
        fetch(a[1])
    elif len(a) == 2 and a[0] == "make":
        make(a[1])
    elif len(a) == 3 and a[0] == "sheet":
        sheet(a[1], a[2])
    elif len(a) == 2 and a[0] == "meta":
        meta(a[1])
    else:
        print(__doc__)
