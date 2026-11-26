---
name: novena-maker
description: Make a new 9-day Catholic novena for an intention (phone app page in the Pray a Novena library plus a printable PDF of up to 5 pages). Use when the user names an intention for a novena.
---

# Novena maker

From one intention, produce a novena in the **Pray a Novena** library (Catholic novenas for every intention):

1. `novenas/<slug>/novena.json` and `novenas/<slug>/img/` in the repo
2. A page at `https://prayanovena.com/<slug>/`, with a card on the library home page
3. A printable A4 PDF of 5 pages or fewer, made from novena.json and linked from the page
4. A short report: saints chosen and why, links, anything to decide

Every novena uses the same prayer structure and design. Only the content changes, so put the effort into the content and the checks.

## 0. Get set up

- **Repo:** `chaviotics/prayanovena` (branch `main`; Netlify deploys every push). Never push to `chaviotics/novena-finances`: it is the family's live debt novena.
- **Netlify:** project `prayanovena` (id `3902d84c-0c49-48e4-a0ed-e1a0c45e5d75`). Never deploy to `novena-finances` unless the user asks.
- **Read first, lean:** `PROJECT_LOG.md` (where things live, decisions and rules, open items; the novena list is `log/novenas.csv`). Dated history is in `log/`; grep it only when you need something specific. Then read ONE example, `novenas/habitual-sin/novena.json` (it follows the saints-per-day rule), and match its tone, lengths and polish. From this skill, read sections 1 to 5b now and the rest when you reach them.
- **Tools:** `tools/build.py` (site and artifact), `tools/print_pdf.py` (printable PDF), `tools/check_print.py` (print text check), `tools/shots.py` (screenshots), `tools/og.py` (link-preview images), `tools/art.py` (day pictures), `tools/check_verses.py` (Scripture check). Read each one's docstring before using it.

## 0b. Work lean (usage)

Measured on 15 builds (Nov 2026): most of a build's usage is the coordinating thread re-reading its own memory on every step, so a small memory and fewer steps save more than anything else. The leanest so far (Peace in the Family, $6.96 to a reviewed preview) ran in a fresh thread whose memory stayed at 159k tokens; the same setup run from a long thread (296k) cost $8.11. The Opus review caught real slips every time, so it is never skipped.

- **One fresh thread per novena.** Don't build a novena in a thread that already carries other work.
- **Check the limit meter before you start.** Start only when the 5-hour meter is under about 40%; running out mid-build stalls the work and makes every helper store its memory again.
- **The thread coordinates: it decides and waits.** It picks the intercessors and the 9 verses itself (section 1 and the verse list from the research helper), briefs the helpers, applies small fixes, and takes the final look. It does not write the 9 days itself and never reads helper transcripts; while helpers run, it ends its turn. Novena threads run at **medium** effort.
- **Keep the main memory small:** the standing briefs are in `skill/briefs/` (see its README): write only this novena's decisions to `out/brief/<slug>/plan.md` and start each helper with one line pointing to its brief and the plan; never print a whole file or a long output (`sed -n`, `grep`, `python3 -c`); batch independent commands into one step; look at contact sheets, not single images. Helpers reply in 15 lines or fewer.
- **Helpers (Agent tool):**
  - **Saint facts and verse candidates:** one helper (`model: "sonnet"`) writes a notes file: each fact with its source and a HISTORICAL / EARLY BIOGRAPHY / LEGEND label, and candidate RSV-CE passages with exact text, marked clean, archaic or dangling-quote.
  - **Pictures:** one helper (`model: "sonnet"`) does all image work (portraits, sections 5 and 5b). Reuse a saint's portrait from another novena when one exists (the grieving novena reused 3 of 4), and give it the list of image files other novenas already use. It saves its own JSON (no shared scratch scripts) and returns ONE contact sheet. Send it later work and review fixes with SendMessage, so it keeps its context.
  - **Writer:** one fresh helper (`model: "opus"`, medium effort) reads sections 1 to 4, one example novena and the notes, writes `novena.json` and `sources.md`, and runs the verse check (the thread builds with make.py). Review fixes are applied by script (below); message the writer only for a rewrite a script can't do.
  - **Review:** one fresh helper (`model: "opus"`, high effort) checks text and pictures in one pass, before the first preview (section 8), and writes `review.md` plus `review-fixes.json` (exact old/new text per file), which the main thread applies by script instead of waking the writer again.
- **Scripts for the mechanics:** `tools/art.py` for pictures, and `python3 tools/make.py <slug>` for everything else in one step (verses, link preview, PDF and text check, site, artifact, screenshots; about 1 minute, about 15 lines of output, Node fallbacks built in). Then look at its sheets: `out/make/<slug>/shots.jpg`, `pdf.jpg`, `art.jpg`. Apply the reviewer's fixes with `--fixes out/brief/<slug>/review-fixes.json` (misses are listed for you to fix by hand); use `--skip` for steps whose inputs didn't change.
- **Previews:** ask the user to send all changes for a preview in one message. A thread left idle for over an hour must store its whole memory again.

## 1. Intention → saints

- Restate the intention in one line. Widen it only where that helps the person praying. For healing, that means body and spirit, the doctors and the caregivers. Keep the user's focus first.
- Suggest **1–3 intercessors**, and prefer 3:
  - **A Marian title** that fits the intention, such as Our Lady of Lourdes for the sick or Mary, Help of Christians.
  - **A saint with an established, traditional patronage** for this need.
  - **A saint whose own life mirrors the intention**, for example someone who suffered the same trial.
- Prefer canonized saints with well-known stories, and devotions loved in the Philippines when they fit. Say whether a patronage is traditional or official.
- Check that each saint has a public-domain image (step 5) before you settle on them.
- **If the user is present,** offer the choice with one-line reasons. **If they are unattended,** choose, and explain the choice in the report.
- **Slug:** short and lowercase, like `healing` or `relief-from-debt`. Make `storageKey` = `novena-<slug>`.

## 2. Fixed structure (the template handles it)

Each day runs in this order:

1. Opening Prayer (the same every day)
2. Scripture & Reflection (changes each day)
3. The day's Prayer, ending "(Name your intention.) Amen."
4. Closing Prayer: a litany (a Marian title, then each saint, each with "pray for us"), then the closing prayer, then the Memorare
5. Our Father, Hail Mary, Glory Be
6. Sign of the Cross
7. Today's step

**Memorare rule:** use the Marian Memorare (`"memorare": {"to": "Mary"}`; the builder supplies the text). Use the Memorare to St. Joseph (text in the debt example) only when St. Joseph is one of the intercessors.

## 3. Write `novena.json`

Copy an example's shape. Field rules:

| Field | Rule |
|---|---|
| `title` | "Novena for …", up to about 60 characters |
| `cardTitle` | The title without "Novena for", for the library card |
| `icon` | One Phosphor "regular" icon for the library card |
| `barTitle` / `barShort` | Shown in the top bar: up to 28 and up to 14 characters |
| `kicker` | "9 days of …", up to 45 characters |
| `card` | One sentence for the library card, up to 140 characters |
| `description` | Meta description, up to 160 characters |
| `ogDescription` | Link-preview description, under 125 characters: "9 days of prayer for …, through …" with short saint names |
| `status` | `"draft"` (page builds, no library card) until the user approves, then `"published"` |
| `order` | Position on the library page |
| `epigraph`, `closingVerse` | RSV-CE text, up to about 25 words each: `{"text", "ref"}` |
| `printTitle`, `printClosing` | Two lines each, for the print title and the closing verse |
| `saints[]` | `id` (image file stem), `name`, `dates`, `feast`, `patron`, `bio` (up to 35 words, facts only), `alt` (describes the artwork), `openingRole` |
| `litany[]` | `{"img", "text"}`, Marian title first. `img` is optional and points to `img/<img>_face.jpg` |
| `openingPrayer` | 85–110 words. Addresses the Father, names the burden plainly, names each intercessor with a short role, ends "through Christ our Lord." The template adds "Amen." |
| `closingPrayer` | 25–40 words, addressed to Jesus. The template adds "Amen." |
| `tips` | Keep the "Praying with others" text from the examples word for word. "Alongside prayer" names the sacraments that fit (Confession, Mass, Anointing of the Sick…) and one prudent action for this intention, plus a warning against false shortcuts if relevant (loan sharks, "sure cures") |
| `icons` | 9 Phosphor "regular" icon names, one per day. They must exist in `tools/icons/`. Add new ones from `@phosphor-icons/core` (npm, assets/regular) |
| `credits` | Image credits: artist, *title*, date, collection, then "Public domain, via Wikimedia Commons." |
| `days[9]` | See below |

Each day has these fields:

- `title`: 2–5 words.
- `ref`: "Book c:v–v" with an en dash. Never add a version label ("RSV-CE") after a reference, in the app or in print; the RSV-CE permission notice appears once, in the footer and in the PDF's footnotes.
- `verse`: RSV-CE, exact. Put " / " between poetry lines, and keep "LORD" in capitals (it shows in small caps).
- `refl`: paragraph 1, 75–95 words. It is printed. It opens up the Scripture itself and carries it into the person's life; no saint retelling here (the verse's own author or setting is fine).
- `more`: paragraph 2, 55–75 words. Printed too (since 2026-11-24), right after paragraph 1. When one of the novena's saints truly fits the day, give a concrete, relatable moment from their life that lives out the verse, in 2–4 sentences, then at most one sentence tying it back (Chav, 2026-11-24). Never force it: on days with no fitting saint, stay with Scripture (its background, a teaching of the Church with CCC numbers only if certain, or a gentle application). The Scripture block itself never changes.
- `prayer`: 70–90 words. Says "we", names the one intercessor (or two) whose story fits the day, not all of them, with a light touch (one short clause or "St. X, pray for us", never retelling the story), and stops before "(Name your intention.)".
- `step`: one concrete, doable action, up to 30 words.

**The arc of the days:** start with honest fear or need, then trust, then the specific graces asked for, and end on **Day 9: gratitude and surrender to God's will**. Day 9's step is always "Write down three graces you noticed during these nine days, and thank God for them together." The print layout has a "Graces I have noticed" box after it.

**Numbers:** in everything the reader scans (kickers, card text, headings, labels, tips, how-to text), write numbers as digits: "9 days", "Day 3", "10 minutes", "The 3 Intercessors". Prayers, reflections and steps, which are read aloud, keep words ("these nine days", "on this ninth day").

**Voice and faith rules:**
- Write in warm, plain US English, saying "we". Keep the framing general: don't address the reader as a family or as praying alone (cards, kickers, previews). Use the honorific capitals of the examples: You, Your, Him.
- **Never promise outcomes.** No "this novena never fails" and no prosperity-gospel framing. Ask boldly, then trust God's will. For healing, also pray for strength, peace, the doctors' skill and the caregivers, and for the grace to unite suffering with Christ. Say plainly that healing which doesn't come is never a sign of weak faith (CCC 1508), and keep the hope of eternal life in view.
- When the person prayed for is unknown, write "N." and "them", and tell readers how to pray it for themselves.
- Don't put every saint in every day (Chav, 2026-11-24). Weave a saint into a day only where their story or witness truly fits: usually one saint per day's story and prayer, about two or three days each. Day 9's thank-you may name them all.
- **Only quote a saint with a well-attested line.** Otherwise paraphrase ("St. Pio often told people to pray, hope and not worry").
- Facts about saints must be ones you would stake your name on. If unsure, leave them out.

## 4. Verify every Scripture text (RSV-CE, word for word)

- **Check by script, not by fetching each verse into your memory:** `python3 tools/check_verses.py novenas/<slug>/novena.json` compares every passage, including the epigraph and closing verse, with the RSVCE chapter files of `andrewheekin/obsidian-holy-bible` (a sparse git clone into `/tmp/ohb`, only the chapters needed) and flags thee/thou. It prints OK or DIFF per passage; DIFFs from the source's footnote letters or continuing-speech quote marks are expected, anything else is a real mismatch. BibleGateway is blocked from scripts in the cloud.
- For a second source or a passage the script can't settle, a helper can read BibleGateway (`/passage/?search=<Book+c:v-v>&version=RSVCE`) and answer MATCH or MISMATCH (it rate-limits and quotes only short text). For the Old Testament (except the deuterocanonical books), `biblestudytools.com/rsv/...` has the same text as RSV-CE; the New Testament has Catholic Edition changes, so use an RSVCE source there.
- **No thee/thou verses.** Choose passages whose RSV-CE text has no archaic address to God ("thee", "thou", "thy", "thine", "hast", "didst", "art" as a verb, "doth"); if the verse you want has them, pick another RSV-CE verse on the same theme (Chav, 2026-11-21: they feel off to younger readers). Never modernize the words yourself: the RSV-CE permission requires the text unchanged. The traditional prayers (Hail Mary, Memorare) keep their own wording.
- Copy punctuation exactly, including "LORD". Check the verse range: the passage must not start or end in the middle of a quotation (a dangling quote mark means choose a different range).
- If a fetch looks paraphrased or partial, fetch it again or use a second RSV-CE source. Record what you verified in `novenas/<slug>/sources.md`.
- **Permission limits:** under 500 verses in total, no whole book, under 25% of any book. The required notice is already in the templates.

## 5. Images (public domain only)

- Use Wikimedia Commons: paintings, sculpture, mosaics or icons by artists who died more than 100 years ago, and photos of such 2D works or 19th-century photographs. Avoid modern devotional art and recent photographs.
- **Getting the files.** The cloud reaches Wikimedia directly (since 2026-11-22): use `tools/art.py meta` for the licence and details and fetch with curl. Wikimedia rate-limits the shared address: the 960 and 1280 px thumbnails usually come through when originals and the API answer 429, so back off instead of retrying in a loop. (`tools/wm_images.py`, the old route through a Google Doc, is only a fallback.)
- **Credits come only from the Commons page** (author, title, date, institution fields), never from the file name or the uploader's guess. Leave a museum or date out rather than guess it.
- **Crop** with PIL: portrait `img/<id>.jpg` at 480×600 with the face in the upper third, and face `img/<id>_face.jpg` at 112×112, tight on the face. Use JPEG quality 85. For a litany-only image, such as a Marian title that isn't a saint card, make just `<id>_face.jpg`. Look at every crop (on one contact sheet), and leave out anything immodest or distracting next to the saint, in the crop and in the whole picture. Record sources in `novenas/<slug>/images.md`.

## 5b. Day pictures (app only, never in the PDF)

Every day gets a public-domain picture under its verse, plus a "Look again" line after the reflection. Both live in `novenas/<slug>/art.json`, made with `tools/art.py`. The print PDF never reads this file.

- **Choose honestly, in this order:** (1) the scene itself; (2) what the verse names (the sky for Ps 19, a vine for Jn 15); (3) a saint moment tied to the verse (Augustine reading Rom 13:14); (4) what the verse asks us to do (a confession for Jas 5:16). (5) If none of these fit, a **stretch** is allowed: another passage that shows the same truth (the same message, not just the same image: a barren fig tree under threat of being cut down is the wrong picture for Habakkuk's trust "though the fig tree do not blossom"), with `"kind": "stretch"` and `"passage"` naming it, which then shows in the caption ("Raphael, *The Liberation of Saint Peter* (Acts 12), 1514"). **Never use a mood picture** that is merely pretty, with no link to the verse. If an honest search finds nothing, leave the day `null`, which is rare.
- **Modesty:** this is prayer. Leave out bare bodies and anything that distracts, in the crop and in the whole picture (the whole picture shows when someone taps). This is stricter in novenas about chastity or habits.
- **Public domain:** the artist died more than 100 years ago, and the file is a faithful photo of a 2D work, or a pre-1926 photograph. Check the license with `python3 tools/art.py meta "File.jpg"`, which also gives the date. Fill in `year` and `place` (museum) when they're known. Leave them `""` rather than guess.
- **Crop:** 4:3, as fractions of the downloaded image, on exactly the detail the "Look again" line names. Faces must not be cut.
- **Words:** `alt` says plainly what the day picture shows. `look` starts "Look again at …", names something visible in the picture, and ends with a question that leads into the prayer. Vary the questions from day to day.
- **Make:** `python3 tools/art.py fetch <slug>` (curl, cached in `.cache/art/`), then `python3 tools/art.py make <slug>` (writes WebP: `art/day<N>.webp` at 720×540 and `day<N>_full.webp` at most 900 wide and 1200 tall, plus `art/images.md` credits), then `python3 tools/art.py sheet <slug> out/art.jpg` and look at all 9 crops. `build.py` checks the file and copies the pictures. They are not precached for offline use: each one is kept once seen.

## 6. Build and check the app

`python3 tools/make.py <slug>` runs this section and section 7 in one step. The single commands, for when you need one:

```
python3 tools/build.py                    # site/ (library + all novenas)
python3 tools/build.py --artifact <slug>  # out/<slug>.html, one self-contained file
python3 tools/og.py <slug>                # link-preview image (og.jpg), then build again. Optional "ogSaints": [left, right] in novena.json so both portraits face inward
python3 tools/shots.py <slug>             # phone screenshots, light and dark, into out/shots/ (node tools/shots.js <slug> without Python Playwright)
```

- Look at the screenshots: the hero (names should fit on 2 lines), Day 1, a poetry day, Day 9 and the closing.
- Optionally publish `out/<slug>.html` as a Claude artifact so the user can try it before it goes live.

## 7. Printable PDF (A4, 5 pages or fewer)

```
python3 tools/print_pdf.py <slug>                    # novenas/<slug>/<slug>-novena.pdf (A4)
python3 tools/check_print.py novenas/<slug>/<slug>-novena.pdf <slug>
python3 tools/build.py                               # copies the PDF next to the page and adds the link
```

- `tools/print_pdf.py` fills the site layout (`SITE_LAYOUT = "flow6"`, `templates/print-flow6.html`, chosen 2026-11-24; before that `flow4`, 4 pages, paragraph 1 only) from novena.json and prints it with Chromium (Node Playwright). No AI is involved: the same novena.json always gives the same PDF. Print gets the whole reflection, `refl` and `more`.
- The layout, in the order you pray: **page 1** has the title, the saints (portrait on top, then name, dates, feast and patronage), How to Pray as 5 numbered steps, the tips in columns, and the Opening and Closing Prayers and Memorare side by side. **Then the 9 days flow from page to page** under a "The 9 Days" running head; a day never splits across pages. Each day: the verse and its reference inside a gold bar across the full width (a poem of 6+ lines runs in 2 columns, but only where a sentence or clause ends near the middle, each column 3+ lines; otherwise 1 column), then Reflection (both paragraphs) on the left at 60% of the width and Pray on the right at 40% (Today's step in an outlined callout with a walking-figure icon), so the two columns end about level (Chav, 2026-11-24: at 50/50 the prayer ended far above the reflection; 60/40 gives the type about half a point more). Page 1 stays 50/50 for the prayers. The "Meet your intercessor" cards and the closing verse go 2 to a row; each row closes the page of the day it follows (never starts a page), and the 2 rows may land on different pages. The full-width "Graces I have noticed" box (3 to 8 lines) follows Day 9, then the Scripture notice and image credits. White page, no tinted fills; lines are at least .75pt; never use CSS gradients (they turn pink in some PDF viewers).
- The type is auto-fitted: the renderer tries 3, then 4 pages, keeping the shorter only if the body stays at 9pt or more, else 5 pages (about 9.3–9.9pt across the library), then gives the saints' portraits on page 1 its spare room (up to 1.5x), then zooms all of page 1 (title, prayers, pictures) up to 1.15x with what is left, so the daily prayers print larger; then it gives the Graces box 3 to 8 writing lines (Chav: a maximum size; a roomy last page simply ends in white space). It tries every placement of the card rows (after Days 2 to 9) and keeps the one with the fewest pages, then the larger type, then the one leaving the most room on the last page (the fewest gaps elsewhere); this takes about a minute per novena. The render **fails** if the PDF runs past 5 pages or page 1 overflows. If that happens, win back space in this order: shorten the image credits, shorten a long "Alongside prayer" tip, then trim the longest reflections by a sentence. Never remove a section.
- Don't use a day icon of `person-simple-walk`; it is the Today's step icon.
- Look at every page once (`pdftoppm -r 70 -png`). The check confirms every title, ref, verse, both reflection paragraphs, prayer and step is there.
- Run `print_pdf.py` again whenever the novena's words change; `build.py` warns when a PDF is older than its novena.json.
- Google Docs are no longer made for new novenas (decided 2026-11-21). The template doc and `tools/print_fill.py` stay for a one-off personalised copy.

## 8. Review before publishing

- Run a Catholic content review **before the first preview**, using a fresh helper with no stake in the draft (`model: "opus"`, high effort; it may use the catholic-guide skill). Text and pictures go in **one** pass, so a second round isn't needed. It checks:
  - doctrine
  - saints' facts and dates
  - no superstition or guarantees
  - fitting sacraments
  - kindness to those who are not cured
  - correct titles
  - each picture: honest to its verse, modest in the crop and the whole picture, credits and museum as stated on its Commons page, crop not too dark
- Fix what holds up, rebuild, and check again. Note the changes in `sources.md`.

## 9. Publish

1. Set `"status": "published"`, then run `python3 tools/build.py`.
2. Commit and push to `main`. Netlify builds nothing: it publishes `site/` (see `netlify.toml`), so always commit the built `site/`. If the site isn't linked to GitHub yet, deploy with the Netlify MCP `deploy-site` command instead (it may need the user's approval), or publish `site/` as a Claude artifact for review.
3. Open the live page to confirm it works. Commit messages carry no Co-Authored-By trailer.
4. Update `PROJECT_LOG.md` if a rule or open item changed. Add a 3 to 5 line entry to this month's `log/YYYY-MM.md`.
5. Set the novena's row in `log/novenas.csv` to `live` with the live date and `total_usd`, in the same commit, then refresh the dashboard and the cost report (Report, below).

## Report

Every preview message and the final report open with the link and the cost so far, for example "Preview: <link> · $6.96 so far".

- **Reading the cost:** `get_session` with no session id gives this thread's usage, helpers included. It can lag a turn, so also read `total_cost_usd` on the newest `result` event of `list_events` (kinds `["result"]`) and use the larger. Never estimate a missing number; write nothing and the dashboard shows "not measured".
- **Log it:** at the first preview, add the novena's row to `log/novenas.csv` (status `preview`, `to_preview_usd`; same columns as the other rows, or fill the row already there). Then refresh **Novena Admin** (https://claude.ai/artifact/9inRucFoDpdaf7mJoWDvMd): upload the CSV with the Artifact tool (`asset: true`) and point its `novenas` dataset at the new `/_blob/` url with an ArtifactData `update` (new `source.url` and `updated.at`). Do it again after publishing.
- **Cost report:** after publishing, add one line to the `builds` list in `/mnt/project-files/token-test/novena-cost-report.html` (grep for it, copy the last line's shape) and republish it to https://claude.ai/artifact/V8qzCpGgibz24Rk5KU1FZN.

Keep the rest of the report short:
- the saints and why they were chosen
- the live link and the PDF link
- what the reviews changed
- open questions, each with your recommendation
