# Stage 2 — Effects table & scoring engine

Turns a body's balance points (stage 1) plus a garment's techniques
into a verdict: a recommendation label, a numeric score, and the
specific reasons that produced it. This is the layer that makes the
engine explainable — every verdict traces back to named effect tags,
not a black-box shape match.

**Files:** `src/fit_balance/effects.yaml`, `src/fit_balance/scoring.py`,
`src/fit_balance/schemas.py` (`GarmentAttributes`, `Reason`, `Verdict`),
`tests/test_scoring.py`

### 1. Input/output shape

A garment is just a list of technique keys:

```python
class GarmentAttributes(BaseModel):
    techniques: list[str]
```

`score()` returns a `Verdict`:

```python
class Verdict(BaseModel):
    recommendation: Literal["recommended", "neutral", "avoid", "strong_avoid"]
    score: int
    reasons: list[Reason]

class Reason(BaseModel):
    tag: str
    axis: str
    contribution: int   # weight * a severity level in {-2,-1,0,1,2}
    direction: str       # "+" if contribution > 0, "-" otherwise
```

`contribution` is a small discrete severity level, not a raw
balance-point value (decision
[0010](../adr/0010-discrete-severity-level-scoring.md)) — that's what
keeps reasons on different axes safely comparable when summed.

### 2. The effects table

`effects.yaml` maps a technique key to the effect tags it produces —
a fact about the technique, independent of who wears it:

```yaml
sheath_bodycon:
  - clings_to_waist
  - clings_to_hip

belted_natural_waist:
  - defines_waist

drop_waist:
  - elongates_torso
  - shortens_leg
```

`load_effects_table()` reads this into `EFFECTS_TABLE` at import time.
The first 7 techniques back the 5 NOTES.md worked examples; everything
added after that backs the manual garment catalog (see NOTES.md's
"Garment catalog" section) — new techniques since then (`high_rise`,
`structured_shoulder`, `scoop_neck`, etc.) all reuse existing tags
except `narrows_shoulder` (decision
[0013](../adr/0013-narrows-shoulder-effect.md)).

A tag can exist in `effects.yaml` without a scoring rule — `AXIS_RULES`
just won't have an entry for it, and `score()` silently skips it. That's
deliberate for `clings_to_hip`: it's a known fact about a technique that
isn't wired into scoring yet (NOTES.md's "known gaps" — it doesn't yet
distinguish hip-clinging, usually fine, from waist-clinging, bad for an
undefined waist).

### 3. `AXIS_RULES` — wiring a tag to a balance-point axis

```python
@dataclass(frozen=True)
class _AxisRule:
    axis: str
    weight: int
    reference: float = 0.0
```

Each entry says: which balance-point axis this tag interacts with, its
sign (`weight`: does this tag help when the axis is positive or
negative), and the neutral point to measure deviation from
(`reference`, default `0.0`).

```python
AXIS_RULES = {
    "defines_waist":   _AxisRule(axis="waist_definition", weight=1, reference=0.15),
    "clings_to_waist": _AxisRule(axis="waist_definition", weight=1, reference=0.15),
    "hides_waist":     _AxisRule(axis="waist_definition", weight=-1, reference=0.15),
    "elongates_leg":   _AxisRule(axis="torso_leg_balance", weight=1),
    "shortens_torso":  _AxisRule(axis="torso_leg_balance", weight=1),
    "elongates_torso": _AxisRule(axis="torso_leg_balance", weight=-1),
    "shortens_leg":    _AxisRule(axis="torso_leg_balance", weight=-1),
    "reduces_bulk":    _AxisRule(axis="frame_scale_dev", weight=1),
    "adds_bulk":       _AxisRule(axis="frame_scale_dev", weight=-1),
    "adds_volume_top":    _AxisRule(axis="top_hip_balance", weight=-1),
    "adds_volume_bottom": _AxisRule(axis="top_hip_balance", weight=1),
    "narrows_shoulder":   _AxisRule(axis="shoulder_hip_balance", weight=1),
}
```

`waist_definition`'s tags use `reference=0.15` instead of `0.0`:
NOTES.md's formula comment ("~0/− = no natural cinch") implies the
practically meaningful cinch threshold sits above literal zero, so
"defines/clings/hides waist" only score once there's a waist worth
talking about.

`top_hip_balance` isn't a stored `WomensBalancePoints` field. It's
computed on demand by `axis_value()`:

```python
def axis_value(balance_points, axis):
    if axis == "top_hip_balance":
        return max(balance_points.shoulder_hip_balance, balance_points.bust_hip_balance)
    return getattr(balance_points, axis)
```

`adds_volume_top`/`adds_volume_bottom` care about whichever of
shoulder or bust actually reads wider against hip, not one specific
measurement — scoring only against `bust_hip_balance` would
recommend adding top volume onto an already-broad-shouldered build,
missing the case a broad shoulder alone creates. `narrows_shoulder` is
the one tag scored directly against `shoulder_hip_balance` instead:
a scoop neckline only helps a body whose top-heaviness comes from
broad shoulders specifically, not one that's top-heavy from bust with
balanced shoulders (decision
[0013](../adr/0013-narrows-shoulder-effect.md)).

### 4. `signed_level()` — quantizing a deviation into a severity level

```python
def signed_level(value, reference, axis) -> int:
    deviation = value - reference
    deadzone = IMBALANCE_DEADZONE if axis in _SCORING_DEADZONE_AXES else 0.0
    magnitude = abs(deviation)
    level = 0 if magnitude < deadzone else 1 if magnitude < PRONOUNCED_THRESHOLD else 2
    return level if deviation >= 0 else -level
```

Turns a raw axis deviation into `-2, -1, 0, 1, or 2` — sign-preserved.
`0` means "within the deadzone" (same `IMBALANCE_DEADZONE = 0.05` stage
1's `main_concern()` uses, plus `top_hip_balance` added to that
deadzone set); `1` is "notable," `2` is "pronounced" once magnitude
clears `PRONOUNCED_THRESHOLD = 0.15`. `waist_definition` isn't in the
deadzone axis set, so it gets no deadzone here either — same reasoning
as decision [0007](../adr/0007-imbalance-deadzone.md): it's a
favorable-direction threshold, not "0 is neutral both ways."

### 5. `score()` — putting it together

```python
def score(balance_points, garment) -> Verdict:
    reasons = []
    for technique in garment.techniques:
        for tag in EFFECTS_TABLE.get(technique, []):
            rule = AXIS_RULES.get(tag)
            if rule is None:
                continue
            value = axis_value(balance_points, rule.axis)
            contribution = rule.weight * signed_level(value, rule.reference, rule.axis)
            if contribution == 0:
                continue
            reasons.append(Reason(tag=tag, axis=rule.axis,
                                   contribution=contribution,
                                   direction="+" if contribution > 0 else "-"))

    reasons.sort(key=lambda r: abs(r.contribution), reverse=True)
    total = sum(r.contribution for r in reasons)
    ...
```

For every technique on the garment, look up its effect tags, look up
each tag's axis rule, compute that axis's severity level against the
body's balance points, and multiply by the rule's weight. Zero
contributions (deadzone, or no rule for that tag) are dropped —
they'd just be noise in the reasons list. Reasons are sorted
strongest-first so the most decisive factors surface at the top of a
verdict.

`total` (the sum of all contributions) maps to a recommendation via
three thresholds:

```python
RECOMMENDED_THRESHOLD = 1
AVOID_THRESHOLD = -1
STRONG_AVOID_THRESHOLD = -3
```

`total >= 1` → `"recommended"`; `total <= -3` → `"strong_avoid"`;
`total <= -1` → `"avoid"`; otherwise `"neutral"`.

### Testing / verification

`tests/test_scoring.py` re-asserts the same 5 NOTES.md worked examples
as full verdicts (recommendation + score), one test per example. It
also separately pins threshold-boundary behavior (deadzone edge,
pronounced-threshold edge, `waist_definition`'s no-deadzone rule) and
a couple of specific axis-interaction cases (`adds_volume_bottom`
mirroring `adds_volume_top`, `clings_to_hip` staying a known-but-unscored
fact). Any change to `effects.yaml` or `scoring.py` must keep this
suite — and `tests/test_balance_points.py` — green.

### Gotchas / open questions

- `scoring.score()` doesn't dedupe reasons by tag: two different
  techniques producing the same effect tag both contribute that tag's
  axis weight, additively. Currently only observed at the garment-catalog
  layer (stage after this one), where it's treated as intentional
  stacking — see NOTES.md's "Garment catalog" section.
- `clings_to_hip` has no `AXIS_RULES` entry — a known, deliberately
  unscored fact (see "The effects table" above and NOTES.md's "known
  gaps").
