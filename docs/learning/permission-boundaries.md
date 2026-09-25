# Claude Code permission boundaries for this repo

Quick reference for what's actually configured. Everything below lives in
**`.claude/settings.local.json`** (personal to this machine, gitignored —
nothing here is visible to anyone else who clones the repo). For the
reasoning behind each piece, see `docs/plans/0010-permission-constraints.md`
and `docs/plans/0011-commit-check-hook.md`.

## 1. Permission mode

Manual mode (Default) — never Accept Edits or Auto/Bypass mode for this
repo. Anything not explicitly listed below still prompts individually.

## 2. `allow` — skip the prompt

Safe, read-only or idempotent: `git status`, `git diff`, `git log`,
`git show`, `ls`, `cat`, `grep`, `rg`, `find`, `uv run pytest`,
`uv run ruff check`, `npx vitest run`, `npx tsc --noEmit`, `./check.sh`.

## 3. `ask` — always prompt, even if the mode ever changes

Side-effecting: `npm install`, `npm ci`, `pip install`, `pip3 install`,
`uv add`, `uv pip install`, `npx playwright install`, `git push`, `curl`,
`WebFetch`.

## 4. `deny` — refused outright, no prompt to override

`sudo`, `git push --force`/`-f`, `git reset --hard`.

## 5. Commit-blocking hook

`PreToolUse` hook on the `Bash` matcher
(`.claude/hooks/check-before-commit.sh`, also gitignored): intercepts any
`git commit` Claude attempts — including `--no-verify`, since it doesn't
rely on git's own hook mechanism — and runs `./check.sh` first, blocking
the commit if pytest/ruff/tsc/vitest don't all pass. Only covers commits
Claude makes through its own Bash tool, not anything typed manually in the
terminal.

## 6. Auto-accept checklist

Only move to Accept Edits mode when: the tree is clean, the current plan
already names every file expected to change, and verification is defined
for the change.

## Everything else

Falls through to Manual mode's default: it prompts, same as before any of
this was set up.
