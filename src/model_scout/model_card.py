from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

HF_BASE_URL = "https://huggingface.co"


def build_model_card(candidate: dict[str, Any], checked_at: str | None = None) -> dict[str, Any]:
    model_id = candidate.get("model_id") or ""
    license_name = candidate.get("license")
    status = candidate.get("status") or "UNKNOWN"
    if not license_name:
        status = "LICENSE_REVIEW_REQUIRED"

    resource_type = candidate.get("resource_type") or "model"
    segment = "datasets/" if resource_type == "dataset" else "spaces/" if resource_type == "space" else ""
    return {
        "model_id": model_id,
        "resource_type": resource_type,
        "source_url": candidate.get("source_url") or (f"{HF_BASE_URL}/{segment}{model_id}" if model_id else None),
        "pipeline_tag": candidate.get("pipeline_tag"),
        "library_name": candidate.get("library_name"),
        "license": license_name,
        "downloads": int(candidate.get("downloads") or 0),
        "likes": int(candidate.get("likes") or 0),
        "score": int(candidate.get("score") or 0),
        "status": status,
        "reason": candidate.get("reason"),
        "checked_at": checked_at or datetime.now(timezone.utc).isoformat(),
    }


def render_model_card_markdown(card: dict[str, Any]) -> str:
    def value(name: str) -> str:
        v = card.get(name)
        return "UNKNOWN" if v is None or v == "" else str(v)

    return "\n".join(
        [
            f"# MODEL CARD — {value('model_id')}",
            "",
            f"- Source: {value('source_url')}",
            f"- Pipeline: {value('pipeline_tag')}",
            f"- Library: {value('library_name')}",
            f"- License: {value('license')}",
            f"- Downloads: {value('downloads')}",
            f"- Likes: {value('likes')}",
            f"- Score: {value('score')}",
            f"- Status: {value('status')}",
            f"- Reason: {value('reason')}",
            f"- Checked At: {value('checked_at')}",
            "",
        ]
    )
