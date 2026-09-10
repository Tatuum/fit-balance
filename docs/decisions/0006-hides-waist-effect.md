# 0006. oversized_top gains hides_waist

Date: 2026-09-09
Status: Accepted

## Context

Worked example 5 (pear + fuller frame, `oversized_top` + `skinny_straight`)
scored `recommended`. But for a body whose waist is already well-defined,
an oversized/boxy silhouette doesn't just add volume and bulk — it obscures
whatever natural waist definition is already there. That's a genuine,
wearer-independent fact about the technique (per the effects-table
architecture: facts about the technique, not the wearer), missing from
`effects.yaml`.

## Decision

Add `hides_waist` to `oversized_top`'s effects. Wire it into `AXIS_RULES` as
the mirror of `defines_waist`/`clings_to_waist`: same axis
(`waist_definition`) and reference (0.15), opposite-sign weight (-1.0) — so
it only costs anything once `waist_definition` clears the same threshold
those two use; hiding a waist that was never defined isn't a loss.

## Consequences

Changes worked example 5's outcome from `recommended` to `neutral`: the
correction it makes to `bust_hip_balance` is real, but no longer enough on
its own to outweigh hiding an already-defined waist. `NOTES.md`, and
`tests/test_scoring.py`, `tests/test_api.py`, `tests/test_garments.py` all
updated to reflect the new expected verdict — a deliberate, documented
change to a worked example, not a silent regression.
