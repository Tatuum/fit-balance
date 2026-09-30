# fit-balance: Tech stack

## Engine / CLI / API

- Python, managed with `uv`
- `pydantic` — schemas (`Measurements`, `GarmentAttributes`,
  `Verdict`, `Reason`) shared unchanged from the pure functions all
  the way through to the API request/response bodies
- `PyYAML` — loads `effects.yaml` (technique → effect-tag data)
- `pytest` — encodes the worked examples as regression tests
- `ruff` — lint + format
- `Typer` + `rich` — CLI
- `FastAPI` — API layer, pairs directly with `pydantic`

## Web

- React + TypeScript + Vite
- Parametric SVG avatar rendered as a pure function of balance-point
  values — no photorealism, no image assets

## Planned — AI-assisted features (not yet installed)

- A multimodal-capable LLM API, called directly — no orchestration
  framework
- A persistent database — `SQLite` to start (single user, no accounts
  needed yet), Postgres later if multi-user need arises
- Deliberately **no** vector database or image-embedding service —
  closet-item similarity uses tag-set overlap instead, kept
  explainable

## Deferred indefinitely — out of scope for the current goal

- `mediapipe` (pose estimation), `rembg` / Segment Anything
  (segmentation) — considered for garment-photo → measurement
  extraction, not started, no longer prioritized (see `roadmap.md`)

## Non-goals

- No orchestration framework for LLM calls — raw API calls only
- No vector DB, no image embeddings
- No shape-label-driven logic anywhere in the scoring path
