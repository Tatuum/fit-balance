# Requirements: deploy v1 (Phase 14)

## Context

The engine, API and web app are shipped but only run on the owner's
machine. Nothing is packaged, hosted or deployed, and nothing publishes a
change automatically after a merge. Two things are tied to local
development: the web app's API address defaults to `localhost:8000`, and
the API allows only the local dev-server origins.

## Scope

**In**
- Package the API as a Docker image and run it on AWS Lambda behind a
  public HTTPS address.
- Host the built web app as static files on AWS (S3 behind CloudFront),
  on its own HTTPS address.
- Publish a change automatically when a PR merges to `main`.
- A health-check endpoint on the API.
- The README links to the live app and shows a screenshot.

**Out**
- New features: no photo upload, accounts, database or new endpoints
  beyond the health check.
- Infrastructure-as-code, Kubernetes, ECS/Fargate and a load balancer.
- A custom domain, monitoring dashboards and multi-region setups.
- The photo-tagging script stays an offline script (Phase 13). It is not
  part of the image.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Layout | Two separately deployed parts: static web app and API, each with its own address | The standard split. A web-only change does not touch the API, and each part can be updated and scaled on its own. |
| API packaging | Docker image on AWS Lambda, with the Lambda Web Adapter and a Function URL | The API runs unchanged. Scales to zero, so cost is about nothing. No load balancer. |
| Web hosting | Built files in a private S3 bucket, served by CloudFront | Static files need no server. CloudFront gives HTTPS and a CDN. |
| Registry | Amazon ECR | The standard place for images that Lambda runs. |
| Connecting the parts | Web build gets the API address at build time; the API allows only the web app's address (CORS), set by an environment variable | Both settings already exist in the code in a local-only form. |
| Auth to AWS from CI | GitHub OIDC (short-lived, keyless) | No long-lived access keys stored in GitHub. |
| Order of work | Manual deploy first, then automation | Something is live before the pipeline exists. |
| Cost control | Budget alerts and a cap on concurrent executions | A runaway loop or bot cannot create a surprise bill. |
| Access | Fully public, no login, no stored user data | Matches the project: single user for now, no accounts. |

Not chosen: one image serving both parts (simpler, but the parts would
deploy together), App Runner (closed to new AWS customers since April
2026), ECS Express Mode (always-on load balancer cost), ECS Fargate and
Terraform (more setup than the goal needs; named as future work).

## Context for implementers

- The web app already reads its API address from a build-time setting.
  The deployed build sets it to the live API address.
- The API's allowed origins are fixed in code today. They become
  configurable through an environment variable, with the local dev
  origins as the default so development is unchanged.
- The web address is only known after CloudFront exists, and the API
  address after the Function URL exists, so the first deploy sets each
  setting after the other part is created.
- The Function URL's own CORS option stays off; the API answers CORS
  itself.
- Cold starts are expected: the first API request after a quiet period
  can take several seconds. The README says so.
- The image uses the same Python version as CI.
- Secrets: none are needed at runtime (the API has no keys). Nothing
  secret goes into the image or the web build.
- Tone rule from CLAUDE.md applies to the README: it describes a real app
  for real users.

## Requirements

- The API image builds from a clean checkout with one command.
- The container serves all existing API routes unchanged, and `/health`
  returns a small success response and does no work.
- The API accepts requests from the web app's address and from no other
  site.
- The live web address loads the app, and a verdict for default inputs
  matches the local one.
- A merged PR reaches the live addresses without manual steps, updating
  whichever part changed.
- No long-lived AWS credentials exist in the repo or in GitHub secrets.
- `./check.sh` stays green.
