from __future__ import annotations

import re
from typing import Iterable, Mapping

from .request_queue import RequestEnvelope, normalize_request


_REQUEST_MARKERS = (
    "model scout",
    "model_scout_request",
    "모델 스카우트",
)
_HF_MARKERS = ("hugging face", "huggingface", "허깅페이스", "허깅 페이스")
_REQUEST_INTENTS = (
    "scout",
    "shop",
    "shopping",
    "find",
    "search",
    "model request",
    "스카우트",
    "쇼핑",
    "찾아",
    "찾기",
    "검색",
    "모델 요청",
)
_RESOURCE_WORDS = ("model", "dataset", "space", "tool")
CENTRAL_REQUEST_REPOSITORY = "ADAMBUILD-ai/mindle-model-scout"


def request_discovery_repositories(configured_repos: Iterable[str]) -> tuple[str, ...]:
    """Return configured project repositories plus the central request repository."""

    repos = [str(repo or "").strip() for repo in configured_repos]
    repos.append(CENTRAL_REQUEST_REPOSITORY)
    return tuple(dict.fromkeys(repo for repo in repos if repo))


def _text(value: object) -> str:
    return str(value or "").strip()


def is_model_scout_request(title: str, body: str) -> bool:
    haystack = f"{title}\n{body}".casefold()
    if any(marker in haystack for marker in _REQUEST_MARKERS):
        return True
    has_hf = any(marker in haystack for marker in _HF_MARKERS)
    has_intent = any(intent in haystack for intent in _REQUEST_INTENTS)
    return has_hf and has_intent


def infer_priority(title: str, body: str) -> str:
    haystack = f"{title}\n{body}".upper()
    for priority in ("P0", "P1", "P2", "P3"):
        if re.search(rf"(?<![A-Z0-9]){priority}(?![A-Z0-9])", haystack):
            return priority
    return "P1"


def infer_resource(title: str, body: str) -> str:
    haystack = f"{title}\n{body}".casefold()
    if re.search(r"\ball\b", haystack) and any(word in haystack for word in _RESOURCE_WORDS):
        return "all"
    found = [word for word in _RESOURCE_WORDS if re.search(rf"\b{word}s?\b", haystack)]
    if len(found) == 1:
        return found[0]
    return "all"


def infer_project(repo: str, title: str, body: str) -> str:
    for source in (title, body):
        match = re.search(r"\[(?:P[0-3])?\]\s*\[([^\]\r\n]{2,64})\]", source)
        if match:
            return re.sub(r"[^\w-]+", "_", match.group(1).upper(), flags=re.UNICODE).strip("_")
    repo_name = repo.split("/", 1)[-1]
    return repo_name.replace("-", "_").upper()


_FORM_LABELS = {
    "요청 개발팀": "requesting_team",
    "제품 / 앱": "product",
    "요청 Owner / 담당자": "request_owner",
    "필요한 기능 / 해결할 문제": "requested_capability",
    "요청 Model ID": "requested_model_id",
    "Model Family / 계열": "requested_model_family",
    "PASS 기준": "acceptance_criteria",
    "Callback Repository": "callback_repo",
    "Callback Issue": "callback_issue",
    "Resource Type": "resource",
    "우선순위": "priority",
}


def parse_issue_form(body: str) -> dict[str, str]:
    """Parse GitHub's rendered Issue Form headings without inventing missing values."""

    parsed: dict[str, str] = {}
    matches = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", body))
    for index, match in enumerate(matches):
        key = _FORM_LABELS.get(match.group(1).strip())
        if key is None:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        value = body[match.end() : end].strip()
        if value and value != "_No response_":
            parsed[key] = value
    return parsed


def _selection_mode(model_id: str, family: str, capability: str) -> str:
    if model_id == "SCOUT_SELECTION_REQUIRED":
        return "SCOUT_SELECTION_REQUIRED"
    if model_id not in {"", "UNKNOWN"}:
        return "EXACT_MODEL"
    if family not in {"", "UNKNOWN"}:
        return "FAMILY_SELECTION_REQUIRED"
    if capability not in {"", "UNKNOWN"}:
        return "CAPABILITY_SELECTION_REQUIRED"
    return "UNKNOWN_LEGACY"


def normalize_github_issue_request(
    issue: Mapping[str, object], *, configured_repos: Iterable[str]
) -> RequestEnvelope | None:
    repo = _text(issue.get("repository_full_name") or issue.get("repo"))
    configured = {item.strip().casefold() for item in configured_repos if item and item.strip()}
    if not repo or repo.casefold() not in configured:
        return None

    title = _text(issue.get("title"))
    body = _text(issue.get("body"))
    state = _text(issue.get("state")).casefold()
    if state and state != "open":
        return None
    # Central execution directives and binary handoff gates have their own workers.
    # Sending them through the generic Hugging Face search runner produces retries
    # without a model acquisition and can incorrectly exhaust the queue.
    if repo.casefold() == CENTRAL_REQUEST_REPOSITORY.casefold() and (
        "[execution]" in title.casefold()
        or "binary handoff" in title.casefold()
    ):
        return None
    if not is_model_scout_request(title, body):
        return None

    raw_number = issue.get("number") or issue.get("issue_number")
    try:
        issue_number = int(raw_number) if raw_number is not None else None
    except (TypeError, ValueError) as exc:
        raise ValueError("issue number must be an integer") from exc
    if issue_number is None or issue_number <= 0:
        raise ValueError("issue number must be positive")

    request_text = body or title
    form = parse_issue_form(body)
    product = form.get("product", "UNKNOWN")
    requested_model_id = form.get("requested_model_id", "UNKNOWN")
    requested_model_family = form.get("requested_model_family", "UNKNOWN")
    requested_capability = form.get("requested_capability", "UNKNOWN")
    callback_repo = form.get("callback_repo", repo)
    callback_issue_raw = form.get("callback_issue", "SAME_AS_SOURCE")
    callback_issue = issue_number
    if callback_issue_raw not in {"", "SAME_AS_SOURCE"}:
        match = re.search(r"\d+", callback_issue_raw)
        callback_issue = int(match.group()) if match else issue_number
    return normalize_request(
        project=product if product != "UNKNOWN" else infer_project(repo, title, body),
        request_text=request_text,
        resource=form.get("resource", infer_resource(title, body)),
        priority=form.get("priority", infer_priority(title, body)),
        source_repo=repo,
        source_issue=issue_number,
        callback_repo=callback_repo,
        callback_issue=callback_issue,
        requesting_team=form.get("requesting_team", "UNKNOWN"),
        product=product,
        request_owner=form.get("request_owner", "UNKNOWN"),
        requested_capability=requested_capability,
        requested_model_id=requested_model_id,
        requested_model_family=requested_model_family,
        selection_mode=_selection_mode(
            requested_model_id, requested_model_family, requested_capability
        ),
        acceptance_criteria=form.get("acceptance_criteria", "UNKNOWN"),
    )


def discover_github_issue_requests(
    issues: Iterable[Mapping[str, object]], *, configured_repos: Iterable[str]
) -> list[RequestEnvelope]:
    configured = tuple(configured_repos)
    discovered: list[RequestEnvelope] = []
    seen: set[str] = set()
    for issue in issues:
        envelope = normalize_github_issue_request(issue, configured_repos=configured)
        if envelope is None or envelope.fingerprint in seen:
            continue
        seen.add(envelope.fingerprint)
        discovered.append(envelope)
    return discovered
