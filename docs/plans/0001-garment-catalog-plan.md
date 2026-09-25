# 0001. Manual garment-item catalog + outfit scoring with attribution

Date: 2026-09-08
Status: Shipped — see NOTES.md "Garment catalog"

## Context

The web app currently exposes `effects.yaml`'s raw technique keys directly to
the user — `web/src/App.tsx`'s `KNOWN_TECHNIQUES` checkbox list renders
literal snake_case strings like `sheath_bodycon` as the garment picker, with
a code comment admitting this is a hand-sync hack ("there's no endpoint to
list known techniques yet, so this v0 duplicates the technique names by
hand"). The user doesn't want this internal vocabulary visible at all —
wants a picker of real garment names ("slim-fitted top", "oversized
jacket"), which resolve to technique(s) internally.

Beyond hiding the vocabulary, the user wants to select **several items at
once as an outfit** (a top + a bottom + a jacket, say) and see one combined
verdict for whether they work together, organized into **slots**
(top/bottom/dress/outerwear, one per slot). When the verdict has negative
reasons, the app should **point at which selected item is responsible** —
attribution only, not an automatic replacement suggestion (that's
explicitly deferred).

This is presentation-layer work sitting on top of the existing, untouched
scoring engine — not the deferred "stage 6: multi-garment outfit parsing"
(NOTES.md/`plan.md`), which is specifically about a CV pipeline parsing
garments from a photo plus a combination/matching layer, gated as
higher-risk. This feature is a hand-curated catalog with no photos, no CV —
it doesn't trigger that gate, but NOTES.md should say so explicitly since
it's adjacent territory.

Confirmed with the user: multi-item outfit (not one-item-at-a-time),
attribution-only for "what to replace" (no auto-suggested swap), items
organized into slots, and **one item per slot** (radio-style, not free
multi-select within a slot).

## Approach

Add a small catalog layer (`garments.yaml` + `garments.py`) that resolves
catalog item ids to the existing `GarmentAttributes` the engine already
understands, plus a post-processing attribution pass — `scoring.py`,
`schemas.py`, `effects.yaml`, and all 5 worked-example tests stay completely
untouched. New API endpoints and web UI sit on top.

### 1. New: `src/fit_balance/garments.yaml`

Dict keyed by item id, mirroring `effects.yaml`'s shape. ~14 items across
all 4 slots, reusing all 7 existing technique keys (no new techniques
needed for v1) — includes one intentional overlap (`vertical_detail` and
`skinny_straight` both produce `reduces_bulk`) so the "two items, same
effect tag" case is exercised on purpose:

```yaml
sheath_dress:        { label: Bodycon sheath dress,          slot: dress,     techniques: [sheath_bodycon] }
belted_sheath_dress: { label: Belted sheath dress,           slot: dress,     techniques: [sheath_bodycon, belted_natural_waist] }
empire_dress:        { label: Empire-waist dress,            slot: dress,     techniques: [empire_waistline] }
drop_waist_dress:    { label: Drop-waist dress,              slot: dress,     techniques: [drop_waist] }
oversized_top:       { label: Oversized top,                 slot: top,       techniques: [oversized_top] }
fitted_top:          { label: Slim-fitted top,                slot: top,       techniques: [skinny_straight] }
belted_blouse:       { label: Belted blouse,                  slot: top,       techniques: [belted_natural_waist] }
seamed_top:          { label: Top with vertical seam detail,  slot: top,       techniques: [vertical_detail] }
slim_trousers:       { label: Slim straight-leg trousers,     slot: bottom,    techniques: [skinny_straight] }
seamed_trousers:     { label: Trousers with vertical seam detail, slot: bottom, techniques: [vertical_detail] }
belted_skirt:        { label: Belted skirt,                   slot: bottom,    techniques: [belted_natural_waist] }
oversized_jacket:    { label: Oversized jacket,                slot: outerwear, techniques: [oversized_top] }
belted_coat:         { label: Belted coat,                     slot: outerwear, techniques: [belted_natural_waist] }
fitted_blazer:       { label: Slim-fitted blazer,              slot: outerwear, techniques: [skinny_straight] }
```

(Write as normal multi-line YAML entries, not flow-style — the inline
format above is just for compactness here.)

### 2. New: `src/fit_balance/garments.py`

Mirrors `EFFECTS_TABLE`'s load pattern in `scoring.py`. Contents:

- `Slot = Literal["top", "bottom", "dress", "outerwear"]`
- `GarmentItem` (frozen dataclass): `id`, `label`, `slot: Slot`, `techniques: tuple[str, ...]`
- `load_garments_table()` / `GARMENTS_TABLE` / `CATALOG: dict[str, GarmentItem]` — same pattern as `load_effects_table()` / `EFFECTS_TABLE`
- `UnknownGarmentItemError(ValueError)`
- `list_items() -> list[GarmentItem]`, `get_item(item_id) -> GarmentItem`
- `resolve_outfit(item_ids: list[str]) -> tuple[list[GarmentItem], GarmentAttributes]` — looks up each id, de-duplicates identical technique keys across items (not effect tags — two different techniques that happen to share a tag are NOT merged; see Risks), returns both the resolved items (needed for attribution) and the merged `GarmentAttributes` (fed unchanged into `scoring.score()`)
- `AttributedReason(BaseModel)`: `Reason`'s 4 fields + `item_ids: list[str]`
- `attribute_reasons(reasons: list[Reason], items: list[GarmentItem]) -> list[AttributedReason]` — pure function; for each reason, finds every selected item with a technique that produces that tag (via `EFFECTS_TABLE`, imported from `scoring.py`) and lists all of them (not just one) — honest reflection of shared responsibility when tags overlap, not an error

### 3. Edit: `api/main.py`

Additive only — `/score`, `ScoreRequest`, `ScoreResponse` stay exactly as-is
(still used by `tests/test_api.py` and as a lower-level raw-technique API).

- Widen CORS: `allow_methods=["GET", "POST"]` (currently `["POST"]` only —
  `GET /garments` will silently fail from the browser, though not from
  `TestClient` in pytest, if this is missed)
- New models: `GarmentSummary` (`id`, `label`, `slot` — **no `techniques`
  field**, so the catalog's technique vocabulary never goes over the wire,
  not just off the UI), `ScoreOutfitRequest` (`measurements`, `item_ids:
  list[str]`), `OutfitVerdict` (`recommendation` reusing the same literal
  type as `schemas.Verdict.recommendation`, `score`, `reasons:
  list[AttributedReason]`), `ScoreOutfitResponse` (`balance_points`,
  `main_concern`, `verdict: OutfitVerdict`)
- New endpoints:
  - `GET /garments` → `list[GarmentSummary]`
  - `POST /score-outfit` → resolves `item_ids` via `resolve_outfit`
    (catching `UnknownGarmentItemError` → `HTTPException(422)`), computes
    balance points and verdict exactly like `/score` does today, then calls
    `attribute_reasons()` before returning `ScoreOutfitResponse`

### 4. New: `tests/test_garments.py`

- Catalog covers all 4 slots and all 7 `effects.yaml` technique keys (guards
  against silent drift as either grows)
- `resolve_outfit` de-dupes an identical technique shared by two items
  (`fitted_top` + `slim_trousers`, both `skinny_straight`)
- `resolve_outfit` raises `UnknownGarmentItemError` for a bad id
- Attribution reuses worked example 5 (`PEAR_FULLER` from
  `tests/fixtures.py`): resolving `["oversized_top", "slim_trousers"]`
  produces the same techniques as that example's `oversized_top` +
  `skinny_straight`, same `recommended` verdict, and the `adds_bulk` reason
  attributes to `["oversized_top"]` while `reduces_bulk` attributes to
  `["slim_trousers"]`
- Overlap case: `["seamed_top", "slim_trousers"]` (both hit `reduces_bulk`
  via different techniques) produces **two** separate `reduces_bulk`
  reasons, each attributing to both items — pins the additive-stacking
  behavior as an intentional, tested v1 choice (see Risks)

### 5. Edit: `tests/test_api.py`

Add (without touching the two existing tests): `GET /garments` returns only
`{id, label, slot}` keys (locks in "never on the wire"); `POST
/score-outfit` on the same worked-example-5 combo asserts recommendation +
attribution; `POST /score-outfit` with a bogus item id returns 422.

### 6. Edit: `web/src/lib/types.ts`

Add `Slot`, `GarmentSummary`, `AttributedReason` (extends `Reason` with
`item_ids: string[]`), `OutfitVerdict`, `ScoreOutfitResponse`. Leave
`GarmentAttributes`, `Reason`, `Verdict`, `ScoreResponse` untouched.

### 7. Edit: `web/src/lib/api.ts`

Add `getGarments()` (GET) and `scoreOutfit()` (POST `/score-outfit`),
matching `scoreGarment`'s existing shape/error convention. Leave
`scoreGarment` in place.

### 8. New: `web/src/lib/garments.ts` + `garments.test.ts`

Pure helper `groupBySlot(items: GarmentSummary[]): Record<Slot,
GarmentSummary[]>`, extracted for unit testing per the existing
`avatarGeometry.ts`/`avatarGeometry.test.ts` pattern (this repo's only
current frontend tests are pure-function tests, no component-level testing
exists — keep following that).

### 9. Edit: `web/src/App.tsx`

- Remove `KNOWN_TECHNIQUES` and its hand-sync comment entirely
- Add `garments: GarmentSummary[]` state, fetched via `useEffect` on mount
  (separate loading/error state from the score-submit flow)
- Replace `techniques: Set<string>` with one-selection-per-slot state, e.g.
  `Record<Slot, string | null>` — **radio buttons per slot** (with a "None"
  option), not checkboxes, per the confirmed one-per-slot decision
- Render via `groupBySlot(garments)`: one `<fieldset>` per slot, radio
  inputs labeled with `item.label` — never `item.id` or a technique key
- `handleSubmit` calls `scoreOutfit(measurements, <selected ids>)` instead
  of `scoreGarment`; `result` becomes `ScoreOutfitResponse | null`
- Reasons list: resolve `reason.item_ids` to labels via the fetched
  `garments` list and render them next to each reason — this is the "point
  at the problem item" surface
- Submit disabled when no slot has a selection

### 10. Edit: `NOTES.md`

New subsection ("Garment catalog (manual, v1 — explicitly not stage
5/6)") after "Worked examples (now automated tests)": what it is, why it's
not stage 5/6 (no CV, no photos, hand-authored data exactly like
`effects.yaml`), that it deliberately reuses only the existing 7 techniques,
the tag-overlap/additive-stacking behavior as a documented v1 choice (not a
bug) pinned by `test_attribution_lists_both_items_when_tags_overlap`, and
that "point at the problem item" is a deliberately scoped-down v1 of "what
to replace" — auto-suggested replacements are a separate, explicitly
deferred follow-up.

## Risks (accepted, documented — not blocking)

- **Double-counted effect tags across items**: `scoring.score()` doesn't
  dedupe reasons by tag, so two items using different techniques that share
  an effect tag (e.g. `vertical_detail` + `skinny_straight`, both →
  `reduces_bulk`) contribute that axis's weight twice, additively. Not
  fixed in `scoring.py` (would touch the untouchable engine + require a new
  worked example) — instead pinned by an explicit test and called out in
  NOTES.md as intentional stacking for v1. Revisit only if real usage shows
  surprising totals.
- **Attribution lists all responsible items, not one** — correct behavior
  when two items share a technique or a tag; v1 doesn't try to apportion
  "how much" of a shared reason belongs to which item.

## Verification

- `uv run pytest` — all existing 16 tests plus new `test_garments.py` and
  `test_api.py` cases green
- `uv run ruff check .`
- From `web/`: `npx vitest run` (existing 12 + new `garments.test.ts`),
  `npm run build` (typecheck)
- Manually run the API (`uv run uvicorn api.main:app --port 8000`) and web
  dev server (`npm run dev` from `web/`), confirm in the browser: `/garments`
  populates the slot-grouped radio picker with real names (no snake_case
  visible anywhere, including in Network tab responses), selecting items
  across slots and submitting produces one combined verdict, and a
  negative-reason row names the correct selected item.
