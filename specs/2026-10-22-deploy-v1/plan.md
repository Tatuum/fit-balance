# Plan: deploy v1

Slices run riskiest-first. Each one ends with something that works on its
own, and the plan can stop after any of them.

## 1. API container that runs locally

The riskiest assumption is that the API runs correctly from an image, with
configurable CORS, so prove it before touching AWS.

- [x] 1. API: add a health endpoint. Make the allowed origins configurable by an
   environment variable (comma-separated, defaulting to the local dev
   origins), read through a `Settings` class (`pydantic-settings`). The app
   is built by `create_app(settings)`; `app = create_app()` stays at module
   level, so the run command is unchanged.
- [ ] 2. Image: install the library and API on the same Python version as CI.
   Add the Lambda Web Adapter as a Lambda extension (inert outside
   Lambda). The API does not stream, so leave the default response mode.
   `Dockerfile` in the repo root:
   ```dockerfile
   FROM python:3.11-slim

   COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.0.0 \
        /lambda-adapter /opt/extensions/lambda-adapter

   COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

   WORKDIR /app
   COPY pyproject.toml uv.lock README.md ./
   COPY src ./src
   COPY api ./api
   RUN uv sync --frozen --no-dev --group api

   ENV PORT=8000
   CMD [".venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
   If the build names a missing file, remove it from the `COPY` line or add it.
- [ ] 3. Add an ignore file so the build context excludes dependencies, caches,
   secrets, the data folder, the web app and git history. `.dockerignore`
   in the repo root:
   ```
   .git
   .venv
   .env
   .claude
   data
   web
   docs
   specs
   tests
   scripts
   **/__pycache__
   .pytest_cache
   .mypy_cache
   .ruff_cache
   ```
- [ ] 4. Build for the Lambda CPU architecture: `--platform linux/amd64
   --provenance=false`. Without them an Apple Silicon build fails on
   Lambda with "exec format error".
   ```sh
   docker build --platform linux/amd64 --provenance=false -t fit-balance-api .
   ```
- [ ] 5. Run it locally with Docker and point the local web dev server at it.
   Load the page, get advice and a verdict, hit the health endpoint, and
   check that a request from a different origin is refused.
   ```sh
   docker run --rm -p 8000:8000 fit-balance-api
   curl -s localhost:8000/health
   curl -s localhost:8000/garments | head -c 200
   # no output expected (origin refused):
   curl -s -i -H "Origin: https://evil.example" localhost:8000/garments | grep -i access-control
   # prints the header (origin allowed):
   curl -s -i -H "Origin: http://localhost:5173" localhost:8000/garments | grep -i access-control
   ```
   Then `npm run dev` from `web/` and walk through measurements, advice and
   a verdict (the dev server talks to `localhost:8000`, now the container).

Done when: the container behaves like the local API.

## 2. API live on Lambda (manual)

The second-riskiest assumption is that the adapter and a Function URL work
for this app. Do this slice and slice 3 from the AWS CLI; use the web
console only to view what the commands created. Save each command as you
go, so slice 4 can reuse them.

- [ ] 1. AWS account: root MFA, billing budget alerts, a daily-use admin user or
   role, and a chosen region.
   - Console, once: sign up (Personal account); turn on MFA for root; create
     an IAM admin user (`AdministratorAccess`, console access, MFA, one
     access key for the CLI); sign out of root and use that user.
   - If billing is hidden from the admin user, enable "IAM user and role
     access to Billing information" as root.
   - CLI, with one region used for everything (example `eu-west-1`):
     ```sh
     brew install awscli
     aws configure
     aws sts get-caller-identity   # shows the 12-digit account id
     export AWS_REGION=eu-west-1
     export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
     ```
   - Budget (keep `budget.json` and `notifications.json` out of the repo, e.g.
     in `~/aws-setup/`; they hold your email):
     ```json
     { "BudgetName": "monthly-5-usd",
       "BudgetLimit": { "Amount": "5", "Unit": "USD" },
       "TimeUnit": "MONTHLY", "BudgetType": "COST" }
     ```
     `notifications.json` is one entry per threshold, 20 and 100 (percent),
     each with `NotificationType` `ACTUAL`, `ComparisonOperator`
     `GREATER_THAN`, `ThresholdType` `PERCENTAGE`, and an `EMAIL` subscriber:
     ```json
     [{ "Notification": { "NotificationType": "ACTUAL",
          "ComparisonOperator": "GREATER_THAN", "Threshold": 20,
          "ThresholdType": "PERCENTAGE" },
        "Subscribers": [{ "SubscriptionType": "EMAIL", "Address": "you@example.com" }] }]
     ```
     ```sh
     aws budgets create-budget --account-id $ACCOUNT_ID \
       --budget file://budget.json \
       --notifications-with-subscribers file://notifications.json
     aws budgets describe-budgets --account-id $ACCOUNT_ID
     ```
- [ ] 2. Create an ECR repository. Push the image from the local machine.
   ```sh
   aws ecr create-repository --repository-name fit-balance-api --region $AWS_REGION
   aws ecr get-login-password --region $AWS_REGION \
     | docker login --username AWS --password-stdin \
       $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
   docker build --platform linux/amd64 --provenance=false -t fit-balance-api .
   docker tag fit-balance-api:latest \
     $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fit-balance-api:v1
   docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fit-balance-api:v1
   aws ecr list-images --repository-name fit-balance-api
   ```
   Tag each push with a version (`v1`, `v2`), not `latest`.
- [ ] 3. Create the Lambda function from the image. Set memory and timeout
   sensibly for a small app. Set reserved concurrency to a small number
   (not provisioned concurrency, which costs money while idle). Requests
   over the cap are throttled with HTTP 429; setting it to 0 is the
   emergency stop.
   ```sh
   # execution role
   cat > trust.json <<'EOF'
   { "Version": "2012-10-17",
     "Statement": [{ "Effect": "Allow",
       "Principal": { "Service": "lambda.amazonaws.com" },
       "Action": "sts:AssumeRole" }] }
   EOF
   aws iam create-role --role-name fit-balance-api-role \
     --assume-role-policy-document file://trust.json
   aws iam attach-role-policy --role-name fit-balance-api-role \
     --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
   # wait ~10 s for the role, then:
   aws lambda create-function --function-name fit-balance-api \
     --package-type Image \
     --code ImageUri=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fit-balance-api:v1 \
     --role arn:aws:iam::$ACCOUNT_ID:role/fit-balance-api-role \
     --memory-size 512 --timeout 30 \
     --environment "Variables={ALLOWED_ORIGINS=http://localhost:5173}"
   aws lambda put-function-concurrency --function-name fit-balance-api \
     --reserved-concurrent-executions 4
   ```
   "Role cannot be assumed": wait and retry. If AWS refuses the cap ("below
   its minimum value"), check `aws lambda get-account-settings`, rely on the
   budget alert, and note what you saw here.
- [ ] 4. Create a Function URL with no AWS auth (the app is public) and normal
   buffered responses. Do not turn on the URL's own CORS option; the API
   handles CORS.
   ```sh
   aws lambda create-function-url-config --function-name fit-balance-api \
     --auth-type NONE
   aws lambda add-permission --function-name fit-balance-api \
     --statement-id public-url-invoke-url \
     --action lambda:InvokeFunctionUrl \
     --principal "*" --function-url-auth-type NONE
   aws lambda add-permission --function-name fit-balance-api \
     --statement-id public-url-invoke \
     --action lambda:InvokeFunction \
     --principal "*" --invoked-via-function-url
   ```
   Without both permissions the URL answers 403 even with auth `NONE`.
- [ ] 5. Call the health endpoint and one scoring endpoint at the live address.
   A 502 or 500 means look in CloudWatch logs first
   (`/aws/lambda/<function-name>`) for the traceback. Pushing a new image
   to the same tag does not update the function; run `aws lambda
   update-function-code` to point it at the new image.
   ```sh
   URL=$(aws lambda get-function-url-config --function-name fit-balance-api \
     --query FunctionUrl --output text)
   time curl -s ${URL}health
   curl -s ${URL}garments | head -c 200
   aws logs tail /aws/lambda/fit-balance-api --since 10m
   # shipping a new image:
   docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fit-balance-api:v2
   aws lambda update-function-code --function-name fit-balance-api \
     --image-uri $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fit-balance-api:v2
   ```
   403: missing permission (step 4). 429: cap hit or set to 0. "exec format
   error": built without `--platform linux/amd64`. Timeout: raise
   `--timeout`. `update-function-configuration --environment` replaces all
   variables, so list every one.
- [ ] 6. Record the real cold-start time and the region for the README.

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
  New items: `pydantic-settings`, Docker, AWS (ECR, Lambda, S3,
  CloudFront, IAM/OIDC, CloudWatch), the Lambda Web Adapter, and a GitHub
  Actions deploy workflow. The document is updated in slice 5.
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
