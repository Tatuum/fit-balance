# CLAUDE.md

## Purpose

fit-balance is an explainable styling-recommendation system. Every
verdict comes with editable, inspectable reasons tied to the user's
balance points — never a black-box shape label.

## Primary stack

- Python (`uv`, `pydantic`, `pytest`, `ruff`, `FastAPI`) for the
  engine/CLI/API.
- React + TypeScript + Vite for the web frontend.
- See `specs/architecture.md` for the full architecture.

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
├── CURRENT_STATE.md, README.md, CLAUDE.md
└── check.sh          — the one gate: pytest, ruff, tsc, vitest
```

**Folder map**

`CURRENT_STATE.md` — source of truth. Read it before any design decision. Architecture and formulas live there, not here.

`specs/` — architecture/mission/stack/roadmap docs, plus active
per-feature specs.
- `architecture.md` — stack decisions (Tech stack section), layering
  (High-level architecture section), and future direction. Read by
  the `feature-spec` skill before drafting every spec, and again for
  its architecture-fit check after `plan.md` is drafted.
- `mission.md` — the *why* behind Purpose above. Read by the
  `feature-spec` skill before drafting every spec.
- `roadmap.md` — phase list; `feature-spec` finds the next incomplete
  phase here to branch and scaffold.
- `YYYY-MM-DD-<slug>/{requirements,plan,validation}.md` — one dated
  folder per feature, written by the `feature-spec` skill (see Agent
  skills, below). Never deleted — same historical-record treatment as
  `docs/adr/`.

`docs/adr/` — holds the *why*.
- One immutable file per past engine change.
- Each is referenced from the relevant `CURRENT_STATE.md` section.

`docs/plans/` — frozen history of the old plan-doc workflow, from
before `specs/` existed. No new entries; existing files stay as
historical record, same as `docs/adr/`.

`docs/project_docs/` — human-readable, per-stage write-ups.
- The clean tier meant to be reread, not the dense engine detail.

`docs/agents/` — behavioral conventions an agent actually follows in
this repo (how to explore domain docs before working in an area).

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

The engine, CLI, API, and web app are shipped. See `specs/roadmap.md`
for phase-by-phase build status.

## Standing rules (from CURRENT_STATE.md)

- **Balance points, not shape categories, drive scoring.** Continuous
  signed numbers (e.g. `bust_hip_balance`, `waist_definition`) are the
  internal model. A shape label (pear/hourglass/apple/rectangle) may be
  shown to the user as a display string. It must never be used in the
  scoring logic itself.
- **Worked examples must be automated tests, not eyeballed.** Rule
  changes have silently regressed prior-correct worked examples before
  (the "apple + bodycon" case in CURRENT_STATE.md). Every engine change must
  keep `tests/test_balance_points.py` and `tests/test_scoring.py`
  green. That suite encodes all 5 worked examples.

## Workflow

Every non-trivial change gets a spec before code (trivial changes skip
straight to Implement).

1. **Kick off** — `feature-spec` skill: reads `specs/roadmap.md`
   (finds the next incomplete phase), then `specs/mission.md` +
   `specs/architecture.md` in full for guidance; branches, interviews,
   and writes
   `specs/YYYY-MM-DD-<slug>/{requirements,plan,validation}.md`. Once
   `plan.md` is drafted, checks architecture fit (layering/stack)
   against that same `specs/architecture.md` read before requesting
   approval. See `.claude/skills/feature-spec/SKILL.md`.
2. **Wait for explicit approval** of `requirements.md` + `plan.md`
   before implementing.
3. **Implement.** `validation.md` must require `./check.sh` passing in
   full, not just a new assertion for this feature.
4. **Engine change?** (any edit to `balance_points.py` /
   `effects.yaml` / `scoring.py`): run `new-decision` — writes
   `docs/adr/NNNN-slug.md` + `docs/adr/README.md`, updates `CURRENT_STATE.md`
   with the resulting current-state behavior. Land the worked example
   in `tests/test_balance_points.py` or `tests/test_scoring.py`
   specifically — `validation.md` must say so explicitly.
5. **Before merging:** run `changelog` — writes `CHANGELOG.md` from
   `git log`.
6. One commit per decision. Merge to `main`, delete the branch.
7. **Close out:** update `CURRENT_STATE.md` (and `docs/project_docs/` if
   stage-worthy). `specs/` folders are never deleted, same as
   `docs/adr/`.

## Agent skills

| Skill | Reads | Writes |
|---|---|---|
| `feature-spec` (`AskUserQuestion`: Scope/Decisions/Context) | `specs/roadmap.md`, `specs/mission.md`, `specs/architecture.md` (read once in full — used both for guidance and the later architecture-fit check) | `specs/YYYY-MM-DD-<slug>/{requirements,plan,validation}.md`. See `.claude/skills/feature-spec/SKILL.md`. |
| `new-decision` | `docs/adr/*.md` (next number) | `docs/adr/NNNN-slug.md`, `docs/adr/README.md`; updates `CURRENT_STATE.md`'s current-state text. |
| `changelog` | `git log` | `CHANGELOG.md`; run before merging a branch. See `.claude/skills/changelog/SKILL.md`. |
| `/domain-modeling` | — | `docs/adr/` (same pre-existing convention as `new-decision` — not overridden), plus a thin `CONTEXT.md` that grows lazily alongside it. See `docs/agents/domain.md`. |
