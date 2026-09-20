# 0002. Add shoulder_hip_balance axis

Date: 2026-09-08
Status: Accepted

## Context

`bust_hip_balance` alone can't distinguish a broad-shoulder/narrow-hip build
from a top-heavy-by-bust build — both read identically on that one axis, but
they're different bodies calling for different garment techniques.

## Decision

Add `shoulder_hip_balance = (shoulder - hip) / max(shoulder, hip)` as its
own balance point, using `shoulder` as a **circumference** around the
fullest part of the shoulders/upper arms (the stylist body-shape-calculator
convention) — not the tailoring point-to-point shoulder width, which is a
different scale and isn't comparable to bust/hip circumferences.

## Consequences

At the time, not wired into any `effects.yaml`/`AXIS_RULES` scoring — no
garment technique reacted to it yet (same "known fact, not yet scored"
status as `clings_to_hip`). Later partially addressed by 0009
(`top_hip_balance`); which techniques should react to shoulder width
specifically (structured shoulders, halter necklines, raglan sleeves)
remains an open, not-yet-made decision.
