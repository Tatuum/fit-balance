# System architecture overview

`specs/architecture.md` is the source of truth for layering rules and
stack choices/non-goals. This file is a companion for a human to get
oriented at a glance — a diagram of the same layering, plus the
per-library rationale behind each choice. If this ever looks out of
sync with that file, it wins.

```
                    ┌─────────────────────────────┐
 phases 1-3         │   fit_balance (Python lib)   │
 (library, no UI)   │                              │
                    │  schemas.py   — pydantic:    │
                    │    Measurements, Garment,     │
                    │    Verdict, Reason             │
                    │  balance_points.py — pure fns │
                    │    (women's v0)                │
                    │  effects.yaml — technique →    │
                    │    effect-tag data             │
                    │  scoring.py — (verdict,        │
                    │    reasons[]) = score(...)     │
                    │  cli.py — Typer CLI            │
                    └──────────────┬───────────────┘
                                   │ imported directly, no network
                    ┌──────────────┴───────────────┐
 phase 4            │   api/ — FastAPI service       │
 (API)              │   reuses schemas.py models      │
                    │   as request/response bodies    │
                    └──────────────┬───────────────┘
                                   │ JSON over HTTP
                    ┌──────────────┴───────────────┐
 phase 5            │   web/ — React + TS (Vite)     │
 (web avatar)       │   form → API → parametric SVG   │
                    │   avatar rendered from verdict  │
                    └───────────────────────────────┘
```

Three layers, one direction of dependency: `fit_balance` (the engine)
→ `api/` → `web/`. The engine has zero UI/network dependencies —
everything above it is a consumer, not a dependency, so it's fully
usable and testable on its own.

## Frameworks & libraries

| Concern | Choice | Why |
|---|---|---|
| Package/dep management | `uv` (`pyproject.toml`) | Fast, single tool for venv+deps+lockfile; `pip`/`venv` as fallback if preferred |
| Data validation / schemas | `pydantic` | One set of models (`Measurements`, `GarmentAttributes`, `Verdict`, `Reason`) reused unchanged from the pure functions all the way to the FastAPI request/response bodies in phase 4 |
| Rule data | `PyYAML` | Loads `effects.yaml` (technique → effect tags) |
| Testing | `pytest` | Encodes the 5 CURRENT_STATE.md worked examples as regression tests (phase 1) |
| Lint/format | `ruff` | Single fast tool for both; addresses the "no lint config yet" gap noted in CLAUDE.md |
| CLI (phase 3) | `Typer` + `rich` | Type-hint-driven CLI reusing the pydantic models directly; `rich` for a readable verdict/reasons table |
| API (phase 4) | `FastAPI` | Pairs directly with pydantic (already in use) and gets OpenAPI docs for free |
| Frontend (phase 5) | `React` + `TypeScript` + `Vite` | SVG avatar is a natural fit for React's component model; Vite keeps tooling minimal |
| Multimodal LLM API (future development, not yet a committed phase) | TBD — a vision-capable LLM, called directly, no orchestration framework | Garment-photo tag extraction, grounded explanation generation, tool-calling assistant |
| Database (future development, not yet a committed phase) | `SQLite` (Postgres later if needed) | Persists closet items — tags + verdict only, no images, no vector store. Single user for now, no accounts; a file-based DB avoids running a server for that |

- Phase 4+ libraries are not installed until their phase begins —
  phases 1–3 have zero web dependencies.
