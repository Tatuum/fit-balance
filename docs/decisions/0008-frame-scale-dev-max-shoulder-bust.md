# 0008. frame_scale_dev uses max(shoulder, bust)

Date: 2026-09-09
Status: Accepted

## Context

`frame_scale_dev` averaged bust+waist+hip only. Bust size is confounded by
breast tissue independent of actual frame/width, so using it alone can
undercount a broad-shouldered, less-busty build and overcount a
fuller-busted, narrow-shouldered one.

## Decision

`frame_scale_dev = avg(max(shoulder, bust), waist, hip)/height - baseline`.
Whichever of shoulder or bust is actually wider drives the "how fuller does
the top read" signal.

`WOMEN_FRAME_SCALE_BASELINE` (0.50) left unchanged: across the 5
worked-example fixtures, shoulder exceeds bust by only ~0.5-0.6cm where it
exceeds it at all (`PEAR_FULLER` has bust > shoulder, so it's unaffected) —
too small a shift to justify a new guessed number on top of an
already-guessed baseline.

## Consequences

No worked-example verdict changed. Revisit the baseline alongside real
anthropometric reference data (see "known gaps" in `NOTES.md`).
