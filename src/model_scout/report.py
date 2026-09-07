from __future__ import annotations

from typing import Any


def build_report(result: dict[str, Any], top_n: int = 5) -> dict[str, Any]:
    candidates = list(result.get("candidates") or [])[:top_n]
    recommended = next((c for c in candidates if c.get("status") != "LICENSE_REVIEW_REQUIRED"), candidates[0] if candidates else None)
    return {
        "query": result.get("query"),
        "candidate_count": result.get("candidate_count", len(candidates)),
        "recommended": recommended,
        "shortlist": candidates,
        "warnings": [
            f"{c.get('model_id')}: LICENSE_REVIEW_REQUIRED"
            for c in candidates
            if c.get("status") == "LICENSE_REVIEW_REQUIRED"
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
    if report.get("warnings"):
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {warning}" for warning in report["warnings"])
    return "\n".join(lines) + "\n"
