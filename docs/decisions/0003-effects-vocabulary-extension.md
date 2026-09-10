# 0003. Extend effects vocabulary for new garment catalog items

Date: 2026-09-08
Status: Accepted

## Context

The v1 garment catalog (`garments.yaml`) started by deliberately reusing
only the original 7 `effects.yaml` technique keys. Adding 4 new catalog
items (rise/leg-width trousers, a bomber jacket) needed new techniques —
each addition should be deliberate about which existing effect tag it
reuses versus genuinely needing a new one, not a batch exercise.

## Decision

- `high_rise` → `elongates_leg` (reuses the existing tag).
- `low_rise` → `elongates_torso` + `shortens_leg` — the same tags
  `drop_waist` already uses, since a low rise sits below the natural waist
  the same way a dropped waist seam does.
- `wide_leg` → `adds_volume_bottom` — a genuinely new effect tag, wired into
  `AXIS_RULES` as the mirror image of `adds_volume_top` (same axis,
  opposite-sign weight): bottom volume helps a top-heavy build and works
  against an already bottom-heavy one.
- `cropped_ankle_length` → `shortens_leg`.
- `bomber_jacket` needed no new technique at all — it reuses `oversized_top`
  verbatim, since a bomber's boxy, bulk-adding silhouette is the same real
  effect that technique already models (the same reuse `oversized_jacket`
  already relied on).

## Consequences

`adds_volume_bottom` tested in
`test_scoring.py::test_adds_volume_bottom_mirrors_adds_volume_top_with_opposite_sign`.
Later revised by 0009 to score against `top_hip_balance` rather than
`bust_hip_balance` alone.
