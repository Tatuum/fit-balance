# 0009. adds_volume_top/bottom scored against top_hip_balance

Date: 2026-09-09
Status: Accepted

## Context

`adds_volume_top`/`adds_volume_bottom` (0003) were scored against
`bust_hip_balance` alone. That meant the engine had no way to know the
shoulder line was already broad: it would recommend adding *more* top
volume onto an already-broad-shouldered body, and would completely miss
recommending bottom volume to balance a broad-shouldered build with an
otherwise-balanced bust — exactly the distinction `shoulder_hip_balance`
(0002) exists to make, which `bust_hip_balance` alone can't see.

## Decision

Both rules now key off a derived `top_hip_balance = max(shoulder_hip_balance,
bust_hip_balance)`, computed on demand in `scoring.py`'s `_axis_value`
helper — not a stored `WomensBalancePoints` field, so it doesn't compete
with the two real axes for `main_concern()`. Same deadzone treatment
(0007) as the four zero-neutral axes.

## Consequences

`adds_volume_top` can now fire as an explicit *negative* reason for an
already-broad-shouldered body (not just silence), and `adds_volume_bottom`
fires for a broad-shouldered build even when bust alone reads as balanced.
`test_scoring.py::test_adds_volume_bottom_mirrors_adds_volume_top_with_opposite_sign`'s
`bottom_heavy` fixture updated: a neutral `shoulder_hip_balance=0` would win
the `max()` and mask a hip-heavy `bust_hip_balance` as "balanced," so it now
sets both axes negative for a genuinely bottom-heavy body. Two new tests
pin the broad-shoulder interaction in both directions. No worked-example
verdict changed.
