# Plan: Quantized main_concern()

Ordered riskiest-assumption-first: the core quantization + tie-
surfacing logic is the part most likely to reveal a problem (a worked
example behaving unexpectedly, a tie showing up somewhere unplanned),
so it's proven out before anything downstream is touched.

## Group 1 — Quantize at the source, fix main_concern (engine + CLI)

The riskiest slice: the actual behavior change, fully verifiable at
the engine's own test seam without touching scoring, the API, or the
web app.

1.1 Add a per-axis reference-point table to the engine's balance-point
    layer (today this value is scattered across scoring's per-tag
    rules; only one axis is currently non-zero).
1.2 Add a quantization step — reusing the existing deadzone/pronounced-
    threshold bucketing logic verbatim, just relocated — producing a
    parallel discrete-severity-level view of the five balance-point
    axes.
1.3 Rewrite `main_concern()` to compare quantized levels instead of
    raw magnitudes, returning every axis sharing the single highest
    cleared level (a list: empty, one entry, or several on a genuine
    tie).
1.4 Update the CLI's balance-point table to badge every axis
    `main_concern()` returns, instead of assuming at most one.
1.5 Tests: re-verify all 5 worked examples' `main_concern()` result
    (one is expected to change — document why, as a deliberate,
    signed-off change, not a silent regression); add a dedicated tie
    case; add boundary tests at the deadzone/pronounced-threshold
    edges for the new quantization step, mirroring the original
    severity-level decision's own boundary tests.

## Group 2 — Scoring reads pure quantized data

Depends on Group 1's quantized representation existing. Mechanical,
but touches the core scoring contract, so verified against the full
worked-example suite before moving on.

2.1 Drop the per-tag reference value from scoring's axis-rule table;
    look up the axis's already-quantized level directly instead of
    recomputing it from the raw value and a reference.
2.2 Confirm every one of the 5 documented verdicts is byte-for-byte
    unchanged — this slice must not alter any score or verdict, only
    where the quantization math lives.

## Group 3 — API surfaces the list shape

Low-risk propagation: a type change on an existing field, no new
endpoint or behavior.

3.1 Update the main-concern field on the 4 response bodies that expose
    it, from an optional single value to a list.
3.2 Update the API tests covering those endpoints for the new shape,
    including a tie case (reusing Group 1's tie fixture if it
    produces one through the same inputs, or adding a minimal new one
    if not).

## Group 4 — Web consumes the list shape

Also low-risk propagation, dependent on Group 3's response shape.

4.1 Update the shared response type for the main-concern field across
    its call sites.
4.2 Update the chart's badge logic to label every axis in the list,
    instead of assuming one.
4.3 Manual check: the chart renders correctly both for the common
    single-concern case and a tied case.

## Architecture fit

- **Groups 1–2 are entirely engine-layer** (the `fit_balance` library)
  — no new dependency, no network boundary crossed, and the engine's
  "zero UI/network dependencies" property holds throughout. This is
  an engine change under this project's own definition (it edits the
  balance-point and scoring modules), so it closes out through the
  decision-record workflow, not just a plain merge.
- **Group 3 is API-layer** — reuses the existing response-model
  pattern (a thin layer over the engine), no new network surface,
  just a type change on a field that already exists on 4 response
  models.
- **Group 4 is web-layer** — same existing component and type, no new
  page, no new dependency.
- **No boundary crossed**: each group stays inside its own documented
  layer, and the dependency direction (engine → API → web) holds in
  both directions — nothing in the engine comes to depend on API or
  web.
- **Not ahead of the build order**: this doesn't touch or depend on
  any unshipped phase. It's a correctness fix to already-shipped work,
  not new roadmap progress.
