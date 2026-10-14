# Validation: remove unused outfit features and frontend leftovers

1. **`./check.sh` passes in full** (pytest, ruff, mypy, tsc, vitest), not just the touched tests.
2. **Worked examples untouched:** `tests/test_balance_points.py` and `tests/test_scoring.py` are unchanged and green.
3. **Nothing left behind:** `grep -rnE "score-outfit|recommend-outfits|recommend_outfits|attribute_reasons|AttributedReason|scoreOutfit|recommendOutfits|scoreGarment" --exclude-dir=node_modules --exclude-dir=.git .` returns hits only in frozen history (`docs/adr`, `docs/plans`, other `specs/2026-*` folders, `CHANGELOG.md`) and this spec folder, which names the removed items on purpose.
4. **API surface:** run `uv run uvicorn api.main:app --reload`. `/docs` lists exactly `/score`, `/garments`, `/technique-recommendations`, `/balance-garment`. `POST /score-outfit` and `POST /recommend-outfits` return 404.
5. **UI by hand:** run `npm run dev` in `web/`. The page loads, the advice cards render, and picking a garment from the dropdown shows a verdict, its reasons, and the overlay avatar.
6. **Docs:** `CURRENT_STATE.md` has no outfit-ranking section and no "currently unwired" overlay claim; `specs/roadmap.md` and `main-logic-overview.md` match the code.
