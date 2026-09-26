from src.model_scout.scout import normalize_model, score_model


def test_normalize_model_keeps_exact_search_weight_listing():
    model = normalize_model({"id": "example/vision", "sha": "a" * 40,
                             "siblings": [{"rfilename": "model.safetensors"}, {"rfilename": "README.md"}]})
    assert model["model_files"] == ["model.safetensors", "README.md"]
    assert normalize_model({"id": "example/unknown"})["model_files"] is None

def test_normalize_license():
    model = normalize_model({"id": "a/b", "tags": ["license:apache-2.0"], "downloads": 123, "likes": 5})
    assert model["model_id"] == "a/b"
    assert model["license"] == "apache-2.0"

def test_missing_license_gate():
    model = {"model_id": "x", "pipeline_tag": None, "downloads": 0, "likes": 0, "library_name": None, "license": None, "tags": []}
    score, status, reason = score_model(model)
    assert status == "LICENSE_REVIEW_REQUIRED"
    assert reason == "LICENSE_REVIEW_REQUIRED"
    assert 0 <= score <= 100
