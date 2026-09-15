import importlib


scout_module = importlib.import_module("src.model_scout.scout")


def _model(model_id, task, license_name, downloads, likes):
    return {
        "model_id": model_id,
        "pipeline_tag": task,
        "downloads": downloads,
        "likes": likes,
        "library_name": "transformers",
        "license": license_name,
        "tags": [],
    }


def test_scout_applies_requirement_profile_before_scoring(monkeypatch):
    models = [
        _model("keep", "text-to-speech", "apache-2.0", 5000, 40),
        _model("no-license", "text-to-speech", None, 9000, 80),
        _model("wrong-task", "text-generation", "apache-2.0", 12000, 90),
        _model("low-downloads", "text-to-speech", "apache-2.0", 500, 90),
        _model("low-likes", "text-to-speech", "apache-2.0", 5000, 10),
    ]
    monkeypatch.setattr(scout_module, "search_huggingface", lambda query, limit: models)

    result = scout_module.scout("tts license downloads at least 1000 likes at least 20")

    assert result["requirement_profile"]["task_hint"] == "text-to-speech"
    assert result["requirement_profile"]["license_required"] is True
    assert result["requirement_profile"]["min_downloads"] == 1000
    assert result["requirement_profile"]["min_likes"] == 20
    assert result["searched_candidate_count"] == 5
    assert result["candidate_count"] == 1
    assert [candidate["model_id"] for candidate in result["candidates"]] == ["keep"]


def test_scout_zero_match_is_valid_result(monkeypatch):
    models = [_model("small", "text-to-speech", "apache-2.0", 10, 1)]
    monkeypatch.setattr(scout_module, "search_huggingface", lambda query, limit: models)

    result = scout_module.scout("tts license downloads 99999 likes 99999")

    assert result["searched_candidate_count"] == 2
    assert result["candidate_count"] == 0
    assert result["candidates"] == []


def test_plain_query_remains_unfiltered(monkeypatch):
    models = [
        _model("a", "text-generation", None, 0, 0),
        _model("b", "text-to-speech", "apache-2.0", 100, 5),
    ]
    monkeypatch.setattr(scout_module, "search_huggingface", lambda query, limit: models)

    result = scout_module.scout("bert")

    assert result["query"] == "bert"
    assert result["requirement_profile"]["task_hint"] is None
    assert result["requirement_profile"]["license_required"] is False
    assert result["candidate_count"] == 2
    assert {candidate["model_id"] for candidate in result["candidates"]} == {"a", "b"}


def test_3d_requests_retry_with_three_structured_queries_and_reject_irrelevant_results(monkeypatch):
    calls = []

    def fake_model_search(query, limit):
        calls.append(("model", query))
        return [_model("acme/token-classifier", "token-classification", "mit", 20, 2)]

    def fake_resource_search(resource, query, limit):
        calls.append((resource, query))
        if resource == "space" and query == "3d":
            return [{
                **_model("acme/blender-3d-render", None, "mit", 20, 2),
                "resource_type": "space",
                "source_url": "https://huggingface.co/spaces/acme/blender-3d-render",
                "last_modified": None,
            }]
        return []

    monkeypatch.setattr(scout_module, "search_huggingface", fake_model_search)
    monkeypatch.setattr(scout_module, "search_resource", fake_resource_search)

    result = scout_module.scout("Find a GLB/GLTF render provider for a 3D scene", resource_type="model")

    assert result["candidate_count"] == 1
    assert result["semantic_match"] == "PASS"
    assert result["searched_resource_types"] == ["model", "dataset", "space"]
    assert [attempt["semantic_match"] for attempt in result["attempts"]] == ["REJECT", "REJECT", "PASS"]
    assert result["candidates"][0]["model_id"] == "acme/blender-3d-render"


def test_3d_render_gate_rejects_generic_3d_and_wrong_direction_candidates(monkeypatch):
    generic_models = [
        _model("keras-io/3D_CNN_Pneumonia", None, "mit", 0, 5),
        _model("YipengGao/3DCode", None, "mit", 90000, 25),
        _model("stabilityai/stable-fast-3d", "image-to-3d", "mit", 10000, 100),
        _model("wkplhc/3dRender", "text-to-image", "mit", 54, 2),
    ]
    monkeypatch.setattr(scout_module, "search_huggingface", lambda query, limit: generic_models)
    monkeypatch.setattr(scout_module, "search_resource", lambda resource, query, limit: [])

    result = scout_module.scout("Find a GLB/GLTF render provider for an existing 3D scene", resource_type="model")

    assert result["candidate_count"] == 0
    assert result["semantic_match"] == "REJECT"
    assert result["success_gate"] is False
    assert [attempt["semantic_match"] for attempt in result["attempts"]] == ["REJECT", "REJECT", "REJECT"]
