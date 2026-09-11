from src.model_scout.model_card import build_model_card
from src.model_scout.scout import score_model
from src.model_scout.watch import diff_candidates


def test_dataset_card_uses_dataset_url():
    card = build_model_card({"model_id": "org/data", "resource_type": "dataset", "license": "mit"})
    assert card["source_url"] == "https://huggingface.co/datasets/org/data"


def test_commercial_noncommercial_license_is_blocked():
    model = {"model_id": "x", "downloads": 1, "likes": 1, "license": "cc-by-nc-4.0"}
    assert score_model(model, {"commercial_use": True})[1] == "LICENSE_NOT_PERMITTED"


def test_watch_keeps_resource_types_separate():
    previous = [{"model_id": "same", "resource_type": "model"}]
    current = [{"model_id": "same", "resource_type": "dataset"}]
    delta = diff_candidates(previous, current)
    assert len(delta["added"]) == 1 and len(delta["removed"]) == 1


def test_report_never_recommends_commercially_blocked_candidate():
    from src.model_scout.report import build_report
    result = {
        "query": "commercial image",
        "candidates": [
            {"model_id": "blocked", "resource_type": "model", "license": "cc-by-nc-4.0", "score": 95, "status": "LICENSE_NOT_PERMITTED"},
            {"model_id": "allowed", "resource_type": "model", "license": "apache-2.0", "score": 80, "status": "APPROVED"},
        ],
    }
    report = build_report(result)
    assert report["recommended"]["model_id"] == "allowed"
    assert any("LICENSE_NOT_PERMITTED" in warning for warning in report["warnings"])


def test_json_output_contains_comparison_and_warnings():
    import json
    from src.model_scout.scout import render_output
    result = {
        "query": "commercial image",
        "candidates": [
            {"model_id": "blocked", "resource_type": "model", "license": "cc-by-nc-4.0", "score": 95, "status": "LICENSE_NOT_PERMITTED", "reason": "LICENSE_NOT_PERMITTED"}
        ],
        "candidate_count": 1,
    }
    payload = json.loads(render_output(result, "json"))
    assert "comparison" in payload
    assert "warnings" in payload
    assert payload["recommended"] is None
