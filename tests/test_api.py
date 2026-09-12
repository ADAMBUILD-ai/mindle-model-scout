from unittest.mock import patch

from fastapi.testclient import TestClient

from src.model_scout_api.main import app


def _mock_scout_result():
    return {
        "query": "bert",
        "search_query": "bert",
        "query_plan": ["bert"],
        "resource_type": "model",
        "searched_candidate_count": 3,
        "candidates": [
            {
                "model_id": "test/model-a",
                "pipeline_tag": "fill-mask",
                "downloads": 100,
                "likes": 12,
                "license": "apache-2.0",
                "status": "APPROVED",
                "score": 90,
                "reason": "reason-a",
                "resource_type": "model",
                "source_url": "https://huggingface.co/test/model-a",
            },
            {
                "model_id": "test/model-b",
                "pipeline_tag": "fill-mask",
                "downloads": 1,
                "likes": 1,
                "license": None,
                "status": "LICENSE_REVIEW_REQUIRED",
                "score": 20,
                "reason": "LICENSE_REVIEW_REQUIRED",
                "resource_type": "model",
                "source_url": "https://huggingface.co/test/model-b",
            },
        ],
    }


def test_health_returns_ok():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "mindle-model-scout-api"


def test_capabilities_respects_auth_state(monkeypatch):
    monkeypatch.setenv("MODEL_SCOUT_API_KEY", "secret")
    with TestClient(app) as client:
        unauthorized = client.get("/v1/capabilities")
        authorized = client.get("/v1/capabilities", headers={"X-API-KEY": "secret"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    capabilities_payload = authorized.json()
    assert "resource_types" in capabilities_payload
    assert "all" in capabilities_payload["resource_types"]


def test_scout_get_and_post_require_api_key_when_enabled(monkeypatch):
    monkeypatch.setenv("MODEL_SCOUT_API_KEY", "secret")
    with patch("src.model_scout_api.main.run_scout_core", return_value=_mock_scout_result()):
        with TestClient(app) as client:
            no_key = client.get("/v1/scout?query=bert&limit=3")
            with_key_get = client.get("/v1/scout?query=bert&limit=3", headers={"X-API-KEY": "secret"})
            with_key_post = client.post("/v1/scout", headers={"X-API-KEY": "secret"}, json={"query": "bert", "limit": 3})

    assert no_key.status_code == 401
    assert with_key_get.status_code == 200
    assert with_key_post.status_code == 200

    payload = with_key_get.json()
    assert payload["response"]["candidate_count"] == 2
    assert payload["response"]["top_n"] == 5
    assert payload["response"]["shortlist"][0]["model_id"] == "test/model-a"
