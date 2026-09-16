# Running this project with Claude Code's `run` skill

Notes on what the built-in `run` skill does, how it was actually used to
verify the single-garment balance-advice feature end-to-end in a browser,
and exactly what that touched on this machine — written up on request
after a security/privacy question about headless-Chrome access.

## What the skill does

`run` is a built-in Claude Code skill for actually launching and driving
an app, not just running its test suite. Its logic:

1. **Check for a project-specific launch skill first** — grep
   `.claude/skills/*/SKILL.md` walking up to the repo root. If one exists
   that covers launching/driving the app, use it verbatim (it's the
   maintainer's already-verified recipe: exact install commands, env vars,
   driver code). This repo has no such skill yet (only `new-decision`
   exists), so the fallback patterns below were used instead.
2. **Otherwise, match the project's shape** against a small table of
   patterns (CLI tool, web server, TUI, Electron/desktop GUI,
   browser-driven web app, library/SDK) and follow that pattern's example.
3. **Drive it, don't just launch it** — the skill is explicit that
   starting the process and walking away doesn't count; it wants an actual
   interaction (a click, a `curl`, a keypress) and evidence it worked (a
   screenshot, a response body, an exit code).

## How it was used for this project

fit-balance is a "browser-driven web app" (FastAPI backend + Vite/React
frontend), which the skill's table points at driving a headless browser
against the dev servers with a tool called `chromium-cli`. That tool
wasn't installed on this machine, so — per the skill's own documented
fallback for that case — a small raw Playwright script was written
instead, adapted from the skill's Electron-pattern example.

Concretely, to verify the "try on a garment" feature:

1. Started the two dev servers already defined by this project, with no
   new dependencies: `uv run uvicorn api.main:app --port 8000` (backend)
   and `npm run dev` in `web/` (frontend) — both run in the background.
2. In a session-scoped scratch directory (outside the repo, not committed,
   not part of the project), ran `npm init -y` then
   `npm install playwright@1.63.0`.
3. Tried `npx playwright install chromium` to get a bundled browser —
   this **failed outright**: Playwright doesn't support its own bundled
   Chromium on this machine's macOS version (13 / Ventura).
4. Fell back to `chromium.launch({ channel: 'chrome', headless: true })` —
   telling Playwright to drive the **already-installed system Google
   Chrome** app instead of downloading a browser of its own.
5. Wrote three small driver scripts that navigate to `localhost:5173`,
   select different garments from the new picker, fill in measurement
   inputs, and take screenshots — then read a screenshot back to confirm
   the feature actually rendered and updated correctly.

## What got installed

| What | Where | Persists? |
|---|---|---|
| `playwright` npm package (~19MB incl. deps) | a session-scoped temp folder under `/private/tmp/claude-501/...`, **not** `web/node_modules` | No — tied to this session's scratchpad, not part of the repo, not committed |
| A Chromium browser binary | **not installed** — `playwright install chromium` failed on this OS version | N/A |
| Anything global (`npm -g`, `pip`) | nothing | N/A |
| Anything in the project itself | nothing — `web/package.json`, `pyproject.toml`, and their lockfiles were never touched | N/A |

Verified directly (not just described from memory): `npm ls -g` and
`pip3 list` show no Playwright; `web/package.json` has no Playwright
dependency; the only Playwright install lives in the temp scratch folder.

## What access it had to Chrome — and what it could have had

`chromium.launch({ channel: 'chrome' })` runs the **real Chrome binary**
(the same app in `/Applications/Google Chrome.app`) as a **brand-new,
separate OS process** — it does not attach to, read, or interrupt your
actual day-to-day Chrome windows/tabs in any way.

**What it did NOT have access to:**
- Your regular browser session, open tabs, or windows — entirely separate
  process.
- Saved passwords, cookies, browsing history, bookmarks, extensions, or
  any logged-in session — Playwright's `launch()` starts from a **fresh,
  empty, temporary profile** by default. No `--user-data-dir` or
  `storageState` was ever passed (confirmed by grepping the driver
  scripts), so each run got a disposable profile, discarded on
  `browser.close()`.
- Anything outside `localhost:5173` — the scripts only ever navigated to
  the project's own dev server, nothing else.
- The browser also ran fully **headless** — no visible window ever
  appeared on screen.

**What it did have, and why:**
- It ran as a subprocess under the same OS user account the coding
  session already runs as (via the Bash tool) — same trust boundary as
  any other command run on your behalf, nothing elevated.
- Standard Playwright remote-control over that one isolated instance:
  navigate, click, fill inputs, read the DOM, screenshot, read console
  output.

**What it *could* have had, if asked to:** because it launches as a
subprocess under your own account, it's technically possible to point
Playwright at your **real** Chrome profile directory (a `--user-data-dir`
flag) and get real access to your actual cookies, saved logins, and
history — the isolation above is a default, not an OS-level sandbox.
That was never done here and would only happen with an explicit, separate
ask and confirmation first, since it's a meaningfully more invasive action
than the throwaway-profile approach actually used.

## Cleaning up

The scratch folder (Playwright install + driver scripts + screenshots)
lives outside this repo under a session-specific temp path and was never
committed. It can be deleted any time without affecting the project; it
will also naturally age out as ordinary OS temp-file cleanup, since a new
Claude Code session gets its own fresh scratchpad path rather than reusing
this one.
