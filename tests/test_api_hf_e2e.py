from fastapi.testclient import TestClient

from src.model_scout_api.main import app


def test_live_scout_api_returns_hf_candidates():
    with TestClient(app) as client:
        response = client.get("/v1/scout?query=bert&limit=3&top_n=3")

    assert response.status_code == 200
    payload = response.json()
    assert payload["response"]["query"] == "bert"
    assert payload["response"]["resource_type"] == "model"
    assert payload["response"]["shortlist"]
    assert payload["response"]["candidate_count"] > 0
    assert payload["response"]["top_n"] == 3
