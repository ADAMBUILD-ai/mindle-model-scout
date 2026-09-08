import json

from src.model_scout.report import build_report, render_markdown
from src.model_scout.scout import render_output


def _result():
    return {
        "query": "floor plan wall door",
        "candidate_count": 2,
        "candidates": [
            {
                "model_id": "org/licensed-model",
                "pipeline_tag": "image-segmentation",
                "downloads": 1000,
                "likes": 50,
                "library_name": "transformers",
                "license": "apache-2.0",
                "score": 88,
                "status": "APPROVED",
                "reason": "license:apache-2.0",
            },
            {
                "model_id": "org/unlicensed-model",
                "pipeline_tag": "image-segmentation",
                "downloads": 500,
                "likes": 10,
                "library_name": "transformers",
                "license": None,
                "score": 82,
                "status": "LICENSE_REVIEW_REQUIRED",
                "reason": "LICENSE_REVIEW_REQUIRED",
            },
        ],
    }


def test_report_contains_structured_model_cards():
    report = build_report(_result(), top_n=2)
    assert len(report["model_cards"]) == 2
    assert report["model_cards"][0]["source_url"] == "https://huggingface.co/org/licensed-model"
    assert report["model_cards"][1]["status"] == "LICENSE_REVIEW_REQUIRED"


def test_markdown_contains_model_cards_section():
    markdown = render_markdown(build_report(_result(), top_n=2))
    assert "## Model Cards" in markdown
    assert "### org/licensed-model" in markdown
    assert "LICENSE_REVIEW_REQUIRED" in markdown


def test_cli_json_contains_model_cards():
    payload = json.loads(render_output(_result(), "json", top_n=2))
    assert len(payload["model_cards"]) == 2
    assert payload["model_cards"][0]["model_id"] == "org/licensed-model"
