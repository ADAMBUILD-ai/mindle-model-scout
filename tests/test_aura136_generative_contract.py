import hashlib

import pytest

from src.model_scout.aura136_contract import real_sources, validate_source_citations


def _source(index: int, language: str):
    content = f"verified architectural source {index}"
    return {
        "source_id": f"SRC-{index:02d}",
        "language": language,
        "verifiedContent": content,
        "sourceValidation": {"contentHash": hashlib.sha256(content.encode("utf-8")).hexdigest()},
        "artifactRef": f"evidence/{index}.json",
    }


def test_aura136_requires_real_verified_kr10_global10_inputs():
    sources = [_source(index, "ko") for index in range(10)]
    sources.extend(_source(index, "en") for index in range(10, 20))
    result = real_sources({"scout_result": {"aura136_benchmark": {"sources": sources}}})
    assert len(result) == 20


def test_aura136_rejects_missing_real_corpus_without_model_call():
    with pytest.raises(RuntimeError, match="AURA_136_REAL_BENCHMARK_INPUT_INCOMPLETE"):
        real_sources({"scout_result": {}})


def test_aura136_rejects_invented_source_citations():
    with pytest.raises(RuntimeError, match="invented or invalid source_id"):
        validate_source_citations({"coverageMatrix": [{"source_id": "FAKE-1"}]}, {"SRC-01"})


def test_aura136_requires_structured_source_citations():
    with pytest.raises(RuntimeError, match="no structured source_id"):
        validate_source_citations({"coverageMatrix": []}, {"SRC-01"})

