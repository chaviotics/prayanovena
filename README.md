# Pray a Novena

A small library of 9-day Catholic novenas, each with a phone prayer app and a 4-page printable PDF.
Live at https://prayanovena.com

- `novenas/<slug>/novena.json`: all of a novena's words (saints, prayers, 9 days)
- `novenas/<slug>/img/`: portraits (480×600) and round faces (112×112), all public domain
- `templates/`: the novena page and the library page
- `tools/build.py`: builds `site/` (what Netlify serves), or one self-contained HTML file with `--artifact <slug>`
- `tools/print_pdf.py`, `templates/print-flow4.html` (+ `tools/print_render.js`): the printable A4 PDF of each novena (`novenas/<slug>/<slug>-novena.pdf`), made from novena.json
- `tools/check_print.py`: checks a print PDF has every word; `tools/print_fill.py`: fills the older Google Docs layout
- `tools/shots.py`, `tools/og.py`: phone screenshots and link-preview images
- `skill/SKILL.md`: the step-by-step guide for making a new novena
- `PROJECT_LOG.md`: decisions, history and open items; read it first

## Older print docs (Google Drive, folder "[12] 🙏 Faith"; new novenas use the PDF instead)

- Template (copy it, don't edit): `1XUCutiQexpVtGP8w_eaT1nzfjXx3h6Xb-VrQNfrgkkU`
- Relief from Debt and Financial Hardship: `1U4e3egURWhaJilOSCgWKGs1_5QTVNGVfmtKWpVCciOk`, tab "With Intention" (`t.m63jflj0vk3u`; the other tabs are old drafts)
- Healing of the Sick: `1Yz-AE_-9x21WjOByFdheCzJbUdAFIlmtgKFc5i9u8XE`

The original debt novena at novena-finances.netlify.app (repo `chaviotics/novena-finances`) is a separate site that people are using. This repo never deploys to it.

Scripture quotations are from the Revised Standard Version, Catholic Edition (RSV-CE), copyright © 1965, 1966
National Council of the Churches of Christ in the United States of America. Used by permission. All rights reserved worldwide.
