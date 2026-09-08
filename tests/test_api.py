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
    assert body["verdict"]["recommendation"] == "recommended"
    reasons_by_tag = {r["tag"]: r["item_ids"] for r in body["verdict"]["reasons"]}
    assert reasons_by_tag["adds_bulk"] == ["oversized_top"]
    assert reasons_by_tag["reduces_bulk"] == ["slim_trousers"]


def test_score_outfit_endpoint_rejects_unknown_item_id():
    response = client.post(
        "/score-outfit",
        json={"measurements": PEAR_FULLER.model_dump(), "item_ids": ["not_a_real_item"]},
    )
    assert response.status_code == 422
