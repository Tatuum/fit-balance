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

Every non-trivial change moves through six stages below. Trivial
changes (typos, a one-line config tweak) can skip straight to
Implement.

1. **Shape** — talk it through (plan mode or normal conversation).
   Pull in research, a quick prototype, or a domain-modeling pass only
   if the topic actually needs it. Nothing written yet.
2. **Plan** — write `docs/plans/NNNN-slug.md` (next number after the
   highest in `docs/plans/README.md`; template at
   `docs/plans/TEMPLATE.md`). This is the rereadable record: context,
   options considered, decision, reasoning. For any change touching
   `balance_points.py` / `effects.yaml` / `scoring.py`, the plan must
   state a worked example ("body X + garment Y → verdict Z", with
   reasoning) before implementation starts — this is the existing
   worked-example rule (see decision 0006's `hides_waist` for the
   pattern), just pinned to this stage explicitly. **Wait for explicit
   approval before moving on.**
3. **Publish the spec** — once approved, open one GitHub issue: title +
   summary + a link back to the plan doc. Cross-link both ways: the
   plan doc's header gets `GitHub: #NN`; the issue body links back to
   `docs/plans/NNNN-slug.md`. The issue is a pointer, not a duplicate —
   the plan doc stays the source of depth.
4. **Steps** — break the plan into an ordered checklist, added to the
   plan doc as `## Steps`. Mirror each step as a child GitHub issue
   linked to the spec issue, noting blocking order. **Wait for
   explicit approval of the breakdown before implementing.**
5. **Implement** — work one step at a time. Use `tdd` at the seams
   NOTES.md already calls out. `./check.sh` must pass. `code-review`
   before committing. One commit per decision, message references
   `Closes #N`. Close that step's GitHub issue and check off its line
   in the plan doc.
   - **A step that edits `balance_points.py`, `effects.yaml`, or
     `scoring.py` is an engine change**: write its ADR (`new-decision`
     skill) and update `NOTES.md` — including the worked-example line
     if one changed — in the *same* change, immediately, even if other
     steps in the plan are still open. Never deferred to stage 6.
   - Plans and step issues can change during implementation. Small
     corrections: edit in place. An actual change of decision: append
     a dated note under the plan's `## Updates` (`**YYYY-MM-DD:**
     switched from X to Y because...`) rather than rewriting the
     original reasoning — a step issue's comment thread does the same
     job.
6. **Close out** — once *all* steps are done (not per-step): update
   `NOTES.md`, and add/update a `docs/project_docs/` write-up if the
   feature is stage-worthy. Close the parent spec issue. Add `Status:
   Shipped — see NOTES.md §X` (or `ADR NNNN`) to the top of the plan
   doc; everything else in it stays untouched and readable.

`docs/plans/README.md` indexes every plan (number, title, status) —
same pattern as `docs/adr/README.md`.

- **One commit per decision.** Made when it's agreed — not batched up
  and split apart later. Keeps `git log` a legible record of the
  conversation.
- **Run `./check.sh` before calling any change done.** One gate:
  `pytest`, `ruff check`, the frontend's `tsc --noEmit`, and
  `vitest run`.

## Agent skills

- **Issue tracker:** issues and specs live as GitHub issues via the
  `gh` CLI, on the `Tatuum/fit-balance` remote (already configured as
  `origin`). The `gh` CLI itself still needs installing + `gh auth
  login` before stages 3+ of the Workflow are usable. See
  `docs/agents/issue-tracker.md`.
- **Domain docs:** `/domain-modeling` and `new-decision` both write to
  `docs/adr/` (see Project, above). That's a pre-existing convention,
  not overridden. `NOTES.md` remains the current-state spec. A thin
  `CONTEXT.md` may grow lazily via `/domain-modeling` alongside it. See
  `docs/agents/domain.md`.
