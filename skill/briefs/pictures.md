# Brief: portraits and day pictures (Sonnet helper)

Read `out/brief/<slug>/plan.md`, `out/brief/<slug>/verses.json`, skill/SKILL.md sections 5 and 5b, and the docstring of `tools/art.py`. Copy the shape of `novenas/peace-in-the-family/art.json`. Work only inside `novenas/<slug>/`, `out/brief/<slug>/` and your own scratch folder; another novena may be building at the same time, so no shared scratch scripts. Wikimedia rate-limits: use 960 or 1280 px thumbnails, space API calls 4 to 5 s apart, back off on 429, never retry in a fast loop.

**A. Portraits** into `novenas/<slug>/img/`. Reuse first: copy the files the plan lists from other novenas (`ls novenas/*/img/` shows what exists). For a new saint, a public-domain portrait whose Commons page confirms it: `<id>.jpg` 480×600 with the face in the upper third, `<id>_face.jpg` 112×112, JPEG quality 85. Write `novenas/<slug>/images.md`.

**Credits:** write the finished credit line for every portrait and litany image to `out/brief/<slug>/credits.txt`, one line in the house format (copy an example's `credits`): `Images: Artist, <em>Title</em>, date, collection · Artist, <em>Title</em>, date. Public domain, via Wikimedia Commons.` Reused images keep their credit from the other novena; new ones only from the Commons page fields, leaving a date or museum out rather than guessing. (Day pictures get their credits from `art.json`, not here.)

**B. Day pictures** in `novenas/<slug>/art.json`, one per day, following 5b's honesty order (mark stretches with `kind: "stretch"` and `passage`). Modest in the crop and in the whole picture. Don't reuse a file another novena uses unless it truly fits this verse better than anything else; list them with `python3 -c "import json,glob;print(*sorted({d['file'] for p in glob.glob('novenas/*/art.json') for d in json.load(open(p))['days'] if d}),sep='\n')"`. Fill `alt` (plain), `look` ("Look again at …", something visible, a question that leads into the prayer, varied from day to day), and `year` and `place` only from Commons.

**C. Make and show.** `python3 tools/art.py fetch <slug>`, `make <slug>`, then ONE sheet each: `python3 tools/art.py sheet <slug> out/brief/<slug>/art.jpg` and a portrait sheet `out/brief/<slug>/portraits.jpg` (all crops, faces included, labelled). Look at both once yourself and fix what's off before replying.

Reply in 15 lines or fewer: per day the file, kind and one line on why; any doubts; the two sheet paths. Later fixes come to you by message, so keep your notes.
