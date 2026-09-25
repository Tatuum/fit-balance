# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues on the
`Tatuum/fit-balance` remote (already configured as `origin`). Use the
`gh` CLI for all operations. `gh` itself still needs installing (`brew
install gh`) and authenticating (`gh auth login`, interactive — the
user's own step) before any of this is usable.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

Infer the repo from `git remote -v`; `gh` does this automatically when run inside a clone.

## The spec + steps convention (see `CLAUDE.md`'s Workflow)

This repo pairs a local, permanent plan doc (`docs/plans/NNNN-slug.md`
— the rereadable record) with GitHub issues (the trackable,
closable-as-you-go layer). GitHub is not the primary record; the plan
doc is. Cross-link both ways.

- **Publish the spec** (Workflow stage 3): once the plan doc is
  approved, `gh issue create` with the plan's title and a short
  summary + a link back to `docs/plans/NNNN-slug.md`. Add the returned
  `GitHub: #NN` to the plan doc's header.
- **Publish the steps** (Workflow stage 4): once the `## Steps`
  checklist in the plan doc is approved, create one child issue per
  step (`gh issue create`, body notes `Part of #<spec-issue>` and any
  `Blocked by: #<n>`), and record each step's issue number back onto
  its checklist line in the plan doc.
- **Work a step** (Workflow stage 5): pick a step whose blockers are
  all closed. On completion, `gh issue close <n> --comment "..."`
  summarizing what shipped, and check off its line in the plan doc.
- **Close out** (Workflow stage 6): once every step issue is closed,
  `gh issue close <spec-issue>`.

No labels, sub-issue API, or dependency graph beyond a plain `Blocked
by: #<n>` line — that's deliberately skipped here as more than a
single-person, single-session-sized project needs. `/wayfinder` and
`/triage` (from `mattpocock-skills`) aren't part of this repo's
workflow; if a future effort genuinely outgrows one session, revisit
then rather than pre-adopting the heavier machinery now.
