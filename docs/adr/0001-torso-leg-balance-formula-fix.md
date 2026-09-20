# 0001. torso_leg_balance formula fix

Date: 2026-09-08
Status: Accepted

## Context

`torso` and `leg` are measured at different, standard landmarks (ISO 8559 /
tailoring convention): `torso` = back waist length (nape of neck / C7
vertebra down to the natural waist); `leg` = inseam (crotch seam down to the
floor, standing barefoot). These are independent, self-measurable numbers —
they are *not* expected to sum to height (a clinical pair that does, sitting
height + subischial leg length, bakes the head into "torso" and needs a
stadiometer, so it doesn't fit a self-measured consumer flow).

The original formula, `torso_leg_balance = (torso - leg) / max(torso, leg)`,
looked plausible but was wrong for real bodies: back waist length
(~39-41cm per ASTM misses sizing) and inseam (~0.45-0.46 × height) are
structurally different magnitudes for *everyone* — back waist length is
roughly half of inseam — so the raw ratio read as strongly "long legs" for
essentially every body, regardless of actual proportion. The worked-example
fixtures had masked this by using unrealistic torso values inflated to sit
near leg's magnitude.

## Decision

Compare each measurement's deviation from its *own* baseline ratio-to-height
instead of comparing the two raw measurements to each other — mirroring
`frame_scale_dev`'s approach:

```
torso_leg_balance = (torso/height - TORSO_HEIGHT_RATIO_BASELINE) - (leg/height - LEG_HEIGHT_RATIO_BASELINE)
```

`TORSO_HEIGHT_RATIO_BASELINE = 0.245`, `LEG_HEIGHT_RATIO_BASELINE = 0.455` —
guessed from general published ranges, not a rigorous study (same caveat as
the `frame_scale` baselines).

## Consequences

Reads ~0 for baseline proportions and only diverges when a body is actually
long/short-torsoed or long/short-legged relative to average, instead of
reading "long legs" universally. Pinned by the worked examples in
`tests/test_balance_points.py` and `tests/test_scoring.py`.
