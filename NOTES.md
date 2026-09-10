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
   with the contribution scaled by how far the balance point is from
   neutral (not a flat +1/-1 for a category match). Output = a verdict
   *plus the specific reasons that fired*, e.g. "+ defines your waist
   (asset) / − clings to hip (works against your shape) / + reduces bulk
   (helps your frame scale)."

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
as a strength to build around, not a problem to fix.

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
  (decision [0009](docs/decisions/0009-top-hip-balance-axis.md)), but has no
  dedicated `effects.yaml`/`AXIS_RULES` entry of its own yet — no v0 garment
  technique (structured shoulders, halter necklines, raglan sleeves) reacts
  specifically to shoulder width; that's a separate, not-yet-made decision
  needing its own worked example.

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
5. shape≈pear,      frame_scale=fuller,   garment=[oversized_top, skinny_straight]         → neutral, with a noted tension (shape wants some added volume on top, frame_scale wants less overall bulk, but oversized_top also hides this body's defined waist — a real asset — so the net doesn't clear "recommended")
```

Any change to `balance_points.py`, `effects.yaml`, or `scoring.py` must keep
this suite green — that's the whole point of having it.

## Garment catalog (manual, v1 — explicitly not stage 5/6)

`src/fit_balance/garments.yaml` + `garments.py` add a small, hand-curated
catalog of named items (id/label/slot/techniques) so the web UI shows real
item names ("Slim-fitted top", "Oversized jacket") instead of raw
`effects.yaml` technique keys, and so users can select one item per slot
(top/bottom/dress/outerwear) as an outfit and get one combined verdict for
how it works together — `GET /garments` (never returns `techniques`, so the
vocabulary never reaches the wire either) and `POST /score-outfit`
(`api/main.py`).

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
[0006](docs/decisions/0006-hides-waist-effect.md). Further vocabulary
growth stays a case-by-case decision, not a batch exercise — each addition
should be this deliberate about which existing tag it reuses versus
genuinely needing a new one.

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
