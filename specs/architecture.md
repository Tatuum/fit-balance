# Tech stack

## Engine / CLI / API

- Python, managed with `uv`
- `pydantic` — schemas (`Measurements`, `GarmentAttributes`,
  `Verdict`, `Reason`) shared unchanged from the pure functions all
  the way through to the API request/response bodies
- `PyYAML` — loads `effects.yaml` (technique → effect-tag data)
- `pytest` — encodes the worked examples as regression tests
- `ruff` — lint + format
- `mypy` — type check (staged strictness: lenient on undecorated defs,
  strict on return types)
- `Typer` + `rich` — CLI
- `FastAPI` — API layer, pairs directly with `pydantic`
- `pre-commit` — local gate on every commit (hygiene, `ruff`/
  `ruff-format`, `mypy`)
- GitHub Actions (`.github/workflows/ci.yml`) — remote gate on
  push/PR to `main`, mirroring `check.sh`
- GitHub branch protection on `main` — requires all 4 CI checks to
  pass before merging, enforced for admins too; no direct pushes

## Web

- React + TypeScript + Vite
- Parametric SVG avatar rendered as a pure function of balance-point
  values — no photorealism, no image assets

## Non-goals

- No orchestration framework for LLM calls — raw API calls only
- No vector DB, no image embeddings
- No shape-label-driven logic anywhere in the scoring path

# High-level architecture

Three layers, one direction of dependency:

- **`fit_balance`** (Python lib, phases 1–3) — `schemas.py` (pydantic:
  `Measurements`, `GarmentAttributes`, `Verdict`, `Reason`),
  `balance_points.py` (pure functions, women's v0), `effects.yaml`
  (technique → effect-tag data), `scoring.py` (`(verdict, reasons[]) =
  score(...)`), `cli.py` (Typer CLI). Imported directly by the layer
  above — no network boundary.
- **`api/`** (FastAPI service, phase 4) — reuses `schemas.py` models
  unchanged as request/response bodies. Talks to `web/` over JSON/HTTP.
- **`web/`** (React + TS/Vite, phase 5) — form → API → parametric SVG
  avatar rendered from the verdict.

## Key property

- The `fit_balance` library has zero UI/network dependencies.
- Within it, the engine (`balance_points.py`, `effects.yaml`,
  `scoring.py`) is the scoring core; `schemas.py` and `cli.py` are
  thin wrappers around it (see CLAUDE.md's Main logic section — an
  "engine change" means an edit to those three files specifically).
- Everything above the library (API, web) is a consumer, not a
  dependency — the library is fully usable and testable independent of
  either.
- A `feature-spec` architecture-fit check uses this section to decide
  which layer a new feature belongs to and whether it crosses a
  boundary (e.g. business logic leaking into a layer meant to stay
  thin).

See [`docs/project_docs/architecture-overview.md`](../docs/project_docs/architecture-overview.md)
for the same layering as a visual diagram, plus the stack rationale.

# Future development

> AI-assisted features — **not committed, early direction only**;
> order, scope, and inclusion may all change before any of this
> becomes an actual roadmap phase.

## Goal

- Give users grounded, explainable AI assistance (natural-language
  explanations, a photo-upload closet, a conversational assistant)
  without touching computer vision.
- Keep the engine's core "editable data, not a trained model's
  opinion" identity intact.
- The LLM never gets to invent a verdict — it only proposes tags
  (subject to human review) or phrases already-derived reasons
  (subject to a faithfulness check).
- `balance_points.py`, `scoring.py`, and `effects.yaml` stay
  untouched, same as every presentation-layer addition above them.

## Pieces, in build order

One coherent layer, four pieces:

### 1. Private photo-upload closet (build first)

- User uploads a photo.
- LLM suggests technique tags.
- Flag tags that don't fit `effects.yaml`'s vocabulary as
  uncertain-match (see CURRENT_STATE.md's `clings_to_hip`).
- User reviews and edits the tags.
- Engine scores the tags — unchanged.
- Save tags + verdict only. No images, no embeddings, no vector store.
- Find similar closet items by tag overlap, not embeddings.
- Single user, no accounts. New: first persistent database.
- Not computer vision — just an LLM call on a photo.

### 2. Grounded explanation generation + faithfulness check

- Turns the engine's existing structured reasons into
  natural-language prose.
- Constrained to only say what those reasons (and, once built, piece
  3's RAG corpus) actually support.
- Plus an eval/groundedness check that flags drift instead of
  trusting the LLM's output blindly.

### 3. Text RAG corpus

- Ship a small seed corpus: a few self-authored or clearly-licensed
  notes, committed to the repo.
- Works out of the box — retrieval has something to find with no
  setup.
- User can also upload articles or video transcripts they find
  useful.
- Personal use only. Never redistributed or shown to other users.
- Single user, no accounts — same as piece 1.
- Retrieve notes to ground piece 2's explanations.

### 4. Tool-calling conversational assistant (build last)

- Sits on top of the rest.
- A chat interface where the LLM calls the real endpoints (scoring,
  closet items, retrieval) as tools instead of reasoning from
  scratch.
- Demonstrates agentic orchestration on a real system rather than toy
  tools.

## New stack needs

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

# Verification

- **Future development** (AI-assisted features, once actually
  planned): same worked-example discipline as phases 1–2, extended.
- A fixed set of test photos/descriptions with expected extracted tags
  (including at least one deliberately-ambiguous case that should trip
  the uncertain-match flag).
- A golden set of reasons → expected faithful explanation, asserting
  the groundedness check rejects an injected unfaithful rewrite.
- Scoring itself still verified by the existing `tests/test_scoring.py`
  suite, untouched.
