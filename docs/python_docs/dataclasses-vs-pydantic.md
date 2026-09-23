# dataclasses vs pydantic

## What they are

Both are ways to define a class that's just "a bag of typed fields"
without hand-writing `__init__`, `__eq__`, `__repr__` yourself.

- **`@dataclass`** (Python's standard library, `dataclasses` module) —
  generates that boilerplate from field annotations. No validation: if
  you pass a string where a float was declared, it just accepts it
  silently. No JSON conversion built in.
- **`pydantic.BaseModel`** — same idea, but adds runtime
  **validation** (wrong type → raises an error) and **serialization**
  (`.model_dump()` → dict, and FastAPI uses it to parse incoming JSON
  into the model automatically, and outgoing models back into JSON).

## Why this project uses both

The rule, consistently applied across the codebase: **pydantic at the
boundary, dataclass internally.**

- **`schemas.py`** — `Measurements`, `MenswearMeasurements`,
  `GarmentAttributes`, `Reason`, `Verdict` — all `pydantic.BaseModel`.
  These are exactly the objects that cross the API: a user's raw JSON
  body has to be *validated* into `Measurements` (catch a malformed
  request before it hits any math), and `Verdict` has to be
  *serialized* back into JSON. `garments.py`'s `AttributedReason` is
  pydantic for the same reason — it's part of `/score-outfit`'s
  response.

- **Everywhere else** — `WomensBalancePoints`/`MenswearBalancePoints`
  (`balance_points.py`), the scoring result (`scoring.py`), the advice
  structures (`technique_advice.py`, `garment_balance.py`), the
  recommendation/catalog structures (`recommend.py`, `garments.py`) —
  all `@dataclass(frozen=True)`. These are never built from raw
  external input; they're always *computed* by a pure function from an
  already-validated `Measurements`/`Verdict`. There's nothing left to
  validate, so pydantic's extra machinery (and dependency weight) buys
  nothing — a plain dataclass is the lighter, stdlib-only choice.

`frozen=True` specifically means immutable — once built, fields can't
be reassigned. That matches the engine's "pure functions in, pure data
out" style: nothing downstream should be able to mutate a
balance-point or verdict object after the fact.

## How the two meet

`api/main.py` imports `dataclasses.asdict` — when a route needs to
turn an internal dataclass result (e.g. from `recommend.py`) into an
API response, it converts it to a plain dict with `asdict()`, and
FastAPI/pydantic handles turning that dict into JSON. That's the one
seam where the two systems touch.
