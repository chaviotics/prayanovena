# CLAUDE.md

Pray a Novena: a static library of 9-day Catholic novenas. `novenas/<slug>/novena.json` → `tools/build.py` → `site/`, which is committed; Netlify publishes `site/` on every push and builds nothing. Never touch novena-finances.

## Start lean

- Read `PROJECT_LOG.md` (current state, about 4k tokens). Dated history is in `log/YYYY-MM.md`; grep it, don't read it whole.
- New novena: follow `skill/SKILL.md`, which has its own reading list. Content rules (Scripture, saints, print, numbers) live there and in the log's "Decisions and rules"; don't restate them elsewhere.
- Read a tool's docstring before its code, and only the parts of large files you need.

## How to work

After Karpathy's coding-agent rules, adapted to threads Chav checks hours later.

1. **Think first.** State your reading of the ask. Ask once only if the answer changes Chav's goal or the step can't be undone; otherwise take the likeliest reading and say which.
2. **Simplest change that works.** No new scripts, options or abstractions for a one-off; extend the existing tool. If a simpler way exists, say so and push back.
3. **Surgical.** Touch only what the ask needs. Don't reword other novenas, tidy neighbouring code, or regenerate every PDF, picture or link preview when one slug changed. Mention unrelated problems; don't fix them unasked.
4. **Know the check before you start, then run only that:** build.py warnings, `check_verses.py`, `check_print.py`, or `shots.py <slug>` for the page you changed; `tools/make.py <slug>` runs them all for one novena (add `--skip pdf,og` when the words didn't change). After a failure, re-run only what failed.

## Shipping

How a finished `/ship` change lands. New novenas use the novena-maker skill (`skill/SKILL.md`), not ship.

- **Gate**, in a clean clone of the branch tip, every exit code 0: `python3 tools/build.py` (no WARNING lines) then `git diff --exit-code site/` (committed `site/` matches the build); plus `python3 tools/make.py <slug>` for each novena touched.
- **Preview:** a change to the site is shown to Chav as a Claude artifact (`build.py --artifact <slug>` or `shots.py` screenshots) before it lands.
- **Merge:** one change per pull request into `main`, after the gate and an independent review; Chav merges it, or says "land it". Merging to `main` is the deploy: Netlify publishes `site/` within a minute.
- **Stop and ask before merging:** new dependencies; anything published outside the repo; prayer, reflection or Scripture wording; the locked print format; anything that changes every novena (templates, all PDFs).
- **Review with the strongest model:** prayer and Scripture wording, saint facts, the Privacy page, CSP and analytics.
- Ideas researched with `/scout` are listed in `docs/research/ideas.md`.

## Logging

`PROJECT_LOG.md` is read at the start of every session, so it holds state only and stays under 20 KB. Entries go in this month's `log/YYYY-MM.md`, 3 to 5 lines each: what changed, where, the commit. A tweak gets no entry; its commit message is the record. Lasting rules go in "Decisions and rules", not in entries. Commits carry no Co-Authored-By lines.
