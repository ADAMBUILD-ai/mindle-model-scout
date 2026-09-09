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
    }
    for task, keywords in task_keywords.items():
        if any(keyword in lowered for keyword in keywords):
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

    query = normalized
    return asdict(
        RequirementProfile(
            raw=normalized,
            query=query,
            task_hint=task_hint,
            license_required=license_required,
            commercial_use=commercial_use,
            min_downloads=min_downloads,
            min_likes=min_likes,
        )
    )
