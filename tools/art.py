#!/usr/bin/env python3
"""The day pictures in the app's Scripture & Reflection step (app only: never in the printable PDF).

Each novena may have novenas/<slug>/art.json:
  {"days": [ {day 1}, ..., {day 9} ]}      (null for a day left plain, which should be rare)
  a day = {
    "file":   Wikimedia Commons file name (public domain only),
    "width":  the Commons thumbnail width to download (500, 960, 1280 or 1920), or 0 for the original file when it is
              narrower than the size you need
    "crop":   [left, top, right, bottom] of the day picture as fractions (0-1) of the downloaded image, 4:3,
    "full":   optional [left, top, right, bottom] fractions: the part of the download shown as the whole picture (trims a frame),
    "kind":   "scene" | "names" | "saint" | "practice" | "stretch"   (see skill/SKILL.md, Day pictures),
    "artist", "title", "year" (may be ""), "place" (museum, may be ""),
    "passage": for a stretch only, the passage the picture shows, e.g. "Acts 12" (shown in the caption),
    "alt":    what the picture shows, for screen readers (one plain sentence),
    "look":   the line after the reflection: "Look again at ... ?" about something visible in the day picture,
    "license": why it is public domain (for images.md)
  }

Commands:
  python3 tools/art.py fetch <slug>     download each day's source to .cache/art/ (curl; skips files already there)
  python3 tools/art.py make <slug>      crop + resize into novenas/<slug>/art/day<N>.webp (720x540) and day<N>_full.webp
                                        (at most 900 wide, 1200 tall), and write novenas/<slug>/art/images.md
  python3 tools/art.py sheet <slug> <out.jpg>   contact sheet of the 9 day pictures, to check the crops by eye
  python3 tools/art.py meta "File name.jpg"     Commons metadata (artist, date, license, credit), to fill in art.json
  python3 tools/art.py search "query" [n]       Commons file search: name | size | date | artist | license per hit
  python3 tools/art.py cands <out.jpg> "File 1.jpg" "File 2.jpg" ...   numbered contact sheet of candidates (view once)
  python3 tools/art.py boxes <slug> <out.jpg>   each day's whole picture with its crop drawn in red

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
        for f in ("day%d.webp" % i, "day%d_full.webp" % i):
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
            os.path.join(out, "day%d.webp" % i), "WEBP", quality=80, method=6)
        if a.get("full"):  # optional [l, t, r, b]: trim a museum photo's frame and wall from the whole picture
            fl, ft, fr, fb = a["full"]
            im = im.crop((round(fl * W), round(ft * H), round(fr * W), round(fb * H)))
            W, H = im.size
        k = min(1, FULL_W / W, FULL_H / H)  # the whole picture: at most 900 wide and 1200 tall (tall paintings)
        im.resize((round(W * k), round(H * k)), Image.LANCZOS).save(
            os.path.join(out, "day%d_full.webp" % i), "WEBP", quality=80, method=6)
        kb = [os.path.getsize(os.path.join(out, f)) // 1024 for f in ("day%d.webp" % i, "day%d_full.webp" % i)]
        print("day", i, "%d KB + %d KB" % tuple(kb), a["artist"], "-", a["title"])
        work = "%s, *%s*%s%s%s" % (a["artist"], a["title"], ", " + a["year"] if a.get("year") else "",
                                    ", " + a["place"] if a.get("place") else "", " (%s)" % a["passage"] if a.get("passage") else "")
        rows.append("| day%d.webp, day%d_full.webp | Day %d (%s) | %s. Commons `%s`, %s; day crop %s | %s |" % (
            i, i, i, a["kind"], work, a["file"], ("%dpx thumbnail" % a["width"]) if a["width"] else "original file", [round(x, 3) for x in a["crop"]], a["license"]))
    with open(os.path.join(out, "images.md"), "w", encoding="utf-8") as f:
        f.write("# Day pictures (app only, all public domain)\n\nMade by `tools/art.py make %s` from `novenas/%s/art.json`.\n\n"
                "| Files | Used for | Work | Why public domain |\n|---|---|---|---|\n" % (slug, slug) + "\n".join(rows) + "\n")


def sheet(slug, dest):
    from PIL import Image
    s = Image.new("RGB", (3 * 360 + 20, 3 * 270 + 20), "white")
    for i in range(1, 10):
        p = os.path.join(ROOT, "novenas", slug, "art", "day%d.webp" % i)
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


def search(query, n=12):
    """Commons file search: one line per hit with size, date, artist and license, to shortlist candidates"""
    q = ["curl", "-s", "-G", "https://commons.wikimedia.org/w/api.php", "-A", UA,
         "--data-urlencode", "action=query", "--data-urlencode", "generator=search", "--data-urlencode", "gsrsearch=" + query,
         "--data-urlencode", "gsrnamespace=6", "--data-urlencode", "gsrlimit=%d" % n, "--data-urlencode", "prop=imageinfo",
         "--data-urlencode", "iiprop=size|extmetadata", "--data-urlencode", "iiextmetadatafilter=Artist|DateTimeOriginal|LicenseShortName",
         "--data-urlencode", "format=json"]
    r = subprocess.run(q, capture_output=True, text=True).stdout
    try:
        pages = sorted(json.loads(r)["query"]["pages"].values(), key=lambda p: p.get("index", 0))
    except Exception:
        print("no answer (rate limit or no hits): wait 5 s and try again"); return
    for p in pages:
        info = p.get("imageinfo", [{}])[0]
        m = info.get("extmetadata", {})
        f = lambda k: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.get(k, {}).get("value", ""))).strip()[:40]
        print("%s | %sx%s | %s | %s | %s" % (p["title"][5:], info.get("width"), info.get("height"), f("DateTimeOriginal"), f("Artist"), f("LicenseShortName")))


def _label(im, text):
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 8 + 8 * len(text), 18), fill="black")
    d.text((4, 3), text, fill="white")


def cands(dest, names):
    """labelled contact sheet of candidate files (330px thumbs), so a finder views many candidates in one image"""
    from PIL import Image
    os.makedirs(os.path.join(CACHE, "cands"), exist_ok=True)
    tiles = []
    for i, n in enumerate(names, 1):
        p = os.path.join(CACHE, "cands", hashlib.md5(n.encode()).hexdigest()[:10] + ".jpg")
        if not (os.path.exists(p) and os.path.getsize(p) > 3000):
            for w in (330, 500):
                code = subprocess.run(["curl", "-s", "-o", p, "-w", "%{http_code}", "-A", UA, thumb(n, w)], capture_output=True, text=True).stdout
                if code == "200":
                    break
            else:
                code = subprocess.run(["curl", "-s", "-o", p, "-w", "%{http_code}", "-A", UA, original(n)], capture_output=True, text=True).stdout
            time.sleep(1.5)
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            print(i, "failed:", n); continue
        im.thumbnail((300, 300))
        tile = Image.new("RGB", (300, 300), "white")
        tile.paste(im, ((300 - im.width) // 2, (300 - im.height) // 2))
        _label(tile, str(i))
        tiles.append(tile)
        print(i, n)
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    s = Image.new("RGB", (cols * 305, max(1, rows) * 305), "white")
    for k, t in enumerate(tiles):
        s.paste(t, ((k % cols) * 305, (k // cols) * 305))
    s.save(dest, quality=80)
    print(dest)


def boxes(slug, dest):
    """each day's whole downloaded picture with its crop drawn in red: check the crop and the whole picture's modesty at once"""
    from PIL import Image, ImageDraw
    tiles = []
    for i, a in enumerate(load(slug)["days"], 1):
        tile = Image.new("RGB", (400, 400), "white")
        if a and os.path.exists(src_path(a)):
            im = Image.open(src_path(a)).convert("RGB")
            im.thumbnail((400, 400))
            l, t, r, b = a["crop"]
            ImageDraw.Draw(im).rectangle((l * im.width, t * im.height, r * im.width - 1, b * im.height - 1), outline="red", width=3)
            tile.paste(im, ((400 - im.width) // 2, (400 - im.height) // 2))
        _label(tile, "Day %d" % i)
        tiles.append(tile)
    s = Image.new("RGB", (3 * 405, 3 * 405), "white")
    for k, t in enumerate(tiles):
        s.paste(t, ((k % 3) * 405, (k // 3) * 405))
    s.save(dest, quality=80)
    print(dest)


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
    elif len(a) in (2, 3) and a[0] == "search":
        search(a[1], int(a[2]) if len(a) == 3 else 12)
    elif len(a) >= 3 and a[0] == "cands":
        cands(a[1], a[2:])
    elif len(a) == 3 and a[0] == "boxes":
        boxes(a[1], a[2])
    else:
        print(__doc__)
