# Claude Code setup for this repo

Living reference for what's actually configured for Claude Code in
fit-balance, and what's still open. Mirrors the pattern of
`docs/permission-boundaries.md` and `docs/run-skill-guide.md` — update this
in place as the setup changes, don't fork a new file.

## Configured

**Project instructions — `CLAUDE.md`**
Standing rules (balance-points-not-labels, build-order guard, worked
examples as tests) and workflow (decide-in-writing-first, one commit per
decision, `./check.sh` before done). Read automatically every session.

**Source-of-truth docs**
`NOTES.md` — current-state spec (architecture, formulas). `docs/adr/`
— one immutable file per past engine-level decision, indexed in
`docs/adr/README.md`, scaffolded by the `new-decision` skill
(`.claude/skills/new-decision/SKILL.md`). Renamed from `docs/decisions/`
on 2026-09-20 to align with `mattpocock-skills`' default ADR convention —
same files, same rules, just the directory name changed.

**Verification gate — `check.sh`**
Single script: `pytest`, `ruff check`, frontend `tsc --noEmit`, `vitest
run`. The one thing that must pass before any change counts as done.

**Commit-blocking hook**
`.claude/hooks/check-before-commit.sh`, wired as a `PreToolUse` hook on the
`Bash` matcher in `.claude/settings.local.json`. Intercepts any `git
commit` (including `--no-verify` attempts) and runs `./check.sh` first,
blocking the commit on failure. Details/rationale: `docs/plans/commit-check-hook.md`.

**Permission boundaries — `.claude/settings.local.json`**
Manual mode (never Accept-Edits/Auto). `allow`-listed: read-only commands
plus the test/lint/typecheck commands. `ask`-listed: installs, `git push`,
`curl`, `WebFetch`. `deny`-listed: `sudo`, force-push, `reset --hard`. Full
breakdown: `docs/permission-boundaries.md`.

**Plan/decision doc conventions**
- `docs/plans/<slug>.md` — per-change plan or rationale, written when a
  plan is finalized, kept afterward as historical record.
- `docs/adr/NNNN-slug.md` — immutable engine-decision log, never
  edited after acceptance (a reversal supersedes, it doesn't replace).
- `docs/` root — living, current-state reference docs (this file,
  `permission-boundaries.md`, `run-skill-guide.md`), updated in place.

**Cross-session memory**
Claude Code's own memory system (outside this repo, in
`~/.claude/projects/.../memory/`) has already recorded feedback specific
to this project — e.g. the plan/decision/reference doc split above, and to
keep plan docs lean. Persists across sessions without living in the repo.

**`mattpocock-skills` plugin**
Installed at user scope (v1.2.3, official marketplace) — adds skills like
`tdd`, `code-review`, `diagnosing-bugs`, `domain-modeling`,
`codebase-design`, `grilling`, `research`, `wizard`,
`resolving-merge-conflicts`, `writing-for-agents`. Configured for this
repo via `/setup-matt-pocock-skills`: issue tracker is GitHub
(`docs/agents/issue-tracker.md` — aspirational until a remote is added),
domain docs point at the pre-existing `docs/adr/` (renamed from
`docs/decisions/` to match) plus `NOTES.md` kept as-is
(`docs/agents/domain.md`). Both recorded in `CLAUDE.md`'s `## Agent
skills` section.

## To improve / open items

**Issue tracker points at GitHub with no remote configured.** `gh`
commands in `docs/agents/issue-tracker.md` won't resolve a repo until a
remote is added — revisit if this stays a local-only project.

**The commit-blocking hook and permission list aren't backed up anywhere.**
Both `.claude/settings.local.json` and `.claude/hooks/` are gitignored (by
design — personal to this machine). That means if this machine is lost or
the repo is re-cloned, the commit gate and permission boundaries vanish
silently, with only the prose in `docs/permission-boundaries.md` as a
recovery guide, not the actual files. Worth deciding whether to keep a
template copy checked in (e.g. `.claude/settings.local.json.example`) so
reproducing the setup elsewhere doesn't mean re-deriving it from prose.

**No project-specific `run` skill yet.** The built-in `run` skill falls
back to generic web-app patterns (documented after the fact in
`docs/run-skill-guide.md`), which on this machine meant discovering —
mid-task — that Playwright's bundled Chromium doesn't work on this macOS
version and falling back to system Chrome. Worth capturing that as a
`.claude/skills/run-fit-balance/SKILL.md` (exact launch commands, the
Chrome-channel fallback) so it's a known recipe next time, not a
rediscovery.

**`docs/plans/` has no index.** `docs/adr/` has a `README.md` table
of every decision and its status; `docs/plans/` is now 10 files deep
(`spec.md`, `spec_plan.md`, `dimension_advice_plan.md`,
`discrete_scoring_plan.md`, `garment_catalog_plan.md`,
`garment-catalog-llm-classification.md`, `main-concern-asset-badge-fix.md`,
`permission-constraints.md`, `commit-check-hook.md`,
`single-garment-balance-advice.md`) with no listing of which are live
history versus fully absorbed into `NOTES.md`. Not urgent, but will get
harder to navigate the longer it goes unindexed.
