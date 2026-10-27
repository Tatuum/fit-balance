# Deploy guide — API on AWS Lambda (slices 1 and 2)

Step-by-step runbook for Phase 14 (`specs/2026-10-22-deploy-v1/plan.md`).
Covers slice 1 (API container runs locally) and slice 2 (API live on
Lambda). Slices 3 (web) and 4 (automation) get added after these work.

Every AWS step is a CLI command. Each one says what the thing is, the
command, what you should see, and what to check if it fails. The web
console is only for looking at what the commands created.

**Terms used in the plan.** A *slice* is one piece of the plan that ends
with something working on its own, so you can stop after any slice.
*Docker image*: the API and everything it needs, packed into one file.
*Container*: a running copy of an image.

**Not yet verified.** The Dockerfile and commands below were written from
the AWS docs and a reference guide, not run. Fix this file as you hit
real output.

## Slice 1 — the API runs from a container, locally

### 1.0 Code changes first

Two small changes in `api/main.py`, done as a normal PR with tests in
`tests/test_api.py` (see `validation.md`):

1. A `GET /health` route returning a small fixed body.
2. Allowed CORS origins read from an environment variable, defaulting to
   the two localhost origins that are hard-coded today.

CORS (cross-origin resource sharing) is the browser rule that a page from
address A may only call an API at address B if B says A is allowed. The
live web and API will have different addresses, so B must name A.

### 1.1 Dockerfile

A *Dockerfile* is the recipe for the image. Create `Dockerfile` in the
repo root:

```dockerfile
FROM python:3.11-slim

# Lambda Web Adapter: lets Lambda talk to a normal web server.
# Does nothing when the image runs outside Lambda.
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

Why each part: Python 3.11 matches CI. `uv sync --frozen` installs exactly
what `uv.lock` says. `--no-dev --group api` leaves out test tools and
includes FastAPI and uvicorn. The adapter forwards Lambda requests to the
port in `PORT`.

If the build complains about a missing file (for example `README.md`),
remove it from the `COPY` line or add it; the error names the file.

### 1.2 .dockerignore

`.dockerignore` lists what must not enter the image (secrets, bulk,
history). Create it in the repo root:

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

### 1.3 Build and run

```sh
docker build --platform linux/amd64 --provenance=false -t fit-balance-api .
docker run --rm -p 8000:8000 fit-balance-api
```

- `--platform linux/amd64`: Lambda runs on x86 by default. Your Mac is
  ARM. Without this flag the image builds fine but fails on Lambda with
  "exec format error".
- `--provenance=false`: stops Docker adding extra metadata that Lambda
  rejects.
- `-p 8000:8000`: makes the container's port 8000 reachable at
  `localhost:8000`.

**Expect:** uvicorn prints that it is running on `0.0.0.0:8000`.
Building for x86 on an ARM Mac is slower, and the run may print a
platform warning. That is normal.

### 1.4 Check it

In a second terminal:

```sh
curl -s localhost:8000/health
curl -s localhost:8000/garments | head -c 200
```

Then, from `web/`, `npm run dev`, open the page, and walk through
measurements, advice and a verdict. The web dev server talks to
`localhost:8000`, which is now the container.

Wrong-origin check (should print no `access-control-allow-origin` line):

```sh
curl -s -i -H "Origin: https://evil.example" localhost:8000/garments | grep -i access-control
```

And with a listed origin (should print the header):

```sh
curl -s -i -H "Origin: http://localhost:5173" localhost:8000/garments | grep -i access-control
```

**Done when** the container answers like the local API did.

## Slice 2 — the API live on Lambda

### 2.0 Install the AWS CLI

```sh
brew install awscli
aws --version
```

### 2.1 Create the account (console, once)

This part is the web console: it is where the account and its payment
details are created.

1. Sign up at aws.amazon.com. Choose a *Personal* account.
2. Sign in as the *root user* (the email you signed up with). Root can do
   everything and cannot be restricted, so it is only used for setup.
3. Turn on MFA for root: account menu → Security credentials → Assign MFA
   device → authenticator app.
4. Make an everyday admin user instead of using root. In IAM (identity and
   access management, the service that controls who may do what): Users
   → Create user → give it console access → attach the policy
   `AdministratorAccess` → Security credentials → create an access key for
   CLI use, and turn on MFA for this user too. Save the access key
   somewhere private; it is shown once.
5. Sign out of root. From here on, use this user.

An access key is a long-lived password for the CLI, which is why it stays
on your machine only. Slice 4 uses a keyless method for GitHub instead.

### 2.2 Point the CLI at your account

Pick one region now and use it for everything (a region is a physical AWS
location; resources in different regions cannot see each other). Example
`eu-west-1`; choose one close to you.

```sh
aws configure
# AWS Access Key ID:     <from step 2.1>
# AWS Secret Access Key: <from step 2.1>
# Default region name:   eu-west-1
# Default output format: json

aws sts get-caller-identity
```

**Expect:** JSON with your account id (12 digits), and a user ARN ending
in your user name. If it errors, the key was copied wrong; run
`aws configure` again.

Set these once per terminal; later commands use them:

```sh
export AWS_REGION=eu-west-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo $ACCOUNT_ID
```

### 2.3 Budget alerts

A budget is a monthly spending limit that sends an email when your bill
reaches a percentage of it. It warns you; it does not stop spending.
Create two files.

`budget.json`:

```json
{
  "BudgetName": "monthly-5-usd",
  "BudgetLimit": { "Amount": "5", "Unit": "USD" },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

`notifications.json` (replace the address):

```json
[
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 20,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [{ "SubscriptionType": "EMAIL", "Address": "you@example.com" }]
  },
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 100,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [{ "SubscriptionType": "EMAIL", "Address": "you@example.com" }]
  }
]
```

```sh
aws budgets create-budget \
  --account-id $ACCOUNT_ID \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

The 20% alert fires at $1, the 100% alert at $5. Keep these two files out
of the repo (they hold your email), for example in `~/aws-setup/`.

**Check:** `aws budgets describe-budgets --account-id $ACCOUNT_ID`. In the
console: Billing → Budgets shows it. Billing data can take up to a day to
appear.

Also, as root or an admin with billing access, turn on "IAM user and role
access to Billing information" (account menu → Account) if the console
hides billing from your admin user.

### 2.4 ECR repository and push

ECR (Elastic Container Registry) is AWS's storage for Docker images.
Lambda pulls your image from here.

```sh
aws ecr create-repository --repository-name fit-balance-api --region $AWS_REGION

aws ecr get-login-password --region $AWS_REGION \
  | docker login --username AWS --password-stdin \
    $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build --platform linux/amd64 --provenance=false -t fit-balance-api .
docker tag fit-balance-api:latest \
  $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fit-balance-api:v1
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fit-balance-api:v1
```

The login command trades your CLI credentials for a 12-hour Docker login.
Use a version tag like `v1`, not `latest`, so each push is a different
image you can point Lambda at.

**Check:** `aws ecr list-images --repository-name fit-balance-api`.

### 2.5 Execution role

A role is a set of permissions a service can use. The function needs one
so it is allowed to run and write logs.

```sh
cat > trust.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "lambda.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role --role-name fit-balance-api-role \
  --assume-role-policy-document file://trust.json

aws iam attach-role-policy --role-name fit-balance-api-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

Wait about 10 seconds before the next step; a new role takes a moment to
be usable.

### 2.6 Create the function

```sh
aws lambda create-function \
  --function-name fit-balance-api \
  --package-type Image \
  --code ImageUri=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fit-balance-api:v1 \
  --role arn:aws:iam::$ACCOUNT_ID:role/fit-balance-api-role \
  --memory-size 512 \
  --timeout 30 \
  --environment "Variables={ALLOWED_ORIGINS=http://localhost:5173}"
```

`ALLOWED_ORIGINS` is a placeholder name; use whatever name step 1.0
chose. It gets the CloudFront address in slice 3. Memory 512 MB and
timeout 30 s are generous for a small app; change them if CloudWatch shows
otherwise.

If it errors with "role cannot be assumed", wait 10 more seconds and
retry.

Cap concurrency, so a bot or a loop cannot run up a bill:

```sh
aws lambda put-function-concurrency \
  --function-name fit-balance-api \
  --reserved-concurrent-executions 4
```

*Reserved* means "at most 4 copies of this function at once" and is free.
Do not use *provisioned* concurrency, which keeps copies warm and costs
money while idle. Requests above the cap get HTTP 429. Setting it to `0`
stops the function entirely, which is your emergency brake.

New accounts sometimes have a total limit of 10, and AWS refuses to
reserve below 10 unreserved. If you see an error like "decreases the
account's UnreservedConcurrentExecution below its minimum value", check
`aws lambda get-account-settings`, and rely on the budget alert until the
limit rises. Write down what you saw in this file.

### 2.7 Public address (Function URL)

A Function URL is a built-in HTTPS address for a function, without any
other AWS service in front. `NONE` means anyone may call it, which is what
a public app needs.

```sh
aws lambda create-function-url-config \
  --function-name fit-balance-api \
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

The first command prints the `FunctionUrl`. The two permission commands
are needed because without them the URL answers `403 Forbidden` even with
auth `NONE`. Do not turn on the Function URL's own CORS option; the API
handles CORS itself.

### 2.8 Call it

```sh
URL=$(aws lambda get-function-url-config --function-name fit-balance-api \
  --query FunctionUrl --output text)
time curl -s ${URL}health
curl -s ${URL}garments | head -c 200
```

**Expect:** the first call after a quiet period is slow (a *cold start*:
Lambda has to start the container). The second is fast. Record the first
call's time and the region for the README.

If it fails:

| Symptom | Likely cause and where to look |
|---|---|
| 403 Forbidden | Missing permission from 2.7 |
| 502 or 500 | Look at the logs, see below |
| 429 | Concurrency cap hit, or set to 0 |
| "exec format error" in logs | Built without `--platform linux/amd64` |
| Timeout | Raise `--timeout`, then read the logs |

Logs go to CloudWatch automatically, under `/aws/lambda/fit-balance-api`:

```sh
aws logs tail /aws/lambda/fit-balance-api --since 10m
```

### 2.9 Update the function later

Pushing a new image does not change what Lambda runs. Push with a new tag,
then point the function at it:

```sh
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fit-balance-api:v2
aws lambda update-function-code --function-name fit-balance-api \
  --image-uri $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fit-balance-api:v2
```

Change environment variables with `aws lambda update-function-configuration
--environment "Variables={...}"`. That command replaces all variables, so
list every one.

**Done when** the live health and scoring calls answer, the budget exists,
and the concurrency cap is shown by `aws lambda get-function-concurrency
--function-name fit-balance-api`.

## Cleaning up

To stop all costs: `aws lambda delete-function --function-name
fit-balance-api`, `aws ecr delete-repository --repository-name
fit-balance-api --force`, and `aws iam detach-role-policy` then `aws iam
delete-role` for the role.
