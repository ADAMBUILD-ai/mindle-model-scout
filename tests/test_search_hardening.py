import importlib
import urllib.error

import pytest

scout_module = importlib.import_module("src.model_scout.scout")
HuggingFaceSearchError = scout_module.HuggingFaceSearchError
scout = scout_module.scout
search_huggingface = scout_module.search_huggingface
query_plan = scout_module._query_plan


class _DummyResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_scout_prefers_task_hint_for_upstream_search(monkeypatch):
    seen = {}

    def fake_search(query, limit=10, timeout=20):
        seen["query"] = query
        return []

    monkeypatch.setattr(scout_module, "search_huggingface", fake_search)
    result = scout("상업용 TTS 라이선스 필요 downloads 1000 이상", limit=10)

    assert seen["query"] == "text-to-speech"
    assert result["search_query"] == "text-to-speech"
    assert result["requirement_profile"]["license_required"] is True
    assert result["requirement_profile"]["min_downloads"] == 1000


def test_query_plan_prioritizes_explicit_model_ids():
    profile = {
        "raw": "Validate BAAI/bge-m3 and BAAI/bge-reranker-v2-m3 for Korean retrieval",
        "query": "full issue body",
        "task_hint": "feature-extraction",
    }

    assert query_plan(profile) == [
        "BAAI/bge-m3",
        "BAAI/bge-reranker-v2-m3",
        "full issue body",
    ]


def test_query_plan_ignores_generic_slash_terms():
    profile = {
        "raw": "Validate BAAI/bge-m3 with source/license and input/output evidence",
        "query": "full issue body",
        "task_hint": "feature-extraction",
    }

    assert query_plan(profile) == ["BAAI/bge-m3", "full issue body", "feature-extraction"]


def test_query_plan_maps_architectural_visual_understanding_capability():
    profile = {
        "raw": "ARCHITECTURAL_VISUAL_UNDERSTANDING_REPLACEMENT for site plan, floor plan, section, elevation and proposal page",
        "query": "full issue body",
        "task_hint": None,
    }

    assert query_plan(profile) == [
        "document visual question answering",
        "vision language model",
        "image-to-text",
    ]


def test_query_plan_maps_geometry_preserving_visual_edit_capability():
    profile = {
        "raw": "GEOMETRY_PRESERVING_CONTROLLED_VISUAL_GENERATION_EDIT with protected pixels and outside-mask delta = 0",
        "query": "full issue body",
        "task_hint": None,
    }

    assert query_plan(profile) == [
        "controlnet inpainting",
        "image-to-image",
        "diffusers controlnet",
    ]


@pytest.mark.parametrize("capability,expected", [
    ("ARCHITECTURAL_VISUAL_UNDERSTANDING_REPLACEMENT", "document visual question answering"),
    ("GEOMETRY_PRESERVING_CONTROLLED_VISUAL_GENERATION_EDIT", "controlnet inpainting"),
])
def test_issue_form_paths_and_owner_do_not_displace_capability(capability, expected):
    body = (
        "### 요청 Owner / 담당자\nAURA Commander\n"
        f"### 필요한 기능 / 해결할 문제\n{capability}\n"
        "Reference: docs/model-scout/REQUEST.md\n"
        "Benchmark: docs/model-scout/benchmarks/FIXTURE.json\n"
        "### PASS 기준\npinned revision + SHA-256 + license snapshot + hardware/RAM"
    )
    profile = scout_module.parse_requirement(body)
    assert profile["task_hint"] != "token-classification"
    assert query_plan(profile)[0] == expected
    assert scout_module._explicit_model_ids(body) == []


def test_explicit_model_id_bypasses_inferred_pipeline_mismatch():
    candidates = [{
        "model_id": "BAAI/bge-m3",
        "resource_type": "model",
        "pipeline_tag": "sentence-similarity",
        "license": "mit",
        "downloads": 1,
        "likes": 1,
    }]
    profile = {
        "task_hint": "feature-extraction",
        "explicit_model_ids": ["BAAI/bge-m3"],
    }

    assert scout_module.filter_candidates(candidates, profile) == candidates


def test_search_rejects_unsafe_bounds():
    with pytest.raises(ValueError):
        search_huggingface("tts", limit=0)
    with pytest.raises(ValueError):
        search_huggingface("tts", limit=101)
    with pytest.raises(ValueError):
        search_huggingface("tts", timeout=0)
    with pytest.raises(ValueError):
        search_huggingface("   ")


def test_search_fails_closed_on_invalid_payload(monkeypatch):
    monkeypatch.setattr(scout_module.urllib.request, "urlopen", lambda *args, **kwargs: _DummyResponse())
    monkeypatch.setattr(scout_module.json, "load", lambda response: {"unexpected": "object"})

    with pytest.raises(HuggingFaceSearchError, match="invalid models payload"):
        search_huggingface("tts")


def test_search_fails_closed_on_malformed_entry(monkeypatch):
    monkeypatch.setattr(scout_module.urllib.request, "urlopen", lambda *args, **kwargs: _DummyResponse())
    monkeypatch.setattr(scout_module.json, "load", lambda response: [{"id": "ok"}, "bad-entry"])

    with pytest.raises(HuggingFaceSearchError, match="malformed model entry"):
        search_huggingface("tts")


def test_search_wraps_network_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(scout_module.urllib.request, "urlopen", fail)

    with pytest.raises(HuggingFaceSearchError, match="Hugging Face search failed"):
        search_huggingface("tts")


def test_search_retries_retryable_5xx_then_succeeds(monkeypatch):
    calls = 0

    def flaky(request, timeout):
        nonlocal calls
        calls += 1
        if calls < 3:
            raise urllib.error.HTTPError(request.full_url, 503, "temporary", {}, None)
        return _DummyResponse()

    monkeypatch.setattr(scout_module.urllib.request, "urlopen", flaky)
    monkeypatch.setattr(scout_module.json, "load", lambda response: [])
    monkeypatch.setattr(scout_module.time, "sleep", lambda seconds: None)

    assert search_huggingface("tts") == []
    assert calls == 3


def test_search_does_not_retry_client_error(monkeypatch):
    calls = 0

    def rejected(request, timeout):
        nonlocal calls
        calls += 1
        raise urllib.error.HTTPError(request.full_url, 401, "unauthorized", {}, None)

    monkeypatch.setattr(scout_module.urllib.request, "urlopen", rejected)
    monkeypatch.setattr(scout_module.time, "sleep", lambda seconds: None)

    with pytest.raises(HuggingFaceSearchError, match="after 1 attempt"):
        search_huggingface("tts")
    assert calls == 1
