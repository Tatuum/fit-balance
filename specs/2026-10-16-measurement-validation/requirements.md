# Requirements: validate measurement inputs

## Context

Nothing checks the seven measurements. `Measurements` (`schemas.py`) has no
limits, and the form's `<input type="number" step="0.1">` has no `min`
or `max`. Observed on the live API:

| Input | Result |
|---|---|
| `waist = 1` | 200, `waist_definition` jumps to +0.99 |
| `shoulder = 0` | 200, `shoulder_hip_balance` hits -1.00 |
| `height = 0` | **500**, `ZeroDivisionError` in `compute_womens_balance_points` |
| `height = -5` | 200, `frame_scale_dev` -17.5 |

In the form, clearing a field makes `Number("")` send `0`, so emptying
the height field crashes the request and makes the avatar scale infinite.
Found while writing `docs/project_docs/web-app-overview.md` (Gotchas).

## Requirements

- The API rejects out-of-range measurements with **422**, never a 500 or
  a nonsense 200.
- The form never sends an invalid set of measurements and never draws the
  avatar from one.
- An empty or out-of-range field is marked in the form, with the allowed
  range shown.
- While a field is invalid, the last valid values keep driving the avatar
  and the advice.
- The ranges are written once per layer (Python, TypeScript). The backend
  is the authority.

## Ranges (cm)

Sanity bounds, deliberately wide: they catch typos and impossible values,
not unusual bodies. Chosen by the project owner, not taken from survey
data (same caveat class as the baselines in "Known gaps").

| Field | Min | Max |
|---|---|---|
| height | 120 | 230 |
| shoulder (circumference) | 60 | 160 |
| bust | 60 | 180 |
| waist | 40 | 180 |
| hip | 60 | 200 |
| torso (back waist length) | 25 | 60 |
| leg (inseam) | 50 | 110 |

Bounds are inclusive.

## Out of scope

Cross-field checks (for example waist larger than hip). The verdict score
display and the stale-response handling, which are separate small fixes.
No change to `balance_points.py`, `effects.yaml` or `scoring.py`, so no
ADR.
