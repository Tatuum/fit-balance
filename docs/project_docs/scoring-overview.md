# How scoring works

This walks through the scoring pipeline as implemented today. `NOTES.md` is
still the source of truth for architecture/rationale/known gaps — this file
is a companion explainer for the mechanics.

```
measurements → balance points → (garment techniques → effect tags) → scored reasons → verdict
```

## 1. Balance points (the "who") — `balance_points.py`

Five continuous signed axes, computed purely from measurements — no
"pear"/"hourglass" category anywhere in here, just floats:

```python
shoulder_hip_balance = (shoulder - hip) / max(shoulder, hip)
bust_hip_balance     = (bust - hip) / max(bust, hip)
waist_definition     = 1 - waist / avg(bust, hip)
torso_leg_balance     = (torso/height - 0.245) - (leg/height - 0.455)
frame_scale_dev       = avg(bust, waist, hip)/height - baseline
```

`torso_leg_balance` compares each of torso and leg to *its own* researched
baseline ratio-to-height first, then subtracts the two deviations — a raw
`(torso-leg)/max(...)` doesn't work because back-waist-length and inseam are
structurally different magnitudes on every body (see NOTES.md's "known
gaps" for the full story of that bug and fix).

Each axis has a sign convention (documented next to its formula in
NOTES.md). Magnitude tracks how far from neutral (0) the body reads on that
axis — bigger isn't "worse," just further from average.

## 2. Effects table (the "what a garment does") — `effects.yaml`

Maps a garment technique to the visual effects it produces, independent of
who wears it:

```yaml
sheath_bodycon:
  - clings_to_waist
  - clings_to_hip
```

Pure lookup table — no scoring happens here, just facts about the garment.

## 3. Axis rules (the "does this effect help or hurt this body") — `scoring.py`

`AXIS_RULES` is what actually connects the two: for each effect tag, which
balance-point axis it interacts with, a weight (+1 or -1), and a reference
point (default 0):

```python
"defines_waist": _AxisRule(axis="waist_definition", weight=1.0, reference=0.15),
"elongates_leg": _AxisRule(axis="torso_leg_balance", weight=1.0),
```

Not every tag in `effects.yaml` has a rule. `clings_to_hip` deliberately has
none — it's flagged as too coarse to score confidently (doesn't distinguish
hip-clinging, fine for most shapes, from waist-clinging, bad for an
undefined waist). `shoulder_hip_balance` isn't wired into any rule yet
either — it's measured and shown to the user, but no v0 garment technique
reacts to it. A tag/axis with no rule is a known fact, not yet scored.

## 4. Contribution math — `score()`

For each technique on the garment, for each effect tag it produces, if a
rule exists:

```python
value = getattr(balance_points, rule.axis)
contribution = rule.weight * (value - rule.reference)
```

This is the key design point: **contribution scales with distance from the
reference, not a flat +1/-1 category match.** Someone with
`waist_definition = 0.26` gets a stronger "defines waist" credit than
someone at `0.16` — both are above the 0.15 cinch threshold, but not
equally so. A zero contribution (exactly at reference) is dropped — it
didn't actually fire.

Each nonzero contribution becomes a `Reason` (tag, axis, contribution,
direction `+`/`-`), sorted by `abs(contribution)` descending so the
strongest reasons surface first.

## 5. Verdict — the total

```python
total = sum(r.contribution for r in reasons)
```

| total | recommendation |
|---|---|
| ≥ 0.1 | recommended |
| ≤ -0.3 | strong_avoid |
| ≤ -0.1 (and > -0.3) | avoid |
| otherwise | neutral |

The output isn't just the label — it's the label **plus every reason that
fired**. A garment can help on one axis and hurt on another at the same
time: worked example 5 (NOTES.md) has an oversized top score `+` on
`bust_hip_balance` and `-` on `frame_scale_dev` simultaneously, and both
show up as separate reasons rather than collapsing into one opaque number.

## Why this design

It's what makes the whole thing explainable rather than a black box:
`AXIS_RULES` and `effects.yaml` are the entire ruleset, in plain data you
can read and edit — nothing here is a trained model's opinion.
