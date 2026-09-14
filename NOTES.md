# fit-balance

This is the current-state spec — what the formulas and architecture are
*today*. For why they got this way (rejected alternatives, superseded
values, the reasoning behind a specific number), see
[`docs/decisions/`](docs/decisions/README.md) — one immutable file per
engine-level design decision, referenced from the relevant section below.

## Pitch

An explainable styling recommendation engine. Instead of a black-box "you're a
pear, wear an A-line" label, or a photorealistic-but-unexplainable virtual
try-on render, this tells you *where your body's balance points are* and
*why* a given garment technique works with or against them — every verdict
comes with the specific reasons that produced it, and those reasons are
editable data, not a trained model's opinion.

## The gap (validated via web search)

- Body-shape apps (Style DNA, BodyMuse, MioLook...) exist and are crowded,
  but user reviews consistently complain about vague/inconsistent
  classification and no way to see or override the reasoning.
- Photorealistic virtual try-on (Doppl, TryDrobe, FitRoom, Krea...) is also
  crowded — well-funded, generative, good at "does it look real," bad at
  "why does/doesn't this suit me."
- Explainable AI (XAI) for fashion is called out by industry writing as
  mostly unsolved; an arXiv paper (StePO-Rec, 2025) is actively researching
  "knowledge-guided reasoning" for outfit styling — i.e. still a research
  problem, not a shipped product feature.
- **The gap: transparent, overridable reasoning**, not another body-shape
  classifier or another photorealistic renderer.

## Core architecture

1. **Balance points** — continuous, signed numbers describing body
   proportions. No discrete "shape" categories (pear/hourglass/apple) as the
   internal model — those are lossy, mutually-overlapping, and produce
   arbitrary label flips right at category boundaries. A shape *label* can
   still be shown to the user, but only as a display string derived from
   whichever balance point dominates — never used for scoring.
2. **Effects table** — maps a garment technique (e.g. `high_rise`,
   `sheath_bodycon`) to the visual effects it produces (e.g.
   `elongates_leg`, `clings_to_hip`). This is a fact about the technique,
   independent of who wears it.
3. **Scoring** — for each balance point, a want/avoid list of effect tags,
   with the contribution quantized into one of three hand-picked severity
   levels (0/1/2, sign-preserved) based on how far the balance point is
   from neutral — not a flat +1/-1 for a category match, and not a raw,
   differently-scaled ratio summed directly across axes either, which
   isn't safely comparable (decision
   [0010](docs/decisions/0010-discrete-severity-level-scoring.md)). Output
   = a verdict *plus the specific reasons that fired*, e.g. "+ defines your
   waist (asset) / − clings to hip (works against your shape) / + reduces
   bulk (helps your frame scale)."

## Balance points — women's v0

```
shoulder_hip_balance = (shoulder - hip) / max(shoulder, hip)  # + = broad shoulder vs hip, − = hip wider than shoulder
bust_hip_balance   = (bust - hip) / max(bust, hip)          # + = top wider, − = bottom wider
waist_definition   = 1 - waist / avg(bust, hip)              # + = defined waist (an asset), ~0/− = no natural cinch
torso_leg_balance  = (torso/height - 0.245) - (leg/height - 0.455)  # + = long torso, − = long legs (deviation from each landmark's own baseline ratio-to-height — see "known gaps")
frame_scale_dev    = avg(max(shoulder,bust),waist,hip)/height - baseline    # + = reads fuller relative to height, − = reads slighter
```

`shoulder` is a **circumference** around the fullest part of the shoulders/
upper arms (the stylist body-shape-calculator convention) — not the
tailoring point-to-point shoulder width, which is a different scale and
isn't comparable to bust/hip circumferences. `frame_scale_dev` takes
`max(shoulder, bust)` rather than bust alone, since bust size is confounded
by breast tissue independent of actual frame/width (decision
[0008](docs/decisions/0008-frame-scale-dev-max-shoulder-bust.md)).

"Main concern" = whichever balance point has the largest absolute
magnitude, skipping `shoulder_hip_balance`/`bust_hip_balance`/
`torso_leg_balance`/`frame_scale_dev` values under 0.05
(`balance_points.IMBALANCE_DEADZONE`) — those four are neutral at 0 in both
directions, so a value that small is measurement noise, not a real
proportion difference; `main_concern()` returns `None` if nothing clears it.
`waist_definition` has no deadzone — its own asymmetric threshold (0.15, in
`scoring.py`'s `AXIS_RULES`) already serves that purpose, for a different
reason (one direction is favorable, not "0 is neutral both ways"). Decision
[0007](docs/decisions/0007-imbalance-deadzone.md). A favorable-sign value
(e.g. high `waist_definition`) is an **asset**, not a concern — surface it
as a strength to build around, not a problem to fix. The CLI (`cli.py`)
honors this at the label level: when `main_concern()` names a favorable
`waist_definition`, it shows "(key asset)" instead of "(main concern)" —
a favorable value labeled as a concern read as self-contradictory
("defined waist (an asset) — MAIN CONCERN"). Presentation-only fix,
`main_concern()`'s own selection logic is unchanged. The web
`BalancePointsChart` component has the same honoring logic and its own
tests, but is no longer rendered by `App.tsx` since the frontend was
simplified down to measurements/silhouette/technique-advice (see
"Technique recommendations" below) — it's dead UI-wiring-wise, not
dead code.

## Balance points — menswear v0

```
shoulder_hip_balance = same as women's version
chest_waist_balance = (chest - waist) / chest       # = tailoring's "drop"; convention target ≈ 0.15 (6" drop on a 40" chest)
chest_hip_balance    = (chest - hip) / max(chest, hip)
torso_leg_balance    = same as women's version
frame_scale_dev       = same formula, different baseline (male average build differs)
```

Important asymmetry: unlike the women's axes where 0 = neutral, menswear
convention treats `chest_waist_balance` ≈ 0 as "room to improve," not
neutral — the target is positive. This is a narrower, more rigid convention
than the women's framing; flag it as such wherever it's surfaced to a user.

## Known gaps (calibration/design work still needed, not yet correctness bugs)

- `frame_scale` baseline (both versions) is a guessed placeholder — needs
  real anthropometric reference data, not invented cutoffs. Currently
  implemented as `0.50` (women's v0) / `0.45` (menswear v0) in
  `src/fit_balance/balance_points.py` — chosen only so the ratio lands near
  zero for a roughly average build, not from real data.
- Effect tags are still coarse in places — e.g. `clings_to_hip` doesn't
  distinguish hip-clinging (fine/good for most shapes) from
  waist/midsection-clinging (bad for an undefined waist). Found via a
  worked example, not chased further by hand — better to let real user
  disagreement drive which tags need splitting next.
- `torso_leg` measurement convention (researched via web search against
  ISO 8559 — the international garment-measurement standard — and tailoring
  practice): `torso` = **back waist length** (nape of neck / C7 vertebra
  down to the natural waist); `leg` = **inseam** (crotch seam down to the
  floor, standing barefoot). These are two independent, standard,
  self-measurable numbers anchored at different landmarks (waist vs.
  crotch) — they are *not* expected to sum to height (a clinical pair that
  does, sitting height + subischial leg length, bakes the head into "torso"
  and needs a stadiometer, so it doesn't fit a self-measured consumer
  flow). `torso_leg_balance` compares each measurement's deviation from its
  own baseline ratio-to-height rather than the two raw measurements to each
  other (decision
  [0001](docs/decisions/0001-torso-leg-balance-formula-fix.md) — the two
  landmarks are structurally different magnitudes for everyone, so a raw
  ratio read as "long legs" universally). `TORSO_HEIGHT_RATIO_BASELINE`/
  `LEG_HEIGHT_RATIO_BASELINE` in `balance_points.py` are themselves guessed
  from general published ranges, not a rigorous study — same caveat as the
  `frame_scale` baselines above. Still open: back waist length is harder to
  self-measure accurately than inseam (which is a well-known measurement) —
  self-report vs. a guided photo measurement is still undecided for the
  actual input flow.
- `shoulder_hip_balance` (decision
  [0002](docs/decisions/0002-shoulder-hip-balance-axis.md)) distinguishes a
  broad-shoulder/narrow-hip build from a top-heavy-by-bust build that would
  otherwise look identical on `bust_hip_balance` alone. It feeds
  `adds_volume_top`/`adds_volume_bottom` via the derived `top_hip_balance`
  (decision [0009](docs/decisions/0009-top-hip-balance-axis.md)) —
  `structured_shoulder`/`puff_sleeve` react to it that way (decision
  [0012](docs/decisions/0012-garment-catalog-vocabulary-expansion.md)) — and
  as of decision
  [0013](docs/decisions/0013-narrows-shoulder-effect.md) also has its own
  dedicated `AXIS_RULES` entry, `narrows_shoulder` (`scoop_neck`), for
  techniques that address shoulder width specifically rather than top
  volume generally. Still open: `narrows_shoulder` doesn't surface in
  `technique_advice.py`'s per-dimension advice (its `DIMENSIONS` tuple has
  no standalone `shoulder_hip_balance` entry, only the combined
  `top_hip_balance`), and necklines/sleeves beyond scoop/structured/puff
  (halter, raglan) are still unmodeled.
- `WomensBalancePoints.main_concern()` still picks the axis with the
  largest *raw* magnitude to name as "the" main concern — the same
  cross-axis comparability problem decision
  [0010](docs/decisions/0010-discrete-severity-level-scoring.md) fixed for
  scoring, left unfixed here since it touches the CLI, `BalancePointsChart.tsx`,
  and its own tests, none of which were in scope for that change. A future
  decision could apply the same severity-level concept to it.

## Worked examples (now automated tests)

Rule changes had, at least once, silently broken an earlier-correct worked
example (an "apple + bodycon" regression happened this way) — hand-verifying
by re-reading doesn't scale. These 5 are now encoded as regression tests in
`tests/test_balance_points.py` (balance-point layer) and
`tests/test_scoring.py` (full verdict), and manually reproduced via the CLI
(`uv run fit-balance ...`) — all 5 pass and match the verdicts below.

```
1. shape≈hourglass, frame_scale=balanced,  garment=[sheath_bodycon, belted_natural_waist] → recommended
2. shape≈apple,     torso_leg=long_torso,  garment=[sheath_bodycon, belted_natural_waist] → avoid
3. shape≈rectangle, torso_leg=long_torso, height=petite, garment=[drop_waist]              → strong avoid
4. shape≈rectangle, torso_leg=long_torso, height=petite, garment=[empire_waistline, vertical_detail] → recommended
5. shape≈pear,      frame_scale=fuller,   garment=[oversized_top, skinny_straight]         → avoid (decision 0011: oversized_top no longer credits added top volume, only adds_bulk and hides_waist — both work against this body's fuller frame and defined waist, and skinny_straight's reduces_bulk isn't enough on its own to offset them)
```

Any change to `balance_points.py`, `effects.yaml`, or `scoring.py` must keep
this suite green — that's the whole point of having it.

## Garment catalog (manual, v1 — explicitly not stage 5/6)

`src/fit_balance/garments.yaml` + `garments.py` add a small, hand-curated
catalog of named items (id/label/slot/techniques) so a caller gets real
item names ("Slim-fitted top", "Oversized jacket") instead of raw
`effects.yaml` technique keys, and can select one item per slot
(top/bottom/dress/outerwear) as an outfit and get one combined verdict for
how it works together — `GET /garments` (never returns `techniques`, so the
vocabulary never reaches the wire either) and `POST /score-outfit`
(`api/main.py`). Both endpoints are intact and tested; the web UI's manual
per-slot picker built on top of them was removed when the frontend was
simplified down to measurements/silhouette/technique-advice (see
"Technique recommendations" below) — reachable today via the CLI or a
direct API call, not currently surfaced in `web/`.

This is presentation-layer work sitting on top of the untouched scoring
engine — outfit scoring resolves the selected items' techniques into one
`GarmentAttributes` (de-duplicated by exact technique key) and calls
`scoring.score()` unchanged. It is deliberately **not** stage 5 (garment-
photo attribute extraction) or stage 6 (multi-garment outfit parsing from a
photo, below): there is no computer vision, no photo input — items are
manually authored data, exactly like `effects.yaml`.

The v1 catalog started by deliberately reusing only the original 7
technique keys; the vocabulary has since been extended with `high_rise`
(`elongates_leg`), `low_rise` (`elongates_torso` + `shortens_leg`, same tags
`drop_waist` uses), `wide_leg` (`adds_volume_bottom`),
`cropped_ankle_length` (`shortens_leg`), and reusing `oversized_top`
verbatim for `bomber_jacket` — decision
[0003](docs/decisions/0003-effects-vocabulary-extension.md). `oversized_top`
also carries `hides_waist` — a boxy, unshaped silhouette obscures whatever
natural waist definition is already there, wired as the mirror of
`defines_waist`/`clings_to_waist` — decision
[0006](docs/decisions/0006-hides-waist-effect.md). `oversized_top` no
longer carries `adds_volume_top`: a boxy, uniformly loose cut doesn't
specifically widen the top the way structured/padded shoulders would —
that's already what `adds_bulk` models, so the two tags were double-
counting the same real effect — decision
[0011](docs/decisions/0011-remove-adds-volume-top-from-oversized-top.md).
`adds_volume_top` had no technique producing it until decision
[0012](docs/decisions/0012-garment-catalog-vocabulary-expansion.md) added
`structured_shoulder` (structured/built-up shoulder blazer) and
`puff_sleeve` (gathered sleeve) — both real, independent constructions that
genuinely widen the top of the silhouette. That same decision added
`peplum` (`defines_waist` + `adds_volume_bottom`), `wrap_style`
(`defines_waist`), `v_neck` (`elongates_torso`), `a_line`
(`adds_volume_bottom`), and `pencil_skirt` (`clings_to_hip`) — all reusing
existing tags, no `scoring.py` changes. Decision
[0013](docs/decisions/0013-narrows-shoulder-effect.md) then added
`scoop_neck` → `narrows_shoulder`, this catalog's one technique scored
directly against `shoulder_hip_balance` rather than the derived
`top_hip_balance` (see "Known gaps" above) — a genuinely new `AXIS_RULES`
entry, not a reused tag. Further vocabulary growth stays a case-by-case
decision, not a batch exercise — each addition should be this deliberate
about which existing tag it reuses versus genuinely needing a new one.

**Known interaction, tested not fixed**: `scoring.score()` doesn't dedupe
reasons by tag, so an outfit whose items use two *different* techniques
that happen to produce the same effect tag (e.g. a top with
`vertical_detail` and trousers with `skinny_straight`, both → `reduces_bulk`)
contributes that tag's axis weight twice, additively. Treated as
intentional stacking for v1 (two independent slimming design choices
compounding), pinned by
`tests/test_garments.py::test_attribution_lists_both_items_when_tags_overlap`
— revisit only if real usage shows it produces surprising totals.

When a verdict has negative reasons, `/score-outfit` attributes each reason
back to which selected item(s) produced it (`attribute_reasons()` in
`garments.py`) — "here's what's working against you." This is attribution
only, not a substitution suggestion; recommending a specific replacement
item is explicitly deferred, a further scoped-down step beyond this v1.

## Outfit recommendations (ranking layer, v1)

`src/fit_balance/recommend.py` adds a ranking layer on top of the outfit
catalog above: instead of the user manually picking one item per slot and
getting a single verdict, `POST /recommend-outfits` (`api/main.py`) takes
just `measurements` (+ an optional `limit`, default 5) and returns the
top-scoring outfits out of every valid combination the catalog can produce.

This is the same kind of presentation-layer work as the catalog itself —
`enumerate_outfit_combinations()` builds candidate `item_ids` lists from
`garments.list_items()`, and `recommend_outfits()` scores each one via the
*unchanged* `garments.resolve_outfit()` + `scoring.score()`, then sorts by
`verdict.score` descending and slices to `limit`. No engine change, no new
axis or rule — `balance_points.py`, `scoring.py`, and `effects.yaml` stay
untouched, so this did not get a `docs/decisions/` entry, only this
section (same precedent as the garment-catalog feature above).

Valid combinations are **dress XOR (top + bottom), with outerwear optional
on either branch** — top-alone, bottom-alone, and top+dress/bottom+dress
are never enumerated. With the current catalog (7 dress / 9 top / 8 bottom
/ 5 outerwear items, after decisions 0012/0013) that's exactly 474
candidates, cheap enough to score
fresh on every request with a plain nested loop — no caching. Ranking is a
simple sort with no dedup/near-duplicate suppression (e.g. the same top
paired with several different jackets could fill multiple slots of the top
5) — accepted as v1-simplicity, consistent with the catalog's own
tag-overlap stacking choice; revisit only if real usage shows it producing
an unhelpful list.

This ranks whole candidate outfits from the existing catalog — a different,
broader thing than the single-item "replacement suggestion" still deferred
above (fixing one reason within an outfit the user already picked). The
endpoint and its tests are intact; the web UI's "Recommended for you"
panel that called it was removed in the same frontend simplification that
dropped the manual picker (see "Technique recommendations" below) — the
per-dimension technique advice took over as the web UI's proactive
guidance instead of a ranked outfit list.

## Technique recommendations (independent per-dimension, v1)

`src/fit_balance/technique_advice.py`'s `recommend_techniques()` answers a
different question than the outfit-ranking layer above: not "which whole
outfit scores best," but "for each of the 4 scored dimensions
(`waist_definition`, `top_hip_balance`, `torso_leg_balance`,
`frame_scale_dev`), which garment techniques help, which hurt, and which
catalog items use them" — reported per dimension, **never combined into
one verdict**. `POST /technique-recommendations` (`api/main.py`) takes
just `measurements` and returns a `DimensionAdviceResponse` per axis;
deliberately no `main_concern` field on this response, since naming a
single "most important" axis would contradict the point of reporting
dimensions independently.

Same presentation-layer precedent as the two sections above — no engine
change (`balance_points.py`/`scoring.py`/`effects.yaml` untouched, only
`AXIS_RULES`/`EFFECTS_TABLE` read), so no `docs/decisions/` entry, only
this section. It does lean on a structural fact already true of
`AXIS_RULES`: every tag sharing an axis also shares that axis's
`reference`, so a dimension's severity level is computed once (via
`scoring.py`'s now-public `signed_level`/`axis_value`, promoted from
private helpers only `score()` used before) and reused for every tag on
that axis — which side a tag lands on is purely its `weight`'s sign
against that one level. A level of `0` (axis inside its deadzone) leaves
every tag on that axis empty on both sides, which is how "no strong
trait" fell out for a body with no real torso/leg skew, with no
special-casing needed.

Each dimension also carries `notable: bool` and `direction: "+" | "-" |
None` (the axis's own signed severity level, `!= 0`) plus `pronounced: bool`
(that same level's magnitude `== 2`) — a **highlight, not a ranking**: any
number of dimensions (0, 1, or more) can be pronounced for a given body,
with no forced single "main concern" pick and no cross-axis comparison at
all. `notable`/`direction` are exposed explicitly rather than left for a
caller to infer from whether `recommendations` is non-empty — those can
diverge when a tag has no current catalog item behind it (`adds_volume_top`
was the standing example of this, orphaned per decision 0011, until
decision 0012 gave it real items; `tests/test_garments.py`'s
`test_every_axis_rules_tag_has_a_catalog_producer` now guards against that
gap reopening silently). The web UI's
`DimensionAdvice.tsx` uses these two fields to render a plain-language
description per dimension (e.g. "noticeably defined", "hip notably wider
than shoulders/bust") ahead of the seek/avoid technique lists.

This deliberately supersedes an earlier explored (and shipped-then-not)
direction of fixing `WomensBalancePoints.main_concern()` itself to be
level-based — that path needed a tie-break policy and ran into a
latent-bug/reference-point rabbit hole for no real gain once per-dimension
independence made a single winner unnecessary. `main_concern()` itself
stays exactly as documented in "Known gaps" below — untouched.

A real, expected consequence of reporting dimensions independently: the
same catalog item can appear more than once across dimensions, sometimes
consistently (`oversized_top` reads `avoid` on both `waist_definition`
and `frame_scale_dev` for a fuller-framed body with a defined waist — two
independent reasons pointing the same way, not a combined score), and
sometimes as a genuine split — an item whose two techniques touch two
different axes can be `seek` on one and `avoid` on the other for the same
body (e.g. `wide_leg_high_rise_trousers` on a hip-heavy, long-torsoed
build: `adds_volume_bottom` works against the already-hip-heavy
`top_hip_balance`, `elongates_leg` helps the long `torso_leg_balance`).
That's the actual trade-off, surfaced directly, not a bug to resolve by
picking a winner.

## Single-garment balance advice (v1)

`src/fit_balance/garment_balance.py`'s `suggest_balance(balance_points,
item_id)` answers a third, narrower question than the two features above:
not "which whole outfit scores best" (outfit recommendations) and not
"which techniques generally help/hurt, body-wide" (technique
recommendations), but "I'm set on wearing *this specific* item — what does
it do to my silhouette, and what else (in a different slot) would offset
whatever it hurts." `POST /balance-garment` (`api/main.py`) takes
`measurements` + one `item_id` and returns that item's own `Verdict` (no
attribution needed — there's only one item) plus `suggestions`, a list of
`DimensionAdvice` restricted to the axes where this item scored a negative
reason, `recommendations` filtered to the "seek" (opposite-sign) side, and
`items` filtered to exclude the chosen item's own slot.

This deliberately sits between two things named elsewhere as out of scope:
it is **not** the single-item *replacement* suggestion the "Garment
catalog" section above defers ("recommending a specific replacement item
is explicitly deferred") — nothing here proposes swapping the chosen item,
only complementing it — and it is **not** full outfit recommendation
(`recommend.py`) — it only ever reasons about the one item the user
already committed to. Same presentation-layer precedent as the three
features above: `resolve_outfit()`, `score()`, and `recommend_techniques()`
are reused completely unchanged, no new `AXIS_RULES`/`effects.yaml` logic,
so no `docs/decisions/` entry, only this section.

One consequence of reusing `recommend_techniques()` as-is: a negative
reason on an axis that function doesn't report — currently only
`shoulder_hip_balance` (`narrows_shoulder`, decision 0013; see "Known
gaps" and "Technique recommendations" above) — simply produces no
suggestion for that reason, same documented gap, not a special case here.
The "other slot" filter is a deliberate v1 simplification too: it's
`item.slot != suggestion.slot`, not the full dress-XOR-(top+bottom)
valid-outfit-shape logic `enumerate_outfit_combinations()` uses, since this
feature only ever proposes one complementary item at a time. The web UI's
`GarmentBalance.tsx` renders the item's own verdict/reasons next to a
second `Avatar` (driven by **all** of the item's reason tags, not just the
positive ones — unlike the old removed picker's curated "your recommended
outfit" avatar, the point here is showing the item's real effect, good and
bad) and reuses `DimensionAdvice.tsx` wholesale for the suggestions list.

## Avatar: to-scale, not balance-point-driven

`web/src/lib/avatarGeometry.ts` draws the silhouette directly from real
`Measurements` (one shared cm-to-SVG scale for every width and length), not
from balance-point ratios, so two people with the same proportions but
different absolute sizes render at different sizes. The outline is a closed
Catmull-Rom spline through the measurement keypoints (not a straight-edged
polygon), with a head ellipse sized off total figure height (the classic
"7.5 heads tall" convention) sitting on the neck keypoint. Circumferences
convert to a front-view width via `WIDTH_FROM_CIRCUMFERENCE = 0.32`
(circumference/π for a circular cross-section, nudged up for a torso's
elliptical shape) — an approximation, not exact, same caveat class as
`frame_scale`'s baseline. Neck/ankle aren't measured inputs; they're drawn
as a fixed proportion of shoulder/hip width for visual completeness only.
Decisions [0004](docs/decisions/0004-avatar-to-scale-rendering.md) and
[0005](docs/decisions/0005-avatar-curvy-head-width-fix.md). Purely a
rendering concern — `balance_points.py`, `scoring.py`, and `effects.yaml`
are untouched.

**Garment-corrected overlay — prototype, not finished, and currently
unwired.** `Avatar` can take an `effectTags` prop and draws a second
dashed outline on top of the body silhouette, nudging specific widths per
tag via `avatarGeometry.ts`'s `applyEffectAdjustments()` and a hand-tuned
`EFFECT_WIDTH_ADJUSTMENTS` table (e.g. `defines_waist` → waist ×0.8,
`adds_volume_top` → shoulder/bust ×1.15). It previously drew off a scored
outfit's positive reasons; since the frontend simplification removed the
manual outfit-scoring flow (`result` in `App.tsx`) that fed it, `App.tsx`
now renders `Avatar` with no `effectTags` at all — the capability (prop,
adjustment table, tests) is untouched, just not currently exercised by
any caller. Reconnecting it would need a new source for the tags (e.g.
the "Technique recommendations" section's per-dimension advice), not
resurrecting the removed outfit picker. Only covers tags with an obvious
width-based reading — tags about torso/leg length (`elongates_leg`,
`shortens_torso`, etc.) aren't represented, since those need a
keypoint-position shift, not a width multiplier. Spike-quality: reuses
the existing rendering pipeline (same "purely a rendering concern" scope
as the section above), not yet validated for visual accuracy beyond a
manual spot-check.

## Build order — status

See `plan.md` for the full architecture/stack decisions and per-stage file
layout.

1. **Done.** Pure-function balance-point calculator + the 5 worked examples
   as automated tests. `src/fit_balance/balance_points.py`,
   `tests/test_balance_points.py`.
2. **Done.** `effects.yaml` + scoring function returning `(verdict,
   reasons[])`. `src/fit_balance/effects.yaml`, `src/fit_balance/scoring.py`,
   `tests/test_scoring.py`.
3. **Done.** CLI to type in measurements + a garment's attributes and get
   verdict + reasons — confirmed the rules *feel* right on all 5 worked
   examples. `src/fit_balance/cli.py` (`uv run fit-balance ...`).
4. **Done.** FastAPI `/score` endpoint (`api/main.py`) + a React/TS parametric
   SVG avatar (`web/`, pure geometry in `web/src/lib/avatarGeometry.ts`) —
   no photorealism, per the original plan.
5. **Not started.** Garment-photo → attribute extraction (pose estimation +
   segmentation) for "upload a real item, tell me if it suits me."
6. **Not started.** Multi-garment outfit parsing for "recreate this inspo
   look, adjusted for my proportions."

Do not start (5)/(6) casually — everything useful and differentiated so far
needed zero computer vision; CV is the highest-uncertainty, least-validated
part of this plan.
