from fastapi.testclient import TestClient

from api.main import app
from tests.fixtures import HOURGLASS_BALANCED

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
        "bust_hip_balance",
        "waist_definition",
        "torso_leg_balance",
        "frame_scale_dev",
    }


def test_score_endpoint_rejects_missing_fields():
    response = client.post("/score", json={"measurements": {}, "garment": {}})
    assert response.status_code == 422
