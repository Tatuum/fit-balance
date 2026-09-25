# 0011. Commit-blocking hook + auto-accept checklist

Date: 2026-09-17
Status: Shipped — see docs/claude-code-setup.md

## Context

Follow-up to `docs/plans/0010-permission-constraints.md`. That plan handled
per-command approval (allow/ask/deny for Bash calls). Reading through an
article on structured Claude Code workflows surfaced two gaps that plan
didn't cover:

1. Nothing actually *enforces* `./check.sh` — CLAUDE.md says to run it
   before calling a change done, but that's a instruction Claude could
   forget or skip, not a guarantee. The article's "block-at-submit" pattern
   (gate at `git commit`, not at every file edit) is a stronger version of
   the same intent.
2. There was no written rule for *when* it's actually safe to leave Manual
   mode for Accept Edits — just a vague sense of "when I trust it more."
   The article gives a concrete, checkable criterion instead.

Both are refinements of the same underlying goal from the original
request: fewer pointless approvals, without losing the boundary that
actually matters (nothing side-effecting happens without either your
sign-off or a passing check).

You chose to keep this **personal to this machine** (`.claude/settings.local.json`),
same as the original permission rules — not shared via the tracked
`.claude/settings.json`.

## Plan

### 1. Commit-blocking hook

New file **`.claude/hooks/check-before-commit.sh`** (executable):

- Reads the PreToolUse hook's JSON payload from stdin, extracts
  `.tool_input.command` (via `jq`).
- If the command doesn't contain a `git commit` invocation, exits `0`
  immediately (no-op) — every other Bash call, including `git status` /
  `git diff` / etc. from the existing allowlist, is unaffected and stays
  instant.
- If it does, `cd`s to `$CLAUDE_PROJECT_DIR` and runs `./check.sh` —
  the same single gate CLAUDE.md already asks for (pytest, ruff, tsc,
  vitest; `set -euo pipefail`, so any failing step already exits non-zero).
- Exits `0` (allow) if `check.sh` passes; exits `2` with a reason on
  stderr (block) if it fails. Exit code `2` is Claude Code's documented
  "block this tool call, feed my stderr back as the reason" signal for a
  PreToolUse hook.

Register it in **`.claude/settings.local.json`** (already exists from the
previous plan) by adding a `hooks` block:

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/check-before-commit.sh",
          "timeout": 300
        }
      ]
    }
  ]
}
```

`$CLAUDE_PROJECT_DIR` keeps the path portable instead of hardcoding
`/Users/a1337/repos/fit-balance`. `timeout: 300` gives `check.sh` room to
run all four suites before the hook itself is treated as failed.

Add **`.claude/hooks/`** to `.gitignore`, next to the existing
`.claude/settings.local.json` entry — keeps the whole feature personal
rather than half-tracked (script committed, settings pointing to it not).

**Known scope limit, worth being explicit about:** this only gates commits
Claude Code makes through its own Bash tool. It has no effect on commits
you type directly in your own terminal outside a Claude Code session —
matches the actual goal here (constraining what Claude does on your
behalf), not a general repo-wide commit gate.

### 2. Auto-accept checklist

Add a short section to `docs/plans/0010-permission-constraints.md` (after the
existing "Modes" bullet) recording the article's criterion for when
leaving Manual mode is actually reasonable, so it's a written check next
time rather than a gut call:

> Only move to Accept Edits when: the working tree is clean, the current
> plan already names every file expected to change, and verification for
> the change is defined (for engine changes, that's `./check.sh` — now
> backed by the commit hook above, not just a suggestion).

## Observability: don't expect to see "All checks passed"

Per Claude Code's documented hook behavior: a `PreToolUse` hook that exits
`0` (allow) has its stdout *and* stderr routed to the debug log only —
never shown in the terminal, and never seen by Claude either. Only a
blocking exit (`2`) surfaces anything, via stderr as the shown reason. So
seeing nothing when a commit succeeds is expected, not a sign the hook
didn't run.

To actually confirm the hook fired and passed (e.g. while debugging it),
grep the session's transcript file
(`~/.claude/projects/<project>/<session-id>.jsonl`) for `hook_success` —
entries with `"hookName":"PreToolUse:Bash"` carry the hook's real stdout
in `content` (e.g. starting `== pytest ==`) when it ran `check.sh`, versus
exiting instantly with none for a non-commit command.

## Files touched

- `.claude/hooks/check-before-commit.sh` — new, executable
- `.claude/settings.local.json` — add `hooks` key
- `.gitignore` — add `.claude/hooks/`
- `docs/plans/0010-permission-constraints.md` — add the auto-accept checklist

## Verification

- `git status` after implementing — neither `.claude/settings.local.json`
  nor `.claude/hooks/` should appear as untracked/modified in a way that'd
  get committed.
- Sanity-check the hook directly without needing a real commit: pipe a
  fake payload in — `echo '{"tool_input":{"command":"git commit -m x"}}' | .claude/hooks/check-before-commit.sh; echo $?`
  — should run `check.sh` and exit `0` or `2` accordingly.
- Confirm a non-commit command is untouched: same payload style with
  `"command":"git status"` should exit `0` immediately, without running
  `check.sh`.
- Then do a real end-to-end check inside a Claude Code session: ask it to
  run `git commit` — it should run `check.sh` first and only proceed if
  that passes. Try it once against a deliberately broken test to confirm
  the block (and its stated reason) actually shows up.
- Confirm `git commit --no-verify` is still caught — the hook matches on
  the Bash command string regardless of git's own flags, since it isn't a
  git hook.
