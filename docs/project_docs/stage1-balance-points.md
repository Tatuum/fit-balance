# Stage 1 — Balance-point calculator

Turns a body's raw tape-measure numbers into a small set of continuous,
signed ratios — no shape category (pear/hourglass/apple) anywhere in
the logic. This is the pure-function foundation everything else in the
engine (scoring, CLI, API) builds on.

**Files:** `src/fit_balance/schemas.py`, `src/fit_balance/balance_points.py`,
`tests/test_balance_points.py`

### 1. Input shape

Two pydantic models in `schemas.py`, both flat float fields in
centimeters:

```python
class Measurements(BaseModel):        # women's v0
    shoulder: float
    bust: float
    waist: float
    hip: float
    torso: float
    leg: float
    height: float

class MenswearMeasurements(BaseModel):
    shoulder: float
    chest: float
    waist: float
    hip: float
    torso: float
    leg: float
    height: float
```

`shoulder` is a **circumference** around the fullest part of the
shoulder/upper arm — not a tailor's point-to-point shoulder width. That
keeps it on the same scale as bust/hip circumferences so the ratios
below are comparable.

### 2. Output shape

Frozen dataclasses (immutable, not pydantic — these never cross an API
boundary raw, so no validation/serialization needed):

```python
@dataclass(frozen=True)
class WomensBalancePoints:
    shoulder_hip_balance: float
    bust_hip_balance: float
    waist_definition: float
    torso_leg_balance: float
    frame_scale_dev: float
```

`MenswearBalancePoints` swaps `bust_hip_balance`/`waist_definition` for
`chest_waist_balance`/`chest_hip_balance`.

### 3. The formulas

`compute_womens_balance_points(m)`:

```python
shoulder_hip_balance = (shoulder - hip) / max(shoulder, hip)
bust_hip_balance     = (bust - hip) / max(bust, hip)
waist_definition     = 1 - waist / avg(bust, hip)
torso_leg_balance    = (torso/height - 0.245) - (leg/height - 0.455)
frame_scale_dev      = avg(max(shoulder, bust), waist, hip) / height - 0.50
```

Each reads 0 at "average/neutral" and diverges in a signed direction
that means something specific:

- `shoulder_hip_balance`: + = shoulders read wider than hips, − = hips
  wider. Kept separate from `bust_hip_balance` because a
  broad-shoulder/narrow-hip build and a top-heavy-by-bust build look
  identical on bust alone but are different builds.
- `waist_definition`: how much narrower the waist is than the average
  of bust/hip. Not symmetric-neutral — high is always favorable (an
  asset), not just "different."
- `torso_leg_balance`: each of torso and leg is compared to its own
  expected ratio-to-height first (`0.245` for torso/back-waist-length,
  `0.455` for leg/inseam), then those two deviations are subtracted.
  Comparing torso and leg directly would mislead — they're anchored at
  structurally different landmarks (nape-to-waist vs. crotch-to-floor)
  and are never close in raw magnitude on any real body, so a naive
  ratio would read "long legs" for almost everyone.
- `frame_scale_dev`: how much fuller/slighter the frame reads relative
  to height, using `max(shoulder, bust)` rather than bust alone —
  breast tissue can make bust a misleading proxy for actual frame
  width.

The `0.245` / `0.455` / `0.50` constants (`TORSO_HEIGHT_RATIO_BASELINE`,
`LEG_HEIGHT_RATIO_BASELINE`, `WOMEN_FRAME_SCALE_BASELINE`) are
placeholders picked so an average build lands near zero — not derived
from real anthropometric data yet (see "Gotchas" below).

Menswear swaps in `chest_waist_balance = (chest - waist) / chest`
(tailoring's "drop," conventionally targeting ≈0.15, not 0-neutral) and
`chest_hip_balance = (chest - hip) / max(chest, hip)`, reusing the same
`torso_leg_balance`/`frame_scale_dev` formulas with a different frame
baseline (`0.45`).

### 4. `main_concern()`

`_magnitude()` is what `main_concern()` uses to pick which of the five
balance points to call out as the body's biggest deviation.

Each balance point is a signed value — e.g. `shoulder_hip_balance` can
be +0.3 (shoulders wider) or −0.3 (hips wider). To find "which axis
deviates the most from neutral," you need the absolute value: −0.3 and
+0.3 are equally far from 0, but a plain `max()` on the signed values
would always favor positive numbers and miss a strongly negative one.

So `_magnitude(name)`:
1. Takes `abs()` of that axis's value.
2. If the axis is one of the four deadzone axes and that absolute
   value is under `0.05`, returns `0.0` instead — treating a tiny
   deviation as measurement noise, not a real imbalance.

`main_concern()` then does `max(fields, key=self._magnitude)` — picks
whichever axis has the largest magnitude — and returns `None` if even
the winner's magnitude is `0` (nothing cleared the deadzone).
`waist_definition` isn't part of that deadzone check — it's asymmetric
(favorable one direction, not "0 is neutral both ways"), so it uses its
own threshold in `scoring.py` instead.

### Testing / verification

`tests/test_balance_points.py` encodes the 5 worked examples from
NOTES.md (each originally phrased as `shape≈X`) as concrete
`Measurements` fixtures — real cm numbers chosen to produce the
intended sign/magnitude on the relevant axis — asserted directly
against the computed balance-point values (not a final verdict, since
scoring doesn't exist at this stage). Any future change to
`balance_points.py` must keep this suite green.

### Gotchas / open questions

- `frame_scale` and `torso_leg` baselines (`0.50`/`0.45`/`0.245`/`0.455`)
  are guessed placeholders, not real anthropometric reference data —
  see NOTES.md "Known gaps."
- `WomensBalancePoints.main_concern()` picks the axis with the largest
  *raw* magnitude — the same cross-axis comparability problem that
  `scoring.py`'s severity-level scoring (decision
  [0010](../adr/0010-discrete-severity-level-scoring.md)) later fixed
  for verdicts, left unfixed here since it touches the CLI and web
  chart too.
