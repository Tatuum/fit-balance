# 0011. Remove adds_volume_top from oversized_top

Date: 2026-09-14
Status: Accepted

## Context

`oversized_top`'s `effects.yaml` entry carried `adds_volume_top`,
`adds_bulk`, and `hides_waist`. `adds_volume_top` implies a technique
specifically widens the top of the silhouette (the mirror of
`adds_volume_bottom`/`wide_leg`) — but a boxy, uniformly loose cut doesn't
target width at the top specifically; it just reads as more bulk overall,
which `adds_bulk` already models. Attributing both to the same technique
double-counted the same real-world effect under two different tags.

## Decision

`oversized_top` keeps `adds_bulk` and `hides_waist`, loses
`adds_volume_top`. `adds_volume_top` stays in `scoring.py`'s `AXIS_RULES`
— no `effects.yaml` technique currently produces it, the same "known fact,
not yet scored" situation `clings_to_hip` is in, just inverted (a scored
rule with no technique to fire it, not a technique effect with no scoring
rule). It's kept for a future technique that genuinely targets top width
specifically (structured/padded shoulders, puff sleeves — see `NOTES.md`'s
`shoulder_hip_balance` known gap), not deleted outright.

## Consequences

Changes worked example 5's outcome from `neutral` to `avoid`: pear/fuller
+ `oversized_top`/`skinny_straight` no longer gets any credit toward
`top_hip_balance` (that reason simply doesn't fire anymore), leaving only
`hides_waist` and `adds_bulk` working against it and `reduces_bulk`
working for it — net negative. `NOTES.md`, `tests/test_scoring.py`, and
`tests/test_garments.py`/`tests/test_api.py`'s worked-example-5 assertions
updated to `avoid`, a deliberate, documented change (same precedent as
decision 0006). `tests/test_scoring.py::test_adds_volume_top_works_against_an_already_broad_shoulder`
removed — its premise (`oversized_top` carrying `adds_volume_top`) no
longer holds, and no other technique currently produces that tag, so the
behavior it pinned isn't reachable through any real garment right now.
