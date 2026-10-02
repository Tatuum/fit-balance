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
out: Verdict
      │
      ├─────────────┬─────────────────┬──────────────────────┐
      ▼             ▼                 ▼                      ▼
┌────────────┐ ┌────────────┐ ┌────────────────────┐ ┌────────────────────┐
│ garments.py│ │recommend.py│ │technique_advice.py │ │garment_balance.py  │
└────────────┘ └────────────┘ └────────────────────┘ └────────────────────┘
   Phase 6         Phase 7           Phase 9                Phase 8
in: item_ids/  in: WomensBalance in: WomensBalance      in: WomensBalance
  WomensBalance  Points            Points                 Points + item_id
  Points
out: tuple[    out: list[        out: list[             out:
  list[          OutfitRecom-      DimensionAdvice]       GarmentBalance
  GarmentItem],  mendation]                                Advice
  GarmentAttri-
  butes] /
  list[Attri-
  butedReason]
      │             │                 │                      │
      └─────────────┴─────────┬───────┴──────────────────────┘
                              ▼
                   ┌─────────────────────────┐
                   │      api/main.py        │
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

Everything below `api/main.py` only ever calls `scoring.score()` or
reads `AXIS_RULES` — no feature layer re-derives a verdict
independently, and no shape label ever enters this path, only the
signed axes.
