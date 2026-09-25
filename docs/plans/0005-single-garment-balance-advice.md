# 0005. Single-garment "try it on" balance advice

Date: 2026-09-14
Status: Shipped — see NOTES.md "Single-garment balance advice"

## Context

Right now the web app only ever answers "given my measurements, which
techniques generally help/hurt me" (`/technique-recommendations`, the
"Horizontal balance" etc. cards) — it never lets someone pick a *specific*
garment they're considering and see (a) what that one item actually does
to their silhouette, and (b) what else (in a different slot) would offset
whatever it hurts. NOTES.md explicitly names two *related but different*
deferred/existing features — a single-item *replacement* suggestion
("recommending a specific replacement item is explicitly deferred") and
full *outfit* recommendation (`recommend.py`, already built) — but this
"keep the item, complement it" middle case doesn't exist yet anywhere
(backend or frontend). Confirmed via two research passes: the scoring
engine (`resolve_outfit`/`score`) already works correctly for a single
catalog item with zero changes needed, and `technique_advice.py`'s
`recommend_techniques()` already computes, per axis, "which catalog items
would help" — it's just never been cross-referenced against one specific
item's own negative reasons. No engine formula/axis change is involved
anywhere in this feature, so per CLAUDE.md's workflow rule this does **not**
need a `docs/decisions/` entry (same precedent already established by
`recommend.py`/`technique_advice.py`, both undocumented-by-decision
presentation-layer features built on the untouched scoring engine).

## Design

**Backend — new module `src/fit_balance/garment_balance.py`:**

```python
from dataclasses import dataclass, replace

from .balance_points import WomensBalancePoints
from .garments import GarmentItem, get_item, resolve_outfit
from .schemas import Verdict
from .scoring import score
from .technique_advice import DimensionAdvice, recommend_techniques


@dataclass(frozen=True)
class GarmentBalanceAdvice:
    item: GarmentItem
    verdict: Verdict
    suggestions: list[DimensionAdvice]


def suggest_balance(balance_points: WomensBalancePoints, item_id: str) -> GarmentBalanceAdvice:
    item = get_item(item_id)  # raises UnknownGarmentItemError, same as resolve_outfit
    _, garment = resolve_outfit([item_id])
    verdict = score(balance_points, garment)
    negative_axes = {r.axis for r in verdict.reasons if r.direction == "-"}

    suggestions = []
    for dimension in recommend_techniques(balance_points):
        if dimension.axis not in negative_axes:
            continue
        seek = [
            replace(rec, items=[i for i in rec.items if i.slot != item.slot])
            for rec in dimension.recommendations
            if rec.direction == "+"
        ]
        seek = [rec for rec in seek if rec.items]
        if seek:
            suggestions.append(replace(dimension, recommendations=seek))

    return GarmentBalanceAdvice(item=item, verdict=verdict, suggestions=suggestions)
```

Key design choice: `suggestions` reuses `technique_advice.DimensionAdvice`
wholesale (via `dataclasses.replace`, filtering `recommendations` down to
the item's own negative axes / "+"-direction / other-slot items only)
rather than inventing a new shape. This means:
- Zero new scoring/axis logic — `resolve_outfit`, `score`, and
  `recommend_techniques` are reused exactly as they already exist and are
  already tested.
- The API response and the frontend rendering can reuse the *existing*
  `DimensionAdviceResponse` / `DimensionAdvice.tsx` component wholesale for
  the "how to balance it" half — see below.
- `shoulder_hip_balance` (the axis `narrows_shoulder` scores against,
  decision 0013) is naturally skipped when it's the negative axis, since
  `recommend_techniques()`'s 4 `DIMENSIONS` never include it — no special
  casing needed, matches the documented gap in `technique_advice.py`.
- Filtering suggestions to `i.slot != item.slot` (not the full
  `enumerate_outfit_combinations()` valid-outfit-shape logic) is a
  deliberate v1 simplification — we're always suggesting one complementary
  item at a time, not re-deriving whole-outfit validity.

**API — `api/main.py`:**

```python
class BalanceGarmentRequest(BaseModel):
    measurements: Measurements
    item_id: str


class BalanceGarmentResponse(BaseModel):
    balance_points: dict[str, float]
    main_concern: str | None
    item: GarmentSummary
    verdict: Verdict          # reused directly from schemas, like /score does — single item, no attribution needed
    suggestions: list[DimensionAdviceResponse]


@app.post("/balance-garment", response_model=BalanceGarmentResponse)
def balance_garment_endpoint(request: BalanceGarmentRequest) -> BalanceGarmentResponse:
    balance_points = compute_womens_balance_points(request.measurements)
    try:
        advice = suggest_balance(balance_points, request.item_id)
    except UnknownGarmentItemError as exc:
        raise HTTPException(status_code=422, detail=f"Unknown garment item id: {exc}") from exc
    return BalanceGarmentResponse(
        balance_points=asdict(balance_points),
        main_concern=balance_points.main_concern(),
        item=GarmentSummary(id=advice.item.id, label=advice.item.label, slot=advice.item.slot),
        verdict=advice.verdict,
        suggestions=[_dimension_advice_response(d) for d in advice.suggestions],
    )
```

Factor the existing dimension→response conversion (currently inline inside
`technique_recommendations_endpoint`) into a small `_dimension_advice_response()`
helper and reuse it from both endpoints, rather than duplicating the
nested comprehension a second time.

**Backend tests — new `tests/test_garment_balance.py`**, following the
existing fixture-reuse convention (`tests/fixtures.py`):
- `structured_blazer` (outerwear, `adds_volume_top`) on `BROAD_SHOULDER_NARROW_HIP`
  (decision 0012/0013's fixture) → verdict `avoid`; suggestions has exactly
  one `DimensionAdvice` for `top_hip_balance` whose `recommendations`
  contains `adds_volume_bottom` with items drawn from non-outerwear slots
  (wide-leg trousers/skirts, a_line, peplum items).
- `scoop_neck_top` (top, `narrows_shoulder`) on `PEAR_FULLER` (shoulder
  narrower than hip → negative `shoulder_hip_balance` reason, verdict
  `avoid`) → suggestions is `[]`, proving the documented
  `shoulder_hip_balance`-not-in-`DIMENSIONS` gap degrades gracefully
  instead of erroring.
- An item with no negative reasons for a given body → suggestions `[]`.
- Unknown item id → raises `UnknownGarmentItemError`.

**API tests — extend `tests/test_api.py`**: a `/balance-garment` case
cross-checked against a direct `suggest_balance()` call (same
engine-vs-endpoint cross-check pattern the existing outfit-recommendation
API tests use), plus a 422-on-unknown-id case matching `/score-outfit`'s
existing test.

**Frontend:**

- `web/src/lib/types.ts`: add `BalanceGarmentResponse { balance_points,
  main_concern, item: GarmentSummary, verdict: Verdict, suggestions:
  DimensionAdvice[] }` (the `DimensionAdvice`/`TechniqueExample` interfaces
  already exist and are reused as-is).
- `web/src/lib/api.ts`: add `balanceGarment(measurements, itemId)` →
  `POST /balance-garment`, same fetch-wrapper pattern as the other five
  functions there.
- New `web/src/components/GarmentBalance.tsx`:
  - Fetches the catalog once on mount via the already-defined-but-unused
    `getGarments()`, grouped with the already-defined-but-unused
    `groupBySlot()`/`SLOTS` from `lib/garments.ts` — a `<select>` with one
    `<optgroup>` per slot (mirrors the picker UI structure from the removed
    per-slot picker, `git show 9251c23~1:web/src/App.tsx`, but single-select
    across the whole catalog instead of one radio-group per slot).
  - On `[measurements, selectedItemId]` change, debounced 500ms (same
    pattern as `App.tsx`'s existing technique-advice effect), calls
    `balanceGarment()`.
  - Renders a **second, self-contained** `<Avatar measurements
    effectTags={advice.verdict.reasons.map(r => r.tag)} />` — deliberately
    **all** reason tags, not just `direction === '+'` like the old removed
    picker did for a whole recommended outfit: this feature's point is
    showing the item's real effect, good and bad, not a curated "looks
    great" preview.
  - A verdict label (small local `RECOMMENDATION_LABEL` map, reusing the
    `verdict-${recommendation}` CSS-class convention + green/red hex values
    already used elsewhere in `App.css`) and a plain reasons list (tag +
    axis, via a small local `AXIS_LABELS` map — the 4 from
    `technique_advice.py`'s `DIMENSIONS` plus `shoulder_hip_balance`, since
    a `narrows_shoulder` reason can carry that axis and nothing else labels
    it anywhere today).
  - **Reuses the existing `<DimensionAdvice dimensions={advice.suggestions} />`
    component wholesale** for "how to balance it" — no new
    rendering logic needed; it naturally only ever shows the "seek" half
    since suggestions are pre-filtered to `direction === '+'`.
- `web/src/App.tsx`: render `<GarmentBalance measurements={measurements} />`
  in `.results`, below the existing `.technique-advice-section`.
- `web/src/App.css`: new classes for the select/section layout
  (`.garment-balance-section`, `.garment-balance-result`, `.reasons`,
  `.reason-positive`/`.reason-negative`), reusing the existing
  `#1a7f37`/`#c62828` green/red convention rather than inventing new colors.

**Explicitly not doing** (keep this scoped): no CLI support (the CLI has no
`--item` flag at all today, only raw `--technique` strings — a clean
follow-on later via the same `suggest_balance()`, not required now); no
combined "preview both items together" avatar (suggestions are informational
labels, not a second live scoring round); no re-derivation of full
outfit-shape validity for the "other slot" filter (see above).

**Docs**: add a short new NOTES.md section ("Single-garment balance
advice") after "Garment catalog", explaining current-state behavior and
explicitly distinguishing it from the two adjacent deferred/existing
features named above (mirrors how the "Outfit recommendations"/"Technique
recommendations" sections were added previously — no decision-doc link
needed since no engine change).

## Verification

- `uv run pytest tests/test_garment_balance.py tests/test_api.py -v` for
  the new/changed backend tests, then full `./check.sh` (pytest, ruff,
  `tsc --noEmit`, `vitest run`) before calling it done, per CLAUDE.md.
- Run the app end-to-end in a browser (`uv run fit-balance-api` /
  `uvicorn api.main:app --reload` + `npm run dev` in `web/`, or via the
  `run` skill): select a garment with a known negative reason for the
  default measurements (e.g. an oversized/structured item), confirm the
  avatar silhouette visibly shifts, the verdict/reasons render, and the
  "how to balance it" suggestions list real complementary items from other
  slots; also check an item with no negative reasons renders with no
  suggestions section, and that switching the garment or editing
  measurements updates everything reactively.
