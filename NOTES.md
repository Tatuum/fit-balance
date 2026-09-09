# fit-balance

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
isn't comparable to bust/hip circumferences.

`frame_scale_dev` uses `max(shoulder, bust)`, not bust alone (2026-09): bust
size is confounded by breast tissue independent of actual frame/width, so
using it alone can undercount a broad-shouldered, less-busty build and
overcount a fuller-busted, narrow-shouldered one. Whichever of the two
measurements is actually wider drives the "how fuller does the top read"
signal. `WOMEN_FRAME_SCALE_BASELINE` (0.50) was left unchanged — across the
5 worked-example fixtures, shoulder exceeds bust by only ~0.5-0.6cm where it
exceeds it at all (`PEAR_FULLER` has bust > shoulder, so it's unaffected),
too small a shift to justify a new guessed number on top of an already-
guessed baseline (see "known gaps" below). Revisit alongside that baseline
once real anthropometric data is in.

"Main concern" = whichever balance point has the largest absolute magnitude.
A favorable-sign value (e.g. high waist_definition) is an **asset**, not a
concern — surface it as a strength to build around, not a problem to fix.

**Imbalance deadzone (2026-09)**: `shoulder_hip_balance`, `bust_hip_balance`,
`torso_leg_balance`, and `frame_scale_dev` are neutral at 0 in both
directions, so a value under 0.05 (`balance_points.IMBALANCE_DEADZONE`) is
measurement noise, not a real proportion difference — `main_concern()`
won't name one of these as the concern below that line (returning `None` if
nothing on any axis clears it), and `scoring.score()` won't generate a
reason against that axis either. `waist_definition` is deliberately left
out: it already has its own asymmetric threshold (0.15, in scoring.py's
`AXIS_RULES`) for a different reason — one direction is favorable, not "0 is
neutral both ways" — so stacking a second deadzone on top isn't the same
kind of fix.

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
- `torso_leg` measurement convention (decided, researched via web search
  against ISO 8559 — the international garment-measurement standard — and
  tailoring practice): `torso` = **back waist length** (nape of neck / C7
  vertebra down to the natural waist); `leg` = **inseam** (crotch seam down
  to the floor, standing barefoot). These are two independent, standard, self-measurable
  numbers anchored at different landmarks (waist vs. crotch) — they are
  *not* expected to sum to height (a clinical pair that does, sitting
  height + subischial leg length, bakes the head into "torso" and needs a
  stadiometer, so it doesn't fit a self-measured consumer flow). Still
  open: back waist length is harder to self-measure accurately than
  inseam (which is a well-known measurement) — self-report vs. a guided
  photo measurement is still undecided for the actual input flow.
  **Formula bug found and fixed (2026-09)**: the original
  `torso_leg_balance = (torso - leg) / max(torso, leg)` looked plausible
  but was wrong for real bodies — back waist length (~39-41cm per ASTM
  misses sizing) and inseam (~0.45-0.46 × height) are structurally
  different magnitudes for *everyone* (back waist length is roughly half
  of inseam), so the raw ratio read as strongly "long legs" regardless of
  actual proportion. The worked-example fixtures had masked this by using
  unrealistic torso values inflated to sit near leg's magnitude. Fixed by
  comparing each measurement's deviation from its *own* baseline
  ratio-to-height (mirroring `frame_scale_dev`'s approach) — see the
  formula above and `TORSO_HEIGHT_RATIO_BASELINE`/
  `LEG_HEIGHT_RATIO_BASELINE` in `balance_points.py`. Those two baselines
  are themselves guessed from general published ranges, not a rigorous
  study — same caveat as the `frame_scale` baselines below.
- Shoulder circumference is now in the v0 model as `shoulder_hip_balance`
  (implemented 2026-09) — see the formula above. It distinguishes a
  broad-shoulder/narrow-hip build from a top-heavy-by-bust build that
  would otherwise look identical on `bust_hip_balance` alone. Still not
  wired into a dedicated `effects.yaml`/`AXIS_RULES` entry of its own — no
  v0 garment technique (structured shoulders, halter necklines, raglan
  sleeves) reacts specifically to shoulder width yet; that's a separate,
  not-yet-made decision needing its own worked example.

  It does now feed `adds_volume_top`/`adds_volume_bottom` (2026-09),
  though: those were scored against `bust_hip_balance` alone, which meant
  the engine had no way to know the shoulder line was already broad — it
  would recommend adding *more* top volume onto an already-broad-shouldered
  body, and would completely miss recommending bottom volume to balance a
  broad-shouldered build with an otherwise-balanced bust. Both rules now key
  off `top_hip_balance = max(shoulder_hip_balance, bust_hip_balance)`
  (`scoring.py`'s `_axis_value`) — a derived value, not a stored
  `WomensBalancePoints` field, so it doesn't compete with the two real axes
  for `main_concern()`. Same deadzone treatment as the four zero-neutral
  axes. Pinned by
  `test_scoring.py::test_adds_volume_top_works_against_an_already_broad_shoulder`
  and `test_adds_volume_bottom_fires_for_broad_shoulders_even_with_balanced_bust`.

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
technique keys; the vocabulary has since been extended (2026-09) with 4
more, added specifically to back 4 new catalog items — `high_rise`
(`elongates_leg`, reusing the existing tag), `low_rise` (`elongates_torso`
+ `shortens_leg`, same tags `drop_waist` already uses — a low rise sits
below the natural waist the same way a dropped waist seam does),
`wide_leg` (a new tag, `adds_volume_bottom` — see below), and
`cropped_ankle_length` (`shortens_leg`). `bomber_jacket` needed no new
technique at all — it reuses `oversized_top` verbatim, since a bomber's
boxy, bulk-adding silhouette is the same real effect that technique already
models (the same reuse `oversized_jacket` already relied on). `wide_leg`'s
`adds_volume_bottom` is the one genuinely new effect tag, wired into
`AXIS_RULES` as the mirror image of `adds_volume_top` (same axis,
opposite-sign weight) — bottom volume helps a top-heavy build and works
against an already bottom-heavy one, tested in
`test_scoring.py::test_adds_volume_bottom_mirrors_adds_volume_top_with_opposite_sign`.
Further vocabulary growth stays a case-by-case decision, not a batch
exercise — each addition should be this deliberate about which existing
tag it reuses versus genuinely needing a new one.

`oversized_top` also carries `hides_waist` (2026-09) — a boxy, unshaped
silhouette is a genuine, wearer-independent fact about the technique, not
just "adds volume/bulk": it obscures whatever natural waist definition is
already there. Wired into `AXIS_RULES` as the mirror of
`defines_waist`/`clings_to_waist` (same axis and reference, opposite-sign
weight), so it only costs anything once `waist_definition` clears the same
0.15 threshold those two use — see worked example 5 above, which this
changed from `recommended` to `neutral`: the correction it makes to
`bust_hip_balance` is real, but no longer enough on its own to outweigh
hiding an already-defined waist.

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

## Avatar: to-scale, not balance-point-driven (2026-09)

`web/src/lib/avatarGeometry.ts` now draws the silhouette directly from real
`Measurements` (one shared cm-to-SVG scale for every width and length),
not from balance-point ratios — two people with the same proportions but
different absolute sizes used to render identically; now the avatar is a
true-to-scale drawing of the actual entered numbers. Circumferences convert
to a front-view width via the standard anthropometric ellipse
approximation (~10:7 circumference-to-width ratio) — an approximation, not
exact, same caveat class as `frame_scale`'s baseline. Neck/ankle aren't
measured inputs; they're drawn as a fixed proportion of shoulder/hip width
for visual completeness only. This is purely a rendering change —
`balance_points.py`, `scoring.py`, and `effects.yaml` are untouched.

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
