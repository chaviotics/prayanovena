# CLAUDE.md

Pray a Novena: a static library of 9-day Catholic novenas. `novenas/<slug>/novena.json` → `tools/build.py` → `site/`, which is committed; Netlify publishes `site/` on every push and builds nothing. Never touch novena-finances.

## Start lean

- Read the top of `PROJECT_LOG.md` and its open items, not the dated log (about 5k tokens instead of 23k): `sed -n '1,/^## Log/p' PROJECT_LOG.md; sed -n '/^## Open items/,$p' PROJECT_LOG.md`. Grep the log when you need something specific.
- New novena: follow `skill/SKILL.md`, which has its own reading list. Content rules (Scripture, saints, print, numbers) live there and in the log's "Decisions and rules"; don't restate them elsewhere.
- Read a tool's docstring before its code, and only the parts of large files you need.

## How to work

After Karpathy's coding-agent rules, adapted to threads Chav checks hours later.

1. **Think first.** State your reading of the ask. Ask once only if the answer changes Chav's goal or the step can't be undone; otherwise take the likeliest reading and say which.
2. **Simplest change that works.** No new scripts, options or abstractions for a one-off; extend the existing tool. If a simpler way exists, say so and push back.
3. **Surgical.** Touch only what the ask needs. Don't reword other novenas, tidy neighbouring code, or regenerate every PDF, picture or link preview when one slug changed. Mention unrelated problems; don't fix them unasked.
4. **Know the check before you start, then run only that:** build.py warnings, `check_verses.py`, `check_print.py`, or `shots.py <slug>` for the page you changed. After a failure, re-run only what failed.

## Logging

`PROJECT_LOG.md` is read at the start of every session, so keep it short. A log entry is 3 to 5 lines: what changed, where, the commit. A tweak gets no entry; its commit message is the record. Lasting rules go in "Decisions and rules", not in entries. Commits carry no Co-Authored-By lines.
