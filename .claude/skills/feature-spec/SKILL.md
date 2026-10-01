---
name: feature-spec
description: Kicks off a new feature by finding the next incomplete phase in specs/roadmap.md, creating a git branch, interviewing the user about scope/decisions/context, and writing a dated spec directory under specs/ containing plan.md, requirements.md, and validation.md. Trigger when the user says "feature spec", "next phase", "start the next feature", or invokes /feature-spec.
---

# Feature Spec

## Workflow

### 1. Find the next phase

Read `specs/roadmap.md`. The next phase is the first section whose items are all `[ ]`. Note its name to derive the branch and directory name.

### 2. Create the branch

```
git checkout -b phase-N-<kebab-name>
```

### 3. Interview the user — BEFORE writing any files

Use `AskUserQuestion` with exactly **3 questions in one call**:

| Header | Question focus |
|--------|---------------|
| **Scope** | What the feature collects, exposes, or does — fields, behaviour, data shape |
| **Decisions** | Key implementation choices — storage, visibility, validation, UX pattern |
| **Context** | Tone, constraints, or anything shaping the spec — copy style, stack limits, open questions |

Do **not** write any files until the user has answered all three questions.

### 4. Read guidance files

Read `specs/mission.md` and `specs/architecture.md` (in full) before
drafting. Keep `specs/architecture.md`'s content for step 6 — no need
to re-read it.

### 5. Sketch test seams

Before drafting `plan.md`, identify the seam(s) at which this feature will be tested — the boundary where a test can verify behaviour without reaching into implementation details. Prefer an existing seam over a new one, and use the highest seam that still proves the behaviour (e.g. the engine's public functions, as `tests/test_balance_points.py`/`tests/test_scoring.py` already do, rather than poking internals). Fewer seams across the codebase is better — one is ideal.

Confirm the seam(s) match the user's expectations before proceeding.

### 6. Create the spec directory

Name: `specs/YYYY-MM-DD-<feature-name>/` using today's date.

#### `requirements.md`
- Scope section: what is and is not included; field/data table if applicable
- Decisions section: choices made and why (draw from user answers)
- Context section: tone rules, stack pointers, existing patterns to follow

#### `plan.md`
- Numbered task groups as **vertical slices**, not horizontal layers: each group cuts a narrow but complete path through every layer it touches (e.g. engine → API → web for a feature spanning all three) and is demoable/verifiable on its own — not "Data, then Components, then Page & Route, then Tests"
- Order groups riskiest-assumption-first — the slice most likely to invalidate the plan goes first, so it's proven (or the plan revised) before later slices build on it
- Each group has numbered sub-tasks; groups should be independently implementable

#### `validation.md`
- Automated: project test and typecheck commands pass; specific assertions required
- Testing decisions: the seam(s) chosen in step 5, what makes a good test here (behaviour, not implementation detail), and prior art — similar existing tests to model after
- Manual: walkthrough, behaviour, edge cases
- Tone check if the feature has user-facing copy
- Definition of done

### 7. Check architecture fit

Using `specs/architecture.md` (already read in step 4), append an
"## Architecture fit" section to `plan.md` answering:
- Which layer does this belong to (engine, API, web)?
- Does it respect the existing layering, or cross a boundary (e.g.
  business logic leaking into a layer meant to stay thin)?
- Does it introduce anything outside the stack, or jump ahead of the
  build order?

State the fit plainly, or name the conflict found — this must be
resolved or flagged before requesting approval.

## Constraints

- Respect the existing tech stack defined in `specs/architecture.md`'s "Tech stack" section — no new dependencies without user approval
- Follow existing conventions and patterns already established in the codebase
- Keep feature scope focused and independently shippable
- No file paths or code snippets in `requirements.md`/`plan.md` — they go stale fast. Exception: a snippet that encodes a decision more precisely than prose (a state machine, schema, or type shape) may be inlined, noted briefly as coming from a prototype
