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

    assert result["searched_candidate_count"] == 1
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
