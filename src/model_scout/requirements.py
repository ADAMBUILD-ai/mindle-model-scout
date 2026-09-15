from __future__ import annotations

from dataclasses import dataclass, asdict
import re


@dataclass
class RequirementProfile:
    raw: str
    query: str
    task_hint: str | None = None
    license_required: bool = False
    commercial_use: bool = False
    min_downloads: int = 0
    min_likes: int = 0
    languages: list[str] | None = None
    library_hint: str | None = None
    semantic_intent: str | None = None
    fallback_queries: list[str] | None = None


def _contains_keyword(value: str, keyword: str) -> bool:
    if keyword.isascii():
        return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", value) is not None
    return keyword in value


def _structured_search_query(normalized: str, lowered: str) -> tuple[str, str | None, list[str]]:
    """Produce a lane-specific query plan for 3D work orders.

    Provider/download/runtime language is an explicit delivery request. It must not be
    swallowed by incidental context or placement words in a longer work order.
    """
    provider_terms = (
        "render provider", "provider shopping", "rendering provider", "renderer",
        "download model", "model download", "runtime validation", "local rendering",
        "deterministic local rendering", "렌더 제공", "모델 다운로드", "런타임",
    )
    placement_terms = (
        "placement drawing", "building footprint", "footprint", "transform assist",
        "scene placement", "배치도", "배치",
    )
    context_terms = (
        "context modeling", "surrounding buildings", "surrounding context",
        "terrain context", "terrain/context", "terrain", "surrounding", "context model",
        "주변 건물", "지형", "컨텍스트",
    )
    rendering_terms = ("glb", "gltf", "3d", "3d scene", "scene composition", "렌더", "렌더링")
    if any(_contains_keyword(lowered, term) for term in provider_terms):
        return ("glb gltf render provider", "3d_render_provider", ["glb gltf render provider", "blender three.js gltf runtime", "gltf local rendering"])
    if any(_contains_keyword(lowered, term) for term in placement_terms):
        return ("3d placement footprint", "3d_placement", ["building footprint placement", "3d scene placement transform"])
    if any(_contains_keyword(lowered, term) for term in context_terms):
        return ("3d terrain context scene", "3d_context", ["surrounding buildings terrain", "3d terrain context scene"])
    if any(_contains_keyword(lowered, term) for term in rendering_terms):
        return ("3d rendering gltf", "3d_rendering", ["glb gltf 3d scene", "3d rendering"])
    return normalized, None, []


def parse_requirement(text: str) -> dict:
    normalized = " ".join(text.strip().split())
    lowered = normalized.lower()

    task_hint = None
    task_keywords = {
        "text-generation": ["llm", "chat", "text generation", "대화", "텍스트 생성"],
        "text-to-image": ["image generation", "text to image", "이미지 생성"],
        "automatic-speech-recognition": ["speech recognition", "asr", "음성 인식"],
        "text-to-speech": ["tts", "text to speech", "음성 합성"],
        "image-classification": ["image classification", "이미지 분류"],
        "feature-extraction": ["embedding", "embeddings", "임베딩"],
        "image-segmentation": ["segmentation", "세그멘테이션", "분할"],
        "object-detection": ["object detection", "객체 탐지"],
        "text-classification": ["text classification", "텍스트 분류"],
        "token-classification": ["ner", "named entity", "개체명"],
        "image-to-text": ["image to text", "이미지 설명"],
    }
    for task, keywords in task_keywords.items():
        if any(_contains_keyword(lowered, keyword) for keyword in keywords):
            task_hint = task
            break

    commercial_use = any(token in lowered for token in ["commercial", "상업", "상업용", "commercial use"])
    license_required = commercial_use or any(token in lowered for token in ["license", "라이선스", "licensed"])

    min_downloads = 0
    min_likes = 0
    m = re.search(r"(?:downloads?|다운로드)\s*(?:>=|at least|이상)?\s*([0-9][0-9,]*)", lowered)
    if m:
        min_downloads = int(m.group(1).replace(",", ""))
    m = re.search(r"(?:likes?|좋아요)\s*(?:>=|at least|이상)?\s*([0-9][0-9,]*)", lowered)
    if m:
        min_likes = int(m.group(1).replace(",", ""))

    query, semantic_intent, fallback_queries = _structured_search_query(normalized, lowered)
    languages = [lang for lang in ("korean", "한국어", "english", "영어", "multilingual", "다국어") if lang in lowered]
    library_hint = next((name for name in ("transformers", "diffusers", "sentence-transformers", "pytorch", "onnx") if name in lowered), None)
    return asdict(
        RequirementProfile(
            raw=normalized,
            query=query,
            task_hint=task_hint,
            license_required=license_required,
            commercial_use=commercial_use,
            min_downloads=min_downloads,
            min_likes=min_likes,
            languages=languages,
            library_hint=library_hint,
            semantic_intent=semantic_intent,
            fallback_queries=fallback_queries,
        )
    )
