# Plan: deploy v1

Slices run riskiest-first. Each one ends with something that works on its
own, and the plan can stop after any of them.

## 1. API container that runs locally

The riskiest assumption is that the API runs correctly from an image, with
configurable CORS, so prove it before touching AWS.

1. API: add a health endpoint. Make the allowed origins configurable by an
   environment variable, defaulting to the local dev origins.
2. Image: install the library and API on the same Python version as CI.
   Add the Lambda Web Adapter as a Lambda extension (inert outside
   Lambda). The API does not stream, so leave the default response mode.
3. Add an ignore file so the build context excludes dependencies, caches,
   secrets, the data folder, the web app and git history.
4. Run it locally with Docker and point the local web dev server at it.
   Load the page, get advice and a verdict, hit the health endpoint, and
   check that a request from a different origin is refused.
5. Build for the Lambda CPU architecture and note the platform flag needed
   on Apple Silicon.

Done when: the container behaves like the local API.

## 2. API live on Lambda (manual)

The second-riskiest assumption is that the adapter and a Function URL work
for this app.

1. AWS account: root MFA, billing budget alerts, a daily-use admin user or
   role, and a chosen region.
2. Create an ECR repository. Push the image from the local machine.
3. Create the Lambda function from the image. Set memory and timeout
   sensibly for a small app. Cap concurrent executions at a small number.
4. Create a Function URL with no AWS auth (the app is public) and normal
   buffered responses.
5. Call the health endpoint and one scoring endpoint at the live address.
6. Record the real cold-start time and the region for the README.

Done when: the live API answers, and a budget alert is in place.

## 3. Web live on S3 and CloudFront (manual)

1. Create a private S3 bucket and a CloudFront distribution that reads it
   (origin access control, HTTPS only, default domain).
2. Build the web app with the live API address, upload the files, and note
   the CloudFront address.
3. Set the API's allowed-origins variable to the CloudFront address and
   redeploy the function's configuration.
4. Open the live web address and walk through the same flows as slice 1.
   Check the browser console for CORS errors.

Done when: the live web address works end to end against the live API.

## 4. Continuous deployment

1. In AWS: an identity provider for GitHub's OIDC and a role that GitHub
   Actions can assume, limited to this repository and the `main` branch,
   with only the permissions needed to push an image, update the function,
   write to the bucket, and invalidate the CloudFront cache.
2. A GitHub Actions workflow that runs only after the existing CI checks
   pass on `main`, with two jobs:
   - API: build the image, push it to ECR tagged with the commit, update
     the function, call the health endpoint and fail if it does not
     answer.
   - Web: build with the live API address, sync to the bucket, invalidate
     the cache, and fail if the live page does not load.
3. Keep the existing CI workflow as it is. The branch protection rules do
   not change.
4. Merge a trivial change and watch both parts update.

Done when: a merge to `main` updates the live app with no manual step.

## 5. Docs and close-out

1. README: live link, screenshot, one line on cold starts.
2. `specs/architecture.md`: add a short deployment section (hosting and
   packaging), because the stack list changes.
3. `docs/project_docs/architecture-overview.md`: show the deployed shape.
4. Roadmap: mark Phase 14 shipped. Run the `doc-audit` skill.
5. Run `changelog` before the last merge.

## Architecture fit

- **Layer:** none of the three. This is packaging, hosting and
  configuration around `api/` and `web/`; no library or scoring code
  changes. It is not an engine change, so no ADR.
- **Layering:** unchanged. The web app talks to the API over HTTP using
  the same routes as before, now across two addresses. The only code
  changes are in `api/`: a health endpoint and configurable CORS origins.
  The library stays free of UI and network code.
- **Outside the stack list:** yes, and it needs approval. The stack in
  `specs/architecture.md` has no container, cloud or deployment entry.
  New items: Docker, AWS (ECR, Lambda, S3, CloudFront, IAM/OIDC,
  CloudWatch), the Lambda Web Adapter, and a GitHub Actions deploy
  workflow. The document is updated in slice 5.
- **Build order:** does not skip ahead. The AI-assisted features in
  "Future development" are untouched, and the photo-tagging script is not
  packaged. Their later need for a database and API keys would revisit the
  hosting choice.
- **Conflict flagged:** `architecture.md` says nothing about deployment, so
  there is no conflict, only a gap that slice 5 fills.

## How it works in reality

Here are the two flows in our setup: what happens when someone uses the app, and what happens when you ship a change.

**1. A visitor uses the app**

```
Browser
  │ 1. opens https://<id>.cloudfront.net
  ▼
CloudFront (CDN) ──reads──► S3 bucket (index.html, JS, CSS)
  │ 2. browser runs the React app
  │ 3. app sends POST /balance-garment to the API address
  ▼
Lambda Function URL (https://<id>.lambda-url.<region>.on.aws)
  ▼
Lambda starts your container (if none is running = cold start)
  ▼
Web Adapter turns the request into a normal HTTP call to FastAPI
  ▼
FastAPI → engine → verdict → JSON back to the browser
```

- Steps 1 and 2 are only file serving. No code of yours runs on the server.
- Step 3 is the only moment your Python runs.
- If no one has called the API for a while, AWS has shut the container down. The next request starts it, which is the cold start. After that it answers quickly until it goes idle again.

**2. You ship a change**

```
You: open PR → CI runs (lint, types, tests, web)
  ▼
Merge to main
  ▼
GitHub Actions deploy workflow
  ├─ asks AWS for short-lived credentials (OIDC, no stored keys)
  ├─ API job:  docker build → push image to ECR (tagged with commit)
  │            → tell Lambda "use this image" → call /health to check
  └─ Web job:  npm build (with the API address) → copy files to S3
               → clear the CloudFront cache → check the page loads
```

**What each piece is in plain words**

| Piece | Role |
|---|---|
| **ECR** | Warehouse for the API image. Lambda pulls from here. |
| **Lambda** | Runs the image when there's a request. |
| **Function URL** | The public address of the API. |
| **S3** | Holds the web files. |
| **CloudFront** | Serves them over HTTPS, quickly. |
| **IAM role + OIDC** | Lets GitHub deploy without a password stored anywhere. |
| **CloudWatch** | Where the API's logs go, for debugging. |

**What a visitor notices:** the page loads fast. The first result after a quiet period can take a few seconds. Everything else behaves like local.

**What you notice:** merge a PR, wait a few minutes, and the live app is updated. If the health check fails, the job fails and you see it in GitHub.
