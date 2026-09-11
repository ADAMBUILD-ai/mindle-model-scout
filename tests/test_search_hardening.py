import urllib.error

import pytest

import model_scout.scout as scout_module
from model_scout.scout import HuggingFaceSearchError, scout, search_huggingface


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
