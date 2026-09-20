# 0004. Avatar renders to-scale from measurements

Date: 2026-09-08
Status: Superseded in part by 0005 (circumference-to-width ratio)

## Context

The original avatar drew a silhouette from balance-point *ratios*, so two
people with the same proportions but different absolute sizes rendered
identically — not actually to-scale.

## Decision

`web/src/lib/avatarGeometry.ts` draws the silhouette directly from real
`Measurements` (one shared cm-to-SVG scale for every width and length), not
from balance-point ratios. Circumferences convert to a front-view width via
an anthropometric ellipse approximation (originally ~10:7
circumference-to-width ratio — see 0005 for the correction). Neck/ankle
aren't measured inputs; they're drawn as a fixed proportion of shoulder/hip
width for visual completeness only.

## Consequences

Purely a rendering change — `balance_points.py`, `scoring.py`, and
`effects.yaml` untouched. The 10:7 (0.7) ratio was later found to be
roughly double a physically reasonable value and corrected in 0005.
