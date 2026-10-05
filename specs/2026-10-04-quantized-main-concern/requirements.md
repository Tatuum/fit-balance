# Requirements: Quantized main_concern()

## Scope

In scope:
- A per-axis reference point for quantization, defined once in the
  engine's balance-point layer, replacing the per-tag reference values
  currently scattered across scoring's axis-rule table.
- A quantization step that converts each raw balance-point axis into
  the same small discrete severity level scoring already uses, run
  immediately after the raw balance points are computed.
- `main_concern()` rewritten to compare quantized severity levels
  instead of raw magnitudes, and to return **every** axis that shares
  the single highest cleared severity level — not just one. Empty when
  nothing clears the deadzone, a single entry for a clear winner, two
  or more entries for a genuine tie.
- Scoring's axis-rule table drops its per-tag reference value, since
  quantization now happens upstream; scoring reads the already-
  quantized level directly instead of computing it itself.
- Every consumer of `main_concern()` — the CLI's balance-point table,
  the web chart's badge, and the API response field exposed by 4
  endpoints (`/score`, `/score-outfit`, `/recommend-outfits`,
  `/balance-garment`) — updated to handle a list instead of a single
  optional value.

Out of scope:
- `top_hip_balance`'s combining rule (max of `shoulder_hip_balance`
  and `bust_hip_balance`). Proven equivalent under this change
  (quantize-then-max equals max-then-quantize, since the quantization
  function is monotonic) — left untouched.
- The deadzone/pronounced-threshold constants themselves, or any
  axis's scoring weight/direction. This is a comparison-logic fix, not
  a rule change.
- Garment scoring/verdict behavior. All 5 worked examples' verdicts
  must stay byte-for-byte identical.
- The per-dimension technique-recommendations endpoint, which already
  reports every axis independently and never used `main_concern()`.

## Decisions

- **Ties are surfaced, not resolved.** When two or more axes share the
  single highest cleared severity level, `main_concern()` returns all
  of them rather than picking one via a tie-break heuristic. User's
  call: "need to know all if we can't find one main concern."
- **Quantization moves upstream**, into the engine's balance-point
  layer, immediately after the raw continuous values are computed —
  not deferred into scoring. Scoring becomes a pure consumer of
  already-quantized data for its own axis-rule lookups.
- **Scoring's axis-rule table is simplified in the same change**
  (drops its now-redundant per-tag reference value), rather than left
  as dead data for a later cleanup.
- **Recorded as a new, separate decision record** that references the
  original severity-level decision as a followup — that original
  record is left untouched as an immutable historical record, matching
  how prior follow-on decisions have been handled.

## Context

- This closes a gap the original severity-level decision explicitly
  flagged as future work: `main_concern()` has the identical
  cross-axis raw-magnitude-comparison problem that decision fixed for
  scoring, but was deliberately left unfixed at the time, pending "a
  future decision."
- `main_concern()` is purely a display/labeling signal everywhere it's
  used — it has never driven scoring, ranking, or any decision logic.
  This change can only affect what gets labeled "the main concern" in
  the UI/CLI/API; it cannot change a verdict, a score, or an outfit's
  rank.
- The raw continuous balance-point values stay exactly as they are
  today — unchanged formulas, unchanged display. This is additive (a
  new quantized representation computed alongside the existing raw
  one), not a replacement of any existing field.
- The mission's one fixed rule — continuous signed balance points
  drive scoring, never a shape category — is unaffected: this only
  changes how axes are compared for a label, not what drives scoring.
