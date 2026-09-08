from dataclasses import asdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fit_balance.balance_points import compute_womens_balance_points
from fit_balance.schemas import GarmentAttributes, Measurements, Verdict
from fit_balance.scoring import score as score_garment

app = FastAPI(title="fit-balance API")

# Vite's default dev-server ports.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class ScoreRequest(BaseModel):
    measurements: Measurements
    garment: GarmentAttributes


class ScoreResponse(BaseModel):
    balance_points: dict[str, float]
    main_concern: str
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
