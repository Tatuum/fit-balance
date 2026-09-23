<!--
Template for docs/project_docs/*.md — Tatiana's own stage/feature
write-ups. One file per whole stage (e.g. stage1-balance-points.md,
stage4-web-api-avatar.md), not per sub-feature.

Rules:
- Prose sentences inside each numbered section, not bare bullet
  fragments — meant to be re-readable months later without the code
  open.
- Quote the actual formula/schema/constant, not a paraphrase.
- Skip "Gotchas" entirely when there's nothing non-obvious; don't pad.
- For *why* a decision was made, link NOTES.md / docs/adr/NNNN-*.md
  instead of re-explaining it here — this doc is *how it works now*.
- If the stage grew multiple additions after its initial build, give
  each its own "## <feature name>" header, with that feature's own
  numbered breakdown underneath.

Delete this comment block when copying the template into a real file.
-->

# Stage <N> — <stage name>

<One or two sentences: what this stage delivered and why it exists —
the goal, not a restatement of the file names.>

**Files:** `path/to/file.py`, `path/to/other.py`

### 1. <First component/mechanism>

Explanation in full sentences, with a code block or formula quoted
inline wherever the actual shape/values matter (a data model's fields,
a formula, a constant) — enough that this section stands alone without
re-opening the source file.

### 2. <Next component/mechanism>

... one numbered section per real moving part (e.g. input shape →
core computation → key rule/threshold → output shape), same depth as
above. Number of sections varies by what the piece actually contains —
don't pad to a fixed count.

### Testing / verification

How correctness is actually checked (tests, worked examples, manual
verification) and where that lives.

### Gotchas / open questions

Only the non-obvious stuff — a subtlety that isn't visible just from
reading the code, an open caveat, a known gap. Omit the whole section
if there's nothing here.
