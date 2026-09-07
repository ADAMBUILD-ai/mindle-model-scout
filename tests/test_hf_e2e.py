from src.model_scout.scout import scout, search_huggingface


def test_huggingface_live_search_returns_normalized_models():
    models = search_huggingface("bert", limit=3, timeout=30)
    assert models, "Hugging Face API returned no models for a stable query"
    assert len(models) <= 3
    for model in models:
        assert model["model_id"]
        assert isinstance(model["downloads"], int)
        assert isinstance(model["likes"], int)
        assert "license" in model
        assert "tags" in model


def test_live_scout_pipeline_returns_ranked_candidates():
    result = scout("bert", limit=3)
    assert result["query"] == "bert"
    assert result["candidate_count"] == len(result["candidates"])
    assert result["candidate_count"] > 0

    for candidate in result["candidates"]:
        assert candidate["model_id"]
        assert 0 <= candidate["score"] <= 100
        assert candidate["status"] in {
            "PRIORITY",
            "APPROVED",
            "TEST",
            "HOLD",
            "REJECT",
            "LICENSE_REVIEW_REQUIRED",
        }
