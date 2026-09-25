# Plan log

One file per planning session (see `CLAUDE.md`'s Workflow), approved
before implementation starts. Unlike `docs/adr/`, plans are never
deleted and can be lightly edited in place — they're the rereadable
record of *how* a feature got shaped, not an immutable ruling. Template
at `TEMPLATE.md`.

`NOTES.md` and `docs/project_docs/` stay the current-state spec.
`docs/adr/` stays the curated log of hard-to-reverse engine decisions.
Start here if you want to relive how a feature was reasoned through;
start there if you want to know what's true today.

| # | Title | Status |
|---|-------|--------|
| [0001](0001-garment-catalog-plan.md) | Manual garment-item catalog + outfit scoring with attribution | Shipped — NOTES.md "Garment catalog" |
| [0002](0002-recommend-outfits-plan.md) | Outfit recommendations: ranking layer over the existing outfit scoring | Shipped — NOTES.md "Outfit recommendations" |
| [0003](0003-garment-catalog-llm-classification.md) | Real, LLM-classified garment catalog (replaces hand-authored `garments.yaml`) | Not started — deferred |
| [0004](0004-main-concern-asset-badge-fix.md) | Fix: "MAIN CONCERN" badge shown on a favorable waist_definition (asset) result | Shipped (commit `b462f8e`) |
| [0005](0005-single-garment-balance-advice.md) | Single-garment "try it on" balance advice | Shipped — NOTES.md "Single-garment balance advice" |
| [0006](0006-dimension-advice-plan.md) | Per-dimension technique recommendations with garment examples | Shipped — NOTES.md "Technique recommendations" |
| [0007](0007-discrete-scoring-plan.md) | Discrete severity-level scoring (replaces continuous cross-axis summation) | Shipped — ADR 0010 |
| [0008](0008-spec.md) | Original app spec (raw) | Superseded by 0009 |
| [0009](0009-spec-plan.md) | Hourglass silhouette goal: ranked outfits + corrected overlay | Partially shipped — NOTES.md "Avatar" (spike-quality, unwired) |
| [0010](0010-permission-constraints.md) | Set up permission constraints for Claude Code in fit-balance | Shipped — docs/permission-boundaries.md |
| [0011](0011-commit-check-hook.md) | Commit-blocking hook + auto-accept checklist | Shipped — docs/claude-code-setup.md |
| [0012](0012-personal-fit-spike.md) | Personal-fit spike: photo + self-reported tags, before Stage 4.5's closet feature | Active — Spike 0 done, Spike 1 next |
