# Validation: deploy v1

## Automated

1. **`./check.sh` passes in full** (pytest, ruff, mypy, tsc, oxlint,
   vitest). `test_balance_points.py` and `test_scoring.py` are unchanged
   and green.
2. **API tests** in `tests/test_api.py`:
   - the health endpoint returns 200 and a small fixed body;
   - with the allowed-origins variable set, a request from a listed origin
     gets the matching CORS header and a request from an unlisted origin
     does not;
   - with the variable unset, the local dev origins are allowed and all
     existing routes behave as before.
3. **CI deploy jobs:** after a merge, the API job's health check passes
   against the live function and the web job's page check passes against
   the live address. Each job fails if its check does not.

## Testing decisions

- **Seam:** the API's HTTP surface, tested through the existing
  `TestClient` setup in `tests/test_api.py`. It is the highest seam that
  proves the two API changes: health and CORS. One seam, no new test
  framework.
- **Good test here:** asserts what a request gets back (status, body,
  headers), not how the middleware is configured.
- **Prior art:** the existing tests in `tests/test_api.py`.
- Docker and AWS are verified by the manual steps below and by the deploy
  jobs' checks; they are not unit-tested.

## Manual

1. **Local container:** build, run, point the local web dev server at it.
   Change each measurement, get a verdict, view advice, confirm the avatar
   draws. The health endpoint answers.
2. **Live web address:** the same walk-through, with the browser console
   open. No CORS errors. A verdict for the default inputs matches the
   local one.
3. **Wrong origin:** a request to the live API from a page on another
   address is blocked.
4. **Cold start:** wait about 15 minutes, load the page, and record how
   long the first API response took.
5. **Cost guard:** a budget alert exists, and the concurrency cap shows in
   the Lambda configuration.
6. **No stored credentials:** the repository and its GitHub secrets list
   contain no AWS access keys; the deploy jobs authenticate through OIDC.
7. **Pipeline:** merge a trivial docs change and see both the function's
   new image tag and an updated web file, with no manual step.

## Docs

- README has the live link, a screenshot and the cold-start note.
- `specs/architecture.md` and `architecture-overview.md` show the
  deployment.
- `doc-audit` run with no stale findings.

## Definition of done

- The live web address works against the live API, with CORS limited to
  the web address.
- A merge to `main` deploys automatically and is checked.
- Budget alert and concurrency cap are in place.
- `./check.sh` is green and the CI checks pass.
- Docs updated, roadmap shows Phase 14 shipped.
