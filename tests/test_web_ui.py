import pytest

from src.model_scout import web


def test_ui_index_has_required_inputs():
    page = web.ui_index_html()

    assert 'id="query"' in page
    assert 'id="resource"' in page
    assert 'id="limit"' in page
    assert "Top recommendation" in page
    assert "Comparison" in page
    assert "License / status" in page
    assert "error" in page


def test_normalize_limit_rejects_out_of_range():
    with pytest.raises(ValueError, match="between 1 and 100"):
        web.normalize_limit("0")

    with pytest.raises(ValueError, match="between 1 and 100"):
        web.normalize_limit("101")


def test_build_search_payload_handles_query_and_resource_validation(monkeypatch):
    def fake_scout(query, limit, resource):
        return {
            "query": query,
            "resource_type": resource,
            "searched_candidate_count": 2,
            "candidate_count": 2,
            "candidates": [
                {
                    "model_id": "org/allowed",
                    "resource_type": resource,
                    "license": "apache-2.0",
                    "score": 92,
                    "status": "APPROVED",
                    "downloads": 1200,
                    "source_url": "https://huggingface.co/org/allowed",
                },
                {
                    "model_id": "org/review",
                    "resource_type": resource,
                    "license": None,
                    "score": 70,
                    "status": "LICENSE_REVIEW_REQUIRED",
                    "downloads": 300,
                },
            ],
        }

    monkeypatch.setattr(web, "scout", fake_scout)
    payload = web.build_search_payload("tts", 2, "model")

    assert payload["query"] == "tts"
    assert payload["resource_type"] == "model"
    assert len(payload["shortlist"]) == 2
    assert payload["shortlist"][0]["model_id"] == "org/allowed"
    assert payload["recommended"]["model_id"] == "org/allowed"
    assert payload["recommended"]["license"] == "apache-2.0"
    assert payload["comparison"][0]["model_id"] == "org/allowed"
    assert "LICENSE_REVIEW_REQUIRED" in payload["warnings"][0]


def test_build_search_payload_validates_empty_query():
    with pytest.raises(ValueError, match="query is required"):
        web.build_search_payload("", 3, "model")
