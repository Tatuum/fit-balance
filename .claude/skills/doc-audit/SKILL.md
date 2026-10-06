---
name: doc-audit
description: Checks fit-balance's core docs (the entries marked (core) in CLAUDE.md's Folder map) for staleness against the current codebase — tech-stack lists, example output, function/class names the docs mention by name, phase status. Use at Workflow step 7 (close-out after implementing a feature) or on demand whenever the user says "check core docs" / "check important docs". Reports findings; does not edit files itself.
---

# Doc audit

Checks fit-balance's core docs for staleness. Two modes, same
underlying checks — the difference is scope, not rigor:

- **Scoped** (Workflow step 7, right after implementing something):
  you already know what changed. Check `CURRENT_STATE.md` and the two
  `docs/project_docs/` diagrams in full regardless (per CLAUDE.md,
  they're always-check); check the other core docs only if this
  feature's subject matter overlaps what they cover.
- **Full** (on demand — "check core docs", "check important docs", no
  argument given): check every core doc in full, cold, as if nothing
  is already known about what might be stale.

## Steps

1. **Read `CLAUDE.md`'s Folder map** for the current list of docs
   marked **(core)** and what each one covers. That section is the
   source of truth for *which* docs are in scope — don't hardcode a
   copy of the list here, since it can change without this skill file
   changing.
2. **For each core doc in scope, check its specific claims against
   current code** — not a vibe check. Concretely:
   - `README.md` — tech stack list vs. `pyproject.toml`
     dependencies + `web/package.json`; example/worked-example output
     vs. `tests/fixtures.py` + `CURRENT_STATE.md`'s worked examples
     table; "Engineering approach" bullets vs. what `check.sh`/CI/
     pre-commit actually run.
   - `CURRENT_STATE.md` — each section's current-state text vs. the
     actual formula/function it describes; "Known gaps" doesn't list
     anything already fixed; "History/rationale" links resolve to
     real files in `docs/adr/`.
   - `specs/architecture.md` — Tech stack section vs. actual
     dependencies/tooling; High-level architecture vs. actual
     `src/`/`api/`/`web/` layering.
   - `specs/mission.md` — the one rule ("balance points, not shape
     categories, drive scoring") still holds; rarely needs a change.
   - `specs/roadmap.md` — phase checkboxes match what's actually
     shipped (cross-check against `docs/adr/` count and recent
     `CHANGELOG.md` entries).
   - `docs/project_docs/architecture-overview.md` — frameworks table
     vs. actual tooling; ASCII layering diagram vs. actual folder
     structure.
   - `docs/project_docs/main-logic-overview.md` — **every function/
     class name it mentions** (grep for each one in `src/fit_balance/`
     and `api/`) actually exists under that name; the pipeline diagram
     matches actual call patterns between modules.
3. **Report findings as a list** — file, the stale claim, what's
   actually true now. Don't report "looks fine" vaguely; either name
   a specific mismatch or say a doc was checked and found current.
4. **Don't edit files automatically.** A trivial factual correction
   (a renamed function, a version bump) can be fixed directly once
   reported; anything involving a judgment call (wording, scope,
   whether something's worth mentioning at all) gets flagged for the
   user to decide, same as any other doc edit in this project.
