# Hourglass silhouette goal: ranked outfits + corrected overlay

## Context

`spec.md` restates the app's flow in four steps. The first three are
already fully built (stages 1-4 per `NOTES.md`'s "Build order — status"):
enter measurements → to-scale SVG silhouette
(`avatarGeometry.ts`/`Avatar.tsx`) → balance points shown as
balanced/notable (`BalancePointsChart.tsx`). The fourth step is new:

> app proposes some common silhouettes to recreate (user can choose one)
> and app draws dotted lines above the user's silhouette to show corrected
> silhouette and propose outfit combos to recreate it (and show them as a
> simple drawing)

Clarified with the user: start with a single target silhouette,
**hourglass** (not a multi-option catalog); represent proposed outfit
combos with a generic per-slot pictogram, not per-item art; the new
"target silhouette" UI coexists with the existing manual per-slot
picker/"Score outfit" flow rather than replacing it.

This turns out to be almost entirely a presentation/ranking-layer feature,
same category as the existing "Garment catalog" and "Outfit
recommendations" `NOTES.md` sections — it reuses `scoring.score()`
unchanged and only re-aggregates its already-computed per-axis
`Reason.contribution` output differently for ranking. It does **not**
touch `balance_points.py`, `effects.yaml`, or `scoring.py`, so per
`CLAUDE.md`'s workflow rule it does not need a new `docs/decisions/` file
— only a new `NOTES.md` section, matching that precedent. It also
respects the standing rule that shape categories never drive scoring:
"hourglass" here is just a fixed, named subset of two *existing* axes
(`waist_definition`, `top_hip_balance`) used only to re-sort already-scored
candidates — `scoring.score()`'s recommendation/verdict logic is
untouched.

An hourglass read = a defined waist + a balanced top vs. hip, so the
target maps onto exactly the two axes that already drive
`defines_waist`/`clings_to_waist`/`hides_waist` (`waist_definition`) and
`adds_volume_top`/`adds_volume_bottom` (`top_hip_balance`) in `scoring.py`'s
`AXIS_RULES` — no new axis, no new effect tag.

## Backend

**`src/fit_balance/recommend.py`** — small refactor, extract the
enumerate+score loop already in `recommend_outfits()` into a private
`_score_all_combinations(balance_points) -> list[OutfitRecommendation]`
helper, so the new hourglass ranking can reuse it instead of duplicating
the loop. `recommend_outfits()`'s public signature/behavior is unchanged.

**`src/fit_balance/silhouettes.py`** (new file) — the "hourglass" target
only, not a generic multi-silhouette framework (no product surface needs
more than one yet, per the user's steer):

```python
HOURGLASS_AXES = frozenset({"waist_definition", "top_hip_balance"})

def recommend_outfits_for_hourglass(
    balance_points: WomensBalancePoints, limit: int = 5
) -> list[OutfitRecommendation]:
    """Same candidates as recommend_outfits(), re-sorted by how much of
    the total score comes from hourglass-relevant axes only, instead of
    total verdict.score."""
```

Reuses `recommend.py`'s `_score_all_combinations()` and
`OutfitRecommendation` (items + verdict) unchanged — no new dataclass
field needed; the "helps" tags for the frontend overlay come from
`verdict.reasons` filtered to `direction == "+"`, exactly like the
existing manual-outfit overlay already does.

**`api/main.py`** — extend `RecommendOutfitsRequest` with
`silhouette: Literal["hourglass"] | None = None`. In
`recommend_outfits_endpoint`, branch to `recommend_outfits_for_hourglass`
when set, else the existing `recommend_outfits`. `RecommendOutfitsResponse`
is reused unchanged — no new response shape.

**Tests**:
- `tests/test_silhouettes.py` (new) — a worked-style case using or adapting
  `tests/fixtures.py`'s `RECTANGLE_LONG_TORSO_PETITE` (undefined waist:
  `waist_definition` ≈ 0.06, below the 0.15 threshold) or a new tailored
  fixture: assert `recommend_outfits_for_hourglass` ranks a waist-defining
  item above a candidate that scores higher on unrelated axes
  (`frame_scale_dev`/`torso_leg_balance`) but does nothing for
  `waist_definition`/`top_hip_balance` — proving the re-ranking is real,
  not just `recommend_outfits` under another name.
- Extend `tests/test_api.py` for the new `silhouette` request field
  (omitted → unchanged behavior; `"hourglass"` → hourglass-ranked
  response).

**`NOTES.md`** — new section "Silhouette goal (hourglass), v1" alongside
the existing "Outfit recommendations" section, documenting: what
"hourglass" maps to (`waist_definition` + `top_hip_balance`), that it's
presentation/ranking-layer only (`scoring.py` untouched, so no
`docs/decisions/` entry — same precedent as the garment catalog and
recommend-outfits sections), and that it's deliberately a single hardcoded
target for v1, not a generic catalog — more targets are a future,
deliberate addition.

## Frontend

**`web/src/lib/api.ts`** — add an optional `silhouette` param to
`recommendOutfits()`, passed through to the request body.

**`web/src/lib/types.ts`** — add `silhouette?: 'hourglass'` to whatever
request type backs it (inline in `api.ts` today, no dedicated request
type file to change beyond that call site).

**`web/src/App.tsx`**:
- Add a checkbox "Target: Hourglass silhouette" next to the existing
  "Recommended for you" `fieldset`. Toggling it re-runs the existing
  debounced `recommendOutfits()` effect with `silhouette: 'hourglass'`,
  and swaps the fieldset legend text (e.g. "Recommended for hourglass").
  The manual per-slot picker and "Score outfit" button are untouched —
  this coexists as a second, independent input, exactly as clarified.
- Overlay precedence for `Avatar`'s `effectTags`: keep today's behavior
  (manually-scored `result.verdict.reasons`) when a manual outfit has been
  scored; when the hourglass toggle is on and no manual `result` exists
  yet, fall back to the top hourglass recommendation's positive reasons
  (`recommendations.recommendations[0]`) — the same "+"-direction-tag
  derivation already used for the manual flow, just sourced from the
  ranked list instead of a submitted form. This is what produces the
  "dotted lines above the user's silhouette to show corrected silhouette"
  from spec.md without any new overlay mechanism — `Avatar.tsx` and
  `avatarGeometry.ts`'s `applyEffectAdjustments()`/`EFFECT_WIDTH_ADJUSTMENTS`
  are reused unchanged.
- Render each recommendation's outfit combo as a row of small per-slot
  pictograms instead of (or alongside) today's plain label text — needs
  each `item_id`'s `slot`, which isn't on `RecommendedOutfit` today but is
  already available client-side from the already-fetched `GarmentSummary[]`
  (`/garments`, which has `.slot`): build a `slotById` lookup the same way
  `labelById` is already built, no backend change needed for this part.

**`web/src/components/SlotIcon.tsx`** (new) — one small inline-SVG
pictogram per `Slot` (`dress`/`top`/`bottom`/`outerwear`), simple enough
to match the avatar's existing minimal line-drawing style (same stroke
colors as `Avatar.tsx` for visual consistency). Reused across every item
in that slot, per the user's "generic per-slot pictogram" choice — no
per-item art.

**Styling** — small additions to `web/src/App.css` for the toggle
checkbox and the pictogram row layout; no broader restyle.

## Verification

- `uv run pytest` — new `tests/test_silhouettes.py` and the extended
  `tests/test_api.py` case green, full existing suite (5 worked examples
  included) still green.
- `uv run ruff check .`
- `npx vitest run` from `web/` — if any new frontend unit tests are added
  for the `slotById` lookup or icon selection logic.
- `npx tsc --noEmit` from `web/`.
- Manually run the app (`uv run fastapi dev api/main.py` +
  `npm run dev` in `web/`): confirm the hourglass toggle changes the
  "Recommended for you" ranking and legend, the avatar's dashed overlay
  appears once the toggle is on (even before manually scoring an outfit),
  and each recommended combo shows per-slot pictograms. Confirm the
  existing manual picker/"Score outfit" flow still works exactly as
  before, including its own overlay taking precedence when used.
- `./check.sh` before calling this done, per `CLAUDE.md`.
