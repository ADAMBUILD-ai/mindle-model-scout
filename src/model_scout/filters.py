from __future__ import annotations

from typing import Any


def filter_candidates(candidates: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    explicit_model_ids = {
        str(value).casefold()
        for value in profile.get("explicit_model_ids", ())
    }
    for candidate in candidates:
        explicitly_requested = str(candidate.get("model_id") or "").casefold() in explicit_model_ids
        if profile.get("task_hint") and not explicitly_requested and candidate.get("resource_type", "model") == "model":
            allowed_tasks = {profile["task_hint"]}
            if profile["task_hint"] == "feature-extraction" and any(
                word in str(profile.get("raw") or "").casefold() for word in ("embedding", "임베딩")
            ):
                allowed_tasks.add("sentence-similarity")
            if candidate.get("pipeline_tag") not in allowed_tasks:
                continue
        if profile.get("license_required") and not candidate.get("license"):
            continue
        if int(candidate.get("downloads") or 0) < int(profile.get("min_downloads") or 0):
            continue
        if int(candidate.get("likes") or 0) < int(profile.get("min_likes") or 0):
            continue
        if profile.get("library_hint") and not explicitly_requested and candidate.get("library_name") != profile["library_hint"]:
            continue
        requested_languages = {str(value).casefold() for value in profile.get("languages") or ()}
        if requested_languages & {"korean", "한국어"} and not explicitly_requested:
            documented = {str(value).casefold() for value in candidate.get("languages") or ()}
            if not documented & {"ko", "kor", "korean", "한국어", "multilingual", "multi"}:
                continue
        result.append(candidate)
    return result
