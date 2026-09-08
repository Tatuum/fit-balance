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
bust_hip_balance   = (bust - hip) / max(bust, hip)          # + = top wider, − = bottom wider
waist_definition   = 1 - waist / avg(bust, hip)              # + = defined waist (an asset), ~0/− = no natural cinch
torso_leg_balance  = (torso - leg) / max(torso, leg)          # + = long torso, − = long legs
frame_scale_dev    = avg(bust,waist,hip)/height - baseline    # + = reads fuller relative to height, − = reads slighter
```

"Main concern" = whichever balance point has the largest absolute magnitude.
A favorable-sign value (e.g. high waist_definition) is an **asset**, not a
concern — surface it as a strength to build around, not a problem to fix.

## Balance points — menswear v0

```
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
  real anthropometric reference data, not invented cutoffs.
- Effect tags are still coarse in places — e.g. `clings_to_hip` doesn't
  distinguish hip-clinging (fine/good for most shapes) from
  waist/midsection-clinging (bad for an undefined waist). Found via a
  worked example, not chased further by hand — better to let real user
  disagreement drive which tags need splitting next.
- `torso_leg` has no defined input-collection method yet (self-report? a
  guided photo measurement?).
- Every rule change has, at least once, silently broken an earlier-correct
  worked example (an "apple + bodycon" regression happened this way). The
  worked examples below need to become actual automated tests before the
  rule set grows much further — hand-verifying by re-reading is not going
  to scale.

## Worked examples to encode as regression tests first

```
1. shape≈hourglass, frame_scale=balanced,  garment=[sheath_bodycon, belted_natural_waist] → recommended
2. shape≈apple,     torso_leg=long_torso,  garment=[sheath_bodycon, belted_natural_waist] → avoid
3. shape≈rectangle, torso_leg=long_torso, height=petite, garment=[drop_waist]              → strong avoid
4. shape≈rectangle, torso_leg=long_torso, height=petite, garment=[empire_waistline, vertical_detail] → recommended
5. shape≈pear,      frame_scale=fuller,   garment=[oversized_top, skinny_straight]         → recommended, with a noted tension (shape wants some added volume on top; frame_scale wants less overall bulk — surface both)
```

## Recommended build order

1. Pure-function balance-point calculator + the 5 tests above as actual
   automated tests. No UI, no images yet.
2. `effects.yaml` + scoring function that returns `(verdict, reasons[])`.
3. A CLI or notebook: type in measurements + a garment's attributes → get
   verdict + reasons. This alone validates whether the rules *feel* right
   before any image work happens.
4. Only after (3) feels right: a parametric SVG avatar to visualize
   recommended silhouettes generically (no photorealism needed here).
5. Only after (4): garment-photo → attribute extraction (pose estimation +
   segmentation) for "upload a real item, tell me if it suits me."
6. Later: multi-garment outfit parsing for "recreate this inspo look,
   adjusted for my proportions."

Do not start with image processing or garment photo parsing — everything
useful and differentiated is in steps 1–3, and they need zero computer
vision.
