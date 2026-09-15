# Per-dimension technique recommendations with garment examples

## Context

Explored in conversation: instead of scoring/ranking full outfit
*combinations* (today's `recommend_outfits()`, which forces a single
combined verdict across differently-scaled axes — the source of all the
`main_concern()`/normalization complexity discussed but never shipped),
answer a simpler, more directly useful question per body: for each of the
4 scored dimensions, which garment *techniques* would help, which would
hurt, and which real catalog items use them? Verified by hand against the
pear/fuller body and confirmed as the direction to build.

This needs **zero engine changes** — it's a new read-only query layer over
`balance_points.py`'s output, `scoring.py`'s `AXIS_RULES`/`EFFECTS_TABLE`,
and `garments.py`'s catalog, all unchanged. No new axis, no new effect
tag, no formula change — same "presentation/query layer, no
`docs/decisions/` entry needed" precedent as `recommend.py` and
`garments.py`'s catalog work (see `NOTES.md`'s "Outfit recommendations"
section).

**Why this sidesteps everything we were stuck on**: within one axis,
summing/comparing is always safe (same units). The entire cross-axis
problem only exists when *combining* axes into one number. This feature
never combines axes — each of the 4 dimensions is reported completely
independently, so there's nothing to normalize, no ties to break, no
"main" axis to pick.

**A useful structural fact, confirmed by re-reading `AXIS_RULES`**: every
tag sharing an axis also shares that axis's `reference` (e.g. all 3
`waist_definition` tags use `reference=0.15`; all `torso_leg_balance`
tags use the default `0.0`). So a dimension's severity level only needs
computing **once per axis**, not once per tag — which tag lands in
"seek" vs "avoid" is purely a function of that tag's `weight` sign vs the
level's sign. If the level is `0` (axis inside its deadzone), *every* tag
on that axis is empty on both sides — which is exactly how "no strong
trait" for `torso_leg_balance` fell out for the pear body, with no
special-casing needed.

## Design

**New module: `src/fit_balance/technique_advice.py`**

```python
DIMENSIONS: tuple[tuple[str, str], ...] = (
    ("waist_definition", "Waist definition"),
    ("top_hip_balance", "Horizontal balance"),
    ("torso_leg_balance", "Vertical proportion"),
    ("frame_scale_dev", "Frame scale"),
)

@dataclass(frozen=True)
class TechniqueExample:
    tag: str
    direction: Literal["+", "-"]
    items: list[GarmentItem]

@dataclass(frozen=True)
class DimensionAdvice:
    axis: str
    label: str
    value: float
    recommendations: list[TechniqueExample]  # empty both sides -> "no strong trait"

def recommend_techniques(balance_points: WomensBalancePoints) -> list[DimensionAdvice]:
    advice = []
    for axis, label in DIMENSIONS:
        value = _axis_value(balance_points, axis)  # reused from scoring.py, handles top_hip_balance's max()
        tags_on_axis = [(tag, rule) for tag, rule in AXIS_RULES.items() if rule.axis == axis]
        level = signed_level(value, tags_on_axis[0][1].reference, axis) if tags_on_axis else 0
        recs = []
        for tag, rule in tags_on_axis:
            if rule.weight * level == 0:
                continue
            direction = "+" if rule.weight * level > 0 else "-"
            items = [item for item in list_items() if any(tag in EFFECTS_TABLE.get(t, []) for t in item.techniques)]
            if items:
                recs.append(TechniqueExample(tag=tag, direction=direction, items=items))
        advice.append(DimensionAdvice(axis=axis, label=label, value=value, recommendations=recs))
    return advice
```

**Small, pre-existing cleanup this needs**: `scoring.py`'s `_signed_level`
is currently private (underscore-prefixed) since only `scoring.score()`
used it. This module needs the same level logic — rather than duplicate
it a third time, rename it to a public `signed_level` in `scoring.py`
(pure rename, zero behavior change, no test impact) and import it here.
`_axis_value` gets the same treatment (needed for `top_hip_balance`'s
`max()` derivation).

**Item lookup reuses the exact pattern `garments.attribute_reasons()`
already uses** ("which items have a technique producing this tag"), just
inverted (asked of the whole catalog, not a specific outfit's items) —
no new matching logic invented.

**API — new endpoint, `api/main.py`**:
```python
class TechniqueExampleResponse(BaseModel):
    tag: str
    direction: Literal["+", "-"]
    items: list[GarmentSummary]  # reuses existing id/label/slot shape, no techniques exposed

class DimensionAdviceResponse(BaseModel):
    axis: str
    label: str
    value: float
    recommendations: list[TechniqueExampleResponse]

class TechniqueRecommendationsRequest(BaseModel):
    measurements: Measurements

class TechniqueRecommendationsResponse(BaseModel):
    balance_points: dict[str, float]
    dimensions: list[DimensionAdviceResponse]

@app.post("/technique-recommendations", response_model=TechniqueRecommendationsResponse)
```
Deliberately **no `main_concern` field** on this response — including a
"which axis matters most" ranking would contradict the whole point of
this feature (independent dimensions, no cross-axis winner). `balance_points`
stays, for transparency/debugging, same as every other endpoint already exposes.

**Frontend — new component, `web/src/components/DimensionAdvice.tsx`**,
rendered as a new section (e.g. "What to look for") using the debounced
measurement-change pattern `App.tsx` already has for
`recommendOutfits()`. Each dimension renders its label, a "seek"
list and an "avoid" list of item labels (plain text for v1 — no new
pictogram work; that idea from the earlier, unimplemented hourglass-
feature sketch (`spec_plan.md`) is a separate, not-yet-decided piece,
not bundled into this). A dimension with empty `recommendations` renders
as "no strong trait — most techniques here are neutral for you," matching
the pear-example wording already validated in conversation.

## Files

**New:** `src/fit_balance/technique_advice.py`,
`tests/test_technique_advice.py`, `web/src/components/DimensionAdvice.tsx`.

**Changed:**
- `src/fit_balance/scoring.py` — rename `_signed_level`→`signed_level`,
  `_axis_value`→`axis_value` (both pure renames)
- `api/main.py` — new request/response models + `/technique-recommendations` endpoint
- `web/src/lib/api.ts`/`types.ts` — new `getTechniqueRecommendations()` call + response types
- `web/src/App.tsx` — new debounced fetch + render section
- `NOTES.md` — new section (same style as "Outfit recommendations" — no
  `docs/decisions/` entry, since no engine file changes)

## Tests

`tests/test_technique_advice.py`, anchored on `PEAR_FULLER` (already
hand-verified in conversation) as the primary case:
- `waist_definition` dimension: `defines_waist`/`clings_to_waist` in
  "seek" (with `belted_*`/`sheath_dress`/`belted_sheath_dress` items),
  `hides_waist` in "avoid" (with `oversized_top`/`oversized_jacket`/`bomber_jacket`)
- `top_hip_balance` dimension: `adds_volume_top` in "seek" (same 3
  oversized items), `adds_volume_bottom` in "avoid" (`wide_leg_*` items)
- **Explicitly assert the same item (`oversized_top`) appears in both a
  "seek" list (horizontal balance) and an "avoid" list (waist definition,
  frame scale) for this one body** — pinning the trade-off-surfacing
  behavior as a feature, not a bug
- `torso_leg_balance` dimension: empty `recommendations` (pear's
  `torso_leg_balance` is exactly `0.0`, inside the deadzone)
- API test for `/technique-recommendations`

## Verification

`uv run pytest`, `uv run ruff check .`, `./check.sh`, manual check: load
the web app, confirm the new section renders and updates as measurements
change, matching the hand-verified pear-body output already validated in
conversation.
