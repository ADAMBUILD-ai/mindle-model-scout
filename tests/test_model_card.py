from src.model_scout.model_card import build_model_card, render_model_card_markdown


def test_build_model_card_preserves_license_and_source():
    candidate = {
        "model_id": "org/model",
        "pipeline_tag": "text-classification",
        "library_name": "transformers",
        "license": "apache-2.0",
        "downloads": 123,
        "likes": 9,
        "score": 88,
        "status": "APPROVED",
        "reason": "license:apache-2.0",
    }
    card = build_model_card(candidate, checked_at="2026-09-08T00:00:00+00:00")
    assert card["source_url"] == "https://huggingface.co/org/model"
    assert card["license"] == "apache-2.0"
    assert card["status"] == "APPROVED"
    assert card["score"] == 88


def test_missing_license_is_always_review_required():
    candidate = {
        "model_id": "org/unlicensed",
        "pipeline_tag": None,
        "library_name": None,
        "license": None,
        "downloads": 0,
        "likes": 0,
        "score": 95,
        "status": "PRIORITY",
        "reason": "LICENSE_REVIEW_REQUIRED",
    }
    card = build_model_card(candidate, checked_at="2026-09-08T00:00:00+00:00")
    assert card["status"] == "LICENSE_REVIEW_REQUIRED"
    assert card["license"] is None


def test_markdown_render_contains_gate_fields():
    card = build_model_card(
        {
            "model_id": "org/model",
            "license": "mit",
            "score": 90,
            "status": "PRIORITY",
            "reason": "license:mit",
        },
        checked_at="2026-09-08T00:00:00+00:00",
    )
    markdown = render_model_card_markdown(card)
    assert markdown.startswith("# MODEL CARD — org/model")
    assert "- License: mit" in markdown
    assert "- Score: 90" in markdown
    assert "- Status: PRIORITY" in markdown
