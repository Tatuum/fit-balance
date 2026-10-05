# 0015. Quantized main_concern(), ties surfaced instead of broken

Date: 2026-10-05
Status: Accepted

## Context

Decision [0010](0010-discrete-severity-level-scoring.md) fixed scoring's
cross-axis comparability problem — summing raw, differently-scaled axis
deviations isn't meaningful — by quantizing each axis into a small integer
severity level before combining them, and explicitly flagged that
`WomensBalancePoints.main_concern()` has the identical problem but was
left untouched: it picked "the" axis with the largest raw `abs()`
magnitude, with no reference-point subtraction. That raw comparison masked
real ties: `APPLE_LONG_TORSO` (one of the 5 `CURRENT_STATE.md` worked examples)
picked `torso_leg_balance` (raw `0.1239`) over `waist_definition` (raw
`0.0929`) and `frame_scale_dev` (raw `0.0687`) by sheer raw number, even
though all three land at the same quantized severity level once each
axis's own reference point and deadzone are applied.

A related discovery while fixing this: `waist_definition` has no deadzone
(decision [0007](0007-imbalance-deadzone.md) — a favorable-direction
threshold, not "0 is neutral both ways"), encoded as `deadzone = 0.0`
fed into a strict `magnitude < deadzone` check. Since `magnitude` is
never negative, that check can never pass, so `waist_definition` can
never quantize to level 0 — not even exactly at its own `0.15` reference
point. It always contributes at least level `±1`.

## Decision

Quantization moves upstream, into `balance_points.py`, as the single
shared basis both `main_concern()` and `scoring.py` compare against:

```python
AXIS_REFERENCE: dict[str, float] = {"waist_definition": 0.15}

def quantize_axis(value: float, axis: str) -> int:
    reference = AXIS_REFERENCE.get(axis, 0.0)
    deviation = value - reference
    deadzone = IMBALANCE_DEADZONE if axis in DEADZONE_AXES else 0.0
    magnitude = abs(deviation)
    level = 0 if magnitude < deadzone else 1 if magnitude < PRONOUNCED_THRESHOLD else 2
    return level if deviation >= 0 else -level
```

(Moved and renamed from `scoring.py`'s `signed_level`, unchanged in
logic.) A new frozen `QuantizedBalancePoints` dataclass and `quantize()`
function produce one of these per axis. `main_concern()` now compares
these discrete levels and returns **every** axis sharing the single
highest cleared magnitude, as a list, instead of picking one:

```python
def main_concern(self) -> list[str]:
    levels = quantize(self)
    magnitudes = {f.name: abs(getattr(levels, f.name)) for f in fields(levels)}
    peak = max(magnitudes.values())
    return [] if peak == 0 else [n for n, m in magnitudes.items() if m == peak]
```

Ties are surfaced rather than broken by a tie-break heuristic — picking
one via raw magnitude is exactly the problem being fixed, and a fixed
priority order would just be a different arbitrary choice.

`scoring.py`'s `_AxisRule` drops its per-tag `reference` field (now
redundant — quantization already happened upstream); `AXIS_RULES` entries
are axis+weight only. `score()` and `technique_advice.recommend_techniques()`
read an already-quantized level via a new `axis_level()` instead of
calling the old `signed_level()` with a reference pulled off `AXIS_RULES`.
`axis_value()` (the raw float, used for display, e.g.
`DimensionAdvice.value`) is unchanged.

`top_hip_balance` (the derived axis = `max(shoulder_hip_balance,
bust_hip_balance)`, decision [0009](0009-top-hip-balance-axis.md)) needed
no change: `quantize_axis()` is monotonic, and both source axes share the
same deadzone/reference treatment, so `max()` of their two already-
quantized levels equals quantizing their raw `max()` — verified
numerically against all 5 worked examples, including a case
(`PEAR_FULLER`) where the two raw values land in different severity
bands, before relying on it.

## Consequences

`main_concern()`'s return type changes from `str | None` to `list[str]`
(empty = nothing clears, one entry = a clear winner, two or more = a
genuine tie). This propagates to `cli.py` (badge logic, plus its asset-
threshold constant now sourced from `AXIS_REFERENCE` instead of
`AXIS_RULES["defines_waist"].reference`), the 4 API response models that
expose `main_concern` (`/score`, `/score-outfit`, `/recommend-outfits`,
`/balance-garment`), and `BalancePointsChart.tsx`/its 4 mirrored
TypeScript response types (equality checks become `.includes()`).

`APPLE_LONG_TORSO`'s `main_concern()` result changes from
`torso_leg_balance` alone to a 3-way tie (`waist_definition`,
`torso_leg_balance`, `frame_scale_dev`) — pinned in
`tests/test_balance_points.py` and `tests/test_api.py`. No verdict or
score changed anywhere: all 5 worked examples in `tests/test_scoring.py`
stay byte-for-byte identical, confirmed via the CLI against the apple
example too.

Because `waist_definition` can never quantize to level 0,
`main_concern()` can no longer return an empty list in practice for any
real body. Two existing tests whose fixtures used `waist_definition =
0.0` to mean "no signal" are rewritten: that value is a real, pronounced
(level `-2`) fact — zero natural waist cinch — not silence.
`tests/test_balance_points.py` also gains `quantize_axis()` boundary
tests mirroring decision 0010's original ones, now at the relocated
seam.
