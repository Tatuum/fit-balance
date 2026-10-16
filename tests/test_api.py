import pytest
from fastapi.testclient import TestClient

from api.main import app
from fit_balance.balance_points import compute_womens_balance_points
from fit_balance.garment_balance import suggest_balance
from fit_balance.schemas import Measurements
from tests.fixtures import (
    APPLE_LONG_TORSO,
    BROAD_SHOULDER_NARROW_HIP,
    HOURGLASS_BALANCED,
    PEAR_FULLER,
)

client = TestClient(app)


def _bounds(field: str) -> tuple[float, float]:
    """The (min, max) a Measurements field declares, read off the model so
    these tests follow the ranges instead of repeating them."""
    low = high = None
    for meta in Measurements.model_fields[field].metadata:
        low = getattr(meta, "ge", low)
        high = getattr(meta, "le", high)
    assert low is not None and high is not None, f"{field} has no range"
    return low, high


MEASUREMENT_FIELDS = list(Measurements.model_fields)


def _technique_status(**override: float) -> int:
    measurements = {**HOURGLASS_BALANCED.model_dump(), **override}
    return client.post(
        "/technique-recommendations", json={"measurements": measurements}
    ).status_code


@pytest.mark.parametrize("field", MEASUREMENT_FIELDS)
def test_measurement_just_below_min_is_rejected(field):
    low, _ = _bounds(field)
    assert _technique_status(**{field: low - 0.1}) == 422


@pytest.mark.parametrize("field", MEASUREMENT_FIELDS)
def test_measurement_just_above_max_is_rejected(field):
    _, high = _bounds(field)
    assert _technique_status(**{field: high + 0.1}) == 422


@pytest.mark.parametrize("field", MEASUREMENT_FIELDS)
def test_measurement_bounds_are_inclusive(field):
    low, high = _bounds(field)
    assert _technique_status(**{field: low}) == 200
    assert _technique_status(**{field: high}) == 200


def test_zero_height_is_a_422_not_a_server_error():
    """height=0 used to reach compute_womens_balance_points and raise
    ZeroDivisionError (a 500)."""
    assert _technique_status(height=0) == 422


def test_score_endpoint_rejects_out_of_range_measurements():
    response = client.post(
        "/score",
        json={
            "measurements": {**HOURGLASS_BALANCED.model_dump(), "waist": 1},
            "garment": {"techniques": ["sheath_bodycon"]},
        },
    )
    assert response.status_code == 422


def test_score_endpoint_matches_engine_for_example_1():
    response = client.post(
        "/score",
        json={
            "measurements": HOURGLASS_BALANCED.model_dump(),
            "garment": {"techniques": ["sheath_bodycon", "belted_natural_waist"]},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"]["recommendation"] == "recommended"
    assert body["main_concern"] == ["waist_definition"]
    assert set(body["balance_points"]) == {
        "shoulder_hip_balance",
        "bust_hip_balance",
        "waist_definition",
        "torso_leg_balance",
        "frame_scale_dev",
    }


def test_score_endpoint_surfaces_a_main_concern_tie():
    """APPLE_LONG_TORSO's main_concern() is a genuine 3-way tie (decision
    0015) -- confirms the API serializes the list shape correctly, not
    just a single value."""
    response = client.post(
        "/score",
        json={
            "measurements": APPLE_LONG_TORSO.model_dump(),
            "garment": {"techniques": ["sheath_bodycon", "belted_natural_waist"]},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["main_concern"] == ["waist_definition", "torso_leg_balance", "frame_scale_dev"]


def test_score_endpoint_rejects_missing_fields():
    response = client.post("/score", json={"measurements": {}, "garment": {}})
    assert response.status_code == 422


def test_garments_endpoint_never_exposes_techniques():
    response = client.get("/garments")
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0
    for item in items:
        assert set(item) == {"id", "label", "slot"}


def test_technique_recommendations_endpoint_matches_pear_dimensions():
    response = client.post(
        "/technique-recommendations",
        json={"measurements": PEAR_FULLER.model_dump()},
    )
    assert response.status_code == 200
    body = response.json()
    assert "main_concern" not in body
    dimensions_by_axis = {d["axis"]: d for d in body["dimensions"]}
    assert set(dimensions_by_axis) == {
        "waist_definition",
        "top_hip_balance",
        "torso_leg_balance",
        "frame_scale_dev",
    }

    waist = dimensions_by_axis["waist_definition"]
    assert waist["notable"] is True
    assert waist["direction"] == "+"
    tags = {r["tag"]: r["direction"] for r in waist["recommendations"]}
    assert tags["hides_waist"] == "-"
    assert tags["defines_waist"] == "+"

    vertical = dimensions_by_axis["torso_leg_balance"]
    assert vertical["notable"] is False
    assert vertical["direction"] is None
    assert vertical["recommendations"] == []
    assert vertical["pronounced"] is False


def test_balance_garment_endpoint_matches_engine_call():
    response = client.post(
        "/balance-garment",
        json={
            "measurements": BROAD_SHOULDER_NARROW_HIP.model_dump(),
            "item_id": "structured_blazer",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["item"] == {
        "id": "structured_blazer",
        "label": "Structured blazer with built-up shoulders",
        "slot": "outerwear",
    }
    assert body["verdict"]["recommendation"] == "avoid"

    bp = compute_womens_balance_points(BROAD_SHOULDER_NARROW_HIP)
    advice = suggest_balance(bp, "structured_blazer")
    assert body["verdict"]["score"] == advice.verdict.score
    assert [d["axis"] for d in body["suggestions"]] == [d.axis for d in advice.suggestions]
    suggested_item_ids = {
        i["id"] for d in body["suggestions"] for r in d["recommendations"] for i in r["items"]
    }
    engine_item_ids = {i.id for d in advice.suggestions for r in d.recommendations for i in r.items}
    assert suggested_item_ids == engine_item_ids


def test_balance_garment_endpoint_rejects_unknown_item_id():
    response = client.post(
        "/balance-garment",
        json={"measurements": HOURGLASS_BALANCED.model_dump(), "item_id": "not_a_real_item"},
    )
    assert response.status_code == 422
