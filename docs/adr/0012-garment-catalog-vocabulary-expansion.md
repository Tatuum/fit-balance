# 0012. Expand garment catalog with realistic garment types and techniques

Date: 2026-09-14
Status: Accepted

## Context

The v1 catalog (16 items, 11 techniques) covers only a narrow slice of real
garment-styling vocabulary — no A-line/pencil/wrap silhouettes, no
neckline or shoulder-construction effects, nothing that reacts to
`shoulder_hip_balance`. That last gap was already flagged in NOTES.md's
"Known gaps": `top_hip_balance` (decision
[0009](0009-top-hip-balance-axis.md)) feeds `adds_volume_top`, but no v0
technique ever produced that tag — `AXIS_RULES["adds_volume_top"]` has
existed as dead code since decision 0011 removed its only producer. Per
NOTES.md's "further vocabulary growth stays a case-by-case decision, not a
batch exercise," each addition below is justified individually, same
pattern as decision 0003.

## Decision

Seven new techniques, each reusing an existing `effects.yaml` tag (no
`scoring.py` or `AXIS_RULES` changes — this is a garments/effects-layer
change only):

- `structured_shoulder` (blazer with padded/built-up shoulders) →
  `adds_volume_top` — the first real producer of this tag. A structured
  shoulder line genuinely widens the top of the silhouette, the exact
  effect `adds_volume_top` was written to model.
- `puff_sleeve` (gathered/puffed sleeve) → `adds_volume_top` — a second,
  independent construction producing the same real effect; same
  technique/tag split precedent as `vertical_detail` and `skinny_straight`
  both producing `reduces_bulk`.
- `peplum` (peplum top/dress) → `defines_waist` + `adds_volume_bottom` — a
  peplum both cinches at the natural waist and flares fullness over the
  hip, classic advice for balancing a top-heavy build while showing waist
  definition.
- `wrap_style` (wrap top/dress) → `defines_waist` — ties and crosses at the
  natural waist, same real effect `belted_natural_waist` models via a
  different construction.
- `v_neck` (V neckline) → `elongates_torso` — draws the eye down the
  centre front, the same "makes the torso read longer" effect
  `drop_waist`/`low_rise` already model, via neckline instead of waist
  placement.
- `a_line` (A-line skirt/dress) → `adds_volume_bottom` — flares gently from
  waist to hem, the skirt/dress equivalent of `wide_leg` trousers.
- `pencil_skirt` (fitted straight through the hip) → `clings_to_hip` — the
  bottom-half analog of `sheath_bodycon`; deliberately not paired with
  `clings_to_waist` or `defines_waist` since a pencil skirt's fit story is
  about the hip line, not the waist.

Ten new catalog items in `garments.yaml` put these to use across all four
slots: `structured_blazer` (outerwear), `puff_sleeve_top` (top),
`peplum_top`/`peplum_dress` (top/dress), `wrap_top`/`wrap_dress`
(top/dress), `v_neck_top` (top), `a_line_skirt`/`a_line_dress`
(bottom/dress), `pencil_skirt` (bottom).

## Consequences

`test_catalog_covers_all_known_techniques` (exact-set equality between the
catalog's techniques and `EFFECTS_TABLE`) stays green since every new
technique gets at least one catalog item and vice versa. A new
`test_garments.py` case pins `structured_shoulder`/`adds_volume_top` firing
for a broad-shouldered/narrow-hip body — the first real (non-synthetic)
verdict to exercise that axis rule. `scoring.py`'s `adds_volume_top`
comment, which said "no current effects.yaml technique produces
adds_volume_top," and NOTES.md's shoulder-width known-gap note are both now
stale and updated alongside this change.
