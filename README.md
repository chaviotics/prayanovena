# Pray a Novena

A small library of 9-day Catholic novenas, each with a phone prayer app and a 4-page print layout.
Live at https://prayanovena.com

- `novenas/<slug>/novena.json`: all of a novena's words (saints, prayers, 9 days)
- `novenas/<slug>/img/`: portraits (480×600) and round faces (112×112), all public domain
- `templates/`: the novena page and the library page
- `tools/build.py`: builds `site/` (what Netlify serves), or one self-contained HTML file with `--artifact <slug>`
- `tools/print_fill.py`, `tools/check_print.py`: fill and check the Google Docs print layout
- `tools/shots.py`, `tools/og.py`: phone screenshots and link-preview images
- `skill/SKILL.md`: the step-by-step guide for making a new novena
- `PROJECT_LOG.md`: decisions, history and open items; read it first

## Print docs (Google Drive, folder "[12] 🙏 Faith")

- Template (copy it, don't edit): `1XUCutiQexpVtGP8w_eaT1nzfjXx3h6Xb-VrQNfrgkkU`
- Relief from Debt and Financial Hardship: `1U4e3egURWhaJilOSCgWKGs1_5QTVNGVfmtKWpVCciOk`, tab "With Intention" (`t.m63jflj0vk3u`; the other tabs are old drafts)
- Healing of the Sick: `1Yz-AE_-9x21WjOByFdheCzJbUdAFIlmtgKFc5i9u8XE`

The original debt novena at novena-finances.netlify.app (repo `chaviotics/novena-finances`) is a separate site that people are using. This repo never deploys to it.

Scripture texts in this work are taken from the New American Bible, revised edition © 2010, 1991, 1986, 1970 Confraternity of Christian Doctrine, Washington, D.C. and are used by permission of the copyright owner. All Rights Reserved. No part of the New American Bible may be reproduced in any form without permission in writing from the copyright owner.
