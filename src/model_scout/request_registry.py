from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping


REQUEST_TYPES = (
    "EXACT_MODEL_REQUEST",
    "CAPABILITY_REQUEST",
    "FAMILY_REQUEST",
    "TOOL_REQUEST",
    "DATASET_REQUEST",
    "UNKNOWN_LEGACY",
)


def classify_request(record: Mapping[str, object]) -> str:
    resource = str(record.get("resource_type") or "").casefold()
    if resource == "tool":
        return "TOOL_REQUEST"
    if resource == "dataset":
        return "DATASET_REQUEST"
    model_id = str(record.get("requested_model_id") or "UNKNOWN")
    if model_id not in {"UNKNOWN", "SCOUT_SELECTION_REQUIRED"}:
        return "EXACT_MODEL_REQUEST"
    family = str(record.get("requested_model_family") or "UNKNOWN")
    if family != "UNKNOWN":
        return "FAMILY_REQUEST"
    if str(record.get("requested_capability") or "UNKNOWN") != "UNKNOWN":
        return "CAPABILITY_REQUEST"
    return "UNKNOWN_LEGACY"


def export_request_registry(records: Iterable[Mapping[str, object]]) -> dict[str, object]:
    """Return a stable, request-centric registry independent of input order."""

    normalized = []
    for record in records:
        item = dict(record)
        item["request_type"] = classify_request(item)
        normalized.append(item)
    normalized.sort(key=lambda item: str(item["request_id"]))
    counts = Counter(str(item["request_type"]) for item in normalized)
    return {
        "schema_version": "1.0",
        "total_requests": len(normalized),
        "request_type_counts": {key: counts.get(key, 0) for key in REQUEST_TYPES},
        "requests": normalized,
    }
