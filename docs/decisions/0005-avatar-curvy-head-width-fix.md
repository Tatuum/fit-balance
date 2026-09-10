# 0005. Avatar curvy silhouette, head, and circumference-to-width fix

Date: 2026-09-09
Status: Accepted

## Context

Three related issues in the 0004 avatar: (1) the outline was a straight-edged
polygon through the measurement keypoints, reading as a faceted schematic
rather than a body; (2) there was no head, so there was no visual reference
point for scale; (3) `WIDTH_FROM_CIRCUMFERENCE = 0.7` (the "~10:7" ratio from
0004) made the torso/hip nearly twice as wide as real proportions — treating
a cross-section as circular gives width ≈ circumference/π ≈ 0.318×, and even
accounting for a torso being wider than it is deep (elliptical, not
circular), a realistic factor is closer to ~0.32-0.35, not 0.7. The
oversized-torso effect was easy to miss without a head for scale reference;
adding one made the mismatch (tiny head, blocky wide torso) obvious.

## Decision

- Replace the straight-line outline with a closed Catmull-Rom spline through
  the same keypoints, converted to cubic Beziers.
- Add a head ellipse sized off total figure height (classic "7.5 heads
  tall" figure-drawing convention), sitting on the existing neck keypoint —
  not sized off shoulder width, which is itself inflated by the
  circumference conversion.
- Correct `WIDTH_FROM_CIRCUMFERENCE` from 0.7 to 0.32.

## Consequences

`web/src/lib/avatarGeometry.test.ts` updated to expect curve (`C`) commands
instead of line (`L`) commands, plus new tests for the head ellipse's
geometry and scale-invariance. Still purely a rendering change.
