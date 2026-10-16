# Validation: validate measurement inputs

1. **`./check.sh` passes in full** (pytest, ruff, mypy, tsc, vitest), not
   just the new tests. `test_balance_points.py` and `test_scoring.py` are
   unchanged and green.
2. **API:** for each of the seven fields, a value just outside either
   bound returns 422 from `/technique-recommendations`, and the bounds
   themselves return 200. `height = 0` returns 422, not 500. Covered by
   the new tests in `tests/test_api.py`.
3. **Parser:** `lib/measurements.test.ts` covers in-range values, both
   boundaries, just outside each boundary, an empty string, non-numeric
   text and decimals.
4. **UI by hand** (`uv run uvicorn api.main:app --reload` and
   `npm run dev` in `web/`):
   - Clear the height field: it is marked with "Enter 120–230 cm", the
     avatar and advice stay as they were, and no request is sent for the
     invalid value.
   - Type `1` into waist: same behaviour, field marked, nothing changes.
   - Type a valid value again: the mark disappears and the avatar and
     advice update.
   - Reload and confirm the defaults all show as valid.
5. **Docs:** `web-app-overview.md` no longer lists the cleared-input
   gotcha and describes `drafts`; `CURRENT_STATE.md` notes the range
   check.
