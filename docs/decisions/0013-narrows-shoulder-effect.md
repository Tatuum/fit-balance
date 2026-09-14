# 0013. narrows_shoulder: a dedicated shoulder_hip_balance effect

Date: 2026-09-14
Status: Accepted

## Context

NOTES.md's "Known gaps" has flagged, since decision 0002, that
`shoulder_hip_balance` has no `effects.yaml`/`AXIS_RULES` entry of its
own — every technique that reacts to top-vs-hip balance does so through
the derived `top_hip_balance = max(shoulder_hip_balance, bust_hip_balance)`
(decision [0009](0009-top-hip-balance-axis.md)), which can't distinguish a
body that's top-heavy because of broad shoulders from one that's top-heavy
because of a fuller bust. Decision
[0012](0012-garment-catalog-vocabulary-expansion.md) closed the
`adds_volume_top` coverage gap but didn't touch this one — everything it
added still scores against `top_hip_balance`. A [stitchfix.com styling
article on
the "heart"/broad-shoulder shape](https://www.stitchfix.com/women/blog/style-guide/how-to-dress-for-a-heart-body-shape/)
names scoop necklines as "streamlining the shoulders" — a real technique
whose effect is specific to shoulder width, not bust size, making it the
concrete case this gap needed.

## Decision

New effect tag `narrows_shoulder`, scored directly against
`shoulder_hip_balance` (not `top_hip_balance`):

```python
"narrows_shoulder": _AxisRule(axis="shoulder_hip_balance", weight=1),
```

Same sign convention as `adds_volume_bottom`: a positive contribution when
`shoulder_hip_balance` is positive (broad-shoulder build), since narrowing
the shoulder line corrects that reading. `shoulder_hip_balance` is already
in `DEADZONE_AXES`, so it gets the same 0.05/0.15 deadzone/pronounced
treatment as every other zero-neutral axis with no extra wiring.

New technique `scoop_neck` → `narrows_shoulder`, and a new catalog item
`scoop_neck_top` (slot: top) in `garments.yaml`.

Worked examples (pinned in `tests/test_garments.py` and
`tests/fixtures.py`):

- **Shoulder-driven**: `BROAD_SHOULDER_NARROW_HIP` (shoulder=100, bust=84,
  hip=88 — decision 0012's fixture) has `shoulder_hip_balance ≈ 0.12`
  (level 1). `scoop_neck_top` → `+1 * 1 = +1` → **recommended**.
- **Bust-driven**: a body with shoulders balanced against hip
  (`shoulder_hip_balance ≈ 0`, inside the deadzone) but a notably fuller
  bust (`bust_hip_balance` pronounced, driving `top_hip_balance` on its
  own) → `scoop_neck_top` produces **no reason at all** (shoulder_hip_balance
  is in its deadzone), while `structured_blazer` (`adds_volume_top`,
  scored against `top_hip_balance`) still correctly reads **avoid** — the
  exact distinction `top_hip_balance` alone can't make.

## Consequences

`scoring.py`'s `AXIS_RULES` gains one entry; `axis_value()` needs no
change (`shoulder_hip_balance` already resolves via the plain `getattr`
branch, unlike `top_hip_balance`'s derived max). `test_catalog_covers_all_known_techniques`
stays green since `scoop_neck` gets exactly one catalog item.
`balance_points.py`'s `shoulder_hip_balance` field comment and NOTES.md's
"Known gaps" entry for it are both updated to point here instead of
describing this as still-open. `technique_advice.py`'s `DIMENSIONS` tuple
is unchanged — `shoulder_hip_balance` still isn't a standalone reported
dimension, only `top_hip_balance` is (per its own comment, matching
`BalancePointsChart.tsx`'s display); `narrows_shoulder` shows up under the
existing "Horizontal balance" (`top_hip_balance`) advice only insofar as a
caller cross-references it, which is a smaller, separate follow-on if it
turns out to matter.
