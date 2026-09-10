# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

fit-balance is an explainable styling-recommendation engine: instead of a black-box
body-shape label or a photorealistic try-on render, it surfaces *why* a garment
technique works with or against a user's proportions, with editable, inspectable
reasons behind every verdict. `NOTES.md` is the current-state spec — full
architecture and formulas — and the source of truth, not this file; read it
before making design decisions. `docs/decisions/` holds the *why*: one
immutable file per past engine-level decision, referenced from the relevant
`NOTES.md` section.

Stack: Python (`uv`, `pydantic`, `pytest`, `ruff`) for the engine/CLI/API,
React + TypeScript + Vite for the web frontend. See `plan.md` for the full
architecture and per-stage file layout.

Stages 1–4 of the build order are implemented (engine, scoring, CLI, web +
API) — see `NOTES.md`'s "Build order — status" section for exactly what's
done and where. Stages 5–6 (garment-photo CV, multi-garment parsing) are
not started.

Commands: `uv run pytest` / `uv run ruff check .` (Python), `npm run build`
/ `npx vitest run` from `web/` (frontend).

## Standing rules (from NOTES.md)

- **Balance points, not shape categories, drive scoring.** Continuous signed
  numbers (e.g. `bust_hip_balance`, `waist_definition`) are the internal model.
  A shape label (pear/hourglass/apple/rectangle) may be shown to the user as a
  display string, but must never be used in the scoring logic itself.
- **Follow the build order — do not jump ahead to image/CV work.** Stages
  1–4 are done (see above); do not start stage 5 (garment-photo attribute
  extraction) or 6 (multi-garment parsing) without an explicit decision to —
  they're the highest-uncertainty, least-validated part of the plan.
- **Worked examples must be automated tests, not eyeballed.** Rule changes have
  silently regressed prior-correct worked examples before (the "apple + bodycon"
  case in NOTES.md). Any change to `balance_points.py`, `effects.yaml`, or
  `scoring.py` must keep `tests/test_balance_points.py` and
  `tests/test_scoring.py` green — that suite encodes all 5 worked examples.

## Workflow

- **Decide in writing first, for anything touching the engine** — not left
  to only exist in chat history. A new formula, axis, or scoring rule gets:
  (1) a new, immutable file in `docs/decisions/NNNN-slug.md` (context /
  decision / consequences — see any existing one for the shape) written as
  part of the same change that implements it, never edited later — a
  reversal gets its own new decision file that supersedes the old one; and
  (2) `NOTES.md` updated to describe the resulting current state, with a
  link to that decision file. If the change alters a documented worked
  example's outcome, update that example's line in `NOTES.md` too,
  deliberately — see decision 0006 (`hides_waist`) for the pattern.
- **New scoring behavior needs a worked example, not just a unit test.**
  Before wiring up a new axis interaction or effect tag, state the concrete
  case in NOTES.md-worked-example form ("body X + garment Y → verdict Z") and
  the reasoning, then implement to match it.
- **One commit per decision, made when it's agreed**, not batched up and
  split apart later. Keeps `git log` a legible record of the conversation.
- **Run `./check.sh` before calling any change done.** One gate: `pytest`,
  `ruff check`, the frontend's `tsc --noEmit`, and `vitest run`.
