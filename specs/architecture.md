# fit-balance: Architecture & Implementation Plan

## High-level architecture

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

Key property: the engine (`fit_balance`) has zero UI/network dependencies.
Everything above it (API, web) is a consumer, not a dependency — the engine
is fully usable and testable independent of either.

## Frameworks & libraries

| Concern | Choice | Why |
|---|---|---|
| Package/dep management | `uv` (`pyproject.toml`) | Fast, single tool for venv+deps+lockfile; `pip`/`venv` as fallback if preferred |
| Data validation / schemas | `pydantic` | One set of models (`Measurements`, `GarmentAttributes`, `Verdict`, `Reason`) reused unchanged from the pure functions all the way to the FastAPI request/response bodies in phase 4 |
| Rule data | `PyYAML` | Loads `effects.yaml` (technique → effect tags) |
| Testing | `pytest` | Encodes the 5 NOTES.md worked examples as regression tests (phase 1) |
| Lint/format | `ruff` | Single fast tool for both; addresses the "no lint config yet" gap noted in CLAUDE.md |
| CLI (phase 3) | `Typer` + `rich` | Type-hint-driven CLI reusing the pydantic models directly; `rich` for a readable verdict/reasons table |
| API (phase 4) | `FastAPI` | Pairs directly with pydantic (already in use) and gets OpenAPI docs for free |
| Frontend (phase 5) | `React` + `TypeScript` + `Vite` | SVG avatar is a natural fit for React's component model; Vite keeps tooling minimal |
| Multimodal LLM API (phases 14–17) | TBD — a vision-capable LLM, called directly, no orchestration framework | Garment-photo tag extraction, grounded explanation generation, tool-calling assistant |
| Database (phase 14) | `SQLite` (Postgres later if needed) | Persists closet items — tags + verdict only, no images, no vector store. Single user for now, no accounts; a file-based DB avoids running a server for that |

Phase 4+ libraries are not installed until their phase begins — phases 1–3
have zero web dependencies.

## Repository layout (target, built incrementally by phase)

```
fit-balance/
├── NOTES.md
├── CLAUDE.md
├── pyproject.toml
├── src/fit_balance/
│   ├── __init__.py
│   ├── schemas.py        # pydantic: Measurements, GarmentAttributes, Verdict, Reason
│   ├── balance_points.py # pure functions, phase 1
│   ├── effects.yaml      # phase 2
│   ├── scoring.py        # phase 2
│   └── cli.py             # phase 3
├── tests/
│   ├── test_balance_points.py  # the 5 worked examples, parametrized
│   └── test_scoring.py
├── api/        # phase 4, added then
└── web/        # phase 5, added then
```

## Future development

> AI-assisted features — **not committed, early direction only**;
> order, scope, and inclusion may all change before any of this
> becomes an actual roadmap phase.

### Goal

Give users grounded, explainable AI assistance (natural-language
explanations, a photo-upload closet, a conversational assistant)
without touching computer vision, while keeping the engine's core
"editable data, not a trained model's opinion" identity intact. The
LLM never gets to invent a verdict — it only proposes tags (subject to
human review) or phrases already-derived reasons (subject to a
faithfulness check). `balance_points.py`, `scoring.py`, and
`effects.yaml` stay untouched, same as every presentation-layer
addition above them.

### Pieces, in build order

One coherent layer, four pieces:

#### 1. Private photo-upload closet (build first)

- User uploads a photo.
- LLM suggests technique tags.
- Flag tags that don't fit `effects.yaml`'s vocabulary as
  uncertain-match (see NOTES.md's `clings_to_hip`).
- User reviews and edits the tags.
- Engine scores the tags — unchanged.
- Save tags + verdict only. No images, no embeddings, no vector store.
- Find similar closet items by tag overlap, not embeddings.
- Single user, no accounts. New: first persistent database.
- Not computer vision — just an LLM call on a photo.

#### 2. Grounded explanation generation + faithfulness check

Turns the engine's existing structured reasons into natural-language
prose, constrained to only say what those reasons (and, once built,
piece 3's RAG corpus) actually support — plus an eval/groundedness
check that flags drift instead of trusting the LLM's output blindly.

#### 3. Text RAG corpus

- Ship a small seed corpus: a few self-authored or clearly-licensed
  notes, committed to the repo.
- Works out of the box — retrieval has something to find with no
  setup.
- User can also upload articles or video transcripts they find
  useful.
- Personal use only. Never redistributed or shown to other users.
- Single user, no accounts — same as piece 1.
- Retrieve notes to ground piece 2's explanations.

#### 4. Tool-calling conversational assistant (build last)

Sits on top of the rest. A chat interface where the LLM calls the real
endpoints (scoring, closet items, retrieval) as tools instead of
reasoning from scratch — demonstrates agentic orchestration on a real
system rather than toy tools.

### New stack needs

Specifics TBD at implementation time — revisit once this is actually
planned:

- A multimodal-capable LLM API, called directly (no orchestration
  framework) — consistent with prior hands-on experience with raw API
  calls, chunking, and embeddings.
- A persistent database — the app's first. `SQLite` to start (single
  user, no server to run); expand to Postgres later if multi-user
  need arises.
- Deliberately **no** vector database / image-embedding service — the
  earlier idea of visual (image-embedding) matching was considered and
  dropped in favor of tag-overlap similarity, which is both simpler and
  more explainable.

## Verification

- **Future development** (AI-assisted features, once actually planned):
  same worked-example discipline as phases 1–2, extended —
  a fixed set of test photos/descriptions with expected extracted tags
  (including at least one deliberately-ambiguous case that should trip
  the uncertain-match flag); a golden set of reasons → expected faithful
  explanation, asserting the groundedness check rejects an injected
  unfaithful rewrite; scoring itself still verified by the existing
  `tests/test_scoring.py` suite, untouched.
