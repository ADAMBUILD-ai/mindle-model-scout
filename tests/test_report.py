from src.model_scout.report import build_report, render_markdown


def test_build_report_prefers_non_license_blocked_candidate():
    result = {
        "query": "floor plan wall door segmentation",
        "candidate_count": 2,
        "candidates": [
            {"model_id": "blocked/model", "score": 98, "status": "LICENSE_REVIEW_REQUIRED", "license": None},
            {"model_id": "good/model", "score": 88, "status": "APPROVED", "license": "apache-2.0"},
        ],
    }
    report = build_report(result)
    assert report["recommended"]["model_id"] == "good/model"
    assert report["warnings"] == ["blocked/model: LICENSE_REVIEW_REQUIRED"]


def test_render_markdown_contains_recommendation_and_shortlist():
    report = {
        "query": "bert",
        "recommended": {"model_id": "a/b", "score": 90, "status": "PRIORITY", "license": "apache-2.0"},
        "shortlist": [{"model_id": "a/b", "score": 90, "status": "PRIORITY", "license": "apache-2.0"}],
        "warnings": [],
    }
    text = render_markdown(report)
    assert "# MINDLE MODEL SCOUT REPORT" in text
    assert "Model: a/b" in text
    assert "score=90" in text
