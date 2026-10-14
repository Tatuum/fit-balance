# Requirements: remove unused outfit features and frontend leftovers

## Context

Several phases shipped features the app no longer reaches. The web UI was simplified on 2026-09-14 (`9251c23`) to: measurements form, avatar, per-dimension advice cards, and a garment dropdown with a verdict. The outfit endpoints and some frontend leftovers have had no caller since. This change deletes the code and live docs for the unused features, keeps everything the UI or the engine uses, and leaves the engine ready for a later photo-upload flow (`specs/architecture.md` "Future development", piece 1).

Precedent: PR #9 (remove the CLI) — dropped code and all live-doc references, left `docs/adr/`, `docs/plans/` and dated `specs/` folders untouched.

## Remove

| # | Feature | Roadmap phase |
|---|---|---|
| 1 | Outfit scoring with attribution: `POST /score-outfit`, `attribute_reasons`, `AttributedReason`, `scoreOutfit()` | 6 (part) |
| 2 | Outfit recommendations: `POST /recommend-outfits`, `recommend.py`, `recommendOutfits()` | 7, and the backend half of 11 |
| 4 | Unused client wrapper `scoreGarment()` and its types (the `/score` endpoint stays) | 4 / 5 |
| 5 | Vite template leftovers: `web/src/assets/{hero.png,react.svg,vite.svg}`, `web/public/icons.svg`, `web/README.md` | 5 (scaffold) |

## Keep

- **Engine:** `balance_points.py`, `effects.yaml`, `scoring.py`, `schemas.py`, and `POST /score` with its tests (the engine's public API; the photo flow will call it).
- **Garment picker:** `GarmentBalance.tsx`, `lib/garments.ts`, `GET /garments`, `POST /balance-garment`, `garment_balance.py`. The user keeps a dropdown that returns a verdict for one garment.
- **Advice cards:** `/technique-recommendations`, `technique_advice.py`, `DimensionAdvice.tsx`, and the catalog (`garments.yaml`, `garments.py`) they read example garments from.
- **Avatar overlay** (`effectTags`, `applyEffectAdjustments`): `GarmentBalance.tsx` passes the tags.
- **`BalancePointsChart.tsx` + test:** not rendered anywhere, kept on purpose (user decision).

## Out of scope

The photo-upload UI itself (own feature spec). Any engine change. Rewriting frozen history.

## Decisions confirmed with the user

- Remove #1, #2, #4, #5; keep the dropdown picker; keep the chart.
- `POST /score` endpoint stays; only its frontend wrapper goes.
