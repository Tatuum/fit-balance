<!--
Template for docs/plans/NNNN-slug.md — one file per planning session,
approved before implementation starts (see CLAUDE.md's Workflow).

Rules:
- Number sequentially: check docs/plans/README.md for the highest
  existing number, use the next one.
- Write to be reread, not skimmed once — this is your study copy,
  months later, without the conversation open. Quote actual
  formulas/schemas/interfaces where the exact shape matters.
- Worked example is required for any engine change (balance_points.py
  / effects.yaml / scoring.py) — state it before implementing, per
  CLAUDE.md's standing rule. Omit the section entirely otherwise.
- Steps gets filled in once the sections above are approved — a
  separate checkpoint, not written on the first pass.
- Don't rewrite sections when a decision changes mid-implementation —
  append a dated note under Updates instead.
- Delete this comment block when copying into a real file.
-->

# NNNN. <Plan title>

Date: <YYYY-MM-DD>
Status: Active
GitHub: <#NN — added once the spec issue is published, omit until then>

## Context

What prompted this. What exists today, what's missing or wrong, why it
matters now.

## Options considered

<Omit if there was genuinely only one reasonable approach.>
Alternatives on the table, and why each was or wasn't chosen.

## Decision

The approach actually chosen, detailed enough that implementation is
unambiguous.

## Worked example

<Required only for a plan touching balance_points.py / effects.yaml /
scoring.py.>
"Body with <balance points> + garment with <technique> → verdict <X>,
because <reasoning>." Becomes a test in tests/test_scoring.py.

## Out of scope

What this plan deliberately does not cover.

## Steps

<Filled in once Context/Decision above are approved.>

- [ ] Step 1 — <what it delivers> (GitHub: #NN)
- [ ] Step 2 — <what it delivers, note if blocked by Step 1> (GitHub: #NN)

## Verification

How this gets checked — which tests, `./check.sh`, manual steps if any.

## Updates

<Dated notes for any decision that changed mid-implementation.>

## Closed out

<Filled in at stage 6: what NOTES.md/project_docs/ADR now hold the
current truth.>
