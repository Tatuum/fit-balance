# Phase 2 — Effects table & scoring engine

Turns a body's balance points (phase 1) plus a garment's techniques
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
The first 7 techniques back the 5 CURRENT_STATE.md worked examples; everything
added after that backs the manual garment catalog (see CURRENT_STATE.md's
"Garment catalog" section) — new techniques since then (`high_rise`,
`structured_shoulder`, `scoop_neck`, etc.) all reuse existing tags
except `narrows_shoulder` (decision
[0013](../adr/0013-narrows-shoulder-effect.md)).

A tag can exist in `effects.yaml` without a scoring rule — `AXIS_RULES`
just won't have an entry for it, and `score()` silently skips it. That's
deliberate for `clings_to_hip`: it's a known fact about a technique that
isn't wired into scoring yet (CURRENT_STATE.md's "known gaps" — it doesn't yet
distinguish hip-clinging, usually fine, from waist-clinging, bad for an
undefined waist).

### 3. `AXIS_RULES` — wiring a tag to a balance-point axis

```python
@dataclass(frozen=True)
class _AxisRule:
    axis: str
    weight: int
```

Each entry says: which balance-point axis this tag interacts with, and
its sign (`weight`: does this tag help when the axis's quantized level
is positive or negative). There's no per-tag reference point anymore —
decision [0015](../adr/0015-quantized-main-concern.md) moved
quantization (including `waist_definition`'s `0.15` reference)
upstream into `balance_points.py`, so the reference has already been
applied by the time `score()` reads an axis's level.

```python
AXIS_RULES = {
    "defines_waist":   _AxisRule(axis="waist_definition", weight=1),
    "clings_to_waist": _AxisRule(axis="waist_definition", weight=1),
    "hides_waist":     _AxisRule(axis="waist_definition", weight=-1),
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

`waist_definition`'s tags still only score once there's a waist worth
talking about — CURRENT_STATE.md's formula comment ("~0/− = no natural
cinch") implies the practically meaningful cinch threshold sits above
literal zero — but that `0.15` reference now lives in
`balance_points.AXIS_REFERENCE`, not here.

`top_hip_balance` isn't a stored `WomensBalancePoints` field. There are
two parallel helpers for it — one raw, one quantized:

```python
def axis_value(balance_points, axis):
    if axis == "top_hip_balance":
        return max(balance_points.shoulder_hip_balance, balance_points.bust_hip_balance)
    return getattr(balance_points, axis)


def axis_level(quantized, axis):
    if axis == "top_hip_balance":
        return max(quantized.shoulder_hip_balance, quantized.bust_hip_balance)
    return getattr(quantized, axis)
```

`axis_value()` is the raw float — display only (e.g.
`technique_advice.DimensionAdvice.value`), not read by `score()`
anymore. `axis_level()` is the quantized equivalent `score()` actually
reads, against a `QuantizedBalancePoints` computed once per body by
`balance_points.quantize()` rather than recomputed per tag. Taking the
`max()` of the two axes' *already-quantized* levels gives the same
result as quantizing their raw `max()` — `quantize_axis()` is
monotonic and both source axes share the same deadzone/reference
treatment (verified against all 5 worked examples, decision
[0015](../adr/0015-quantized-main-concern.md)).

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

### 4. Quantization happens upstream, in `balance_points.py`

`scoring.py` used to have its own `signed_level()` doing deviation →
severity-level quantization per tag. Decision
[0015](../adr/0015-quantized-main-concern.md) moved that logic
(renamed `quantize_axis()`) to `balance_points.py` as the single
shared basis both `WomensBalancePoints.main_concern()` and `score()`
below compare against — see
[phase1-balance-points.md](phase1-balance-points.md)'s section 4 for
how it buckets a deviation into `-2, -1, 0, 1, or 2`, including the
deadzone and `waist_definition`'s reference-point exception.

`score()` now calls `balance_points.quantize()` once per body to get a
`QuantizedBalancePoints`, then reads each tag's already-quantized
level via `axis_level()` (above) instead of recomputing a deviation
per tag against a reference pulled off `AXIS_RULES`.

### 5. `score()` — putting it together

```python
def score(balance_points, garment) -> Verdict:
    quantized = quantize(balance_points)
    reasons = []
    for technique in garment.techniques:
        for tag in EFFECTS_TABLE.get(technique, []):
            rule = AXIS_RULES.get(tag)
            if rule is None:
                continue
            contribution = rule.weight * axis_level(quantized, rule.axis)
            if contribution == 0:
                continue
            reasons.append(Reason(tag=tag, axis=rule.axis,
                                   contribution=contribution,
                                   direction="+" if contribution > 0 else "-"))

    reasons.sort(key=lambda r: abs(r.contribution), reverse=True)
    total = sum(r.contribution for r in reasons)
    ...
```

`balance_points.quantize()` runs once per body. For every technique on
the garment, look up its effect tags, look up each tag's axis rule,
read that axis's already-quantized level, and multiply by the rule's
weight. Zero contributions (deadzone, or no rule for that tag) are
dropped — they'd just be noise in the reasons list. Reasons are sorted
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

`tests/test_scoring.py` re-asserts the same 5 CURRENT_STATE.md worked examples
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
  layer (a later phase), where it's treated as intentional
  stacking — see CURRENT_STATE.md's "Garment catalog" section.
- `clings_to_hip` has no `AXIS_RULES` entry — a known, deliberately
  unscored fact (see "The effects table" above and CURRENT_STATE.md's "known
  gaps").
