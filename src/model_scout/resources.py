from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

HF_API_ROOT = "https://huggingface.co/api"
HF_BASE_URL = "https://huggingface.co"
SUPPORTED_RESOURCE_TYPES = ("model", "dataset", "space")


class HuggingFaceSearchError(RuntimeError):
    pass


def _license(tags: list[Any]) -> str | None:
    return next((tag.split(":", 1)[1] for tag in tags if isinstance(tag, str) and tag.startswith("license:")), None)


def normalize_resource(raw: dict[str, Any], resource_type: str) -> dict[str, Any]:
    tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
    item_id = raw.get("modelId") or raw.get("id") or raw.get("name") or ""
    card = raw.get("cardData") if isinstance(raw.get("cardData"), dict) else {}
    license_name = _license(tags) or card.get("license") or raw.get("license")
    segment = "datasets" if resource_type == "dataset" else "spaces" if resource_type == "space" else ""
    return {
        "model_id": item_id,
        "resource_type": resource_type,
        "source_url": f"{HF_BASE_URL}/{segment + '/' if segment else ''}{item_id}" if item_id else None,
        "pipeline_tag": raw.get("pipeline_tag") or card.get("pipeline_tag"),
        "downloads": int(raw.get("downloads") or 0),
        "likes": int(raw.get("likes") or 0),
        "library_name": raw.get("library_name") or raw.get("sdk") or card.get("library_name"),
        "license": license_name,
        "tags": tags,
        "last_modified": raw.get("lastModified") or raw.get("last_modified"),
        "languages": card.get("language") or card.get("languages") or [],
        "metadata_complete": bool(item_id and license_name and (raw.get("pipeline_tag") or resource_type != "model")),
    }


def search_resource(resource_type: str, query: str, limit: int = 10, timeout: int = 20, task_hint: str | None = None) -> list[dict[str, Any]]:
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise ValueError(f"unsupported resource_type: {resource_type}")
    if not query or not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= limit <= 100 or timeout <= 0:
        raise ValueError("limit must be 1..100 and timeout must be positive")
    endpoint = {"model": "models", "dataset": "datasets", "space": "spaces"}[resource_type]
    params: dict[str, Any] = {"search": query.strip(), "limit": limit, "full": "true", "sort": "downloads", "direction": "-1"}
    if resource_type == "model" and task_hint:
        params["pipeline_tag"] = task_hint
    req = urllib.request.Request(f"{HF_API_ROOT}/{endpoint}?{urllib.parse.urlencode(params)}", headers={"User-Agent": "mindle-model-scout/0.3"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise HuggingFaceSearchError(f"Hugging Face {resource_type} search failed: {exc}") from exc
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise HuggingFaceSearchError(f"Hugging Face returned an invalid {resource_type} payload")
    return [normalize_resource(row, resource_type) for row in data]


def checked_at() -> str:
    return datetime.now(timezone.utc).isoformat()
