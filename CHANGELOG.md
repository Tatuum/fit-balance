# Changelog

## 2026-10-07
- Document changelog script's incremental-update assumption (#7)
- Fix phase3-cli.md: Typer collapses the single-command invocation (#6)
- Fix README's Example reasons to match score()'s real output
- Second garment vocabulary expansion: 9 techniques, 8 catalog items

## 2026-10-06
- Fix stale docs: reconcile "engine" definition, update post-0015 scoring docs (#3)
- doc-audit fixes: branch protection mentions + changelog script bug (#2)
- Document that main is now branch-protected (#1)
- Add doc-audit skill, mark core docs in the Folder map instead of a separate list

## 2026-10-05
- Fix CI: install the api dependency group too
- Workflow: make the two engine-diagram docs an explicit, mandatory check
- Sync project docs with recent engine/tooling changes
- Document CI/pre-commit, adopt PR-based merge workflow
- Add CI workflow and pre-commit gate
- Workflow: codify the post-implementation doc-staleness sweep
- Merge branch 'fix-quantized-main-concern'
- Add CHANGELOG.md
- Add ADR 0015, fix decision-number refs, update CURRENT_STATE.md
- Web: consume main_concern as a list
- API: test the main_concern tie case
- Scoring reads pure quantized data
- Quantize main_concern(), surface ties instead of picking one

## 2026-10-02
- Fix main-logic-overview diagram: WomensBalancePoints, not Verdict, fans out
- Drop shape-label jargon from README example
- Document mypy in stack/architecture docs
- Add mypy as a type-checking gate
- Add main-logic-overview.md: pipeline diagram companion doc
- Fix stale NOTES.md references, renamed to CURRENT_STATE.md
- Document Phase 11's parked status and CURRENT_STATE.md's section order

## 2026-10-01
- Adopt test-seam and vertical-slice guidance in feature-spec; retire stale issue-tracker doc
- Consolidate docs source of truth: rename NOTES.md, merge tech-stack into architecture

## 2026-09-30
- Add phase write-ups to docs/project_docs/
- Restructure planning docs into specs/

## 2026-09-29
- Split Plan into Decision + Technical plan, add architecture-fit check

## 2026-09-26
- Restructure CLAUDE.md: bulleted sections, folder map, dedicated Run & test

## 2026-09-25
- Rework Workflow section: table overview + prose detail, third-person voice
- Fix stale plan.md reference in ADR 0014, clarify ADR immutability scope
- Rename plan.md to ARCHITECTURE.md
- Untrack docs/learning/ from git
- Rename docs/python_docs to docs/learning, fold in the three Claude Code guides
- Establish plan/spec/steps workflow: number docs/plans/, add template + index

## 2026-09-24
- Refine Spike 1 design in personal-fit-spike.md, mark Spike 0 done
- Remove menswear support (decision 0014)
- Add stage 2 project guide (effects table & scoring engine)
- Restructure NOTES.md for scannability

## 2026-09-23
- Add project README
- Add project_docs and python_docs personal reference folders
- Plan a personal-fit spike ahead of Stage 4.5's closet feature
- Sharpen NOTES.md prose to short sentences
- Restructure and sharpen CLAUDE.md
- Keep personal user.md notes local, not tracked

## 2026-09-22
- Plan Stage 4.5: AI-assisted features (photo closet, grounded explanations, RAG, tool-calling)

## 2026-09-21
- Document delegating-vs-manual heuristic in claude-code-setup.md

## 2026-09-20
- Configure mattpocock-skills for this repo, migrate decisions to docs/adr/

## 2026-09-19
- Add claude-code-setup.md as a living reference summary

## 2026-09-17
- Document the commit hook's silent-on-pass / loud-on-block behavior
- Add permission-boundaries.md as a quick-reference summary
- Add commit-blocking check.sh hook and auto-accept checklist

## 2026-09-16
- Ignore personal Claude Code permission settings, add setup plan
- Add guide documenting the run skill's usage and Chrome access for this repo

## 2026-09-15
- Consolidate scattered root-level plan files into docs/plans/

## 2026-09-14
- Smooth the measurement-guide silhouette and fix crotch/hip overlap
- Add single-garment balance advice: try one item, see what complements it
- Add regression test for AXIS_RULES-to-catalog producer coverage
- narrows_shoulder: a dedicated shoulder_hip_balance effect
- Expand garment catalog with realistic garment types and techniques
- Fix NOTES.md sections left stale by the frontend simplification
- Simplify frontend to measurements/silhouette/advice; add plain-language dimension descriptions
- Add per-dimension technique recommendations, independent of a combined verdict
- Remove adds_volume_top from oversized_top

## 2026-09-11
- Score against discrete severity levels, not raw axis magnitudes
- Document the main-concern label fix and avatar-overlay spike in NOTES.md
- Add implementation plan for an LLM-classified garment catalog
- Sketch a garment-corrected silhouette overlay on the avatar
- Stop labeling a favorable waist_definition as the "main concern"

## 2026-09-10
- Recommend outfits ranked by balance-point fit, not just score-on-request
- Add new-decision skill to scaffold docs/decisions/ entries
- Split dated decision narration out of NOTES.md into docs/decisions/

## 2026-09-09
- Add a workflow section to CLAUDE.md and a single check.sh gate
- Redesign balance chart as plain-language rows, no numeric scale
- Score adds_volume_top/bottom against shoulder too, not bust alone
- Use max(shoulder, bust) for frame_scale_dev, not bust alone
- Add a deadzone so small deviations aren't scored as imbalances
- Score oversized silhouettes as hiding an already-defined waist
- Match the waist-definition chart threshold to the scoring engine's
- Draw the avatar as a curvy silhouette with a head, fix torso width

## 2026-09-08
- Draw the avatar to-scale from measurements instead of balance-point ratios
- Extend garment catalog with rise/leg-width trousers and a bomber jacket
- Add manual garment-item catalog with outfit scoring and attribution
- Add shoulder axis, balance-point chart, and fix torso_leg_balance bug
- Implement stage 4: FastAPI service + React/TS web app
- Implement stages 1-3: balance-point engine, scoring, and CLI
- Save design notes: balance-point architecture, worked examples, build order
