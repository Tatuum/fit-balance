# CLAUDE.md

## Purpose

fit-balance is an explainable styling-recommendation system. Every
verdict comes with editable, inspectable reasons tied to the user's
balance points — never a black-box shape label.

## Primary stack

- Python (`uv`, `pydantic`, `pytest`, `ruff`, `FastAPI`) for the
  engine/CLI/API.
- React + TypeScript + Vite for the web frontend.
- See `ARCHITECTURE.md` for the full architecture and per-stage file layout.

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
├── docs/             — see Folder map below
├── NOTES.md, ARCHITECTURE.md, README.md, CLAUDE.md
└── check.sh          — the one gate: pytest, ruff, tsc, vitest
```

**Folder map**

`NOTES.md` — source of truth. Read it before any design decision. Architecture and formulas live there, not here.

`ARCHITECTURE.md` — stack decisions + per-stage roadmap, including
stages not built yet.

`docs/adr/` — holds the *why*.
- One immutable file per past engine change.
- Each is referenced from the relevant `NOTES.md` section.

`docs/plans/` — planning-session history.
- Numbered and indexed like `docs/adr/`, but never deleted.
- See the Workflow section below for how a plan gets there.

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
- **Follow the build order — do not jump ahead to image/CV work.**
  Don't start stage 5 or 6 (see Build order, above) without an explicit
  decision to. They're the highest-uncertainty, least-validated part of
  the plan.
- **Worked examples must be automated tests, not eyeballed.** Rule
  changes have silently regressed prior-correct worked examples before
  (the "apple + bodycon" case in NOTES.md). Every engine change must
  keep `tests/test_balance_points.py` and `tests/test_scoring.py`
  green. That suite encodes all 5 worked examples.

## Workflow

Every non-trivial change moves through six stages below. Trivial
changes (typos, a one-line config tweak) can skip straight to
Implement. `docs/plans/README.md` indexes every plan (number, title,
status), same pattern as `docs/adr/README.md`.

| Stage | Mode | Input | Output | Where |
|---|---|---|---|---|
| 1. Shape | Plan mode or conversation | Human's idea + codebase exploration | Shared understanding | Nothing persisted |
| 2. Plan | AI agent writes it, human approves | Stage 1's discussion | Context, Options considered, Decision, Worked example, Out of scope | `docs/plans/NNNN-slug.md` |
| 3. Publish spec | Human runs this once the plan is approved | The approved plan doc | One GitHub issue, linked both ways | GitHub (`Tatuum/fit-balance`) |
| 4. Steps | Same session | The approved plan | Ordered checklist + one child issue per step | Plan doc's `## Steps` + GitHub child issues |
| 5. Implement | Normal mode, one step at a time | One step's issue | Code + tests, commit, issue closed | `src/`, `tests/`, etc. (+ `docs/adr/` for engine changes) |
| 6. Close out | Once *all* steps are done | The shipped feature | Docs updated, issues closed | `NOTES.md`, `docs/project_docs/`, GitHub |

**1. Shape.** Pull in `research`, `prototype`, or `domain-modeling`
only if the topic actually needs it.

**2. Plan.** Template at `docs/plans/TEMPLATE.md`; number sequentially
after the highest in `docs/plans/README.md` (indexed same as
`docs/adr/README.md`, never deleted). For any change touching
`balance_points.py` / `effects.yaml` / `scoring.py`, state the worked
example ("body X + garment Y → verdict Z", with reasoning) before
implementing — see decision 0006's `hides_waist` for the pattern.
**Wait for explicit approval before moving on.**

**3. Publish spec.** Cross-link both ways: the plan doc's header gets
`GitHub: #NN`; the issue links back to `docs/plans/NNNN-slug.md`. The
issue is a pointer, not a duplicate — the plan doc stays the source of
depth.

**4. Steps.** Mirror each step as a child GitHub issue linked to the
spec issue, noting blocking order. **Wait for explicit approval of the
breakdown before implementing.**

**5. Implement.** `tdd` at the seams NOTES.md already calls out.
`./check.sh` must pass. `code-review` before committing. One commit
per decision, message references `Closes #N`. Close that step's issue
and check off its line in the plan.
   - A step that edits `balance_points.py`, `effects.yaml`, or
     `scoring.py` is an **engine change**: write its ADR
     (`new-decision` skill) and update `NOTES.md` — including the
     worked-example line if one changed — in the *same* change,
     immediately, even if other steps in the plan are still open.
     Never deferred to stage 6.
   - Plans and step issues can change during implementation. Small
     corrections: edit in place. An actual change of decision: append
     a dated note under the plan's `## Updates` (`**YYYY-MM-DD:**
     switched from X to Y because...`) rather than rewriting the
     original reasoning — a step issue's comment thread does the same
     job.

**6. Close out.** Once *all* steps are done (not per-step): update
`NOTES.md`, add/update a `docs/project_docs/` write-up if the feature
is stage-worthy, close the parent spec issue, and add `Status: Shipped
— see NOTES.md §X` (or `ADR NNNN`) to the top of the plan doc —
everything else in it stays untouched and readable.

- **One commit per decision.** Made when it's agreed — not batched up
  and split apart later. Keeps `git log` a legible record of the
  conversation.
- **Run `./check.sh` before calling any change done.** See "Run &
  test", above.

## Agent skills

- **Issue tracker:** issues and specs live as GitHub issues via the
  `gh` CLI, on the `Tatuum/fit-balance` remote (already configured as
  `origin`). The `gh` CLI itself still needs installing + `gh auth
  login` before stages 3+ of the Workflow are usable. See
  `docs/agents/issue-tracker.md`.
- **Domain docs:** `/domain-modeling` and `new-decision` both write to
  `docs/adr/` (see Structure, above). That's a pre-existing convention,
  not overridden. `NOTES.md` remains the current-state spec. A thin
  `CONTEXT.md` may grow lazily via `/domain-modeling` alongside it. See
  `docs/agents/domain.md`.
