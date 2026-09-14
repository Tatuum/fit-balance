from fastapi.testclient import TestClient

from api.main import app
from tests.fixtures import HOURGLASS_BALANCED, PEAR_FULLER

client = TestClient(app)


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
    assert body["main_concern"] == "waist_definition"
    assert set(body["balance_points"]) == {
        "shoulder_hip_balance",
        "bust_hip_balance",
        "waist_definition",
        "torso_leg_balance",
        "frame_scale_dev",
    }


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


def test_score_outfit_endpoint_matches_worked_example_5_and_attributes_problem_item():
    response = client.post(
        "/score-outfit",
        json={
            "measurements": PEAR_FULLER.model_dump(),
            "item_ids": ["oversized_top", "slim_trousers"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"]["recommendation"] == "avoid"
    reasons_by_tag = {r["tag"]: r["item_ids"] for r in body["verdict"]["reasons"]}
    assert reasons_by_tag["adds_bulk"] == ["oversized_top"]
    assert reasons_by_tag["reduces_bulk"] == ["slim_trousers"]
    assert reasons_by_tag["hides_waist"] == ["oversized_top"]


def test_score_outfit_endpoint_rejects_unknown_item_id():
    response = client.post(
        "/score-outfit",
        json={"measurements": PEAR_FULLER.model_dump(), "item_ids": ["not_a_real_item"]},
    )
    assert response.status_code == 422


def test_recommend_outfits_endpoint_returns_ranked_results():
    response = client.post(
        "/recommend-outfits",
        json={"measurements": HOURGLASS_BALANCED.model_dump()},
    )
    assert response.status_code == 200
    body = response.json()
    recommendations = body["recommendations"]
    assert len(recommendations) == 5
    scores = [rec["verdict"]["score"] for rec in recommendations]
    assert scores == sorted(scores, reverse=True)
    for rec in recommendations:
        assert set(rec) == {"item_ids", "labels", "verdict"}


def test_recommend_outfits_endpoint_respects_limit_param():
    response = client.post(
        "/recommend-outfits",
        json={"measurements": HOURGLASS_BALANCED.model_dump(), "limit": 1},
    )
    assert response.status_code == 200
    assert len(response.json()["recommendations"]) == 1


def test_recommend_outfits_endpoint_rejects_non_positive_limit():
    response = client.post(
        "/recommend-outfits",
        json={"measurements": HOURGLASS_BALANCED.model_dump(), "limit": 0},
    )
    assert response.status_code == 422


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
