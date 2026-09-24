# 0014. Remove menswear support

Date: 2026-09-24
Status: Accepted

## Context

`MenswearMeasurements` (`schemas.py`) and `MenswearBalancePoints` /
`compute_menswear_balance_points` / `MEN_FRAME_SCALE_BASELINE`
(`balance_points.py`) were scaffolded in stage 1 alongside the women's
v0 formulas, per the original `plan.md` design. They were never wired
into anything: no test in `tests/` exercises them, no CLI flag selects
them, no API endpoint accepts `MenswearMeasurements`, and no frontend
code references them. Stage 1 through 4 shipped entirely on the
women's v0 formulas. The menswear code has sat as unused, unvalidated
surface area since stage 1 — clutter with no working feature behind
it.

## Decision

Delete menswear support entirely rather than let it keep sitting
unused: `MenswearMeasurements` from `schemas.py`; `MenswearBalancePoints`,
`compute_menswear_balance_points`, and `MEN_FRAME_SCALE_BASELINE` from
`balance_points.py`; and the corresponding exports from
`src/fit_balance/__init__.py`. `WOMEN_FRAME_SCALE_BASELINE` is
untouched (unrelated to this decision) but its docstring comment,
which referenced `MenswearMeasurements`, is narrowed to `Measurements`
only.

Per YAGNI: menswear support can be reintroduced later, but only when
there's an actual need for it — as a fresh formula-design pass with
its own worked examples and tests, not by restoring this unvalidated
code as-is.

## Consequences

`balance_points.py` now only defines the women's v0 formula set;
`WomensBalancePoints` and `compute_womens_balance_points` are the only
balance-point calculator. `NOTES.md`'s "Balance points — menswear v0"
section is removed, and "Core architecture" / "Balance points —
women's v0" no longer frame women's as one of two variants.
`plan.md`'s architecture diagram and stage 1 description are updated
to match, since they described the original two-variant plan. No test
file changes needed — nothing in `tests/` referenced the menswear
code, so the existing suite (including all 5 worked examples) is
unaffected.
