# 0010. Discrete severity-level scoring

Date: 2026-09-11
Status: Accepted

## Context

`scoring.score()` summed `contribution = weight * (axis_value - reference)`
across effect tags, where `axis_value` is the raw output of one of
`balance_points.py`'s 5 formulas. Nothing rescaled these onto a comparable
unit before summing — an axis whose formula naturally produces larger
real-world deviations (e.g. `bust_hip_balance`'s ratio vs.
`frame_scale_dev`'s guessed-baseline deviation) would systematically
dominate `Verdict.score`, independent of whether it's actually the more
meaningful styling concern for that body. A first direction explored real
per-subject calibration data (ANSUR II, the 2012 US Army anthropometric
survey) to derive real population std devs as a rescaling factor. That was
dropped: it needed an external dataset, a one-off calibration script, and
left two of the five NOTES.md worked examples sitting on a knife's edge
pending numbers that weren't available at decision time.

## Decision

Quantize each axis's continuous deviation into a small integer severity
level instead: 0 (within the deadzone, or no deadzone), 1 ("notable"), 2
("pronounced"), sign preserved. A new constant,
`PRONOUNCED_THRESHOLD = 0.15` (`balance_points.py`, alongside the existing
`IMBALANCE_DEADZONE = 0.05`), is the level-1/level-2 boundary:

```python
def _signed_level(value: float, reference: float, axis: str) -> int:
    deviation = value - reference
    deadzone = IMBALANCE_DEADZONE if axis in _SCORING_DEADZONE_AXES else 0.0
    magnitude = abs(deviation)
    level = 0 if magnitude < deadzone else 1 if magnitude < PRONOUNCED_THRESHOLD else 2
    return level if deviation >= 0 else -level
```

`waist_definition` gets `deadzone = 0.0` (it's not in
`_SCORING_DEADZONE_AXES`) — level 1 starts at any nonzero deviation from
its 0.15 reference, matching decision 0007's existing reasoning for
excluding that axis from the deadzone (a favorable-direction threshold,
not "0 is neutral both ways"). That reasoning isn't reopened here, only
reused.

`score()`'s contribution line becomes
`contribution = rule.weight * _signed_level(value, rule.reference, rule.axis)`
— always an integer in `{-2, -1, 0, 1, 2}`, since `_AxisRule.weight` is now
typed `int` (`1`/`-1`, was `1.0`/`-1.0`). `AXIS_RULES`'s tag→axis/reference
mapping is unchanged. `RECOMMENDED_THRESHOLD`/`AVOID_THRESHOLD`/
`STRONG_AVOID_THRESHOLD` became `1`/`-1`/`-3` (same bucket logic, new
integer cutoffs). `schemas.Reason.contribution` and `schemas.Verdict.score`
changed from `float` to `int` (also `garments.AttributedReason.contribution`
and `api/main.py`'s `OutfitVerdict.score`), since every value is now
genuinely discrete. The separate deadzone pre-check `score()` used to run
before computing `contribution` became redundant (level 0 → contribution
0 → already caught by the existing `if contribution == 0: continue`) and
was removed.

Neither `PRONOUNCED_THRESHOLD` nor the new integer thresholds are derived
from external data — same judgment-call category `IMBALANCE_DEADZONE` and
`waist_definition`'s 0.15 reference already are, verified instead against
this project's own worked examples (below).

## Consequences

All 5 `NOTES.md` worked examples reproduce their documented verdict
exactly under this scheme, hand-verified against real measurement numbers
before landing:

| # | body / garment | discrete total | verdict |
|---|---|---|---|
| 1 hourglass, bodycon+belt | +2 | recommended |
| 2 apple, bodycon+belt | −2 | avoid |
| 3 rectangle/petite, drop_waist | −4 | strong_avoid |
| 4 rectangle/petite, empire+vertical | +5 | recommended |
| 5 pear/fuller, oversized+skinny | 0 | neutral |

No worked-example test's expected verdict changed. `tests/test_scoring.py`
gained 5 new boundary-condition tests pinning the exclusive `<` comparison
at both the deadzone and `PRONOUNCED_THRESHOLD` boundaries, and confirming
`waist_definition`'s no-deadzone behavior, since the existing worked
examples don't exercise those exact edges. `cli.py`'s score/contribution
formatting changed from `:.3f` to plain integer display, since the
trailing `.000` would otherwise misrepresent a now-genuinely-discrete
value as still continuous.

`balance_points.WomensBalancePoints.main_concern()` has the identical
underlying cross-axis raw-magnitude-comparison problem this decision
fixes for scoring, but is deliberately left untouched — it touches CLI
output, `BalancePointsChart.tsx`, and its own dedicated tests, none of
which were in scope here. A future decision could apply the same
severity-level concept there.
