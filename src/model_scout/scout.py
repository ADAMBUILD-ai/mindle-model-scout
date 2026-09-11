from __future__ import annotations
import json, urllib.error, urllib.parse, urllib.request
from dataclasses import dataclass, asdict
from typing import Any

from .filters import filter_candidates
from .requirements import parse_requirement

HF_API = "https://huggingface.co/api/models"


class HuggingFaceSearchError(RuntimeError):
    """Raised when Hugging Face search cannot produce a trustworthy candidate list."""


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
    if not isinstance(tags, list):
        tags = []
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
    if not query or not query.strip():
        raise ValueError("query must not be empty")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    if timeout <= 0:
        raise ValueError("timeout must be positive")

    params = urllib.parse.urlencode({"search": query.strip(), "limit": limit, "full": "true"})
    req = urllib.request.Request(f"{HF_API}?{params}", headers={"User-Agent": "mindle-model-scout/0.2"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise HuggingFaceSearchError(f"Hugging Face search failed: {exc}") from exc

    if not isinstance(data, list):
        raise HuggingFaceSearchError("Hugging Face returned an invalid models payload")
    if any(not isinstance(item, dict) for item in data):
        raise HuggingFaceSearchError("Hugging Face returned a malformed model entry")

    return [normalize_model(item) for item in data]


def _upstream_search_query(profile: dict[str, Any]) -> str:
    """Prefer a recognized task hint over a long natural-language constraint sentence."""
    return str(profile.get("task_hint") or profile.get("query") or profile.get("raw") or "").strip()


def scout(query: str, limit: int = 10) -> dict[str, Any]:
    profile = parse_requirement(query)
    search_query = _upstream_search_query(profile)
    models = search_huggingface(search_query, limit)
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
        "search_query": search_query,
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
    parser.add_argument(
        "--watch-snapshot",
        metavar="PATH",
        help="run one watch cycle using PATH as the persisted candidate snapshot; emits JSON delta evidence",
    )
    args = parser.parse_args()

    if args.watch_snapshot:
        from .watch import run_watch

        result = run_watch(args.query, args.watch_snapshot, args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    result = scout(args.query, args.limit)
    print(render_output(result, args.format, args.top_n), end="" if args.format == "markdown" else "\n")


if __name__ == "__main__":
    main()
