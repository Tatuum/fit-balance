# 0016. Second garment vocabulary expansion

Date: 2026-10-07
Status: Accepted

## Context

The catalog still only covered the techniques needed for decisions 0001–0013
plus decision 0012's first realism pass. A second pass was requested to make
the catalog "richer" — more real garment-construction techniques, more
catalog items — without touching the scoring core itself.

## Decision

9 new technique keys added to `effects.yaml`, each reusing an existing
effect tag (no new `AXIS_RULES` entries, no new axes, no new thresholds):

```
cowl_neck       -> elongates_torso
halter_neck     -> narrows_shoulder
off_shoulder    -> adds_volume_top
fit_and_flare   -> defines_waist, adds_volume_bottom
corset_boned    -> defines_waist
maxi_length     -> elongates_leg
midi_length     -> shortens_leg
cape_silhouette -> adds_bulk
ruched_side     -> clings_to_waist
```

`fit_and_flare` is the first single technique to fire two tags on two
different axes at once (mirrors `peplum`'s existing tag pair, just from one
technique instead of one item combining two techniques).

8 new `garments.yaml` catalog items give every new technique a real
producer: `cowl_neck_top`, `off_shoulder_top`, `corset_top`,
`maxi_wrap_skirt` (`wrap_style` + `maxi_length`), `fit_and_flare_dress`,
`halter_midi_dress` (`halter_neck` + `midi_length`), `ruched_dress`,
`cape_coat`.

Two things deliberately left alone: `clings_to_hip` stays unscored (no
`AXIS_RULES` entry) — still the known gap from decision 0002, not addressed
here. `platform_sole` (shoe height) was considered and dropped — footwear
doesn't fit any of the 4 existing slots (top/bottom/dress/outerwear), and
adding a 5th slot is a schema change out of scope for a vocabulary pass.

## Consequences

`tests/test_garments.py` gains one new test
(`test_fit_and_flare_fires_two_tags_on_two_different_axes`, PEAR_FULLER:
`defines_waist` +1 and `adds_volume_bottom` -1 cancel to a net-zero,
`"neutral"` verdict). `tests/test_recommend.py`'s pinned combination count
goes from 474 to 826 (8 more catalog items shift `DRESS_COUNT`/`TOP_COUNT`/
`BOTTOM_COUNT`/`OUTERWEAR_COUNT`). `tests/test_technique_advice.py`'s pinned
per-tag producer-item sets gain the new items wherever a new technique
reuses a tag already exercised by PEAR_FULLER (`defines_waist`,
`clings_to_waist`, `adds_volume_top`, `adds_volume_bottom`, `adds_bulk`). No
existing worked-example verdict changes — all 5 `CURRENT_STATE.md` worked
examples stay byte-for-byte identical, confirmed via `./check.sh`.
