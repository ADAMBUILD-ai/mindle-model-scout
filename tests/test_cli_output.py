import json

import pytest

from src.model_scout.scout import render_output


def _result():
    return {
        "query": "bert",
        "candidate_count": 2,
        "candidates": [
            {
                "model_id": "org/approved-model",
                "pipeline_tag": "text-classification",
                "downloads": 100,
                "likes": 10,
                "library_name": "transformers",
                "license": "apache-2.0",
                "score": 88,
                "status": "APPROVED",
                "reason": "license:apache-2.0",
            },
            {
                "model_id": "org/review-model",
                "pipeline_tag": "text-classification",
                "downloads": 50,
                "likes": 2,
                "library_name": "transformers",
                "license": None,
                "score": 70,
                "status": "LICENSE_REVIEW_REQUIRED",
                "reason": "LICENSE_REVIEW_REQUIRED",
            },
        ],
    }


def test_render_output_json_preserves_payload_and_adds_model_cards():
    source = _result()
    rendered = render_output(source, "json")
    payload = json.loads(rendered)

    assert payload["query"] == source["query"]
    assert payload["candidate_count"] == source["candidate_count"]
    assert payload["candidates"] == source["candidates"]

    assert len(payload["model_cards"]) == 2
    approved, review_required = payload["model_cards"]
    assert approved["model_id"] == "org/approved-model"
    assert approved["source_url"] == "https://huggingface.co/org/approved-model"
    assert approved["status"] == "APPROVED"
    assert approved["checked_at"]
    assert review_required["model_id"] == "org/review-model"
    assert review_required["status"] == "LICENSE_REVIEW_REQUIRED"
    assert review_required["license"] is None
    assert review_required["checked_at"]


def test_render_output_markdown_uses_report_layer():
    rendered = render_output(_result(), "markdown", top_n=2)
    assert "# MINDLE MODEL SCOUT REPORT" in rendered
    assert "org/approved-model" in rendered
    assert "LICENSE_REVIEW_REQUIRED" in rendered


def test_render_output_rejects_unknown_format():
    with pytest.raises(ValueError, match="unsupported output format"):
        render_output(_result(), "xml")
