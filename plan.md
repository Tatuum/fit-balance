# fit-balance: Architecture & Implementation Plan

## Context

The repo currently holds only `NOTES.md` (design notes: balance-point scoring
architecture, effects table, worked examples) and `CLAUDE.md`. No code, no
stack, no manifest files exist yet. NOTES.md defines a strict build order —
pure-function calculator + tests first, no image/CV work until much later —
and this plan turns that order into concrete stages with a chosen stack.

Decisions confirmed with the user:
- **Core engine: Python.** Chosen specifically because stage 5 (garment-photo
  attribute extraction) needs pose estimation/segmentation, where Python's
  ecosystem (mediapipe, rembg/SAM) is far stronger than JS's. Python is also
  a natural fit for the YAML rule files and notebook-based rule validation
  NOTES.md calls for in stage 3.
- **Eventual web product.** Stage 4 (parametric SVG avatar) is planned as a
  web UI from the start, with a clean API boundary between engine and
  frontend — but per NOTES.md, stages 1–3 stay UI-free.

## High-level architecture

```
                    ┌─────────────────────────────┐
 stages 1-3         │   fit_balance (Python lib)   │
 (library, no UI)   │                              │
                    │  schemas.py   — pydantic:    │
                    │    Measurements, Garment,     │
                    │    Verdict, Reason             │
                    │  balance_points.py — pure fns │
                    │    (women's v0, menswear v0)  │
                    │  effects.yaml — technique →    │
                    │    effect-tag data             │
                    │  scoring.py — (verdict,        │
                    │    reasons[]) = score(...)     │
                    │  cli.py — Typer CLI            │
                    └──────────────┬───────────────┘
                                   │ imported directly, no network
                    ┌──────────────┴───────────────┐
 stage 4            │   api/ — FastAPI service       │
 (web product)      │   reuses schemas.py models      │
                    │   as request/response bodies    │
                    └──────────────┬───────────────┘
                                   │ JSON over HTTP
                    ┌──────────────┴───────────────┐
                    │   web/ — React + TS (Vite)     │
                    │   form → API → parametric SVG   │
                    │   avatar rendered from verdict  │
                    └───────────────────────────────┘

 stage 5 (later)    A CV service (mediapipe pose estimation + rembg/SAM
                    segmentation) that turns an uploaded garment/body photo
                    into Measurements/Garment objects, then calls the same
                    scoring.py — no changes to stages 1-3 needed.

 stage 6 (later)    Multi-garment outfit parsing — extends stage 5's
                    pipeline; not architected yet, deliberately deferred.
```

Key property: the engine (`fit_balance`) has zero UI/network dependencies.
Everything above it (API, web, CV) is a consumer, not a dependency — matches
NOTES.md's explicit "don't start with image processing" instruction, since
the engine is fully usable and testable long before any of that exists.

## Frameworks & libraries

| Concern | Choice | Why |
|---|---|---|
| Package/dep management | `uv` (`pyproject.toml`) | Fast, single tool for venv+deps+lockfile; `pip`/`venv` as fallback if preferred |
| Data validation / schemas | `pydantic` | One set of models (`Measurements`, `GarmentAttributes`, `Verdict`, `Reason`) reused unchanged from the pure functions all the way to the FastAPI request/response bodies in stage 4 |
| Rule data | `PyYAML` | Loads `effects.yaml` (technique → effect tags) |
| Testing | `pytest` | Encodes the 5 NOTES.md worked examples as regression tests (stage 1) |
| Lint/format | `ruff` | Single fast tool for both; addresses the "no lint config yet" gap noted in CLAUDE.md |
| CLI (stage 3) | `Typer` + `rich` | Type-hint-driven CLI reusing the pydantic models directly; `rich` for a readable verdict/reasons table |
| API (stage 4) | `FastAPI` | Pairs directly with pydantic (already in use) and gets OpenAPI docs for free |
| Frontend (stage 4) | `React` + `TypeScript` + `Vite` | SVG avatar is a natural fit for React's component model; Vite keeps tooling minimal |
| Pose estimation (stage 5) | `mediapipe` | Established, runs without GPU, extracts body landmarks from a photo |
| Segmentation (stage 5) | `rembg` (fallback: Segment Anything) | Lightweight garment/background segmentation; SAM only if `rembg` accuracy proves insufficient |

Stage 4+ libraries are not installed until their stage begins — stages 1–3
have zero web/CV dependencies.

## Repository layout (target, built incrementally by stage)

```
fit-balance/
  NOTES.md
  CLAUDE.md
  pyproject.toml
  src/fit_balance/
    __init__.py
    schemas.py        # pydantic: Measurements, GarmentAttributes, Verdict, Reason
    balance_points.py # pure functions, stage 1
    effects.yaml       # stage 2
    scoring.py          # stage 2
    cli.py               # stage 3
  tests/
    test_balance_points.py  # the 5 worked examples, parametrized
    test_scoring.py
  api/        # stage 4, added then
  web/        # stage 4, added then
```

## Implementation stages

### Stage 1 — Balance-point calculator + regression tests
- Scaffold `pyproject.toml` (uv), `src/fit_balance/` package layout, `ruff` config, `pytest` config.
- `schemas.py`: pydantic `Measurements` (bust, waist, hip, torso, leg, height, chest) and `MenswearMeasurements` if the two variants need distinct fields.
- `balance_points.py`: pure functions for both formula sets in NOTES.md (`bust_hip_balance`, `waist_definition`, `torso_leg_balance`, `frame_scale_dev` for women's v0; `chest_waist_balance`, `chest_hip_balance` + shared `torso_leg_balance`/`frame_scale_dev` for menswear v0), plus a `main_concern()` helper (largest absolute-magnitude balance point).
- **Decision needed at this stage:** the 5 worked examples in NOTES.md are expressed as `shape≈X` labels, not raw measurements — translate each into a concrete `Measurements` fixture that produces the intended balance-point signs before encoding as a test.
- `tests/test_balance_points.py`: the 5 worked examples as parametrized pytest cases, asserting on balance-point values and `main_concern()`, not on the final verdict (scoring doesn't exist yet).
- No UI, no images — matches NOTES.md exactly.

### Stage 2 — Effects table + scoring engine
- `effects.yaml`: technique → effect-tag list (start with the techniques named in the worked examples: `sheath_bodycon`, `belted_natural_waist`, `drop_waist`, `empire_waistline`, `vertical_detail`, `oversized_top`, `skinny_straight`).
- `schemas.py` additions: `GarmentAttributes` (list of techniques), `Reason` (tag, direction, balance point it came from), `Verdict` (recommendation level + `reasons: list[Reason]`).
- `scoring.py`: for each balance point, a want/avoid effect-tag list; contribution scaled by `abs(balance_point_value)`, not a flat category match; aggregate into `Verdict`.
- Extend `tests/` with the same 5 worked examples, now asserting on full verdict + reasons — this is the point where the "apple + bodycon regression" NOTES.md warns about becomes impossible to reintroduce silently.

### Stage 3 — CLI / notebook validation
- `cli.py` (Typer): a `score` command taking measurements + garment techniques as flags or a prompt flow, printing verdict + reasons via `rich`.
- Optional Jupyter notebook for interactively tuning `effects.yaml` weights and re-running the worked-example suite.
- Goal (per NOTES.md): confirm the rules *feel* right on real inputs before any image or web work starts.

### Stage 4 — Web product: API + parametric SVG avatar
- `api/`: FastAPI app exposing `POST /score`, reusing `schemas.py` models unchanged as request/response bodies — no duplicate schema definitions.
- `web/`: React + TypeScript + Vite app — a measurement/garment form, calling the API, rendering a parametric SVG avatar whose proportions are a pure function of the returned balance-point values (no photorealism, per NOTES.md).
- Keep the SVG-rendering function pure and unit-testable independent of React state.

### Stage 5 — Garment-photo attribute extraction (deferred, exploratory)
- A CV service (can start as another FastAPI route) using `mediapipe` for pose landmarks and `rembg` for garment segmentation, producing `Measurements`/`GarmentAttributes` objects that feed unchanged into `scoring.py`.
- Library choices here are the least certain in this plan — revisit once this stage actually starts, per NOTES.md's explicit instruction not to front-load CV work.

### Stage 6 — Multi-garment outfit parsing (later, not architected)
- Extends stage 5's pipeline to multiple detected garments plus a combination/matching layer. Left unplanned until stages 1–5 are solid.

## Verification

- **Stage 1–2**: `pytest` passes with all 5 worked examples green; `ruff check` clean.
- **Stage 3**: manually run the CLI against each worked example and confirm output matches the expected verdict in NOTES.md.
- **Stage 4**: `POST /score` via curl/HTTPie returns the same verdict as the CLI for the same inputs (schema reuse should guarantee this); manually load the web app and confirm the SVG avatar updates with measurement changes.
- **Stage 5+**: no automated verification defined yet — deferred until the stage starts, since inputs (real photos) and accuracy targets aren't defined.
