from __future__ import annotations

from typing import Any

from .model_card import build_model_card, render_model_card_markdown


def build_report(result: dict[str, Any], top_n: int = 5) -> dict[str, Any]:
    candidates = list(result.get("candidates") or [])[:top_n]
    recommended = next((c for c in candidates if c.get("status") not in {"LICENSE_REVIEW_REQUIRED", "LICENSE_NOT_PERMITTED", "REJECT"}), None)
    return {
        "query": result.get("query"),
        "candidate_count": result.get("candidate_count", len(candidates)),
        "recommended": recommended,
        "shortlist": candidates,
        "model_cards": [build_model_card(candidate) for candidate in candidates],
        "warnings": [
            f"{c.get('model_id')}: {c.get('status')}"
            for c in candidates
            if c.get("status") in {"LICENSE_REVIEW_REQUIRED", "LICENSE_NOT_PERMITTED"}
        ],
        "comparison": [
            {key: candidate.get(key) for key in ("model_id", "resource_type", "pipeline_tag", "license", "downloads", "likes", "library_name", "score", "status", "reason")}
            for candidate in candidates
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# MINDLE MODEL SCOUT REPORT", "", f"Query: {report.get('query')}", ""]
    recommended = report.get("recommended")
    if recommended:
        lines.extend([
            "## Recommended",
            f"- Model: {recommended.get('model_id')}",
            f"- Score: {recommended.get('score')}",
            f"- Status: {recommended.get('status')}",
            f"- License: {recommended.get('license') or 'UNKNOWN'}",
            "",
        ])
    lines.append("## Shortlist")
    for candidate in report.get("shortlist") or []:
        lines.append(
            f"- {candidate.get('model_id')} | score={candidate.get('score')} | status={candidate.get('status')} | license={candidate.get('license') or 'UNKNOWN'}"
        )

    if report.get("comparison"):
        lines.extend(["", "## Comparison", "", "| Candidate | Type | License | Downloads | Likes | Score | Status |", "|---|---|---|---:|---:|---:|---|"])
        for item in report["comparison"]:
            lines.append(f"| {item.get('model_id')} | {item.get('resource_type') or 'model'} | {item.get('license') or 'UNKNOWN'} | {item.get('downloads') or 0} | {item.get('likes') or 0} | {item.get('score') or 0} | {item.get('status')} |")

    cards = report.get("model_cards") or []
    if cards:
        lines.extend(["", "## Model Cards", ""])
        for card in cards:
            rendered = render_model_card_markdown(card).strip().splitlines()
            if rendered:
                rendered[0] = rendered[0].replace("# MODEL CARD —", "###", 1)
            lines.extend(rendered)
            lines.append("")

    if report.get("warnings"):
        lines.extend(["## Warnings"])
        lines.extend(f"- {warning}" for warning in report["warnings"])
    return "\n".join(lines).rstrip() + "\n"
