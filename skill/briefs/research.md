# Brief: saint facts and verse candidates (Sonnet helper)

Read `out/brief/<slug>/plan.md` and skill/SKILL.md sections 1 and 4. Write `out/brief/<slug>/notes.md` (at most about 150 lines). Write nothing outside `out/brief/<slug>/`. Reply in 10 lines or fewer: what is certain, what you couldn't confirm.

**Saint facts.** For each saint and title in the plan: dates, feast (say if it is the General Roman Calendar or a national one), established patronages, and the facts the plan asks for. Sources: Vatican, USCCB, Catholic Encyclopedia (1913), Britannica, the saint's own writings or shrine. Every fact gets its source URL and a label: HISTORICAL, EARLY BIOGRAPHY or LEGEND. Anything you can't confirm is UNCONFIRMED; never guess. Quote a saint only with a well-attested line, with the work and a public-domain translation. If another novena already has this saint, copy its `saints[]` entry (name, dates, feast, patron, bio, alt) and its part of that novena's `credits` line into the notes instead of researching it again.

**Church teaching.** CCC paragraph numbers the plan names, each with a one-line paraphrase, checked on vatican.va.

**Verse candidates** for each day theme in the plan, plus the epigraph and closing verse: 2 to 3 RSV-CE passages each, with the exact text from an RSVCE source (section 4 lists what works), each marked clean, archaic (thee, thou, thy, art, doth…) or dangling-quote. To check a batch, put them in a scratch file in the `verses.json` shape (skill/briefs/README.md) and run `python3 tools/check_verses.py` on it.
