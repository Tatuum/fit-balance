# Claude Code setup for this repo

Living reference for what's actually configured for Claude Code in
fit-balance, and what's still open. Mirrors the pattern of
`docs/learning/permission-boundaries.md` and `docs/learning/run-skill-guide.md` — update this
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
blocking the commit on failure. Details/rationale: `docs/plans/0011-commit-check-hook.md`.

**Permission boundaries — `.claude/settings.local.json`**
Manual mode (never Accept-Edits/Auto). `allow`-listed: read-only commands
plus the test/lint/typecheck commands. `ask`-listed: installs, `git push`,
`curl`, `WebFetch`. `deny`-listed: `sudo`, force-push, `reset --hard`. Full
breakdown: `docs/learning/permission-boundaries.md`.

**Plan/spec/decision doc conventions**
- `docs/plans/NNNN-slug.md` — one file per planning session (see
  `CLAUDE.md`'s Workflow), numbered like `docs/adr/`, indexed in
  `docs/plans/README.md`, template at `docs/plans/TEMPLATE.md`. Never
  deleted; can be lightly edited in place (small corrections) or
  appended to (`## Updates`, for an actual change of decision).
- GitHub issues (`Tatuum/fit-balance`, via `gh`) — the spec (Workflow
  stage 3) and per-step tickets (stage 4) for a plan, cross-linked to
  its `docs/plans/` file. See `docs/agents/issue-tracker.md`.
- `docs/adr/NNNN-slug.md` — immutable engine-decision log, never
  edited after acceptance (a reversal supersedes, it doesn't replace).
- `docs/learning/` — living, current-state reference/study docs (this
  file, `permission-boundaries.md`, `run-skill-guide.md`,
  `dataclasses-vs-pydantic.md`), updated in place.

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

## Delegating vs. doing it yourself

Heuristic: delegate what you can verify (code changes — checked by
`check.sh`/tests); do it yourself what you can't yet verify (git/GitHub
actions, until fluent with them), and treat hard-to-reverse actions as
manual regardless of fluency. Consistency between delegated and manual
work comes from the same written rules applying to both, not from who
does the work:

> Agentic development forces externalization. The agent has no memory or
> intuition to fall back on between sessions, so anything you want
> followed consistently has to become a written, checkable artifact —
> `CLAUDE.md`, `check.sh`, the ADR log — rather than staying an intention
> in your head. That artifact then exists independent of who's doing the
> work, which is why it helps your manual work too, not just the agent's.

One gap this doesn't close automatically: the commit-blocking hook only
fires on commits made through Claude's own Bash tool — a manual commit
still needs `./check.sh` run by hand first.

## To improve / open items

**Issue tracker points at GitHub with no remote configured.** `gh`
commands in `docs/agents/issue-tracker.md` won't resolve a repo until a
remote is added — revisit if this stays a local-only project.

**The commit-blocking hook and permission list aren't backed up anywhere.**
Both `.claude/settings.local.json` and `.claude/hooks/` are gitignored (by
design — personal to this machine). That means if this machine is lost or
the repo is re-cloned, the commit gate and permission boundaries vanish
silently, with only the prose in `docs/learning/permission-boundaries.md` as a
recovery guide, not the actual files. Worth deciding whether to keep a
template copy checked in (e.g. `.claude/settings.local.json.example`) so
reproducing the setup elsewhere doesn't mean re-deriving it from prose.

**No project-specific `run` skill yet.** The built-in `run` skill falls
back to generic web-app patterns (documented after the fact in
`docs/learning/run-skill-guide.md`), which on this machine meant discovering —
mid-task — that Playwright's bundled Chromium doesn't work on this macOS
version and falling back to system Chrome. Worth capturing that as a
`.claude/skills/run-fit-balance/SKILL.md` (exact launch commands, the
Chrome-channel fallback) so it's a known recipe next time, not a
rediscovery.

**`docs/plans/` now has an index and numbering** (`docs/plans/README.md`,
`docs/plans/NNNN-slug.md`), matching `docs/adr/`'s pattern — resolved
2026-09-25. Check the index for current status of any plan.
