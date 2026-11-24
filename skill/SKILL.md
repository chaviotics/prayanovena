---
name: novena-maker
description: Make a new 9-day Catholic novena for an intention (phone app page in the Pray a Novena library plus a 4-page printable PDF). Use when the user names an intention for a novena.
---

# Novena maker

From one intention, produce a novena in the **Pray a Novena** library (Catholic novenas for every intention):

1. `novenas/<slug>/novena.json` and `novenas/<slug>/img/` in the repo
2. A page at `https://prayanovena.com/<slug>/`, with a card on the library home page
3. A printable A4 PDF of 4 pages or fewer, made from novena.json and linked from the page
4. A short report: saints chosen and why, links, anything to decide

Every novena uses the same prayer structure and design. Only the content changes, so put the effort into the content and the checks.

## 0. Get set up

- **Repo:** `chaviotics/prayanovena` (branch `main`; Netlify deploys every push). Never push to `chaviotics/novena-finances`: it is the family's live debt novena.
- **Netlify:** project `prayanovena` (id `3902d84c-0c49-48e4-a0ed-e1a0c45e5d75`). Never deploy to `novena-finances` unless the user asks.
- **Read first:** `PROJECT_LOG.md` (decisions, history, open items), then `novenas/relief-from-debt/novena.json` and `novenas/healing/novena.json`. They are the approved examples: match their tone, lengths and polish.
- **Tools:** `tools/build.py` (site and artifact), `tools/print_pdf.py` (printable PDF), `tools/check_print.py` (print text check), `tools/shots.py` (screenshots), `tools/og.py` (link-preview images), `tools/wm_images.py` (Wikimedia images). Read each one's docstring before using it.

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
- `refl`: paragraph 1, 75–95 words. It is printed. It opens from the verse into the person's life.
- `more`: paragraph 2, 55–75 words, app only. A saint's story, a teaching of the Church (cite CCC numbers only if certain), or a gentle application.
- `prayer`: 70–90 words. Says "we", names at least one intercessor, and stops before "(Name your intention.)".
- `step`: one concrete, doable action, up to 30 words.

**The arc of the days:** start with honest fear or need, then trust, then the specific graces asked for, and end on **Day 9: gratitude and surrender to God's will**. Day 9's step is always "Write down three graces you noticed during these nine days, and thank God for them together." The print layout has a "Graces I have noticed" box after it.

**Numbers:** in everything the reader scans (kickers, card text, headings, labels, tips, how-to text), write numbers as digits: "9 days", "Day 3", "10 minutes", "The 3 Intercessors". Prayers, reflections and steps, which are read aloud, keep words ("these nine days", "on this ninth day").

**Voice and faith rules:**
- Write in warm, plain US English, saying "we". Keep the framing general: don't address the reader as a family or as praying alone (cards, kickers, previews). Use the honorific capitals of the examples: You, Your, Him.
- **Never promise outcomes.** No "this novena never fails" and no prosperity-gospel framing. Ask boldly, then trust God's will. For healing, also pray for strength, peace, the doctors' skill and the caregivers, and for the grace to unite suffering with Christ. Say plainly that healing which doesn't come is never a sign of weak faith (CCC 1508), and keep the hope of eternal life in view.
- When the person prayed for is unknown, write "N." and "them", and tell readers how to pray it for themselves.
- Rotate the saints across the days so each gets about three days.
- **Only quote a saint with a well-attested line.** Otherwise paraphrase ("St. Pio often told people to pray, hope and not worry").
- Facts about saints must be ones you would stake your name on. If unsure, leave them out.

## 4. Verify every Scripture text (RSV-CE, word for word)

- Fetch each passage, including the epigraph and closing verse, from BibleGateway with WebFetch: `https://www.biblegateway.com/passage/?search=<Book+c:v-v>&version=RSVCE`. Ask for the exact text with no verse numbers, footnote letters or headings.
- A URL you build yourself may need the user's approval to fetch. If nobody is there to approve, run WebSearch first (for example "Mark 2:3-5 RSVCE") and fetch only URLs that appear in its results. BibleGateway's verse pages (`/verse/en/<ref>`) list the RSVCE text, and EWTN's online Bible is labeled RSV-CE. For the Old Testament (except the deuterocanonical books), `biblestudytools.com/rsv/...` has the same text as RSV-CE. The New Testament has Catholic Edition changes, so use an RSVCE source there.
- **No thee/thou verses.** Choose passages whose RSV-CE text has no archaic address to God ("thee", "thou", "thy", "thine", "hast", "didst", "art" as a verb, "doth"); if the verse you want has them, pick another RSV-CE verse on the same theme (Chav, 2026-11-21: they feel off to younger readers). Never modernize the words yourself: the RSV-CE permission requires the text unchanged. The traditional prayers (Hail Mary, Memorare) keep their own wording.
- Copy punctuation exactly, including "LORD". Check the verse range: the passage must not start or end in the middle of a quotation (a dangling quote mark means choose a different range).
- If a fetch looks paraphrased or partial, fetch it again or use a second RSV-CE source. Record what you verified in `novenas/<slug>/sources.md`.
- **Permission limits:** under 500 verses in total, no whole book, under 25% of any book. The required notice is already in the templates.

## 5. Images (public domain only)

- Use Wikimedia Commons: paintings, sculpture, mosaics or icons by artists who died more than 100 years ago, and photos of such 2D works or 19th-century photographs. Avoid modern devotional art and recent photographs.
- **Getting the files.** The workspace can't reach Wikimedia, so let Google fetch them, using `tools/wm_images.py`:
  1. Add a scratch tab to any working Doc (`addDocumentTab`; the "Novena scratch doc" in the Faith folder is meant for this).
  2. `python3 tools/wm_images.py requests <tabId> "File_A.jpg" "File_B.jpg"` prints Docs requests that insert Wikimedia thumbnails. Send them with `update_doc`. Wikimedia serves only standard thumbnail widths, so keep the default 960. If an image fails, its original is narrower: use `--width 500`, or insert the original file URL.
  3. Export the Doc with Drive `download_file_content`, `exportMimeType: "application/zip"`, then `python3 tools/wm_images.py unzip <zip> <dir>` (files come out in insertion order).
  4. Delete the scratch tab.
- **Crop** with PIL: portrait `img/<id>.jpg` at 480×600 with the face in the upper third, and face `img/<id>_face.jpg` at 112×112, tight on the face. Use JPEG quality 85. For a litany-only image, such as a Marian title that isn't a saint card, make just `<id>_face.jpg`. Look at every crop, and leave out anything immodest or distracting next to the saint. Record sources in `novenas/<slug>/images.md`.

## 5b. Day pictures (app only, never in the PDF)

Every day gets a public-domain picture under its verse, plus a "Look again" line after the reflection. Both live in `novenas/<slug>/art.json`, made with `tools/art.py`. The print PDF never reads this file.

- **Choose honestly, in this order:** (1) the scene itself; (2) what the verse names (the sky for Ps 19, a vine for Jn 15); (3) a saint moment tied to the verse (Augustine reading Rom 13:14); (4) what the verse asks us to do (a confession for Jas 5:16). (5) If none of these fit, a **stretch** is allowed: another passage that shows the same truth, with `"kind": "stretch"` and `"passage"` naming it, which then shows in the caption ("Raphael, *The Liberation of Saint Peter* (Acts 12), 1514"). **Never use a mood picture** that is merely pretty, with no link to the verse. If an honest search finds nothing, leave the day `null`, which is rare.
- **Modesty:** this is prayer. Leave out bare bodies and anything that distracts, in the crop and in the whole picture (the whole picture shows when someone taps). This is stricter in novenas about chastity or habits.
- **Public domain:** the artist died more than 100 years ago, and the file is a faithful photo of a 2D work, or a pre-1926 photograph. Check the license with `python3 tools/art.py meta "File.jpg"`, which also gives the date. Fill in `year` and `place` (museum) when they're known. Leave them `""` rather than guess.
- **Crop:** 4:3, as fractions of the downloaded image, on exactly the detail the "Look again" line names. Faces must not be cut.
- **Words:** `alt` says plainly what the day picture shows. `look` starts "Look again at …", names something visible in the picture, and ends with a question that leads into the prayer. Vary the questions from day to day.
- **Make:** `python3 tools/art.py fetch <slug>` (curl, cached in `.cache/art/`), then `python3 tools/art.py make <slug>` (writes WebP: `art/day<N>.webp` at 720×540 and `day<N>_full.webp` at most 900 wide and 1200 tall, plus `art/images.md` credits), then `python3 tools/art.py sheet <slug> out/art.jpg` and look at all 9 crops. `build.py` checks the file and copies the pictures. They are not precached for offline use: each one is kept once seen.

## 6. Build and check the app

```
python3 tools/build.py                    # site/ (library + all novenas)
python3 tools/build.py --artifact <slug>  # out/<slug>.html, one self-contained file
python3 tools/og.py <slug>                # link-preview image (og.jpg), then build again. Optional "ogSaints": [left, right] in novena.json so both portraits face inward
python3 tools/shots.py <slug>             # phone screenshots, light and dark, into out/shots/
```

- Look at the screenshots: the hero (names should fit on 2 lines), Day 1, a poetry day, Day 9 and the closing.
- Optionally publish `out/<slug>.html` as a Claude artifact so the user can try it before it goes live.

## 7. Printable PDF (A4, 4 pages or fewer)

```
python3 tools/print_pdf.py <slug>                    # novenas/<slug>/<slug>-novena.pdf (A4)
python3 tools/check_print.py novenas/<slug>/<slug>-novena.pdf <slug>
python3 tools/build.py                               # copies the PDF next to the page and adds the link
```

- `tools/print_pdf.py` fills the site layout (`SITE_LAYOUT = "flow4"`, `templates/print-flow4.html`, chosen 2026-11-22) from novena.json and prints it with Chromium (Node Playwright). No AI is involved: the same novena.json always gives the same PDF. Print gets `refl` only; `more` stays in the app.
- The layout, in the order you pray: **page 1** has the title, the saints (portrait on top, then name, dates, feast and patronage), How to Pray as 5 numbered steps, the tips in columns, and the Opening and Closing Prayers and Memorare side by side. **Pages 2 to 4** hold Days 1–3, 4–6 and 7–9; each day is one band, Scripture & Reflection on the left (the verse and its reference inside a gold bar) and Pray on the right (Today's step in an outlined callout with a walking-figure icon). After the days come 2-up cards: "Meet your intercessor" stories and the closing verse. Page 4 ends with the full-width "Graces I have noticed" box. The Scripture notice and image credits sit at the foot of page 3 or 4. White page, no tinted fills; lines are at least .75pt; never use CSS gradients (they turn pink in some PDF viewers).
- The type is auto-fitted: the renderer picks the largest body size (about 9–9.8pt) that keeps the PDF to 4 pages, and tries the card and footnote arrangements, keeping the one with the larger type. The render **fails** if the PDF runs past 4 pages or page 1 overflows. If that happens, win back space in this order: shorten the image credits, shorten a long "Alongside prayer" tip, then trim the longest reflections by a sentence. Never remove a section.
- Don't use a day icon of `person-simple-walk`; it is the Today's step icon.
- Look at every page once (`pdftoppm -r 70 -png`). The check confirms every title, ref, verse, reflection, prayer and step is there.
- Run `print_pdf.py` again whenever the novena's words change; `build.py` warns when a PDF is older than its novena.json.
- Google Docs are no longer made for new novenas (decided 2026-11-21). The template doc and `tools/print_fill.py` stay for a one-off personalised copy.

## 8. Review before publishing

- Run a Catholic content review, using the catholic-guide skill or a fresh subagent with no stake in the draft. It checks:
  - doctrine
  - saints' facts and dates
  - no superstition or guarantees
  - fitting sacraments
  - kindness to those who are not cured
  - correct titles
- Fix what holds up, rebuild, and check again. Note the changes in `sources.md`.

## 9. Publish

1. Set `"status": "published"`, then run `python3 tools/build.py`.
2. Commit and push to `main`. Netlify builds nothing: it publishes `site/` (see `netlify.toml`), so always commit the built `site/`. If the site isn't linked to GitHub yet, deploy with the Netlify MCP `deploy-site` command instead (it may need the user's approval), or publish `site/` as a Claude artifact for review.
3. Open the live page to confirm it works. Commit messages carry no Co-Authored-By trailer.
4. Update `PROJECT_LOG.md`: add the novena to the table and a dated log entry, and move any finished open items out.

## Report

Keep the report short:
- the saints and why they were chosen
- the live link and the PDF link
- what the reviews changed
- open questions, each with your recommendation
