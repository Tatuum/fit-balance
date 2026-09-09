#!/usr/bin/env bash
# Single gate for "did this actually work": Python tests + lint, frontend
# typecheck + tests. Run before calling any change done.
set -euo pipefail
cd "$(dirname "$0")"

echo "== pytest =="
uv run pytest -q

echo "== ruff =="
uv run ruff check .

echo "== tsc (web) =="
(cd web && npx tsc --noEmit -p .)

echo "== vitest (web) =="
(cd web && npx vitest run)

echo "All checks passed."
