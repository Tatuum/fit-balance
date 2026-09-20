# 0007. Imbalance deadzone for the four zero-neutral axes

Date: 2026-09-09
Status: Accepted

## Context

`main_concern()` always named whichever axis had the largest absolute
magnitude, even if every axis was tiny (near-balanced measurement noise,
not a real proportion difference). `scoring.score()` generated reasons
against an axis regardless of how small its value was, letting negligible
deviations tip a garment's verdict.

## Decision

`shoulder_hip_balance`, `bust_hip_balance`, `torso_leg_balance`, and
`frame_scale_dev` are neutral at 0 in both directions, so a value under 0.05
(`balance_points.IMBALANCE_DEADZONE`) is treated as not a real imbalance:

- `main_concern()` won't name one of these axes as the concern below that
  line, returning `None` if nothing on any axis clears it.
- `scoring.score()` won't generate a reason against one of these axes
  either.

`waist_definition` is deliberately excluded: it already has its own
asymmetric threshold (0.15, in `scoring.py`'s `AXIS_RULES`) for a different
reason — one direction is favorable, not "0 is neutral both ways" — so
stacking a second deadzone on top isn't the same kind of fix. The 0.05
threshold matches the "near-balanced" cutoff `test_balance_points.py`'s
worked-example assertions already used informally (`abs(...) < 0.05`).

## Consequences

`main_concern`'s return type is `str | None` end-to-end (API response
models, frontend types, `BalancePointsChart`'s prop) — no axis name ever
equals `null`, so existing comparisons stayed safe.
`tests/test_garments.py::test_attribution_lists_both_items_when_tags_overlap`
switched from `HOURGLASS_BALANCED` to `PEAR_FULLER`: the former's
`frame_scale_dev` (~0.013) now falls inside the deadzone, which would
suppress the `reduces_bulk` reasons that test exists to check for.
