# 0004. Fix: "MAIN CONCERN" badge shown on a favorable waist_definition (asset) result

Date: 2026-09-11
Status: Shipped (commit `b462f8e`) — see NOTES.md "Main concern"

**Implemented** (commit `b462f8e`) — see NOTES.md's "Main concern"
paragraph for the current-state summary.

## Context

Reported case: measurements read as bust-waist-hip ≈ 90-60-70. Computed:
`bust_hip_balance = (90-70)/90 ≈ 0.222`, `waist_definition = 1 - 60/80 = 0.25`.
`WomensBalancePoints.main_concern()` (`src/fit_balance/balance_points.py`)
correctly names `waist_definition` — it has the larger raw magnitude, per its
documented "largest absolute magnitude" rule.

The bug: both the web UI and the CLI unconditionally label whatever
`main_concern` names as "(main concern)" / a "MAIN CONCERN" badge — even
when that axis is `waist_definition` reading as *favorable*. The result is
literally self-contradictory copy: **"Waist definition: defined waist (an
asset) — MAIN CONCERN"**.

`balance_points.py`'s own docstring already says the right thing: *"A
favorable-sign value (e.g. high `waist_definition`) is an asset, not a
concern — callers should check the sign before treating this as a
problem."* Neither `src/fit_balance/cli.py` nor
`web/src/components/BalancePointsChart.tsx` does that check — this is a gap
between the documented contract and the two consumers, not a flaw in
`main_concern()` itself.

Confirmed via `scoring.py`: `score()` never calls `main_concern()` at all —
verdict/reasons computation is entirely independent per-technique/per-axis.
So this is purely a headline-label bug, not a scoring-correctness bug, and
touches neither `balance_points.py`, `effects.yaml`, nor `scoring.py` —
per CLAUDE.md's workflow rule, that means **no `docs/decisions/` entry is
required** (that rule is scoped to changes in those three files).

## Fix

Presentation-layer only, in the two surfaces that render the label:

**1. `src/fit_balance/cli.py`** (~line 80-84): currently
```python
label = f"{axis_name} (main concern)" if axis_name == main_concern else axis_name
```
Change to special-case `waist_definition` reading favorable (`value >= 0.15`
— the same threshold `AXIS_RULES["defines_waist"].reference` and
`BalancePointsChart`'s `AXIS_META.waist_definition.isBalanced` already use):
label it `"waist_definition (key asset)"` instead of `"(main concern)"`.
Every other case (the four deadzone axes, or an unfavorable
`waist_definition`) keeps the existing `"(main concern)"` label unchanged —
those never carry an asset framing today.

**2. `web/src/components/BalancePointsChart.tsx`**: extract a small pure
helper (e.g. `mainConcernBadgeText(axis: SingleAxis, balanced: boolean):
string`, returning `'key asset'` when `axis === 'waist_definition' &&
balanced`, else `'main concern'`) and use it in place of the hardcoded
`'main concern'` string on the per-axis row's badge. The combined "Top vs
hip" row never has this asset framing (shoulder/bust-hip balance has no
favorable direction), so it's unaffected. Add a small unit test for the new
pure helper (colocated with the component or in `web/src/lib/`, matching
how `avatarGeometry.ts`/`garments.ts` keep pure logic unit-testable) — no
React Testing Library/jsdom needed since the helper itself takes no
DOM/props, matching this project's existing test style (there's no
component-rendering test infra in this repo today, and this fix doesn't
need to add one).

**3. `web/src/App.css`**: give the asset-badge case a distinct, positive
(not warning-toned) style — reuse the existing green from
`.balance-dot-balanced` (`#2e9e4a`) for a new `.balance-badge-asset` class,
applied conditionally alongside the existing `.balance-badge`.

## Out of scope (flagged, not being changed)

- **Not renaming** `main_concern()`/the API's `main_concern` field/NOTES.md
  terminology — that's a bigger blast-radius change (API contract, `cli.py`,
  `api/main.py`'s response models, `web/src/lib/types.ts`, every test
  referencing the field) for a problem the docstring already anticipated
  correctly; the two consumers just need to honor it.
- **Not changing how `main_concern()` picks a winner** (raw-magnitude
  comparison across favorable/unfavorable axes). In this exact case it
  doesn't hide information either way — `bust_hip_balance` still renders as
  its own "Top vs hip: ..." row regardless of which axis wins the badge, so
  nothing is suppressed, only the badge placement was contradictory.

## Verification

- `uv run fit-balance score ...` (or equivalent CLI invocation) against
  measurements reproducing this case (bust=90, waist=60, hip=70, plus
  placeholder shoulder/torso/leg/height) — confirm the balance-points table
  now prints `waist_definition (key asset)`, not `(main concern)`.
- `npx vitest run` — new pure-helper test green, existing suite unaffected.
- `npx tsc --noEmit` clean.
- Manually reload the web UI with the same measurements, confirm the
  "Waist definition" row shows a "key asset" badge instead of "main
  concern", styled distinctly (green, not the neutral/warning badge color).
- `./check.sh` green (pytest untouched/still passing, ruff, tsc, vitest).
