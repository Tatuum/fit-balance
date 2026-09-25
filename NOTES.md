# fit-balance

This is the current-state spec. It describes the formulas and
architecture as they are *today*. For why they got this way — rejected
alternatives, superseded values, the reasoning behind a specific number
— see [`docs/adr/`](docs/adr/README.md). One immutable file per
engine-level design decision, referenced from the relevant section
below.

## Pitch

An explainable styling recommendation engine. Not a black-box "you're a
pear, wear an A-line" label. Not a photorealistic-but-unexplainable
virtual try-on render. This tells you *where your body's balance points
are* and *why* a given garment technique works with or against them.
Every verdict comes with the specific reasons that produced it. Those
reasons are editable data, not a trained model's opinion.

## The gap (validated via web search)

- Body-shape apps (Style DNA, BodyMuse, MioLook...) are crowded. User
  reviews consistently complain about vague/inconsistent classification
  and no way to see or override the reasoning.
- Photorealistic virtual try-on (Doppl, TryDrobe, FitRoom, Krea...) is
  also crowded — well-funded, generative, good at "does it look real,"
  bad at "why does/doesn't this suit me."
- Explainable AI (XAI) for fashion is mostly unsolved, per industry
  writing. An arXiv paper (StePO-Rec, 2025) is actively researching
  "knowledge-guided reasoning" for outfit styling — still a research
  problem, not a shipped product feature.
- **The gap: transparent, overridable reasoning.** Not another
  body-shape classifier. Not another photorealistic renderer.

## Core architecture

1. **Balance points** — continuous, signed numbers describing body
   proportions. No discrete "shape" categories (pear/hourglass/apple) as
   the internal model: those are lossy, mutually-overlapping, and
   produce arbitrary label flips right at category boundaries. A shape
   *label* can still be shown to the user, but only as a display string
   derived from whichever balance point dominates. Never used for
   scoring.
2. **Effects table** — maps a garment technique (e.g. `high_rise`,
   `sheath_bodycon`) to the visual effects it produces (e.g.
   `elongates_leg`, `clings_to_hip`). This is a fact about the
   technique, independent of who wears it.
3. **Scoring** — for each balance point, a want/avoid list of effect
   tags. The contribution is quantized into one of three hand-picked
   severity levels (0/1/2, sign-preserved), based on how far the
   balance point is from neutral. Not a flat +1/-1 for a category
   match. Not a raw, differently-scaled ratio summed directly across
   axes either — that isn't safely comparable. Decision
   [0010](docs/adr/0010-discrete-severity-level-scoring.md). Output = a
   verdict *plus the specific reasons that fired*, e.g. "+ defines your
   waist (asset) / − clings to hip (works against your shape) / +
   reduces bulk (helps your frame scale)."

## Balance points — women's v0

```
shoulder_hip_balance = (shoulder - hip) / max(shoulder, hip)  # + = broad shoulder vs hip, − = hip wider than shoulder
bust_hip_balance   = (bust - hip) / max(bust, hip)          # + = top wider, − = bottom wider
waist_definition   = 1 - waist / avg(bust, hip)              # + = defined waist (an asset), ~0/− = no natural cinch
torso_leg_balance  = (torso/height - 0.245) - (leg/height - 0.455)  # + = long torso, − = long legs (deviation from each landmark's own baseline ratio-to-height — see "known gaps")
frame_scale_dev    = avg(max(shoulder,bust),waist,hip)/height - baseline    # + = reads fuller relative to height, − = reads slighter
```

**Current state**

- `shoulder` is a **circumference** around the fullest part of the
  shoulders/upper arms (the stylist body-shape-calculator convention),
  not the tailoring point-to-point shoulder width — that's a different
  scale, not comparable to bust/hip circumferences.
- `frame_scale_dev` takes `max(shoulder, bust)` rather than bust alone:
  bust size is confounded by breast tissue independent of actual
  frame/width.
- "Main concern" = whichever balance point has the largest absolute
  magnitude. It skips `shoulder_hip_balance`/`bust_hip_balance`/
  `torso_leg_balance`/`frame_scale_dev` values under 0.05
  (`balance_points.IMBALANCE_DEADZONE`) — those four are neutral at 0 in
  both directions, so a value that small is measurement noise, not a
  real proportion difference. `main_concern()` returns `None` if
  nothing clears it.
- `waist_definition` has no deadzone — its own asymmetric threshold
  (0.15, in `scoring.py`'s `AXIS_RULES`) already serves that purpose,
  for a different reason: one direction is favorable, not "0 is
  neutral both ways." A favorable-sign value (e.g. high
  `waist_definition`) is an **asset**, not a concern — surface it as a
  strength to build around, not a problem to fix.
- The CLI (`cli.py`) honors this at the label level: when
  `main_concern()` names a favorable `waist_definition`, it shows "(key
  asset)" instead of "(main concern)" — a favorable value labeled as a
  concern reads as self-contradictory. Presentation-only fix —
  `main_concern()`'s own selection logic is unchanged. The web
  `BalancePointsChart` component has the same honoring logic and its
  own tests, but `App.tsx` no longer renders it, since the frontend was
  simplified down to measurements/silhouette/technique-advice (see
  "Technique recommendations" below). It's dead UI-wiring-wise, not
  dead code.

**History / rationale**

- [0008](docs/adr/0008-frame-scale-dev-max-shoulder-bust.md) —
  `frame_scale_dev` uses `max(shoulder, bust)`.
- [0007](docs/adr/0007-imbalance-deadzone.md) — the 0.05 deadzone on
  `main_concern()`'s four symmetric axes.

Menswear support (a parallel `chest_waist_balance`/`chest_hip_balance`
formula set) was scaffolded in stage 1 but never wired into any test,
CLI flag, API endpoint, or frontend code. Removed as unused clutter —
decision [0014](docs/adr/0014-remove-menswear-support.md). Reintroduce
only with an actual need, as a fresh formula-design pass with its own
worked examples and tests, not by restoring the old code as-is.

## Known gaps (calibration/design work still needed, not yet correctness bugs)

- `frame_scale` baseline is a guessed placeholder. It needs real
  anthropometric reference data, not invented cutoffs. Currently
  implemented as `0.50` (`WOMEN_FRAME_SCALE_BASELINE` in
  `src/fit_balance/balance_points.py`) — chosen only so the ratio
  lands near zero for a roughly average build, not from real data.
- Effect tags are still coarse in places. E.g. `clings_to_hip` doesn't
  distinguish hip-clinging (fine/good for most shapes) from
  waist/midsection-clinging (bad for an undefined waist). Found via a
  worked example, not chased further by hand. Better to let real user
  disagreement drive which tags need splitting next.
- `torso_leg` measurement convention (researched via web search against
  ISO 8559 — the international garment-measurement standard — and
  tailoring practice): `torso` = **back waist length** (nape of neck /
  C7 vertebra down to the natural waist); `leg` = **inseam** (crotch
  seam down to the floor, standing barefoot). These are two
  independent, standard, self-measurable numbers anchored at different
  landmarks (waist vs. crotch). They are *not* expected to sum to
  height — a clinical pair that does, sitting height + subischial leg
  length, bakes the head into "torso" and needs a stadiometer, so it
  doesn't fit a self-measured consumer flow. `torso_leg_balance`
  compares each measurement's deviation from its own baseline
  ratio-to-height, rather than the two raw measurements to each other:
  the two landmarks are structurally different magnitudes for
  everyone, so a raw ratio read as "long legs" universally. Decision
  [0001](docs/adr/0001-torso-leg-balance-formula-fix.md).
  `TORSO_HEIGHT_RATIO_BASELINE`/`LEG_HEIGHT_RATIO_BASELINE` in
  `balance_points.py` are themselves guessed from general published
  ranges, not a rigorous study — same caveat as the `frame_scale`
  baselines above. Still open: back waist length is harder to
  self-measure accurately than inseam, which is a well-known
  measurement. Self-report vs. a guided photo measurement is still
  undecided for the actual input flow.
- `shoulder_hip_balance` distinguishes a broad-shoulder/narrow-hip
  build from a top-heavy-by-bust build that would otherwise look
  identical on `bust_hip_balance` alone. Decision
  [0002](docs/adr/0002-shoulder-hip-balance-axis.md). It feeds
  `adds_volume_top`/`adds_volume_bottom` via the derived
  `top_hip_balance`. Decision
  [0009](docs/adr/0009-top-hip-balance-axis.md).
  `structured_shoulder`/`puff_sleeve` react to it that way. Decision
  [0012](docs/adr/0012-garment-catalog-vocabulary-expansion.md). As of
  decision [0013](docs/adr/0013-narrows-shoulder-effect.md), it also
  has its own dedicated `AXIS_RULES` entry, `narrows_shoulder`
  (`scoop_neck`), for techniques that address shoulder width
  specifically rather than top volume generally. Still open:
  `narrows_shoulder` doesn't surface in `technique_advice.py`'s
  per-dimension advice — its `DIMENSIONS` tuple has no standalone
  `shoulder_hip_balance` entry, only the combined `top_hip_balance`.
  Necklines/sleeves beyond scoop/structured/puff (halter, raglan) are
  still unmodeled.
- `WomensBalancePoints.main_concern()` still picks the axis with the
  largest *raw* magnitude to name as "the" main concern. That's the
  same cross-axis comparability problem decision
  [0010](docs/adr/0010-discrete-severity-level-scoring.md) fixed for
  scoring — left unfixed here since it touches the CLI,
  `BalancePointsChart.tsx`, and its own tests, none of which were in
  scope for that change. A future decision could apply the same
  severity-level concept to it.

## Worked examples (now automated tests)

Rule changes had, at least once, silently broken an earlier-correct
worked example — an "apple + bodycon" regression happened this way.
Hand-verifying by re-reading doesn't scale. These 5 are now encoded as
regression tests in `tests/test_balance_points.py` (balance-point
layer) and `tests/test_scoring.py` (full verdict), and manually
reproduced via the CLI (`uv run fit-balance ...`). All 5 pass and match
the verdicts below.

```
1. shape≈hourglass, frame_scale=balanced,  garment=[sheath_bodycon, belted_natural_waist] → recommended
2. shape≈apple,     torso_leg=long_torso,  garment=[sheath_bodycon, belted_natural_waist] → avoid
3. shape≈rectangle, torso_leg=long_torso, height=petite, garment=[drop_waist]              → strong avoid
4. shape≈rectangle, torso_leg=long_torso, height=petite, garment=[empire_waistline, vertical_detail] → recommended
5. shape≈pear,      frame_scale=fuller,   garment=[oversized_top, skinny_straight]         → avoid (decision 0011: oversized_top no longer credits added top volume, only adds_bulk and hides_waist — both work against this body's fuller frame and defined waist, and skinny_straight's reduces_bulk isn't enough on its own to offset them)
```

Any change to `balance_points.py`, `effects.yaml`, or `scoring.py` must
keep this suite green. That's the whole point of having it.

## Garment catalog (manual, v1 — explicitly not stage 5/6)

**Current state**

`src/fit_balance/garments.yaml` + `garments.py`: a hand-curated
catalog of named items (id/label/slot/techniques). Manually authored
data, exactly like `effects.yaml` — no computer vision, no photo
input (stays out of stage 5/6 scope).

- `GET /garments` — lists items with real names ("Slim-fitted top",
  "Oversized jacket"); never returns raw `techniques`.
- `POST /score-outfit` (`api/main.py`) — takes one item per slot
  (top/bottom/dress/outerwear), resolves their techniques into one
  `GarmentAttributes` (de-duplicated by exact technique key), calls
  `scoring.score()` unchanged.
- Not currently surfaced in `web/` (the manual per-slot picker was
  removed in the frontend simplification) — reachable via the CLI or
  a direct API call.
- `attribute_reasons()` attributes each negative reason back to the
  item(s) that produced it. Attribution only — not a substitution
  suggestion (deferred).

**Known interaction (tested, not fixed):** `scoring.score()` doesn't
dedupe reasons by tag. Two different techniques producing the same
effect tag (e.g. `vertical_detail` + `skinny_straight`, both →
`reduces_bulk`) contribute that tag's axis weight twice, additively.
Treated as intentional stacking for v1. Pinned by
`tests/test_garments.py::test_attribution_lists_both_items_when_tags_overlap`.
Revisit only if real usage shows surprising totals.

**Technique vocabulary, current:** original 7 keys, plus (in order
added) `high_rise`, `low_rise`, `wide_leg`, `cropped_ankle_length`,
`bomber_jacket` (0003) · `oversized_top`: `hides_waist` added, no
longer carries `adds_volume_top` (0006, 0011) · `structured_shoulder`,
`puff_sleeve`, `peplum`, `wrap_style`, `v_neck`, `a_line`,
`pencil_skirt` (0012) · `scoop_neck` → `narrows_shoulder`, scored
directly against `shoulder_hip_balance` (0013).

**History / rationale**

- [0003](docs/adr/0003-effects-vocabulary-extension.md) — extended
  vocabulary beyond the original 7 keys.
- [0006](docs/adr/0006-hides-waist-effect.md) — `oversized_top` gains
  `hides_waist` (mirrors `defines_waist`/`clings_to_waist`).
- [0011](docs/adr/0011-remove-adds-volume-top-from-oversized-top.md) —
  `oversized_top` loses `adds_volume_top`: was double-counting what
  `adds_bulk` already models.
- [0012](docs/adr/0012-garment-catalog-vocabulary-expansion.md) — gave
  `adds_volume_top` a real producer (`structured_shoulder`,
  `puff_sleeve`); added several reused-tag techniques.
- [0013](docs/adr/0013-narrows-shoulder-effect.md) — `scoop_neck`, the
  first technique to need a genuinely new `AXIS_RULES` entry rather
  than a reused tag. Further vocabulary growth stays case-by-case.

## Outfit recommendations (ranking layer, v1)

**Current state**

- `src/fit_balance/recommend.py`: a ranking layer on top of the
  garment catalog. `POST /recommend-outfits` (`api/main.py`) takes
  `measurements` (+ optional `limit`, default 5), returns the
  top-scoring outfits across every valid combination the catalog can
  produce.
- `enumerate_outfit_combinations()` builds candidate `item_ids` lists
  from `garments.list_items()`; `recommend_outfits()` scores each via
  the *unchanged* `garments.resolve_outfit()` + `scoring.score()`,
  sorts by `verdict.score` descending, slices to `limit`.
- Valid combinations: **dress XOR (top + bottom), with outerwear
  optional on either branch**. Top-alone, bottom-alone, and
  top+dress/bottom+dress are never enumerated. With the current
  catalog (7 dress / 9 top / 8 bottom / 5 outerwear items, after
  decisions 0012/0013) that's exactly 474 candidates — cheap enough to
  score fresh on every request with a plain nested loop, no caching.
- No dedup/near-duplicate suppression (e.g. the same top paired with
  several jackets could fill multiple slots of the top 5) — accepted
  as v1-simplicity, consistent with the catalog's own tag-overlap
  stacking choice. Revisit only if real usage shows an unhelpful list.
- Ranks whole candidate outfits — a different, broader thing than the
  single-item "replacement suggestion" still deferred in "Garment
  catalog" above (fixing one reason within an outfit already picked).
  Endpoint and tests intact. The web UI's "Recommended for you" panel
  that called it was removed in the same frontend simplification that
  dropped the manual picker — the per-dimension technique advice took
  over as the web UI's proactive guidance instead of a ranked outfit
  list.
- No engine change — `balance_points.py`, `scoring.py`, and
  `effects.yaml` stay untouched. So this did not get a `docs/adr/`
  entry, only this section (same precedent as the garment-catalog
  feature above).

## Technique recommendations (independent per-dimension, v1)

**Current state**

- `src/fit_balance/technique_advice.py`'s `recommend_techniques()`
  answers a different question than the outfit-ranking layer above.
  Not "which whole outfit scores best," but "for each of the 4 scored
  dimensions (`waist_definition`, `top_hip_balance`,
  `torso_leg_balance`, `frame_scale_dev`), which garment techniques
  help, which hurt, and which catalog items use them" — reported per
  dimension, **never combined into one verdict**. `POST
  /technique-recommendations` (`api/main.py`) takes just
  `measurements` and returns a `DimensionAdviceResponse` per axis.
  Deliberately no `main_concern` field — naming a single "most
  important" axis would contradict the point of reporting dimensions
  independently.
- Leans on a structural fact already true of `AXIS_RULES`: every tag
  sharing an axis also shares that axis's `reference`. A dimension's
  severity level is computed once (via `scoring.py`'s now-public
  `signed_level`/`axis_value`, promoted from private helpers only
  `score()` used before) and reused for every tag on that axis. Which
  side a tag lands on is purely its `weight`'s sign against that one
  level. A level of `0` (axis inside its deadzone) leaves every tag on
  that axis empty on both sides — how "no strong trait" falls out for
  a body with no real torso/leg skew, with no special-casing needed.
- Each dimension also carries `notable: bool` and `direction: "+" |
  "-" | None` (the axis's own signed severity level, `!= 0`), plus
  `pronounced: bool` (that same level's magnitude `== 2`) — a
  **highlight, not a ranking**. Any number of dimensions (0, 1, or
  more) can be pronounced for a given body, with no forced single
  "main concern" pick and no cross-axis comparison at all.
  `notable`/`direction` are exposed explicitly rather than left for a
  caller to infer from whether `recommendations` is non-empty: those
  can diverge when a tag has no current catalog item behind it.
  `adds_volume_top` was the standing example of this — orphaned per
  decision 0011, until decision 0012 gave it real items.
  `tests/test_garments.py`'s
  `test_every_axis_rules_tag_has_a_catalog_producer` now guards
  against that gap reopening silently.
- The web UI's `DimensionAdvice.tsx` uses `notable`/`pronounced` to
  render a plain-language description per dimension (e.g. "noticeably
  defined", "hip notably wider than shoulders/bust") ahead of the
  seek/avoid technique lists.
- A real, expected consequence of reporting dimensions independently:
  the same catalog item can appear more than once across dimensions.
  Sometimes consistently — `oversized_top` reads `avoid` on both
  `waist_definition` and `frame_scale_dev` for a fuller-framed body
  with a defined waist, two independent reasons pointing the same way,
  not a combined score. Sometimes as a genuine split: an item whose
  two techniques touch two different axes can be `seek` on one and
  `avoid` on the other for the same body (e.g.
  `wide_leg_high_rise_trousers` on a hip-heavy, long-torsoed build —
  `adds_volume_bottom` works against the already-hip-heavy
  `top_hip_balance`, `elongates_leg` helps the long `torso_leg_balance`).
  That's the actual trade-off, surfaced directly, not a bug to resolve
  by picking a winner.
- No engine change (`balance_points.py`/`scoring.py`/`effects.yaml`
  untouched, only `AXIS_RULES`/`EFFECTS_TABLE` read), so no
  `docs/adr/` entry, only this section — same presentation-layer
  precedent as the two sections above.

**History / rationale**

- Deliberately supersedes an earlier explored (and shipped-then-not)
  direction of fixing `WomensBalancePoints.main_concern()` itself to
  be level-based. That path needed a tie-break policy and ran into a
  latent-bug/reference-point rabbit hole for no real gain, once
  per-dimension independence made a single winner unnecessary.
  `main_concern()` itself stays exactly as documented in "Known gaps"
  above — untouched.

## Single-garment balance advice (v1)

**Current state**

- `src/fit_balance/garment_balance.py`'s `suggest_balance(balance_points,
  item_id)` answers a third, narrower question than the two features
  above. Not "which whole outfit scores best" (outfit recommendations).
  Not "which techniques generally help/hurt, body-wide" (technique
  recommendations). But "I'm set on wearing *this specific* item —
  what does it do to my silhouette, and what else (in a different
  slot) would offset whatever it hurts."
- `POST /balance-garment` (`api/main.py`) takes `measurements` + one
  `item_id` and returns that item's own `Verdict` (no attribution
  needed — there's only one item), plus `suggestions`: a list of
  `DimensionAdvice` restricted to the axes where this item scored a
  negative reason, `recommendations` filtered to the "seek"
  (opposite-sign) side, and `items` filtered to exclude the chosen
  item's own slot.
- Deliberately sits between two things named elsewhere as out of
  scope. It is **not** the single-item *replacement* suggestion the
  "Garment catalog" section above defers ("recommending a specific
  replacement item is explicitly deferred") — nothing here proposes
  swapping the chosen item, only complementing it. And it is **not**
  full outfit recommendation (`recommend.py`) — it only ever reasons
  about the one item the user already committed to.
- One consequence of reusing `recommend_techniques()` as-is: a
  negative reason on an axis that function doesn't report — currently
  only `shoulder_hip_balance` (`narrows_shoulder`, decision 0013; see
  "Known gaps" and "Technique recommendations" above) — simply
  produces no suggestion for that reason. Same documented gap, not a
  special case here.
- The "other slot" filter is a deliberate v1 simplification too: it's
  `item.slot != suggestion.slot`, not the full
  dress-XOR-(top+bottom) valid-outfit-shape logic
  `enumerate_outfit_combinations()` uses, since this feature only ever
  proposes one complementary item at a time.
- The web UI's `GarmentBalance.tsx` renders the item's own
  verdict/reasons next to a second `Avatar` — driven by **all** of the
  item's reason tags, not just the positive ones. Unlike the old
  removed picker's curated "your recommended outfit" avatar, the point
  here is showing the item's real effect, good and bad. It reuses
  `DimensionAdvice.tsx` wholesale for the suggestions list.
- Same presentation-layer precedent as the three features above:
  `resolve_outfit()`, `score()`, and `recommend_techniques()` are
  reused completely unchanged, no new `AXIS_RULES`/`effects.yaml`
  logic. So no `docs/adr/` entry, only this section.

## Avatar: to-scale, not balance-point-driven

**Current state**

- `web/src/lib/avatarGeometry.ts` draws the silhouette directly from
  real `Measurements` (one shared cm-to-SVG scale for every width and
  length), not from balance-point ratios. Two people with the same
  proportions but different absolute sizes render at different sizes.
- The outline is a closed Catmull-Rom spline through the measurement
  keypoints (not a straight-edged polygon), with a head ellipse sized
  off total figure height (the classic "7.5 heads tall" convention)
  sitting on the neck keypoint.
- Circumferences convert to a front-view width via
  `WIDTH_FROM_CIRCUMFERENCE = 0.32` (circumference/π for a circular
  cross-section, nudged up for a torso's elliptical shape) — an
  approximation, not exact, same caveat class as `frame_scale`'s
  baseline.
- Neck/ankle aren't measured inputs; they're drawn as a fixed
  proportion of shoulder/hip width for visual completeness only.
- Purely a rendering concern — `balance_points.py`, `scoring.py`, and
  `effects.yaml` are untouched.

**Garment-corrected overlay — prototype, not finished, and currently
unwired.**

- `Avatar` can take an `effectTags` prop and draws a second dashed
  outline on top of the body silhouette, nudging specific widths per
  tag via `avatarGeometry.ts`'s `applyEffectAdjustments()` and a
  hand-tuned `EFFECT_WIDTH_ADJUSTMENTS` table (e.g. `defines_waist` →
  waist ×0.8, `adds_volume_top` → shoulder/bust ×1.15).
- It previously drew off a scored outfit's positive reasons. Since the
  frontend simplification removed the manual outfit-scoring flow
  (`result` in `App.tsx`) that fed it, `App.tsx` now renders `Avatar`
  with no `effectTags` at all — the capability (prop, adjustment
  table, tests) is untouched, just not currently exercised by any
  caller. Reconnecting it would need a new source for the tags (e.g.
  the "Technique recommendations" section's per-dimension advice), not
  resurrecting the removed outfit picker.
- Only covers tags with an obvious width-based reading: tags about
  torso/leg length (`elongates_leg`, `shortens_torso`, etc.) aren't
  represented, since those need a keypoint-position shift, not a width
  multiplier.
- Spike-quality: reuses the existing rendering pipeline (same "purely
  a rendering concern" scope as the section above), not yet validated
  for visual accuracy beyond a manual spot-check.

**History / rationale**

- [0004](docs/adr/0004-avatar-to-scale-rendering.md) — to-scale
  rendering approach.
- [0005](docs/adr/0005-avatar-curvy-head-width-fix.md) — head-width
  fix for curvier builds.

## Build order — status

See `ARCHITECTURE.md` for the full architecture/stack decisions and per-stage file
layout.

1. **Done.** Pure-function balance-point calculator + the 5 worked examples
   as automated tests. `src/fit_balance/balance_points.py`,
   `tests/test_balance_points.py`.
2. **Done.** `effects.yaml` + scoring function returning `(verdict,
   reasons[])`. `src/fit_balance/effects.yaml`, `src/fit_balance/scoring.py`,
   `tests/test_scoring.py`.
3. **Done.** CLI to type in measurements + a garment's attributes and
   get verdict + reasons. Confirmed the rules *feel* right on all 5
   worked examples. `src/fit_balance/cli.py` (`uv run fit-balance
   ...`).
4. **Done.** FastAPI `/score` endpoint (`api/main.py`) + a React/TS
   parametric SVG avatar (`web/`, pure geometry in
   `web/src/lib/avatarGeometry.ts`) — no photorealism, per the
   original plan.
5. **Not started — deprioritized indefinitely (decided 2026-09-21).**
   Garment-photo → attribute extraction via pose estimation +
   segmentation. "Upload a real item, tell me if it suits me" is now
   handled a different way: a private per-user photo-upload closet
   using a multimodal LLM call (not CV) to extract technique tags,
   reviewed by the user before scoring. See `ARCHITECTURE.md`'s Stage 4.5 for
   the full design. This stage (5) specifically — pose/segmentation-
   based extraction — is not needed for that and stays out of scope.
6. **Not started.** Multi-garment outfit parsing for "recreate this
   inspo look, adjusted for my proportions."

Do not start (5)/(6) casually. Everything useful and differentiated so
far needed zero computer vision. CV is the highest-uncertainty,
least-validated part of this plan.
