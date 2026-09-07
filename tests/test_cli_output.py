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


def test_render_output_json_preserves_payload():
    rendered = render_output(_result(), "json")
    assert json.loads(rendered) == _result()


def test_render_output_markdown_uses_report_layer():
    rendered = render_output(_result(), "markdown", top_n=2)
    assert "# MINDLE MODEL SCOUT REPORT" in rendered
    assert "org/approved-model" in rendered
    assert "LICENSE_REVIEW_REQUIRED" in rendered


def test_render_output_rejects_unknown_format():
    with pytest.raises(ValueError, match="unsupported output format"):
        render_output(_result(), "xml")
