from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

HF_API_ROOT = "https://huggingface.co/api"
HF_BASE_URL = "https://huggingface.co"
SUPPORTED_RESOURCE_TYPES = ("model", "dataset", "space")
RENDER_TOOL_PACKAGES = ("pyrender", "trimesh", "open3d")


class HuggingFaceSearchError(RuntimeError):
    pass


def search_render_tools(timeout: int = 20) -> list[dict[str, Any]]:
    """Discover a fixed set of render programs from their official PyPI records.

    Metadata is scouting evidence only. A package is not acquired or executable
    until an exact distribution, its license file and CPU output are verified.
    """
    candidates = []
    for package in RENDER_TOOL_PACKAGES:
        request = urllib.request.Request(
            f"https://pypi.org/pypi/{package}/json",
            headers={"User-Agent": "mindle-model-scout/0.3", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
        info = payload.get("info") or {}
        version = str(info.get("version") or "")
        distributions = [item for item in payload.get("urls", [])
                         if isinstance(item, dict) and not item.get("yanked")
                         and item.get("packagetype") == "bdist_wheel"
                         and len(str((item.get("digests") or {}).get("sha256") or "")) == 64]
        if not version or not distributions:
            continue
        classifiers = info.get("classifiers") or []
        reported_license = next((value for marker, value in (
            ("License :: OSI Approved :: MIT License", "mit"),
            ("License :: OSI Approved :: BSD License", "bsd-3-clause"),
            ("License :: OSI Approved :: Apache Software License", "apache-2.0"),
        ) if marker in classifiers), None)
        candidates.append({
            "model_id": f"pypi/{package}", "resource_type": "tool", "source_url": f"https://pypi.org/project/{package}/{version}/",
            "pipeline_tag": "glb-pbr-render", "revision": version, "license": None,
            "reported_license_classifier": reported_license,
            "downloads": 0, "likes": 0, "library_name": "pypi", "tags": [],
            "distributions": [{"filename": item["filename"], "sha256": item["digests"]["sha256"], "size": item["size"]}
                              for item in distributions],
        })
    return candidates


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


def search_resource(resource_type: str, query: str, limit: int = 10, timeout: int = 20, task_hint: str | None = None, max_attempts: int = 3) -> list[dict[str, Any]]:
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise ValueError(f"unsupported resource_type: {resource_type}")
    if not query or not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= limit <= 100 or timeout <= 0:
        raise ValueError("limit must be 1..100 and timeout must be positive")
    if max_attempts < 1 or max_attempts > 5:
        raise ValueError("max_attempts must be between 1 and 5")
    endpoint = {"model": "models", "dataset": "datasets", "space": "spaces"}[resource_type]
    params: dict[str, Any] = {"search": query.strip(), "limit": limit, "full": "true", "sort": "downloads", "direction": "-1"}
    if resource_type == "model" and task_hint:
        params["pipeline_tag"] = task_hint
    req = urllib.request.Request(f"{HF_API_ROOT}/{endpoint}?{urllib.parse.urlencode(params)}", headers={"User-Agent": "mindle-model-scout/0.3"})
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.load(response)
            break
        except urllib.error.HTTPError as exc:
            if exc.code not in {500, 502, 503, 504} or attempt == max_attempts:
                raise HuggingFaceSearchError(
                    f"Hugging Face {resource_type} search failed after {attempt} attempt(s): HTTP {exc.code}"
                ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == max_attempts:
                raise HuggingFaceSearchError(
                    f"Hugging Face {resource_type} search failed after {attempt} attempt(s): {type(exc).__name__}"
                ) from exc
        except json.JSONDecodeError as exc:
            raise HuggingFaceSearchError(f"Hugging Face {resource_type} search returned invalid JSON") from exc
        time.sleep(0.25 * (2 ** (attempt - 1)))
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise HuggingFaceSearchError(f"Hugging Face returned an invalid {resource_type} payload")
    return [normalize_resource(row, resource_type) for row in data]


def checked_at() -> str:
    return datetime.now(timezone.utc).isoformat()
