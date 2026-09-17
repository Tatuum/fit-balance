# Set up permission constraints for Claude Code in fit-balance

## Context

You want fewer manual approvals for routine work, but you explicitly don't
want "auto mode" (Bypass Permissions), because you don't have a clear model
of what boundaries exist once prompts are off — the trigger was the `run`
skill installing Playwright into a scratch folder and launching a real
Chrome binary under Playwright to verify a feature, which you learned about
after the fact via `docs/run-skill-guide.md`.

Checked the current state: there is **no permission configuration anywhere**
— no `.claude/settings.json`, no `.claude/settings.local.json` in this repo,
and the global `~/.claude/settings.json` only sets `model` and
`agentPushNotifEnabled`. So today's prompting behavior is just the CLI's
unconfigured default. Nothing needs to be undone; this is additive.

The intended outcome: stay in normal permission mode (never Bypass), stop
getting prompted for things that are genuinely safe and reversible (reading
files, `git status`/`diff`/`log`, running the test/lint suite), keep getting
prompted individually for anything with real-world side effects (package
installs, browser automation, network calls, `git push`), and hard-block a
short list of actions you never want run without typing them yourself.

## How Claude Code's permission system works (for reference)

- **Modes**: *Default* (prompts per action, filtered through the rules
  below), *Plan* (current mode — read-only), *Accept Edits* (auto-approves
  file Read/Edit/Write only; Bash and everything else still goes through the
  rules below), *Bypass Permissions* ("auto mode" — skips the rules
  entirely). Recommendation: stay in Default mode; there's no need to touch
  Accept Edits or Bypass for this repo.

  The CLI's mode indicator uses different labels than the names above:

  | UI label | Mode name used here |
  |---|---|
  | Manual mode | Default |
  | Accept edits on | Accept Edits |
  | Auto mode on | Bypass Permissions |
  | Plan mode on | Plan |

  Only move to Accept Edits when: the working tree is clean, the current
  plan already names every file expected to change, and verification for
  the change is defined (for engine changes, that's `./check.sh` — now
  backed by the commit hook in `docs/plans/commit-check-hook.md`, not just
  a suggestion).
- **Rules**: `permissions.allow` / `permissions.ask` / `permissions.deny`
  arrays of tool-pattern strings (e.g. `Bash(git status:*)`) live in
  `settings.json` (checked in, shared with the repo) or
  `settings.local.json` (personal, not committed). `allow` skips the prompt,
  `ask` forces one even in Accept Edits/Bypass mode, `deny` refuses outright
  with no prompt to override.
- Pattern matching on `Bash(...)` rules is a prefix/glob match on the
  command string, not semantic understanding — treat `deny` entries as a
  best-effort backstop, not a guarantee, and keep the list short and
  unambiguous.

## Plan

1. **Add `.claude/settings.local.json`** (new file) with:
   - `allow`: read-only/reversible commands that shouldn't need a click —
     `git status`, `git diff`, `git log`, `git show`, `ls`, `cat`, `grep`,
     `rg`, `find`, `uv run pytest`, `uv run ruff check`, `npx vitest run`,
     `npx tsc --noEmit`, `./check.sh` (the repo's own gate command from
     CLAUDE.md).
   - `ask`: force a prompt for anything that installs packages, talks to
     the network, or automates a browser, even if the mode ever changes —
     `npm install`, `npm ci`, `pip install`, `uv add`, `uv pip install`,
     `npx playwright install`, `git push`, `curl`, and the `WebFetch` tool.
     This is exactly the category the Playwright/Chrome incident falls
     into.
   - `deny`: a short hard-block list for things you never want run without
     typing them yourself — `sudo`, `git push --force`/`-f`, `git reset
     --hard`.
2. **Add `.claude/settings.local.json` to `.gitignore`** — the repo's
   `.gitignore` currently has no `.claude/` entry at all, so without this
   the "personal, not shared" file you picked would show up in
   `git status` and could get committed by accident.
3. Leave `.claude/settings.json` (the shared/checked-in file) untouched for
   now, since you chose personal-only rules — nothing to add there.

No code, tests, or engine behavior changes; this only touches Claude Code
configuration.

## Verification

- After writing the file, run `git status` — `.claude/settings.local.json`
  should **not** appear (confirms the `.gitignore` entry works).
- Ask Claude Code to run something on the allowlist (e.g. `git log`) and
  confirm no prompt appears.
- Ask it to run something on the `ask` list (e.g. `npm install <anything>`)
  and confirm a prompt still appears.
- Optionally, once you've used the CLI for a while with real work, run the
  `fewer-permission-prompts` skill — it scans your own transcripts for
  commands you kept approving and proposes allowlist additions, so the list
  grows from what you actually do rather than a guess made now.
