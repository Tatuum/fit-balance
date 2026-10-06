# fit-balance

An explainable styling-recommendation engine. Not a black-box "you're a
pear, wear an A-line" label, and not a photorealistic-but-unexplainable
virtual try-on render — it tells you *where your body's balance points are*
and *why* a given garment technique works with or against them. Every
verdict comes with the specific reasons that produced it, and those reasons
are editable data, not a trained model's opinion.

## Why

Body-shape apps are crowded and their users consistently complain about
vague, inconsistent classification with no way to see or override the
reasoning. Photorealistic virtual try-on is also crowded — good at "does it
look real," bad at "why does this suit me." Explainable AI for fashion is
still mostly a research problem, not a shipped product feature. The gap
this project targets: **transparent, overridable reasoning**, not another
shape classifier or another renderer.

## How it works

1. **Balance points** — continuous, signed numbers describing body
   proportions (e.g. `waist_definition`, `torso_leg_balance`). No discrete
   shape categories in the scoring logic — those are lossy and flip
   arbitrarily right at category boundaries. A shape label can still be
   *shown* to the user, but it's a display string, never an input to
   scoring.
2. **Effects table** — maps a garment technique (`high_rise`,
   `sheath_bodycon`, ...) to the visual effects it produces
   (`elongates_leg`, `clings_to_hip`, ...) — a fact about the technique,
   independent of who wears it.
3. **Scoring** — for each balance point, a want/avoid list of effect tags,
   quantized into one of three severity levels based on how far that
   balance point is from neutral. Output is a verdict *plus the specific
   reasons that fired*, e.g. "+ defines your waist (asset) / − clings to
   hip (works against your shape) / + reduces bulk (helps your frame
   scale)."

## Example

```
Body:    little natural waist definition, long torso
Garment: sheath bodycon + belted natural waist
Verdict: avoid
Reasons: − clings to a hip that isn't the frame's strength
         − a natural-waist belt sits at the wrong point on a long torso
```

This is one of five worked examples encoded as regression tests — see
[Worked examples](CURRENT_STATE.md#worked-examples-now-automated-tests) in
`CURRENT_STATE.md`.

## Engineering approach

- **Every engine change gets a written decision record.** `docs/adr/`
  holds one immutable file per past scoring/formula decision — context,
  decision, consequences — so the reasoning behind a specific number is
  never lost to chat history. See [`docs/adr/`](docs/adr/README.md).
- **Worked examples are automated tests, not eyeballed.** Rule changes
  have silently regressed prior-correct examples before. All 5 worked
  examples are pinned in `tests/test_balance_points.py` and
  `tests/test_scoring.py`, and any engine change must keep that suite
  green.
- **`CURRENT_STATE.md` is the living source of truth** for the current architecture
  and formulas; this README is the front door, not the spec.
- **CI + pre-commit gate every change, enforced.** `.github/workflows/ci.yml`
  runs lint/type-check/test (Python) and typecheck/test (web) on every
  push/PR to `main`; `.pre-commit-config.yaml` runs the equivalent
  Python checks locally on every commit. GitHub branch protection on
  `main` requires all 4 CI checks to pass before merging — no direct
  pushes, not even for the repo admin.

## Tech stack

- **Engine / CLI / API:** Python, [uv](https://docs.astral.sh/uv/),
  Pydantic, Typer, FastAPI, pytest, ruff, mypy
- **Web:** React, TypeScript, Vite, vitest

## Project layout

```
fit-balance/
├── src/fit_balance/  the engine — balance_points.py, effects.yaml,
│                     scoring.py, plus garments/recommend/technique_advice
│                     presentation layers
├── api/              FastAPI app exposing the engine over HTTP
├── web/              React + TS frontend (measurements, silhouette,
│                     technique advice)
├── tests/            pytest suite — includes the 5 worked examples as
│                     regression tests
├── specs/            architecture, mission, stack, and roadmap docs,
│                     plus one dated spec folder per feature
├── docs/adr/         one immutable decision record per past
│                     engine-level design choice
└── CURRENT_STATE.md  current-state spec: formulas, architecture,
                      build-order status
```

## Getting started

**Engine, CLI, API** (requires [uv](https://docs.astral.sh/uv/)):

```bash
uv sync
uv run pre-commit install  # one-time: installs the local commit gate
uv run pytest              # run the test suite
uv run ruff check .        # lint
uv run mypy src api        # type check
uv run fit-balance --help  # CLI: score a garment against a set of measurements
uv run uvicorn api.main:app --reload   # start the API on :8000
```

**Web frontend:**

```bash
cd web
npm install
npm run dev      # dev server, expects the API on :8000
npm run build    # type-checks and builds
npm run test     # vitest
```

**Everything, gated in one script:**

```bash
./check.sh   # pytest + ruff + mypy + tsc --noEmit + vitest — the bar for "done"
```

## Status

The core engine, CLI, API, and web app are shipped and tested.
AI-assisted features (photo-upload closet, grounded explanations, a
personal RAG corpus, a conversational assistant) aren't committed yet
— see [`specs/roadmap.md`](specs/roadmap.md) for phase-by-phase status
and `specs/architecture.md`'s "Future development" section for the
early direction.
