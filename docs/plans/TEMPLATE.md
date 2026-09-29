<!--
Template for docs/plans/NNNN-slug.md — one file per planning session,
approved before implementation starts (see CLAUDE.md's Workflow).

Rules:
- Number sequentially: check docs/plans/README.md for the highest
  existing number, use the next one.
- Write to be reread, not skimmed once — this is your study copy,
  months later, without the conversation open. Quote actual
  formulas/schemas/interfaces where the exact shape matters.
- Requirements (only) is plain behavior — no file names, libraries, or
  technical terms. Every section after it keeps full technical detail,
  same as before.
- Requirements = what. Context = why, now. Don't collapse them.
- Requirements through Decision are Workflow stage 1 (Shape)'s own
  output — write them straight from that conversation, not as a
  separate later pass. Get this approved before stage 2 starts.
- Technical plan is Workflow stage 2 (Plan) — only written once stage
  1's Decision is approved. Exact detail: files touched,
  functions/schemas/data shapes, sequencing. Concrete enough that
  Steps is just this broken into a checklist.
- How it fits into existing architecture sits near the top (right
  after Context) so the fit conclusion is easy to spot on a skim — but
  is still filled in last, checking Decision + Technical plan together
  against `ARCHITECTURE.md`. Write the sections in document order;
  fill this one in once Technical plan is done, then go back and drop
  the conclusion in at the top. Required before stage 2's approval,
  same checkpoint as Technical plan.
- Worked example is required for any engine change (balance_points.py
  / effects.yaml / scoring.py) — state it before implementing, per
  CLAUDE.md's standing rule. Omit the section entirely otherwise.
- Steps gets filled in once Technical plan is approved — Workflow
  stage 4, not written on the first pass.
- Don't rewrite sections when a decision changes mid-implementation —
  append a dated note under Updates instead.
- Delete this comment block when copying into a real file.
-->

# NNNN. <Plan title>

Date: <YYYY-MM-DD>
Status: Active
GitHub: <#NN — added once the spec issue is published, omit until then>

## Requirements

<Plain, short bullet statements of what the system should do — no
tech names, no file paths, one behavior per line.>

- <Behavior 1>
- <Behavior 2>

## Context

Why this, why now — not what it does (Requirements, above). What's
missing or broken today that this responds to.

## How it fits into existing architecture

<Filled in last — once Decision and Technical plan below are both
done — then dropped in here so it's visible on a skim. Checks
Decision + Technical plan together against `ARCHITECTURE.md`:>
- Which stage/layer does this belong to (engine, API, web — see
  `ARCHITECTURE.md`'s architecture diagram)?
- Does it respect the existing layering, or does it cross a boundary
  `ARCHITECTURE.md` draws (e.g. business logic leaking into a layer
  meant to stay thin)?
- Does it introduce anything outside `ARCHITECTURE.md`'s stack, or
  jump ahead of the build order (see CLAUDE.md's Standing rules)?

State the fit plainly, or name the conflict found. **Wait for explicit
approval before breaking Technical plan into Steps.**

## Options considered

<Omit if there was genuinely only one reasonable approach.>
Alternatives on the table, and why each was or wasn't chosen.

## Decision

The approach actually chosen — the bet being made and why. High-level:
enough to evaluate and approve, not yet exact implementation detail.
**Wait for explicit approval before moving to stage 2 (Plan) below.**

## Technical plan

<Workflow stage 2 — filled in once Decision above is approved, not
written on the first pass.>

Exact implementation detail: files touched, functions/schemas/data
shapes affected, sequencing. Concrete enough that a reader could
implement it without guessing. **Wait for explicit approval before
breaking this into Steps** (see "How it fits into existing
architecture", above, for the architecture check before that
approval).

## Worked example

<Required only for a plan touching balance_points.py / effects.yaml /
scoring.py.>
"Body with <balance points> + garment with <technique> → verdict <X>,
because <reasoning>." Becomes a test in tests/test_scoring.py.

## Out of scope

What this plan deliberately does not cover.

## Steps

<Filled in once Technical plan above is approved.>

- [ ] Step 1 — <what it delivers> (GitHub: #NN)
- [ ] Step 2 — <what it delivers, note if blocked by Step 1> (GitHub: #NN)

## Verification

How this gets checked — which tests, `./check.sh`, manual steps if any.

## Updates

<Dated notes for any decision that changed mid-implementation.>

## Closed out

<Filled in at stage 6: what NOTES.md/project_docs/ADR now hold the
current truth.>
