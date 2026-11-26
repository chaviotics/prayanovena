# Helper briefs

Standing briefs for the novena helpers (skill/SKILL.md section 0b). The thread writes only what is new for this novena to `out/brief/<slug>/` (gitignored) and starts each helper with one line:

> Read skill/briefs/<name>.md. Slug: `<slug>`. Plan: out/brief/<slug>/plan.md.

**Order:**
1. Thread: `plan.md` v1: intention and how far to widen it, slug, category, order, card icon, the litany and saints (which portraits to reuse), the day themes, the care points, the facts to look up, picture ideas. Under about 60 lines.
2. `research.md` (sonnet) → `notes.md`: sourced facts and verse candidates.
3. Thread: picks the 9 verses, epigraph and closing verse into `verses.json` (shape below; run `python3 tools/check_verses.py out/brief/<slug>/verses.json`), and adds to `plan.md` which saint fits which day.
4. In parallel: `pictures.md` (sonnet) → portraits, `art.json`, `credits.txt`, sheets; `writer.md` (opus, medium) → `novena.json`, `sources.md`.
5. Thread: `python3 tools/make.py <slug>` (fills the credits from `credits.txt`), one look at the sheets.
6. `review.md` (opus, high) → `review.md`, `review-fixes.json`.
7. Thread: `python3 tools/make.py <slug> --fixes out/brief/<slug>/review-fixes.json`; picture fixes go to the picture helper by message. Then the preview.

**`verses.json`** (the only home of the exact Scripture text; check_verses.py reads it as is):
`{"epigraph": {"text": "…", "ref": "Matthew 5:4"}, "closingVerse": {"text": "…", "ref": "…"}, "days": [{"ref": "John 11:33–35", "verse": "…"}, … 9 days]}`

When a lesson from a build applies to every novena, fix the brief here, not in the next plan.
