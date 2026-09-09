from __future__ import annotations

from typing import Any


def diff_candidates(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> dict[str, list]:
    prev = {item.get("model_id"): item for item in previous if item.get("model_id")}
    curr = {item.get("model_id"): item for item in current if item.get("model_id")}

    added = [curr[key] for key in curr.keys() - prev.keys()]
    removed = [prev[key] for key in prev.keys() - curr.keys()]
    changed = []
    for key in curr.keys() & prev.keys():
        before, after = prev[key], curr[key]
        fields = ("downloads", "likes", "license", "pipeline_tag", "status", "score")
        delta = {field: (before.get(field), after.get(field)) for field in fields if before.get(field) != after.get(field)}
        if delta:
            changed.append({"model_id": key, "changes": delta})

    return {"added": added, "removed": removed, "changed": changed}
