from __future__ import annotations

from typing import Any


def filter_candidates(candidates: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for candidate in candidates:
        if profile.get("task_hint") and candidate.get("pipeline_tag") != profile["task_hint"]:
            continue
        if profile.get("license_required") and not candidate.get("license"):
            continue
        if int(candidate.get("downloads") or 0) < int(profile.get("min_downloads") or 0):
            continue
        if int(candidate.get("likes") or 0) < int(profile.get("min_likes") or 0):
            continue
        result.append(candidate)
    return result
