# Validation: Quantized main_concern()

## Automated

`./check.sh` must pass in full (pytest, ruff, mypy, tsc, vitest) — the
standard bar, not just a new assertion for this change.

Specific required assertions:

- `tests/test_balance_points.py`: all 5 worked examples' `main_concern()`
  result re-verified. The apple-example result is expected to change
  (from the raw-magnitude pick to a quantized-level pick, possibly a
  tie) — the updated assertion must say explicitly, in the test or a
  comment, why it changed, matching CLAUDE.md's rule that a worked-
  example change must be deliberate, not a silent regression.
- A new tie-case test: a constructed body where two or more axes land
  on the same highest cleared severity level, asserting
  `main_concern()` returns all of them.
- Boundary tests at the deadzone/pronounced-threshold edges for the
  new quantization step, mirroring decision 0010's own boundary tests
  for `signed_level`.
- `tests/test_scoring.py`: all 5 worked examples' verdicts
  (recommendation/score/reasons) byte-for-byte unchanged. This is the
  critical regression guard, since scoring's internals are being
  rewired in Group 2.
- `tests/test_api.py`: response shape updated and tested for all 4
  affected endpoints (`/score`, `/score-outfit`, `/recommend-outfits`,
  `/balance-garment`), including a tie case.

## Testing decisions

- **Seam**: `WomensBalancePoints.main_concern()` directly, for the
  engine-level behavior change — same seam `tests/test_balance_points.py`
  already uses. `score()`/the axis-rule table via
  `tests/test_scoring.py`, as the "verdict didn't change" regression
  guard. The 4 endpoint handlers via `tests/test_api.py`, for the
  response-shape change. No new seam introduced — this reuses the
  three existing test entry points the project already tests through.
- **Prior art**: decision 0010's own boundary-condition tests (pinning
  the exclusive `<` comparison at the deadzone and pronounced-
  threshold edges) are the direct model for this change's new
  quantization-function tests.

## Manual

- Run the CLI against the apple worked example; confirm the balance-
  point table badges the (now-updated) main concern correctly,
  matching the new test assertion.
- Load the web app with measurements that produce a genuine tie (a
  close variant of the pear fixture is a known candidate); confirm the
  chart badges every tied axis, not just one.
- Confirm the case where nothing clears the deadzone still shows no
  "main concern" badge anywhere — CLI, web, and API all reporting an
  empty list consistently.

## Tone check

Not applicable — no new user-facing copy or strings beyond the
existing "main concern" label, which already exists today.

## Definition of done

- `./check.sh` green.
- All 5 worked examples' verdicts (`tests/test_scoring.py`)
  byte-for-byte unchanged.
- `main_concern()`'s apple-example change is a documented, deliberate
  update, called out as such — not a silent regression.
- A new decision record written (this is an engine change: the
  balance-point and scoring modules are both edited), referencing
  decision 0010 as a followup; `CURRENT_STATE.md`'s "Known gaps" entry
  for `main_concern()` updated to reflect the fix.
- One commit per plan group, per CLAUDE.md's workflow; merge to
  `main`, delete the branch.
