# Discrete severity-level scoring (replaces continuous cross-axis summation)

## Context

`scoring.py`'s `score()` currently sums `contribution = weight * (axis_value - reference)`
across effect tags, where `axis_value` is each of `balance_points.py`'s 5
formulas' raw, differently-scaled output. Nothing rescales these onto a
comparable unit before summing, so an axis whose formula naturally
produces larger real-world deviations systematically dominates
`Verdict.score`, independent of whether it's actually the more meaningful
styling concern. (Superseded plan: `axis_calibration_plan.md` proposed
fixing this with real population data — ANSUR II std devs used as a
rescaling factor. Dropped in favor of this simpler approach, which needs
no external dataset.)

**The alternative:** quantize each axis's continuous deviation into a
small integer **severity level** before it's used in scoring, so every
contribution is already on the same unit ("levels", not raw ratios) —
comparable across axes by construction, with no calibration data needed.
This isn't a new category of guess for this codebase: `IMBALANCE_DEADZONE
= 0.05` and `waist_definition`'s `reference = 0.15` (`scoring.py`'s
`AXIS_RULES`) are already exactly this kind of hand-picked threshold, not
derived from data. This just extends that existing pattern to cover the
axis's full range instead of only a deadzone boundary.

## Design

**One new constant**, alongside `IMBALANCE_DEADZONE` in
`balance_points.py`:
```python
# Second magnitude band boundary, extending IMBALANCE_DEADZONE's existing
# deadzone/no-deadzone split into a 3-level scheme: within the deadzone
# (0, for axes that have one) / "notable" (1) / "pronounced" (2). A
# starting proposal verified against all 5 NOTES.md worked examples (see
# docs/decisions/0010-...), not derived from external data — same
# judgment-call category as IMBALANCE_DEADZONE and waist_definition's 0.15
# reference already are.
PRONOUNCED_THRESHOLD = 0.15
```

**New helper in `scoring.py`**, replacing the raw `(value - reference)`
term:
```python
def _signed_level(value: float, reference: float, axis: str) -> int:
    deviation = value - reference
    deadzone = IMBALANCE_DEADZONE if axis in _SCORING_DEADZONE_AXES else 0.0
    magnitude = abs(deviation)
    level = 0 if magnitude < deadzone else 1 if magnitude < PRONOUNCED_THRESHOLD else 2
    return level if deviation >= 0 else -level
```
`waist_definition` deliberately gets `deadzone = 0.0` (falls through the
`else`, since it's not in `_SCORING_DEADZONE_AXES`) — level 1 starts at
any nonzero deviation from its 0.15 reference. This matches decision
0007's existing reasoning for excluding that axis from the deadzone
(favorable-direction threshold, not "0 is neutral both ways") — this
change doesn't reopen that decision, just reuses it.

**`score()`'s contribution line becomes:**
```python
contribution = rule.weight * _signed_level(value, rule.reference, rule.axis)
```
Always an integer in `{-2, -1, 0, 1, 2}`, since `rule.weight` is always
`±1.0`. `AXIS_RULES` itself (tags → axis/weight/reference) is **unchanged**
— only how a rule's raw deviation becomes a contribution number changes.

**A small simplification falls out of this:** the existing separate
deadzone pre-check in `score()` (`if rule.axis in _SCORING_DEADZONE_AXES
and abs(value) < IMBALANCE_DEADZONE: continue`) becomes redundant —
level 0 → `contribution == 0` → already caught by the existing `if
contribution == 0: continue` a few lines later. Remove the now-dead
pre-check.

**New integer thresholds** (replacing the float ones, same bucketing
logic in `score()`, only the cutoff values change):
```python
RECOMMENDED_THRESHOLD = 1
AVOID_THRESHOLD = -1
STRONG_AVOID_THRESHOLD = -3
```

**`schemas.py`** — `Reason.contribution: float` → `int`, `Verdict.score:
float` → `int`. Not strictly required (Python/pydantic would happily
carry whole-number floats), but recommended: it makes the discrete nature
of the new scoring visible in the type itself, consistent with this
project's "editable, inspectable reasons" pitch. No frontend type change
needed (`web/src/lib/types.ts`'s `number` already covers both).

## Verified against all 5 worked examples (by hand, real numbers)

| # | body / garment | levels that fire | discrete total | verdict (≥+1 recommended, ≤−1 avoid, ≤−3 strong_avoid) | matches today's documented verdict? |
|---|---|---|---|---|---|
| 1 hourglass, bodycon+belt | `defines_waist` L1, `clings_to_waist` L1 | **+2** | recommended | ✅ |
| 2 apple, bodycon+belt | `defines_waist` L1(−), `clings_to_waist` L1(−) | **−2** | avoid | ✅ |
| 3 rectangle/petite, drop_waist | `elongates_torso` L2(−), `shortens_leg` L2(−) | **−4** | strong_avoid | ✅ |
| 4 rectangle/petite, empire+vertical | `elongates_leg` L2, `shortens_torso` L2, `reduces_bulk` L1 | **+5** | recommended | ✅ |
| 5 pear/fuller, oversized+skinny | `adds_volume_top` L1, `adds_bulk` L1(−), `hides_waist` L1(−), `reduces_bulk` L1 | **0** | neutral | ✅ |

All 5 reproduce the exact documented verdict, with comfortable margin
from every threshold — **no worked-example test needs its expected
verdict changed.** This is a materially safer outcome than the ANSUR
plan, where two examples sat on a knife's edge pending data we didn't
have yet.

## Scope notes

- `main_concern()` (`balance_points.py`) has the same underlying
  cross-axis-comparability problem (compares raw magnitudes to pick "the"
  main concern) but touches CLI output, `BalancePointsChart.tsx`, and its
  own test block — **left untouched**, same as it was scoped out of the
  ANSUR plan. Worth a `NOTES.md` "Known gaps" bullet noting it as a
  related, deliberately-deferred case that this same levels concept could
  address later.
- No external dataset, no calibration script, no `scripts/` directory,
  no `.gitignore` addition — this whole plan is self-contained within the
  existing codebase and its own worked examples.

## Files

**New:**
- `docs/decisions/0010-discrete-severity-level-scoring.md` (scaffold via
  the `new-decision` skill) — context = the cross-axis-comparability gap
  and the dropped ANSUR alternative; decision = the level scheme above;
  consequences = the worked-example table above (all 5 verified
  unchanged), the `_signed_level`/dead-pre-check simplification, and the
  `main_concern()` deferral note
- New unit tests for the level-boundary logic itself in
  `tests/test_scoring.py` (e.g. a value exactly at the 0.05 deadzone
  boundary, one just past `PRONOUNCED_THRESHOLD`, one exactly at
  `waist_definition`'s reference) — the 5 worked examples don't exercise
  every boundary, so this new logic needs its own direct coverage

**Changed:**
- `src/fit_balance/balance_points.py` — add `PRONOUNCED_THRESHOLD`
- `src/fit_balance/scoring.py` — add `_signed_level()`, rewrite the
  `contribution` line, remove the now-redundant deadzone pre-check,
  update the 3 threshold constants to their new integer values
- `src/fit_balance/schemas.py` — `Reason.contribution`/`Verdict.score`
  `float` → `int`
- `NOTES.md` — "Core architecture" #3 and "Scoring" description (no
  longer "scaled by how far from neutral" as a continuous float — now
  "quantized into one of 3 hand-picked severity levels"), "Known gaps"
  (add the `main_concern()` deferral note), link to decision 0010
- `docs/decisions/README.md` — add the 0010 row

## Verification

1. `uv run pytest` — full suite green, including the 5 existing worked
   examples (verified above to need no changes) and the new boundary tests.
2. `uv run ruff check .`
3. `./check.sh` (adds `tsc --noEmit`, `vitest run` — no frontend files
   change in this plan, so these should be no-ops, just confirming
   nothing else broke).
4. Manual CLI spot check (`uv run fit-balance ...`) against at least one
   worked example, matching `NOTES.md`'s own stated verification habit.
