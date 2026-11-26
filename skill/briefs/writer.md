# Brief: write novena.json (Opus helper, medium effort)

Read, in this order and nothing more unless needed: `out/brief/<slug>/plan.md` (the decisions), `out/brief/<slug>/notes.md` (sourced facts), skill/SKILL.md sections 1 to 4, and ONE example, `novenas/habitual-sin/novena.json`, read with python field by field (shape, tone, lengths). Copy the "Praying with others" tip word for word from the example.

**Facts:** HISTORICAL facts may be stated plainly; EARLY BIOGRAPHY and LEGEND only as such ("an early life says", "tradition holds"); UNCONFIRMED never. Never add a saint fact that isn't in the notes.

Write the complete `novenas/<slug>/novena.json` with `status: "draft"` and the slug, order, category, icon and storageKey `novena-<slug>` from the plan. Copy every verse, the epigraph and the closing verse exactly from `out/brief/<slug>/verses.json`, curly quotes as given. Pictures are separate: no art fields, and `"credits": ""` (a string; make.py fills it from the picture helper's `credits.txt`). `icons`: 9 names that exist in `tools/icons/` (never `person-simple-walk`). Each saint appears only on the days the plan gives; prayers get a light touch only. Write `novenas/<slug>/sources.md` (Scripture source and check, saint facts with sources).

Care: follow the plan's care points. Never promise outcomes; no platitudes; warm, plain US English, "we".

Before replying: `python3 tools/check_verses.py novenas/<slug>/novena.json` (OK or expected DIFFs only) and a `python3 -c` field-length check against the section 3 table. Don't build; the thread runs make.py. Reply in 15 lines or fewer: title, kicker, which saint on which day, anything you weren't sure of.
