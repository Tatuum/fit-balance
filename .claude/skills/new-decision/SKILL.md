---
name: new-decision
description: Scaffold a new immutable engine-design decision file in docs/adr/ for the fit-balance project — finds the next number, fills in the context/decision/consequences template, and updates the docs/adr/README.md index. Use whenever a change to balance_points.py, scoring.py, or effects.yaml needs its rationale recorded, or when reversing/narrowing an earlier decision.
---

# New decision

Scaffolds one immutable file in `docs/adr/` for an engine-level
design decision (a new formula, axis, scoring rule, or a reversal of a
prior one). See `docs/adr/README.md` for why this project keeps
decision history separate from `NOTES.md` (which stays the current-state
spec only).

Args (optional): a title or short description of the decision, e.g.
`/new-decision score adds_bulk against frame_scale_dev's deadzone too`. If
not given, ask what the decision is before scaffolding — don't guess.

## Steps

1. **Find the next number.** List `docs/adr/*.md` (excluding
   `README.md`), take the highest `NNNN` prefix, use `NNNN + 1`
   (zero-padded to 4 digits, e.g. `0010`).
2. **Pick a slug** from the decision's subject: lowercase, hyphenated,
   short — matches the style of existing files (e.g.
   `0007-imbalance-deadzone.md`).
3. **Write `docs/adr/NNNN-slug.md`**:

   ```markdown
   # NNNN. <Title>

   Date: <YYYY-MM-DD, today>
   Status: Accepted

   ## Context

   <What problem or gap prompted this — one to a few sentences. Reference
   an existing decision by number if this builds on or conflicts with it.>

   ## Decision

   <The actual formula/rule/change, precisely — code-quote the formula
   where relevant.>

   ## Consequences

   <What this changes: test files updated, worked-example verdicts that
   changed, follow-on work this opens or closes.>
   ```

   Keep each section to a paragraph or two, matching the length of
   existing decisions in this directory — not an essay.
4. **If this decision reverses or narrows an earlier one**, add a one-line
   `Status: Superseded by NNNN` to the *old* file's status line only — do
   not otherwise touch its Context/Decision/Consequences content. An
   accepted decision's body is never edited after the fact.
5. **Update `docs/adr/README.md`**: add a row to the table in
   numeric order — `| [NNNN](NNNN-slug.md) | <Title> | Accepted |` — and
   update the superseded row's Status cell if step 4 applied.
6. **Update `NOTES.md`** to describe the resulting current-state behavior
   (not the history) in whichever section it belongs, with a link to the
   new decision file (`docs/adr/NNNN-slug.md`). Follow the existing
   pattern of terse current-state text plus a decision link, not a
   dated narrative paragraph.
7. **Don't commit automatically.** Leave committing to the normal
   workflow in `CLAUDE.md` — one commit per decision, after `./check.sh`
   passes and any accompanying code/test changes are made.
