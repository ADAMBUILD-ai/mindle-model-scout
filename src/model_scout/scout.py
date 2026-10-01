from __future__ import annotations
import json, time, urllib.error, urllib.parse, urllib.request
import re
from dataclasses import dataclass, asdict
from typing import Any

from .candidate_metadata import AURA_QUERIES, hydrate_candidates, rejection_reasons
from .filters import filter_candidates
from .requirements import parse_requirement
from .resources import SUPPORTED_RESOURCE_TYPES, search_resource, search_render_tools

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
    resource_type: str = "model"
    source_url: str | None = None
    last_modified: str | None = None
    revision: str | None = None
    model_files: list[str] | None = None
    distributions: list[dict[str, Any]] | None = None
    reported_license_classifier: str | None = None
    metadata_evidence: dict[str, Any] | None = None


def _license_from_tags(tags: list[str]) -> str | None:
    for tag in tags:
        if isinstance(tag, str) and tag.startswith("license:"):
            return tag.split(":", 1)[1]
    return None


def normalize_model(raw: dict[str, Any]) -> dict[str, Any]:
    tags = raw.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    card = raw.get("cardData") if isinstance(raw.get("cardData"), dict) else {}
    card_languages = card.get("language") or card.get("languages") or []
    if isinstance(card_languages, str):
        card_languages = [card_languages]
    languages = [str(value).casefold() for value in card_languages if isinstance(value, str)]
    languages.extend(tag.split(":", 1)[1].casefold() for tag in tags
                     if isinstance(tag, str) and tag.startswith("language:"))
    return {
        "model_id": raw.get("modelId") or raw.get("id") or "",
        "source_url": f"https://huggingface.co/{raw.get('modelId') or raw.get('id')}" if raw.get("modelId") or raw.get("id") else None,
        "pipeline_tag": raw.get("pipeline_tag"),
        "downloads": int(raw.get("downloads") or 0),
        "likes": int(raw.get("likes") or 0),
        "library_name": raw.get("library_name"),
        "license": _license_from_tags(tags),
        "tags": tags,
        "languages": list(dict.fromkeys(languages)),
        "revision": raw.get("sha"),
        "model_files": [str(item.get("rfilename")) for item in raw.get("siblings", [])
                        if isinstance(item, dict) and item.get("rfilename")]
        if isinstance(raw.get("siblings"), list) else None,
    }


def _license_status(license_name: str | None, commercial_use: bool = False) -> str:
    value = (license_name or "").lower()
    if not value or value in {"other", "unknown", "proprietary"}:
        return "LICENSE_REVIEW_REQUIRED"
    if commercial_use and ("-nc" in value or "non-commercial" in value):
        return "LICENSE_NOT_PERMITTED"
    return "LICENSE_ALLOWED"


def score_model(model: dict[str, Any], profile: dict[str, Any] | None = None) -> tuple[int, str, str]:
    profile = profile or {}
    popularity = min(25, 5 + int(model.get("likes") or 0) // 100 + int(model.get("downloads") or 0) // 100000)
    task_match = 15 if not profile.get("task_hint") or model.get("pipeline_tag") == profile.get("task_hint") else 0
    metadata = 15 if model.get("metadata_complete") else (10 if model.get("library_name") else 5)
    license_state = _license_status(model.get("license"), bool(profile.get("commercial_use")))
    license_points = 20 if license_state == "LICENSE_ALLOWED" else 0
    score = min(100, 25 + popularity + task_match + metadata + license_points)
    lic = model.get("license")
    components = f"popularity={popularity}; task_match={task_match}; metadata={metadata}; license={license_points}"
    if license_state != "LICENSE_ALLOWED":
        status = license_state
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
    return score, status, (status if status != "LICENSE_ALLOWED" and status.startswith("LICENSE_") else f"{components}; license:{lic or 'UNKNOWN'}")


def _fetch_huggingface_models(params: dict[str, Any], *, timeout: int, max_attempts: int) -> list[dict[str, Any]]:
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if max_attempts < 1 or max_attempts > 5:
        raise ValueError("max_attempts must be between 1 and 5")

    encoded = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{HF_API}?{encoded}", headers={"User-Agent": "mindle-model-scout/0.2"})
    for attempt in range(1, max_attempts + 1):
        retry_after = ""
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.load(resp)
            break
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == max_attempts:
                raise HuggingFaceSearchError(
                    f"Hugging Face search failed after {attempt} attempt(s): HTTP {exc.code}"
                ) from exc
            retry_after = exc.headers.get("Retry-After", "")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == max_attempts:
                raise HuggingFaceSearchError(
                    f"Hugging Face search failed after {attempt} attempt(s): {type(exc).__name__}"
                ) from exc
        delay = float(retry_after) if str(retry_after).isdigit() else 0.25 * (2 ** (attempt - 1))
        time.sleep(min(10.0, max(0.25, delay)))

    if not isinstance(data, list):
        raise HuggingFaceSearchError("Hugging Face returned an invalid models payload")
    if any(not isinstance(item, dict) for item in data):
        raise HuggingFaceSearchError("Hugging Face returned a malformed model entry")

    return [normalize_model(item) for item in data]


def search_huggingface(query: str, limit: int = 10, timeout: int = 20, max_attempts: int = 3) -> list[dict[str, Any]]:
    if not query or not query.strip():
        raise ValueError("query must not be empty")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    return _fetch_huggingface_models(
        {"search": query.strip(), "limit": limit, "full": "true"}, timeout=timeout, max_attempts=max_attempts
    )


def search_huggingface_generation(query: str, limit: int = 10) -> list[dict[str, Any]]:
    return _fetch_huggingface_models(
        {"search": query, "pipeline_tag": "text-generation", "sort": "downloads",
         "direction": "-1", "limit": limit, "full": "true"}, timeout=15, max_attempts=2)


def search_huggingface_task(task: str, limit: int = 10, timeout: int = 20, max_attempts: int = 3) -> list[dict[str, Any]]:
    if not task or not task.strip():
        raise ValueError("task must not be empty")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    return _fetch_huggingface_models(
        {"pipeline_tag": task.strip(), "sort": "downloads", "direction": "-1", "limit": limit, "full": "true"},
        timeout=timeout, max_attempts=max_attempts,
    )


def _upstream_search_query(profile: dict[str, Any]) -> str:
    """Return the legacy primary query for evidence/backward compatibility."""
    return str(profile.get("task_hint") or profile.get("query") or profile.get("raw") or "").strip()


def _explicit_model_ids(raw: str) -> list[str]:
    # An Issue form contains many slash-delimited paths, ratios and callback
    # repositories. Only its dedicated model field can pin a model selection.
    if re.search(r"###\s+요청 Model ID\b", raw, flags=re.IGNORECASE):
        field = re.search(r"###\s+요청 Model ID\s+(.*?)(?=\s+###|$)", raw, flags=re.IGNORECASE | re.DOTALL)
        value = field.group(1).strip() if field else ""
        if value in {"", "UNKNOWN", "SCOUT_SELECTION_REQUIRED"}:
            return []
        return re.findall(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", value)
    matches = re.findall(
        r"(?<![A-Za-z0-9_.-])([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(?![A-Za-z0-9_.-])",
        raw,
    )
    reserved_path_parts = {"docs", "benchmarks", "hardware", "source", "input", "output", "license"}
    return [
        value
        for value in matches
        if value.split("/", 1)[0].casefold() not in reserved_path_parts
        and not value.casefold().endswith((".json", ".md", ".yaml", ".yml", ".py", ".txt"))
        if any(character.isupper() or character.isdigit() or character in ".-" for character in value)
    ]


def _capability_queries(raw: str) -> list[str]:
    """Map open-ended capability requests to short, deterministic Hub queries."""
    if re.search(r"(?<![a-z0-9_])aura_generative_architectural_corpus_analysis_model(?![a-z0-9_])", raw.casefold()):
        # Hub searches are model-name terms; acceptance prose is not a query.
        return AURA_QUERIES
    text = " ".join(raw.casefold().replace("_", " ").split())
    if ("embedding" in text or "임베딩" in text) and ("korean" in text or "한국어" in text):
        # Broad Hub task top hits skew English; search the multilingual embedding
        # family as well, then apply metadata, license and runtime preflight.
        return ["multilingual-e5", "multilingual", "task:feature-extraction"]
    if any(term in text for term in (
        "geometry preserving", "controlled visual", "protected pixel",
        "outside mask delta", "controlnet", "inpainting",
    )):
        return ["controlnet inpainting", "image-to-image", "diffusers controlnet"]
    if any(term in text for term in (
        "architectural visual understanding", "visual understanding",
        "proposal page", "floor plan", "site plan", "cross-view consistency",
    )):
        return ["task:document-question-answering", "task:visual-question-answering", "task:image-to-text"]
    return []


def _capability_compatible(model: dict[str, Any], raw: str) -> bool:
    """Exclude visibly wrong modalities before an open-ended request reaches acquisition."""
    queries = _capability_queries(raw)
    if not queries:
        return True
    model_id = str(model.get("model_id") or "").casefold()
    pipeline_tag = str(model.get("pipeline_tag") or "").casefold()
    if queries == AURA_QUERIES:
        return pipeline_tag == "text-generation"
    if queries[0] == "task:document-question-answering":
        return pipeline_tag in {"image-to-text", "image-text-to-text", "visual-question-answering", "document-question-answering"}
    if queries[0] in {"multilingual", "multilingual-e5"}:
        return pipeline_tag in {"feature-extraction", "sentence-similarity"}
    return ("controlnet" in model_id or "inpaint" in model_id) and pipeline_tag in {"image-to-image", "text-to-image"}


def _query_plan(profile: dict[str, Any]) -> list[str]:
    raw = str(profile.get("raw") or "")
    explicit_model_ids = _explicit_model_ids(raw)
    capability_queries = _capability_queries(raw)
    if capability_queries == AURA_QUERIES:
        return capability_queries
    task_query = f"task:{profile['task_hint']}" if profile.get("task_hint") else None
    values = [*explicit_model_ids, *capability_queries, profile.get("query"), task_query]
    return list(dict.fromkeys(str(value).strip() for value in values if value and str(value).strip()))[:3]


def _hydrate_pinned_languages(models: list[dict[str, Any]], profile: dict[str, Any]) -> None:
    """Use official exact-revision card metadata when Hub list omits languages."""
    if not ({str(x).casefold() for x in profile.get("languages") or []} & {"korean", "한국어"}):
        return
    api = None
    checked = 0
    for model in models:
        if model.get("languages") or not model.get("revision"):
            continue
        if model.get("pipeline_tag") not in {"feature-extraction", "sentence-similarity", "text-generation"}:
            continue
        if not model.get("license"):
            continue
        if checked >= 12:
            break
        checked += 1
        if api is None:
            from huggingface_hub import HfApi
            api = HfApi()
        info = api.model_info(str(model["model_id"]), revision=str(model["revision"]))
        if str(getattr(info, "sha", "")).casefold() != str(model["revision"]).casefold():
            continue
        card = getattr(info, "card_data", None)
        if hasattr(card, "to_dict"):
            card = card.to_dict()
        if not isinstance(card, dict):
            card = {}
        documented = normalize_model({"id": model["model_id"], "tags": list(getattr(info, "tags", None) or []), "cardData": card})
        model["languages"] = documented["languages"]


def scout(query: str, limit: int = 10, resource_type: str = "model") -> dict[str, Any]:
    if resource_type not in (*SUPPORTED_RESOURCE_TYPES, "tool", "all"):
        raise ValueError("resource_type must be model, dataset, space, tool, or all")
    profile = parse_requirement(query)
    is_aura_analysis = _capability_queries(str(profile.get("raw") or "")) == AURA_QUERIES
    if is_aura_analysis:
        profile["task_hint"] = "text-generation"
    # Capability request is selection, not a model ID inferred from repo/path text.
    profile["explicit_model_ids"] = [] if is_aura_analysis else _explicit_model_ids(str(profile.get("raw") or ""))
    query_plan = _query_plan(profile)
    search_query = _upstream_search_query(profile)
    types = SUPPORTED_RESOURCE_TYPES if resource_type == "all" else (resource_type,)
    models: list[dict[str, Any]] = []
    query_receipts = []

    for kind in types:
        if kind == "tool":
            if not any(word in query.casefold() for word in ("render", "mapping", "pbr", "texture", "glb")):
                raise ValueError("tool scouting requires an explicit render or mapping capability")
            models.extend(search_render_tools())
            continue
        for planned_query in query_plan:
            if kind == "model":
                if is_aura_analysis:
                    found = search_huggingface_generation(planned_query, limit)
                    models.extend(found)
                    query_receipts.append({"query": planned_query, "task": "text-generation", "searched_count": len(found),
                                           "candidate_identities": [{"model_id": m.get("model_id"), "revision": m.get("revision")} for m in found]})
                elif planned_query.startswith("task:"):
                    models.extend(search_huggingface_task(planned_query.split(":", 1)[1], limit))
                else:
                    models.extend(search_huggingface(planned_query, limit))
            else:
                models.extend(search_resource(kind, planned_query, limit))

    deduped = {(item.get("resource_type", "model"), item.get("model_id")): item for item in models if item.get("model_id")}
    models = list(deduped.values())
    if resource_type == "model":
        if is_aura_analysis:
            models = hydrate_candidates(models)
        else:
            _hydrate_pinned_languages(models, profile)
    rejection_table = [{"model_id": m.get("model_id"), "revision": m.get("revision"),
                        "hydration_status": m.get("hydration_status"), "metadata_evidence": m.get("metadata_evidence"),
                        "reasons": rejection_reasons(m)} for m in models] if is_aura_analysis else []
    filtered_models = [
        model for model in filter_candidates(models, profile)
        if _capability_compatible(model, str(profile.get("raw") or ""))
        and (not is_aura_analysis or not rejection_reasons(model))
    ]
    if resource_type == "tool":
        filtered_models = models  # PyPI package metadata has no Hub task/language tags.

    candidates = []
    for model in filtered_models:
        score, status, reason = score_model(model, profile)
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
                model.get("resource_type", "model"),
                model.get("source_url"),
                model.get("last_modified"),
                model.get("revision"),
                model.get("model_files"),
                model.get("distributions"),
                model.get("reported_license_classifier"),
                model.get("metadata_evidence"),
            )
        )
    candidates.sort(key=lambda x: (x.status in {"LICENSE_REVIEW_REQUIRED", "LICENSE_NOT_PERMITTED", "REJECT"}, -x.score, -x.downloads))
    return {
        "query": query,
        "search_query": search_query,
        "query_plan": query_plan,
        "resource_type": resource_type,
        "requirement_profile": profile,
        "query_receipts": query_receipts,
        "candidate_rejection_table": rejection_table,
        "metadata_hydration_incomplete": any(m.get("hydration_status") == "METADATA_FETCH_FAILED" for m in models) if is_aura_analysis else False,
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
        enriched["recommended"] = report["recommended"]
        enriched["comparison"] = report["comparison"]
        enriched["warnings"] = report["warnings"]
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
    parser.add_argument("--resource", choices=("model", "dataset", "space", "all"), default="model")
    parser.add_argument(
        "--watch-snapshot",
        metavar="PATH",
        help="run one watch cycle using PATH as the persisted candidate snapshot; emits JSON delta evidence",
    )
    args = parser.parse_args()

    if args.watch_snapshot:
        from .watch import run_watch

        result = run_watch(args.query, args.watch_snapshot, args.limit, resource_type=args.resource)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    result = scout(args.query, args.limit, args.resource)
    print(render_output(result, args.format, args.top_n), end="" if args.format == "markdown" else "\n")


if __name__ == "__main__":
    main()
