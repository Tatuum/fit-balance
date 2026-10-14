from dataclasses import asdict
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fit_balance.balance_points import compute_womens_balance_points
from fit_balance.garment_balance import suggest_balance
from fit_balance.garments import UnknownGarmentItemError, list_items
from fit_balance.schemas import GarmentAttributes, Measurements, Verdict
from fit_balance.scoring import score as score_garment
from fit_balance.technique_advice import DimensionAdvice, recommend_techniques

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
    main_concern: list[str]
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


@app.get("/garments", response_model=list[GarmentSummary])
def list_garments_endpoint() -> list[GarmentSummary]:
    return [GarmentSummary(id=item.id, label=item.label, slot=item.slot) for item in list_items()]


class TechniqueRecommendationsRequest(BaseModel):
    measurements: Measurements


class TechniqueExampleResponse(BaseModel):
    tag: str
    direction: Literal["+", "-"]
    items: list[GarmentSummary]


class DimensionAdviceResponse(BaseModel):
    axis: str
    label: str
    value: float
    notable: bool
    pronounced: bool
    direction: Literal["+", "-"] | None
    recommendations: list[TechniqueExampleResponse]


class TechniqueRecommendationsResponse(BaseModel):
    balance_points: dict[str, float]
    # Deliberately no main_concern here: this endpoint reports each
    # dimension independently, on purpose (see CURRENT_STATE.md's "Technique
    # recommendations" section) — a "which axis matters most" field would
    # contradict that.
    dimensions: list[DimensionAdviceResponse]


def _dimension_advice_response(dimension: DimensionAdvice) -> DimensionAdviceResponse:
    """Shared by /technique-recommendations and /balance-garment — both
    return technique_advice.DimensionAdvice values over the wire."""
    return DimensionAdviceResponse(
        axis=dimension.axis,
        label=dimension.label,
        value=dimension.value,
        notable=dimension.notable,
        pronounced=dimension.pronounced,
        direction=dimension.direction,
        recommendations=[
            TechniqueExampleResponse(
                tag=rec.tag,
                direction=rec.direction,
                items=[
                    GarmentSummary(id=item.id, label=item.label, slot=item.slot)
                    for item in rec.items
                ],
            )
            for rec in dimension.recommendations
        ],
    )


@app.post("/technique-recommendations", response_model=TechniqueRecommendationsResponse)
def technique_recommendations_endpoint(
    request: TechniqueRecommendationsRequest,
) -> TechniqueRecommendationsResponse:
    balance_points = compute_womens_balance_points(request.measurements)
    return TechniqueRecommendationsResponse(
        balance_points=asdict(balance_points),
        dimensions=[
            _dimension_advice_response(dimension)
            for dimension in recommend_techniques(balance_points)
        ],
    )


class BalanceGarmentRequest(BaseModel):
    measurements: Measurements
    item_id: str


class BalanceGarmentResponse(BaseModel):
    balance_points: dict[str, float]
    main_concern: list[str]
    item: GarmentSummary
    # Reused directly from schemas, like /score does — a single item's own
    # verdict needs no per-item attribution (see OutfitVerdict above).
    verdict: Verdict
    suggestions: list[DimensionAdviceResponse]


@app.post("/balance-garment", response_model=BalanceGarmentResponse)
def balance_garment_endpoint(request: BalanceGarmentRequest) -> BalanceGarmentResponse:
    balance_points = compute_womens_balance_points(request.measurements)
    try:
        advice = suggest_balance(balance_points, request.item_id)
    except UnknownGarmentItemError as exc:
        raise HTTPException(status_code=422, detail=f"Unknown garment item id: {exc}") from exc
    return BalanceGarmentResponse(
        balance_points=asdict(balance_points),
        main_concern=balance_points.main_concern(),
        item=GarmentSummary(id=advice.item.id, label=advice.item.label, slot=advice.item.slot),
        verdict=advice.verdict,
        suggestions=[_dimension_advice_response(d) for d in advice.suggestions],
    )
