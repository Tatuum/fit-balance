# CLAUDE.md

## Purpose

fit-balance is an explainable styling-recommendation system. Every
verdict comes with editable, inspectable reasons tied to the user's
balance points — never a black-box shape label.

## Primary stack

- Python (`uv`, `pydantic`, `pytest`, `ruff`, `FastAPI`) for the
  engine/CLI/API.
- React + TypeScript + Vite for the web frontend.
- See `plan.md` for the full architecture and per-stage file layout.

## Project

**The engine** is the scoring core: `balance_points.py`, `effects.yaml`,
`scoring.py`. It turns a body's balance points and a garment's
attributes into a verdict. CLI, API, and web are thin layers on top of
it.

**An engine change** is any edit to those three files.

**Source of truth: `NOTES.md`.** Read it before any design decision.
Architecture and formulas live there, not here.

`docs/adr/` holds the *why*. One immutable file per past engine change.
Each is referenced from the relevant `NOTES.md` section.

- **Build order:** stages 1–4 (balance-point calculator, scoring, CLI,
  web + API) are implemented. Stages 5–6 (garment-photo CV,
  multi-garment parsing) are not started. See `NOTES.md`'s "Build
  order — status" section for exactly what's done and where.
- **Commands:** `uv run pytest` / `uv run ruff check .` (Python),
  `npm run build` / `npx vitest run` from `web/` (frontend).

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

- **Decide in writing first, for any engine change.** Don't leave it in
  chat history. Every engine change gets:
  - A new, immutable file in `docs/adr/NNNN-slug.md` (context /
    decision / consequences). Use the `new-decision` skill to scaffold
    it, or copy the shape of an existing file. Write it in the same
    change that implements the decision. Never edit it later — a
    reversal gets its own new file that supersedes the old one.
  - A `NOTES.md` update describing the resulting current state, linked
    to that decision file.
  - If the change alters a documented worked example's outcome, update
    that example's line in `NOTES.md` too, deliberately. See decision
    0006 (`hides_waist`) for the pattern.
- **New scoring behavior needs a worked example, not just a unit
  test.** Before wiring up a new axis interaction or effect tag: state
  the concrete case in NOTES.md-worked-example form ("body X + garment
  Y → verdict Z"). State the reasoning. Then implement to match it.
- **One commit per decision.** Made when it's agreed — not batched up
  and split apart later. Keeps `git log` a legible record of the
  conversation.
- **Run `./check.sh` before calling any change done.** One gate:
  `pytest`, `ruff check`, the frontend's `tsc --noEmit`, and
  `vitest run`.

## Agent skills

- **Issue tracker:** issues and specs live as GitHub issues via the
  `gh` CLI. No remote is configured yet — add one before this is
  usable. See `docs/agents/issue-tracker.md`.
- **Domain docs:** `/domain-modeling` and `new-decision` both write to
  `docs/adr/` (see Project, above). That's a pre-existing convention,
  not overridden. `NOTES.md` remains the current-state spec. A thin
  `CONTEXT.md` may grow lazily via `/domain-modeling` alongside it. See
  `docs/agents/domain.md`.
