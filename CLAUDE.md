# CLAUDE.md

## Purpose

fit-balance is an explainable styling-recommendation system. Every
verdict comes with editable, inspectable reasons tied to the user's
balance points — never a black-box shape label.

## Primary stack

- Python (`uv`, `pydantic`, `pytest`, `ruff`, `FastAPI`) for the
  engine/CLI/API.
- React + TypeScript + Vite for the web frontend.
- See `specs/architecture.md` for the full architecture and per-stage file layout.

## Run & test

**Run**
- CLI: `uv run fit-balance --help` — score a garment against a set of
  measurements.
- API: `uv run uvicorn api.main:app --reload` — starts on `:8000`.
- Web: `npm run dev` (from `web/`) — dev server, expects the API on
  `:8000`.

**Test / verify**
- `uv run pytest` — Python test suite.
- `uv run ruff check .` — Python lint.
- `npx tsc --noEmit -p .` (from `web/`) — frontend typecheck.
- `npx vitest run` (from `web/`) — frontend tests.
- `./check.sh` — runs all four; the one gate before calling any change
  done.

## Structure

```
fit-balance/
├── src/fit_balance/  — the engine (balance_points.py, effects.yaml,
│                       scoring.py) + schemas.py, cli.py, garments.py
├── api/              — FastAPI, a thin layer over the engine
├── web/              — React + TS frontend
├── tests/            — pytest, mirrors src/
├── specs/            — active per-feature specs (requirements/plan/validation)
├── docs/             — see Folder map below
├── NOTES.md, README.md, CLAUDE.md
└── check.sh          — the one gate: pytest, ruff, tsc, vitest
```

**Folder map**

`NOTES.md` — source of truth. Read it before any design decision. Architecture and formulas live there, not here.

`specs/architecture.md` — stack decisions + per-stage roadmap,
including stages not built yet.

`specs/` — active per-feature specs, one dated folder per feature:
`specs/YYYY-MM-DD-<slug>/{requirements,plan,validation}.md`. Written by
the `feature-spec` skill (see Agent skills, below). Never deleted —
same historical-record treatment as `docs/adr/`.

`docs/adr/` — holds the *why*.
- One immutable file per past engine change.
- Each is referenced from the relevant `NOTES.md` section.

`docs/plans/` — frozen history of the old plan-doc workflow, from
before `specs/` existed. No new entries; existing files stay as
historical record, same as `docs/adr/`.

`docs/project_docs/` — human-readable, per-stage write-ups.
- The clean tier meant to be reread, not the dense engine detail.

`docs/agents/` — behavioral conventions an agent actually follows in
this repo (how to explore, how to file issues).

`docs/learning/` — personal study notes (Claude Code mechanics, Python
concepts).
- Gitignored: local only, never pushed.

## Main logic

**Engine**
- Scoring core: `balance_points.py`, `effects.yaml`, `scoring.py`.
- Turns a body's balance points and a garment's attributes into a
  verdict.
- CLI, API, and web are thin layers on top of it.
- **An engine change** is any edit to those three files.

## Build order

- Stages 1–4 (balance-point calculator, scoring, CLI, web + API) are
  implemented.
- Stages 5–6 (garment-photo CV, multi-garment parsing) are not
  started.
- See `NOTES.md`'s "Build order — status" section for exactly what's
  done and where.

## Standing rules (from NOTES.md)

- **Balance points, not shape categories, drive scoring.** Continuous
  signed numbers (e.g. `bust_hip_balance`, `waist_definition`) are the
  internal model. A shape label (pear/hourglass/apple/rectangle) may be
  shown to the user as a display string. It must never be used in the
  scoring logic itself.
- **Worked examples must be automated tests, not eyeballed.** Rule
  changes have silently regressed prior-correct worked examples before
  (the "apple + bodycon" case in NOTES.md). Every engine change must
  keep `tests/test_balance_points.py` and `tests/test_scoring.py`
  green. That suite encodes all 5 worked examples.

## Workflow

Every non-trivial change gets a spec before code (trivial changes skip
straight to Implement). Use the `feature-spec` skill to branch,
interview, and scaffold `specs/YYYY-MM-DD-<slug>/` — see
`.claude/skills/feature-spec/SKILL.md` for the exact steps.

- **Wait for explicit approval of `requirements.md` + `plan.md`
  before implementing.**
- `validation.md` must require `./check.sh` passing in full, not just
  a new assertion for this feature.
- A change touching `balance_points.py` / `effects.yaml` /
  `scoring.py` must add an entry to `docs/adr/` (via `new-decision`)
  and land its worked example in `tests/test_balance_points.py` or
  `tests/test_scoring.py` specifically — `validation.md` must say so
  explicitly.
- Run the `changelog` skill before merging.
- One commit per decision. Merge to `main`, delete the branch.
- **Close out:** update `NOTES.md` (and `docs/project_docs/` if
  stage-worthy). `specs/` folders are never deleted, same as
  `docs/adr/`.

## Agent skills

- **Feature spec:** `feature-spec` branches, interviews
  (`AskUserQuestion`: Scope/Decisions/Context), and scaffolds
  `specs/YYYY-MM-DD-<slug>/{requirements,plan,validation}.md`. See
  `.claude/skills/feature-spec/SKILL.md`.
- **Changelog:** `changelog` appends new commits into `CHANGELOG.md`
  from `git log`; run before merging a branch. See
  `.claude/skills/changelog/SKILL.md`.
- **Domain docs:** `/domain-modeling` and `new-decision` both write to
  `docs/adr/` (see Structure, above). That's a pre-existing convention,
  not overridden. `NOTES.md` remains the current-state spec. A thin
  `CONTEXT.md` may grow lazily via `/domain-modeling` alongside it. See
  `docs/agents/domain.md`.
