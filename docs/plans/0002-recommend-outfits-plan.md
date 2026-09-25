# 0002. Outfit recommendations: ranking layer over the existing outfit scoring

Date: 2026-09-10
Status: Shipped — see NOTES.md "Outfit recommendations"

## Context

fit-balance can already *score* one outfit a user manually assembles
(`POST /score-outfit`, one item per slot from the hand-curated catalog in
`garments.yaml`) against their balance points. What it can't do yet is tell
the user which outfits — out of everything in the catalog — actually work
best for them, without guessing and checking combinations by hand.

This is presentation-layer work sitting on top of the existing, untouched
scoring engine — exactly like the original outfit-catalog feature
(`garment_catalog_plan.md`): enumerate candidate outfits, score each with
`scoring.score()` unchanged, rank them. It does not touch `balance_points.py`,
`scoring.py`, or `effects.yaml`, so per `CLAUDE.md`'s workflow rules it does
not need a new `docs/decisions/` entry — only a `NOTES.md` update, matching
how the original catalog feature was documented.

Confirmed with the user:
- Valid outfit shapes to enumerate: **dress XOR (top + bottom)**, with
  **outerwear optional** on either branch. Top-alone, bottom-alone, and
  top+dress/bottom+dress are invalid and must not be enumerated.
- Surface: both a new API endpoint and a new web UI panel.
- Ranking: top 5, simple sort by `verdict.score` descending, no
  dedup/near-duplicate suppression — v1-simplicity, consistent with the
  already-accepted tag-overlap additive-stacking behavior in
  `resolve_outfit()`.

With the current catalog (4 dress / 4 top / 6 bottom / 4 outerwear items)
this enumerates to exactly 140 candidate outfits (4 dresses × 5
outerwear-options, plus 4 tops × 6 bottoms × 5 outerwear-options) — cheap
enough to score fresh per request with a plain nested loop, no caching.

## Approach

### 1. New: `src/fit_balance/recommend.py`

Kept separate from `garments.py` (which owns "resolve the one outfit the
caller already picked") so "enumerate + rank all valid outfits" gets its own
file, mirroring the existing `garments.py` (catalog) / `scoring.py` (engine)
split.

- `enumerate_outfit_combinations() -> list[list[str]]` — all valid item-id
  combinations (dress ± outerwear, or top+bottom ± outerwear), built from
  `garments.list_items()` filtered by slot. Each returned list feeds
  straight into `garments.resolve_outfit()` — the same `item_ids` contract
  `/score-outfit` already uses.
- `OutfitRecommendation` (frozen dataclass): `items: list[GarmentItem]`,
  `verdict: Verdict`.
- `recommend_outfits(balance_points: WomensBalancePoints, limit: int = 5) ->
  list[OutfitRecommendation]` — scores every combination via
  `garments.resolve_outfit()` + `scoring.score()` (both unchanged), sorts by
  `verdict.score` descending, returns the top `limit`. Takes balance points
  rather than raw `Measurements` so a caller that already computed them
  (the API endpoint, which also needs `main_concern()`) doesn't pay for it
  twice.

### 2. Edit: `api/main.py`

Additive only — `/score`, `/score-outfit`, `/garments` and their
models/tests stay exactly as-is.

- New models: `RecommendOutfitsRequest` (`measurements`, `limit: int =
  Field(default=5, ge=1)`), `RecommendedOutfit` (`item_ids: list[str]`,
  `labels: list[str]`, `verdict: OutfitVerdict` — reusing the existing
  `OutfitVerdict`/`AttributedReason` types from `/score-outfit`, never raw
  technique keys), `RecommendOutfitsResponse` (`balance_points`,
  `main_concern`, `recommendations: list[RecommendedOutfit]`)
- New endpoint: `POST /recommend-outfits` — computes balance points once,
  calls `recommend.recommend_outfits(balance_points, limit=request.limit)`,
  and for each result calls the existing `attribute_reasons()` before
  building the response. `balance_points`/`main_concern` are computed once
  and shared at the top level of the response (never per-recommendation) —
  neither depends on the outfit, only on `measurements`.

### 3. Edit: `web/src/lib/types.ts`

Add `RecommendedOutfit` (`item_ids: string[]`, `labels: string[]`,
`verdict: OutfitVerdict`) and `RecommendOutfitsResponse`
(`balance_points`, `main_concern`, `recommendations:
RecommendedOutfit[]`). Leave existing types untouched.

### 4. Edit: `web/src/lib/api.ts`

Add `recommendOutfits(measurements, limit = 5)` (POST
`/recommend-outfits`), matching `scoreOutfit`'s existing shape/error
convention.

### 5. Edit: `web/src/App.tsx`

- Add `recommendations`, `recommendLoading`, `recommendError` state.
- Debounced (500ms) `useEffect` keyed on `measurements` calls
  `recommendOutfits()` — independent of the existing manual slot-picker /
  "Score outfit" submit button, since recommendations depend only on
  measurements and gating them behind item selection would hide the exact
  feature meant to help pick items in the first place.
- New "Recommended for you" section rendered alongside the existing manual
  picker: for each `RecommendedOutfit`, `labels.join(' + ')`, a verdict
  badge reusing the existing `RECOMMENDATION_LABEL`/`verdict-${recommendation}`
  pattern, and the score.

### 6. New: `tests/test_recommend.py`

Mirrors `recommend.py`, same pattern as `test_garments.py`:
- `enumerate_outfit_combinations()` returns exactly 140 combos for the
  current catalog, and every combo is one of the valid shapes (never
  top-alone/bottom-alone/top+dress/bottom+dress).
- `recommend_outfits()` results are sorted by `verdict.score`
  non-increasing.
- `recommend_outfits()` respects `limit`, including `limit` larger than 140
  (returns all 140, no error).
- A worked-example-grounded case using `HOURGLASS_BALANCED` (worked example
  1: `sheath_bodycon` + `belted_natural_waist` → recommended): compute the
  expected score directly via `scoring.score()` on that technique list (not
  a hardcoded number) and assert the top-ranked recommendation's score
  matches it, confirming empirically which catalog item is actually the top
  pick for that body.

### 7. Edit: `tests/test_api.py`

Add (without touching existing tests): `POST /recommend-outfits` returns
200 with results sorted descending; `limit` param is respected; `limit=0`
→ 422.

### 8. Edit: `NOTES.md`

New subsection immediately after "Garment catalog (manual, v1 — explicitly
not stage 5/6)" — **"Outfit recommendations (ranking layer, v1)"** —
describing what `recommend.py` does, that it's presentation-layer work with
no engine changes, the 140-combination count, and `POST
/recommend-outfits`. No new `docs/decisions/` file, per the same precedent
as the garment-catalog feature.

## Risks (accepted, documented — not blocking)

- **No dedup/near-duplicate suppression across the top 5** — e.g. the same
  top paired with 5 different outerwear items could plausibly fill the
  whole list. Accepted as v1-simplicity per the confirmed scope; revisit
  only if real usage shows this producing an unhelpful list.
- **Frontend has no dedicated test for the new panel or `recommendOutfits()`**
  — matches this repo's existing precedent (no component-level tests, and
  `scoreOutfit`/`getGarments` also have no dedicated frontend tests); only
  pure helpers get test files here.

## Verification

- `uv run pytest` — all existing suites (worked examples in
  `test_balance_points.py`/`test_scoring.py`, `test_garments.py`,
  `test_api.py`) stay green, plus new `test_recommend.py` and new
  `test_api.py` cases.
- `uv run ruff check .`
- From `web/`: `npx tsc --noEmit -p .` and `npx vitest run`.
- `./check.sh` from repo root — the single gate covering all of the above.
- Manually run the API (`uv run uvicorn api.main:app --port 8000`) and web
  dev server (`npm run dev` from `web/`); confirm the "Recommended for you"
  panel populates within ~0.5s of entering measurements, shows plausible
  ranked outfits with correct verdict badges, and updates independently of
  the manual picker. Spot-check `POST /recommend-outfits` directly to
  confirm the JSON never leaks raw technique keys.
