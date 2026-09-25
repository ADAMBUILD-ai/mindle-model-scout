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
