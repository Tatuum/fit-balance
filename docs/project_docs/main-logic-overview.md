# Main logic overview

`CURRENT_STATE.md` is the source of truth for the formulas and the
reasoning behind each layer. This file is a companion diagram showing
how the engine and the feature layers built on top of it fit together.

## Input / output shape

What goes in and what comes out of the core pipeline (`schemas.py`),
unchanged from the pure functions all the way to the API's
request/response bodies:

```python
class Measurements(BaseModel):   # input — body
    shoulder: float              # circumference, not tailoring width
    bust: float
    waist: float
    hip: float
    torso: float                 # back waist length
    leg: float                   # inseam
    height: float

class GarmentAttributes(BaseModel):  # input — garment
    techniques: list[str]            # keys into effects.yaml

class Verdict(BaseModel):        # output
    recommendation: Literal["recommended", "neutral", "avoid", "strong_avoid"]
    score: int
    reasons: list[Reason]

class Reason(BaseModel):         # one line of the verdict's "why"
    tag: str
    axis: str
    contribution: int            # discrete severity level, not raw balance-point value
    direction: Literal["+", "-"]
```

`WomensBalancePoints` (the midpoint between the two input models and
the verdict) is not a pydantic model — a frozen `dataclass`, since it
never crosses an API boundary raw:

```python
@dataclass(frozen=True)
class WomensBalancePoints:
    shoulder_hip_balance: float
    bust_hip_balance: float
    waist_definition: float
    torso_leg_balance: float
    frame_scale_dev: float
```

`balance_points.quantize()` reduces each of those five raw floats to a
small severity level (`QuantizedBalancePoints`, same five axes, each an
`int`) — the shared comparison basis `main_concern()` and `scoring.py`
both read instead of comparing raw magnitudes directly (decision
[0015](../adr/0015-quantized-main-concern.md)):

```python
@dataclass(frozen=True)
class QuantizedBalancePoints:
    shoulder_hip_balance: int
    bust_hip_balance: int
    waist_definition: int
    torso_leg_balance: int
    frame_scale_dev: int
```

## Pipeline

```
in: Measurements
      │
      ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                     ENGINE                          ┃
┃  (CLAUDE.md: an engine change = an edit to any      ┃
┃   of these three files)                             ┃
┃                                                     ┃
┃  ┌───────────────────────┐                          ┃
┃  │   balance_points.py   │                          ┃
┃  └───────────────────────┘                          ┃
┃          Phase 1                                    ┃
┃        │                                            ┃
┃        ▼                                            ┃
┃  WomensBalancePoints                                ┃
┃        │                                            ┃
┃        │     in: GarmentAttributes                  ┃
┃        │            │                               ┃
┃        ▼            ▼                               ┃
┃  ┌───────────────────────┐   ┌──────────────┐       ┃
┃  │      scoring.py       │◄──│ effects.yaml │       ┃
┃  └───────────────────────┘   └──────────────┘       ┃
┃          Phase 2                                    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
      │
      ▼
out: WomensBalancePoints — this is the shared artifact every feature
     layer below actually takes as input (not `Verdict`: `scoring.py`
     is a function each layer below calls on its own, as many times as
     it needs, not a pipeline stage whose output is piped downstream)
      │
      ├─────────────┬─────────────────┬──────────────────────┐
      ▼             ▼                 ▼                      ▼
┌────────────┐ ┌────────────┐ ┌────────────────────┐ ┌────────────────────┐
│ garments.py│ │recommend.py│ │technique_advice.py │ │garment_balance.py  │
└────────────┘ └────────────┘ └────────────────────┘ └────────────────────┘
   Phase 6         Phase 7           Phase 9                Phase 8
in: item_ids   in: WomensBalance in: WomensBalance      in: WomensBalance
  (catalog       Points            Points                 Points + item_id
  lookup only)
calls
scoring.score()?
  no              yes, once per     no — reads            yes, once for
                   candidate         AXIS_RULES/            the one item
                                     axis_value/
                                     axis_level
                                     directly instead
                                     of a combined
                                     Verdict
out: tuple[    out: list[        out: list[             out:
  list[          OutfitRecom-      DimensionAdvice]       GarmentBalance
  GarmentItem],  mendation]                                Advice
  GarmentAttri-  (.verdict is                               (.verdict is
  butes] /        a Verdict)                                 a Verdict)
  list[Attri-
  butedReason]
      │             │                 │                      │
GET /garments  POST /recommend-  POST /technique-        POST /balance-
                 outfits           recommendations         garment
      │             │                 │                      │
      └─────────────┴─────────┬───────┴──────────────────────┘
                              ▼
                   ┌─────────────────────────┐
                   │      api/main.py        │
                   │  (also calls            │
                   │  scoring.score()        │
                   │  directly, for          │
                   │  POST /score and        │
                   │  POST /score-outfit)    │
                   └─────────────────────────┘
                            Phase 4
                              │
                   ┌──────────┴──────────┐
                   ▼                     ▼
            ┌────────────┐        ┌────────────┐
            │   cli.py   │        │    web/    │
            └────────────┘        └────────────┘
              Phase 3                Phase 5
```

Every feature layer that needs a verdict calls the same
`scoring.score()` itself — `recommend.py` once per candidate outfit,
`garment_balance.py` once for the one item it's given — rather than
reimplementing the scoring logic or receiving a pre-computed `Verdict`
from upstream. `garments.py` never touches scoring at all (pure
catalog lookup); `technique_advice.py` reads `AXIS_RULES`/`axis_value`/
`axis_level` directly instead of producing a combined `Verdict`, by
design (see CURRENT_STATE.md's "Technique recommendations" section).
`axis_level` reads the already-quantized level off
`balance_points.quantize()`'s output — the old `signed_level`, which
computed that same level from a raw value and a reference, moved into
`balance_points.py` and was renamed `quantize_axis()` (decision 0015).
`api/main.py` itself also calls `scoring.score()` directly for `/score`
and `/score-outfit` — those two endpoints don't go through any of the
four feature-layer boxes above. No shape label ever enters this path,
only the signed axes.
