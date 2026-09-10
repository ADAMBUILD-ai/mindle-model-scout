from __future__ import annotations
import json, urllib.parse, urllib.request
from dataclasses import dataclass, asdict
from typing import Any

from .filters import filter_candidates
from .requirements import parse_requirement

HF_API = "https://huggingface.co/api/models"


@dataclass
class Candidate:
    model_id: str
    pipeline_tag: str | None
    downloads: int
    likes: int
    library_name: str | None
    license: str | None
    score: int
    status: str
    reason: str


def _license_from_tags(tags: list[str]) -> str | None:
    for tag in tags:
        if isinstance(tag, str) and tag.startswith("license:"):
            return tag.split(":", 1)[1]
    return None


def normalize_model(raw: dict[str, Any]) -> dict[str, Any]:
    tags = raw.get("tags") or []
    return {
        "model_id": raw.get("modelId") or raw.get("id") or "",
        "pipeline_tag": raw.get("pipeline_tag"),
        "downloads": int(raw.get("downloads") or 0),
        "likes": int(raw.get("likes") or 0),
        "library_name": raw.get("library_name"),
        "license": _license_from_tags(tags),
        "tags": tags,
    }


def score_model(model: dict[str, Any]) -> tuple[int, str, str]:
    score = 25
    score += min(20, 5 + model["likes"] // 100 + model["downloads"] // 100000)
    lic = model.get("license")
    if lic:
        score += 15
        note = f"license:{lic}"
    else:
        note = "LICENSE_REVIEW_REQUIRED"
    score += 10 if model.get("library_name") else 5
    score += 10
    score += 5
    score += 5 if model["downloads"] > 0 else 2
    score += 5
    score += 5
    score = min(100, score)
    if not lic:
        status = "LICENSE_REVIEW_REQUIRED"
    elif score >= 90:
        status = "PRIORITY"
    elif score >= 80:
        status = "APPROVED"
    elif score >= 70:
        status = "TEST"
    elif score >= 60:
        status = "HOLD"
    else:
        status = "REJECT"
    return score, status, note


def search_huggingface(query: str, limit: int = 10, timeout: int = 20) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"search": query, "limit": limit, "full": "true"})
    req = urllib.request.Request(f"{HF_API}?{params}", headers={"User-Agent": "mindle-model-scout/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    return [normalize_model(item) for item in data]


def scout(query: str, limit: int = 10) -> dict[str, Any]:
    profile = parse_requirement(query)
    models = search_huggingface(query, limit)
    filtered_models = filter_candidates(models, profile)

    candidates = []
    for model in filtered_models:
        score, status, reason = score_model(model)
        candidates.append(
            Candidate(
                model["model_id"],
                model["pipeline_tag"],
                model["downloads"],
                model["likes"],
                model["library_name"],
                model["license"],
                score,
                status,
                reason,
            )
        )
    candidates.sort(key=lambda x: (x.status == "LICENSE_REVIEW_REQUIRED", -x.score, -x.downloads))
    return {
        "query": query,
        "requirement_profile": profile,
        "searched_candidate_count": len(models),
        "candidate_count": len(candidates),
        "candidates": [asdict(c) for c in candidates],
    }


def render_output(result: dict[str, Any], output_format: str = "json", top_n: int = 5) -> str:
    from .report import build_report, render_markdown
    report = build_report(result, top_n=top_n)
    if output_format == "json":
        enriched = dict(result)
        enriched["model_cards"] = report["model_cards"]
        return json.dumps(enriched, ensure_ascii=False, indent=2)
    if output_format == "markdown":
        return render_markdown(report)
    raise ValueError(f"unsupported output format: {output_format}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="MINDLE MODEL SCOUT - Hugging Face MVP")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--top-n", type=int, default=5)
    args = parser.parse_args()
    result = scout(args.query, args.limit)
    print(render_output(result, args.format, args.top_n), end="" if args.format == "markdown" else "\n")


if __name__ == "__main__":
    main()
