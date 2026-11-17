# Code review findings: deploy v1, slice 1 (CORS settings)

Built-in `/code-review` on `deploy-v1-container`, 2026-11-16. Findings are
as reported; the "Decision" lines are the triage, not yet applied.

Status: `open` = to fix, `no action` = reviewed and left as is.

## 1. Empty `ALLOWED_ORIGINS` silently disables CORS

- **Where:** `api/settings.py` (the comma-split validator)
- **Problem:** an empty, whitespace-only or comma-only value parses to
  `[]` with no error.
- **Scenario:** the deploy sets `ALLOWED_ORIGINS=` by a templating slip;
  the app starts normally and the browser blocks every call from the
  CloudFront site. Contradicts "fail loudly" in `CLAUDE.md`.
- **Decision:** `open`. Raise `ValueError` when the parsed list is empty.

## 2. Origins are not validated or normalized

- **Where:** `api/settings.py`
- **Problem:** a trailing slash, a bare `*` or a missing scheme is
  accepted as is.
- **Scenario:** `https://d123.cloudfront.net/` never matches the browser's
  `Origin` header, so CORS fails silently; `*` opens the API to all
  origins.
- **Decision:** `open`. Strip a trailing slash; reject `*` and entries
  without a scheme.

## 3. `Settings()` runs at import; tests depend on the ambient environment

- **Where:** `api/main.py` (`app = create_app()`), `tests/test_api.py`
- **Problem:** if `ALLOWED_ORIGINS` is set in the developer's shell or in
  CI, `test_cors_defaults_allow_local_dev_origin_only` and every test using
  the module-level `client` run with those origins and can fail or flip.
- **Decision:** `open`. Build the default test app from explicit
  `Settings()` after `monkeypatch.delenv`.

## 4. Settings tests miss edge cases

- **Where:** `tests/test_api.py`
- **Problem:** no tests for empty, whitespace-only or single-value input,
  or for the unset-means-local-defaults contract at the `Settings` level
  (`validation.md`). A `pydantic-settings` upgrade that starts JSON-decoding
  the value would go unnoticed.
- **Decision:** `open`. Add those tests alongside fixes 1 and 2.

## 5. `pydantic-settings` is only in the `api` dependency group

- **Where:** `pyproject.toml`
- **Problem:** `api.main` imports `api/settings.py`, so an image installed
  without `--group api` fails with `ModuleNotFoundError`. CI uses
  `--all-groups`, so it would not catch this.
- **Decision:** `no action`. The planned Dockerfile uses `--group api`,
  and `fastapi` already has the same property. Slice 1 step 5 (running the
  container) confirms it.

## 6. `create_app` relies on a module-global `router`

- **Where:** `api/main.py`
- **Problem:** every `create_app` call includes the same router, so
  anything attached to the router would leak across apps.
- **Decision:** `no action`. Harmless today; per-app middleware goes inside
  the factory.

## 7. The Configuration rule in `CLAUDE.md` is not enforced

- **Where:** `CLAUDE.md`
- **Problem:** nothing in ruff or pre-commit stops `os.environ` or
  `os.getenv` outside `Settings`.
- **Decision:** `no action` for now. A ruff banned-API rule is the option
  if the rule gets broken.
