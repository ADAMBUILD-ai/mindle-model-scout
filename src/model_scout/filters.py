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
        if profile.get("task_hint") and not explicitly_requested and candidate.get("resource_type", "model") == "model" and candidate.get("pipeline_tag") != profile["task_hint"]:
            continue
        if profile.get("license_required") and not candidate.get("license"):
            continue
        if int(candidate.get("downloads") or 0) < int(profile.get("min_downloads") or 0):
            continue
        if int(candidate.get("likes") or 0) < int(profile.get("min_likes") or 0):
            continue
        if profile.get("library_hint") and not explicitly_requested and candidate.get("library_name") != profile["library_hint"]:
            continue
        result.append(candidate)
    return result
