from dataclasses import asdict
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fit_balance.balance_points import compute_womens_balance_points
from fit_balance.garments import (
    AttributedReason,
    UnknownGarmentItemError,
    attribute_reasons,
    list_items,
    resolve_outfit,
)
from fit_balance.schemas import GarmentAttributes, Measurements, Verdict
from fit_balance.scoring import score as score_garment

app = FastAPI(title="fit-balance API")

# Vite's default dev-server ports.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ScoreRequest(BaseModel):
    measurements: Measurements
    garment: GarmentAttributes


class ScoreResponse(BaseModel):
    balance_points: dict[str, float]
    main_concern: str | None
    verdict: Verdict


@app.post("/score", response_model=ScoreResponse)
def score_endpoint(request: ScoreRequest) -> ScoreResponse:
    balance_points = compute_womens_balance_points(request.measurements)
    verdict = score_garment(balance_points, request.garment)
    return ScoreResponse(
        balance_points=asdict(balance_points),
        main_concern=balance_points.main_concern(),
        verdict=verdict,
    )


class GarmentSummary(BaseModel):
    """The catalog entry shape exposed over the API — deliberately omits
    `techniques` so effects.yaml's internal vocabulary never reaches the
    wire, not just the UI."""

    id: str
    label: str
    slot: str


class ScoreOutfitRequest(BaseModel):
    measurements: Measurements
    item_ids: list[str]


class OutfitVerdict(BaseModel):
    # Duplicated from schemas.Verdict.recommendation rather than imported —
    # schemas.py is the engine surface and stays untouched by this
    # presentation-layer feature (see NOTES.md). Keep these four strings
    # byte-for-byte identical to schemas.Verdict's Literal if either changes.
    recommendation: Literal["recommended", "neutral", "avoid", "strong_avoid"]
    score: float
    reasons: list[AttributedReason]


class ScoreOutfitResponse(BaseModel):
    balance_points: dict[str, float]
    main_concern: str | None
    verdict: OutfitVerdict


@app.get("/garments", response_model=list[GarmentSummary])
def list_garments_endpoint() -> list[GarmentSummary]:
    return [GarmentSummary(id=item.id, label=item.label, slot=item.slot) for item in list_items()]


@app.post("/score-outfit", response_model=ScoreOutfitResponse)
def score_outfit_endpoint(request: ScoreOutfitRequest) -> ScoreOutfitResponse:
    try:
        items, garment = resolve_outfit(request.item_ids)
    except UnknownGarmentItemError as exc:
        raise HTTPException(status_code=422, detail=f"Unknown garment item id: {exc}") from exc

    balance_points = compute_womens_balance_points(request.measurements)
    verdict = score_garment(balance_points, garment)
    return ScoreOutfitResponse(
        balance_points=asdict(balance_points),
        main_concern=balance_points.main_concern(),
        verdict=OutfitVerdict(
            recommendation=verdict.recommendation,
            score=verdict.score,
            reasons=attribute_reasons(verdict.reasons, items),
        ),
    )
