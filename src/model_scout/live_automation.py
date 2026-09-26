from __future__ import annotations

from pathlib import Path
from collections.abc import Callable, Mapping
from typing import Any, Iterable

from .automation_cycle import DurableEvidenceStore, run_runtime_cycle, run_scout_cycle
from .delivery_ledger import DeliveryLedger, DeliveryState
from .github_callback_transport import GitHubIssueCommentWriter
from .github_issue_source import GitHubIssueSource
from .github_request_discovery import request_discovery_repositories
from .persistent_queue import PersistentRequestQueue
from .scout import scout as run_scout_core


RuntimeRunner = Callable[[Any, Mapping[str, Any]], Mapping[str, Any]]


def run_live_cycle(
    *,
    configured_repos: Iterable[str],
    state_dir: str | Path,
    issue_source: GitHubIssueSource | None = None,
    callback_writer: GitHubIssueCommentWriter | None = None,
    runtime_runner: RuntimeRunner | None = None,
    limit: int = 10,
    preferred_source: tuple[str, int] | None = None,
    max_requests: int = 4,
    scoped_requests: Iterable[Mapping[str, str]] = (),
) -> list[dict[str, Any]]:
    """Run one live request-ingestion -> scout -> callback cycle.

    When a runtime runner is supplied, scout results must pass real output validation
    before callback delivery. The legacy scout-only path remains available for callers
    that explicitly omit a runtime runner.
    """

    repos = tuple(repo.strip() for repo in configured_repos if repo and repo.strip())
    if not repos:
        raise ValueError("at least one configured repository is required")

    root = Path(state_dir)
    root.mkdir(parents=True, exist_ok=True)
    discovery_repos = request_discovery_repositories(repos)
    source = issue_source or GitHubIssueSource()
    writer = callback_writer or GitHubIssueCommentWriter()
    issues = source.list_open_issues(discovery_repos)
    issue_index = {
        (str(issue.get("repository_full_name", "")).casefold(), int(issue.get("number") or 0)): issue
        for issue in issues
    }
    for scope in scoped_requests:
        repo = str(scope["source_repo"]).strip()
        number = int(scope["source_issue"])
        original = issue_index.get((repo.casefold(), number))
        if original is None or str(original.get("state", "open")).casefold() != "open":
            continue  # Never manufacture a request from a missing or closed Issue.
        model_id = str(scope["model_id"]).strip()
        capability = str(scope["capability"]).strip()
        if not model_id or not capability:
            raise ValueError("scoped request requires model_id and capability")
        if capability.casefold() not in str(original.get("body") or "").casefold():
            continue  # Scope must be grounded in the real developer request.
        issues.append({
            "repository_full_name": repo,
            "number": number,
            "state": "open",
            "title": f"[P0] MODEL SCOUT scoped {capability}",
            "body": (
                f"MODEL SCOUT scoped subrequest from real Issue #{number}.\n"
                f"### 요청 개발팀\n{str(scope.get('requesting_team') or 'UNKNOWN')}\n"
                f"### 제품 / 앱\n{str(scope.get('product') or 'UNKNOWN')}\n"
                f"### 요청 Model ID\n{model_id}\n"
                f"### 필요한 기능 / 해결할 문제\n{capability} embedding retrieval\n"
                "### PASS 기준\nPinned official model download, license snapshot, SHA-256 and CPU component evidence. "
                "Product TESTED_PASS remains pending the parent Issue's full acceptance inputs."
            ),
        })
    if preferred_source:
        preferred_repo, preferred_issue = preferred_source
        if not any(
            str(item.get("repository_full_name") or "").casefold() == preferred_repo.casefold()
            and int(item.get("number") or 0) == preferred_issue
            for item in issues
        ):
            issues.insert(0, source.get_issue(preferred_repo, preferred_issue))

    queue = PersistentRequestQueue(root / "request_queue.sqlite3")
    evidence_store = DurableEvidenceStore(root / "request_evidence.sqlite3")
    ledger = DeliveryLedger(root / "model_delivery.sqlite3")
    cycle = run_runtime_cycle if runtime_runner is not None else run_scout_cycle
    cycle_args: dict[str, Any] = {
        "issues": issues,
        "configured_repos": discovery_repos,
        "queue": queue,
        "evidence_store": evidence_store,
        "scout_runner": run_scout_core,
        "callback_writer": writer,
        "limit": limit,
        "preferred_source": preferred_source,
        "max_requests": max_requests,
    }
    if runtime_runner is not None:
        cycle_args.update(runtime_runner=runtime_runner, delivery_ledger=ledger)
    results = cycle(**cycle_args)
    for item in queue.snapshot():
        fingerprint = str(item["fingerprint"])
        owner = str(item.get("callback_repo") or item.get("source_repo") or "MODEL_SCOUT_AUTOMATION")
        record = ledger.request(fingerprint, owner=owner, next_action="discover license-compatible candidate")
        if runtime_runner is None and item["state"] in {"EVIDENCE_READY", "DELIVERED"} and record.state == DeliveryState.REQUESTED:
            evidence = evidence_store.get(fingerprint) or {}
            ledger.advance(
                fingerprint,
                DeliveryState.FOUND,
                owner=owner,
                next_action="download selected candidate and run minimum runtime validation",
                evidence=evidence,
            )
    return results
