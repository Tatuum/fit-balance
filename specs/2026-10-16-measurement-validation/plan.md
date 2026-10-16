# Plan: validate measurement inputs

## Architecture fit

Validation lives in `schemas.py`, the pydantic models shared by the
library and the API. It is not one of the three engine files (CLAUDE.md:
an engine change is an edit to `balance_points.py`, `effects.yaml` or
`scoring.py`), so no ADR. `api/` needs no code change: FastAPI already
turns a pydantic validation failure into a 422. `web/` mirrors the ranges
and adds form feedback. Dependency direction is unchanged.

## Backend

- `src/fit_balance/schemas.py`: give each `Measurements` field
  `Field(ge=..., le=...)` using the table in `requirements.md`. Keep the
  docstring's note on units (cm).
- `tests/test_api.py`: for every field, a value just below the minimum and
  just above the maximum returns 422 from `/technique-recommendations`;
  the min and max themselves return 200; `height = 0` returns 422 (it was
  a 500). Pull the ranges from `Measurements.model_fields` so the test
  follows the model.
- The existing fixtures in `tests/fixtures.py` already sit inside the
  ranges; `./check.sh` confirms.

## Frontend (`web/`)

- New `src/lib/measurements.ts` (pure, no React):
  - `MEASUREMENT_RANGES: Record<keyof Measurements, {min, max}>`, with a
    comment that it mirrors `schemas.py` and must be kept in sync.
  - `parseMeasurement(key, text): number | null`, returning `null` for an
    empty string, a non-number, or a value outside the range (inclusive).
- New `src/lib/measurements.test.ts`: in range, both boundaries, just
  outside each boundary, empty string, non-numeric text, decimals.
- `lib/measurements.ts` also exports `FormState` (`{ drafts, measurements }`),
  `initialFormState` and `applyInput(state, key, text)`: the draft always
  takes the typed text, `measurements` changes only when `parseMeasurement`
  returns a number, and an invalid edit returns the same `measurements`
  object so effects do not re-run. Tested in `measurements.test.ts`.
- `src/App.tsx`: hold one `form` state (`initialFormState`) instead of
  `measurements` alone, and update it with `applyInput`. The input shows
  `drafts[key]`, carries `min`/`max`, and when its draft is invalid gets
  `aria-invalid` and a short message ("Enter 40–180 cm"). `measurements`
  stays the last valid set, so `Avatar`, the advice effect and
  `GarmentBalance` are untouched.
- `src/App.css`: styles for the invalid field and the message.

## Docs

- `docs/project_docs/web-app-overview.md`: add `drafts` to the state table,
  describe the new flow and `lib/measurements.ts`, remove the "Cleared
  input becomes 0" gotcha.
- `CURRENT_STATE.md`: one short note in the measurement section that the
  inputs are range-checked, pointing at `schemas.py`.

## Workflow

One branch, `fix/measurement-validation`. Commit 1: backend validation,
its tests, and this spec. Commit 2: frontend validation, its tests, and
the docs. `changelog` runs after the merge, as a follow-up PR.
