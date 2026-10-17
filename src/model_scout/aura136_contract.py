from __future__ import annotations

import hashlib
from typing import Any


ANALYSIS_FIELDS = (
    "patternClusters", "positiveCases", "negativeMismatchCases", "contradictions",
    "constraints", "risks", "unresolvedGaps", "nextSearchTargets",
    "competingDesignHypotheses", "rejectedStrategies", "sourceBoundDesignInference",
    "drawingProofRequirements", "coverageMatrix", "confidence", "applicability",
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def real_sources(input_payload: dict[str, Any]) -> list[dict[str, Any]]:
    benchmark = input_payload.get("aura136_benchmark")
    if not isinstance(benchmark, dict):
        scout_result = input_payload.get("scout_result")
        benchmark = scout_result.get("aura136_benchmark") if isinstance(scout_result, dict) else None
    if not isinstance(benchmark, dict):
        raise RuntimeError("AURA_136_REAL_BENCHMARK_INPUT_INCOMPLETE: missing aura136_benchmark")
    sources = benchmark.get("sources")
    if not isinstance(sources, list):
        raise RuntimeError("AURA_136_REAL_BENCHMARK_INPUT_INCOMPLETE: sources must be a list")
    valid: list[dict[str, Any]] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        source_id, content = source.get("source_id"), source.get("verifiedContent")
        validation, artifact_ref = source.get("sourceValidation"), source.get("artifactRef")
        if not isinstance(source_id, str) or not isinstance(content, str) or not isinstance(validation, dict) or not isinstance(artifact_ref, str):
            continue
        if validation.get("contentHash") == sha256_text(content):
            valid.append(source)
    kr = sum(str(source.get("language", "")).casefold().startswith("ko") for source in valid)
    global_en = sum(str(source.get("language", "")).casefold().startswith("en") for source in valid)
    if len(valid) < 20 or kr < 10 or global_en < 10:
        raise RuntimeError(
            "AURA_136_REAL_BENCHMARK_INPUT_INCOMPLETE: "
            f"verified={len(valid)} kr={kr} global_en={global_en}; require >=20 / KR10 / GLOBAL10"
        )
    return valid


def validate_source_citations(analysis: dict[str, Any], allowed_ids: set[str]) -> set[str]:
    """Require structured source_id/source_ids references and reject unknown IDs."""
    cited: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "source_id":
                    if not isinstance(child, str) or child not in allowed_ids:
                        raise RuntimeError(f"AURA_136_MODEL_QUALITY_FAILED: invented or invalid source_id={child!r}")
                    cited.add(child)
                elif key == "source_ids":
                    if not isinstance(child, list) or not all(isinstance(item, str) and item in allowed_ids for item in child):
                        raise RuntimeError("AURA_136_MODEL_QUALITY_FAILED: invented or invalid source_ids")
                    cited.update(child)
                else:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(analysis)
    if not cited:
        raise RuntimeError("AURA_136_MODEL_QUALITY_FAILED: no structured source_id/source_ids citations")
    return cited
