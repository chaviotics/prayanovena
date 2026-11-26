# Pray a Novena — project log

**Pray a Novena** (formerly Catholic Novenas; tagline "Catholic novenas for every intention") is a library of 9-day Catholic novenas. Each novena has a phone prayer page (light and dark, day-by-day progress) and a printable A4 PDF (up to 5 pages, the whole text) made from the same text. New novenas are made from just an intention with the **novena-maker** skill.

This file is the present state: read it at the start of a work session. Dated history is in `log/` (one file per month, newest `log/2026-11.md`); grep it when you need something specific. At the end of a session that changed something, add a 3 to 5 line entry to this month's log file, update `log/novenas.csv` or the rules here, and move finished items out of "Open items".

## Where things live

| What | Where |
|---|---|
| Live library | https://prayanovena.com (DNS at Cloudflare; free Netlify address prayanovena.netlify.app) |
| Repo | `chaviotics/prayanovena` (renamed from catholic-novenas on 2026-11-21; GitHub forwards the old address), branch `main` |
| Netlify project | `prayanovena` (id `3902d84c-0c49-48e4-a0ed-e1a0c45e5d75`, renamed from catholic-novenas): publishes `site/` on every push, no build step on Netlify (run `tools/build.py` and commit `site/`) |
| How to make a novena | `skill/SKILL.md` (the novena-maker skill) |
| Printable PDFs | `novenas/<slug>/<slug>-novena.pdf` from `tools/print_pdf.py`, linked on each novena page |
| Older print docs | Google Drive folder "[12] 🙏 Faith" (debt and healing only). IDs are in `README.md` |
| Original debt novena (v1) | novena-finances.netlify.app, repo `chaviotics/novena-finances`. **Separate and in use. Never change or deploy to it.** |

## Novenas in the library

One row per novena in `log/novenas.csv` (slug, title, what it's for, intercessors, status, live date, link, cost to preview and total). The private **Novena Admin** dashboard (https://claude.ai/artifact/9inRucFoDpdaf7mJoWDvMd) is built from it. All novenas use the Marian Memorare except `relief-from-debt` (Memorare to St. Joseph); every one has a 5-page PDF, and debt and healing also have an old Google Doc (4 pages, IDs in `README.md`; debt uses the tab "With Intention").

## Decisions and rules

- **Scripture:** RSV Catholic Edition, checked word for word against a source (`novenas/<slug>/sources.md`). No version label after references; the RSV-CE permission notice appears once (site footer, print page 1). Stay under 500 verses per work. **No thee/thou verses** (Chav, 2026-11-21): pick RSV-CE passages without "thee/thou/thy/thine/hast/didst/doth"; never modernize the words (the permission requires unchanged text). Traditional prayers keep their wording. NABRE was tried the same day and dropped: the USCCB grants no web permission for the NABRE until the Catholic American Bible (2027); the finished NABRE version is on branch `nabre-draft` (patch in project files `nabre/`).
- **Quote marks at a passage edge:** the opening quote mark of continuing speech is left off (as before), and so may be a closing mark whose opening lies before the range (first used for Luke 1:76–79 in `christmas`, 2026-11-26); never start or end mid-sentence.
- **Renaming a novena's address:** rename `novenas/<slug>/` and its PDF, keep `storageKey` (progress stays), and list the old slug in `"oldSlugs"`; `build_seo` then writes 301s for the page, PDF and images to `site/_redirects`. Saves ("novenas-saved") are kept by slug, so a saved mark is lost (first used: work-and-livelihood → strength-and-growth-at-work, 2026-11-26).
- **Dated novenas:** optional `startHint` in novena.json replaces the hero's "Begin on any day." (`christmas`: "Begin on December 16 …").
- **Numbers:** digits in anything the reader scans (kickers, cards, headings, labels, tips, how-to): "9 days", "Day 3", "10 minutes". Prayers, reflections and steps, which are read aloud, keep words ("these nine days").
- **Saints:** 1–3 per novena, suggested from the intention. Public-domain images in both the app and print. Facts only when certain; quote a saint only with a well-attested line.
- **Faith:** never promise outcomes, no prosperity-gospel framing. Pray for God's will; for healing, also for strength, peace, doctors and caregivers.
- **Print:** A4, 5 pages at most, with the whole reflection (both paragraphs) (Chav, 2026-11-24; was "3 pages, 4 at most" with paragraph 1 only). A4 because an A4 page prints at full size on A4 and on long bond (8.5 × 13 in) and at 94% on Letter; a long bond PDF would shrink to 90% on A4. `tools/print_pdf.py` fills the site layout (`templates/print-flow6.html`) from novena.json and prints it with Chromium to `novenas/<slug>/<slug>-novena.pdf`; `build.py` copies it next to the page and adds "Print or download (PDF)" under How to Pray and in the desktop sidebar. The render fails past 5 pages or when page 1 overflows; `build.py` warns when a PDF is older than its novena.json (`novenas/print_versions.json`). Fonts: static weights in `tools/print_fonts/` (Chromium embeds variable fonts as Type 3 glyphs, which print badly). PDFs are not precached by the service worker; `netlify.toml` makes them revalidate. No new Google Docs; the template and `tools/print_fill.py` stay for one-off personalised copies.
- **Link previews:** made by `tools/og.py` from each novena's title, kicker and 2 saints (`"ogSaints": [left, right]` in novena.json so they face inward). Cream background, wine and gold accents; no URL or call to action on the image. The site's 9 days mark (from `tools/app_icons.py`, so it always matches the icon) sits above the title in place of a plain cross. The words sit in a 520px column with at least 44px of clear cream from each arch; the subtitle stays on one line (38px at the smallest) or goes to 2 balanced lines; on tall cards the mark shrinks first, then the title, so nothing touches the frame. Chav compared a one-saint-plus-icon card and a ring-of-9-days card and kept this one (2026-11-21). Without Python Playwright: `python3 tools/og.py --html DIR`, then `node tools/og_render.js DIR`.
- **Library cards:** title without "Novena for" (the section heading already says it), icon on the left, saints' faces top right, progress line and "Pray" / "Continue Day N" button.
- **Theme and text size** are shared across the whole site (`novenas-mode`, `novenas-scale`); progress is saved per novena (`novena-<slug>`).
- **Offline:** every build regenerates `site/sw.js` with a new version, so phones pick up changes on their next online visit. Never edit `site/sw.js` by hand; change `templates/sw.js`. Fonts live in `site/fonts/` (no Google Fonts on the site; artifact previews still use Google Fonts).
- **Day pictures (app only, never print):** each day may have a public-domain picture under the verse and a "Look again at …?" callout after the reflection (just the line in a wash box plus an underlined "See the whole picture" link with the expand icon; no label, no icon: Chav, 2026-11-24). Data in `novenas/<slug>/art.json`, made with `tools/art.py`; rules in skill §5b (scene → what the verse names → saint moment → what it asks → a stretch whose passage the caption names; never a mood picture; modest in the crop and the whole picture). Not precached: kept once seen. "Visio divina" is named only on About ("Praying with pictures").
- **Layout:** phone first. 601–1023px: one column with the 9 days in a sticky strip. 1024px and up: sidebar + prayer column. Phones: 9 days in a bottom bar.
- **Share button:** shares only the novena's public link (`share()` in `tools/build.py`: URL, title, one short message), never the page's own address, so the day, intention and progress never travel. Touch screens open the phone's share sheet; computers copy the link ("Link copied"). It sits in the top bar on every size (icon only on phones) and as "Share this novena" at the end of each day's prayer. Not in the hero (on small phones it pushes "Pray Day N" under the day bar) and not on library cards (each card is one link).
- **Footer:** one footer on every page from `site_footer()` in `tools/build.py` (All novenas · About · Privacy, credits, the RSV notice except on Privacy), ending with "To God be the glory". Change it there, not in the templates. No privacy line in the footer (Chav): that reassurance lives under the intention box, in the library's "Where is my intention saved?" question and on the Privacy page. The footer shows a warning only when the browser cannot save.
- **Credit and contact:** About says the site is made by Chav, a personal project and not an official Church publication. Corrections and questions go to hey.there.chav@gmail.com (Chav's public contact address for the site; approved by Chav for publishing). Never publish any other address.
- **AI and review disclosure:** About says the new prayers were written with the help of AI and have no priest review or imprimatur yet. Change that line only when a review has actually happened.
- **Privacy:** no cookies; fonts and pictures self-hosted. The one third-party script is **Cloudflare Web Analytics** (Chav, 2026-11-26): cookieless page counts, added to every site page by `analytics()` in `tools/build.py` (token `CF_ANALYTICS_TOKEN`; `"spa": false` so the library's filter chips don't count as views). The site is DNS-only at Cloudflare, so it's the manual snippet ("Enable with JS Snippet installation" in Cloudflare; auto-inject counts nothing). Stats: Cloudflare dashboard > Web analytics. Offline views and ad-blocked visitors aren't counted. The Privacy page's "Page counts" section says what it sees. Netlify's server logs do count visits (Observability, on by default; IP address, page, browser type), and the Privacy page says so under "Visits and hosting" (Chav). Don't claim "no tracking" or "no analytics". `netlify.toml` sets a Content-Security-Policy that allows only the site's own files plus Cloudflare's two analytics hosts, so anything else external (fonts, scripts, embeds) needs a CSP change and a Privacy page update.
- **App icon:** the "9 days" mark: a wine cross inside a ring of 9 gold segments (one per day of the novena) on cream; "Bold" proportions (viewBox 64: cross 7.5 thick, y 16.5–47.5; ring r 25, stroke 4), about 7 units clear above and below the cross. No name or initials so it survives a rename. `tools/app_icons.py` writes `site/favicon.svg` (switches to navy and pale gold in a dark-mode browser), `favicon.ico` (16/32/48), `apple-touch-icon.png`, `icon-192.png`, `icon-512.png` and `icon-maskable-512.png` (mark at 80% for Android's crop). Run it only when the design changes, then `tools/build.py`.
- **Workflow:** finish new work as a Claude artifact preview first; commit and push only after approval. Every new component or element gets a UI/UX pass (and an IA pass when it changes structure or navigation) before the preview: phone, tablet, desktop, light and dark, largest text, keyboard and screen reader, consistency with existing states and patterns (Chav, 2026-11-23).
- **Name:** the site is **Pray a Novena**; tagline "Catholic novenas for every intention". Don't use "Catholic" as the name (canon 216); it belongs in the tagline and descriptions. Page titles end "| Pray a Novena". Share text keeps "9 days of prayer, one day at a time."
- **Commits:** no Co-Authored-By lines.

## Log

Dated entries are in `log/YYYY-MM.md`, one file per month, newest at the bottom. Add new entries there, not here.

## Open items

1. **Go live:** done (Netlify project linked to the repo; live at prayanovena.com).
2. **Decide:** should prayers, reflections and steps also use digits? (Now: words.)
3. **Optional:** a personalized print copy of the healing novena with the person's name in place of "N.".
4. **Optional cleanup:** the old `catholic-novenas` branch on the novena-finances repo, and the scratch Google Doc used for image imports (`1P0v5bN3QCc97elk4VFMVbsgMDIxItOIKzT5k9Z97Bys`).
5. **Known v1 bug, left alone on purpose:** the novena-finances app drops "&" from day captions. Fixed in the library.

## Ideas to weigh (not decided)

In `docs/research/ideas.md` (one row per idea, Chav's call per row); products looked at are in `docs/research/landscape.md`. `/scout <idea>` researches one; `/ship <idea>` builds one (see "Shipping" in `CLAUDE.md`).
