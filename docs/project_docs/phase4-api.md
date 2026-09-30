# Phase 4 — FastAPI `/score` endpoint

Exposes the engine over HTTP so scoring stops being CLI-only. A thin
pass-through to `score()` — no new logic lives here.

**Files:** `api/main.py`

### 1. The `/score` endpoint

`POST /score` takes a `ScoreRequest` (`measurements`, `garment`) and
returns a `ScoreResponse`:

```python
class ScoreResponse(BaseModel):
    balance_points: dict[str, float]
    main_concern: str | None
    verdict: Verdict
```

The handler does exactly what the CLI does — call
`compute_womens_balance_points()` then `score()` — and reuses
`schemas.py`'s `Measurements`, `GarmentAttributes`, and `Verdict`
unchanged as the request/response bodies, so there's no second copy of
those shapes to drift out of sync with the engine. `balance_points` is
serialized via `dataclasses.asdict()` since `WomensBalancePoints` is a
plain frozen dataclass, not a pydantic model (see
`docs/project_docs/phase1-balance-points.md`).

### Testing / verification

`tests/test_api.py` asserts `/score` returns the same recommendation
and `main_concern` as the engine does directly for a worked example,
and that missing fields 422.
