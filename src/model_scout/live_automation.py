from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .automation_cycle import DurableEvidenceStore, run_scout_cycle
from .delivery_ledger import DeliveryLedger, DeliveryState
from .github_callback_transport import GitHubIssueCommentWriter
from .github_issue_source import GitHubIssueSource
from .persistent_queue import PersistentRequestQueue
from .scout import scout as run_scout_core


def run_live_cycle(
    *,
    configured_repos: Iterable[str],
    state_dir: str | Path,
    issue_source: GitHubIssueSource | None = None,
    callback_writer: GitHubIssueCommentWriter | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Run one live request-ingestion -> scout -> callback cycle.

    This is the concrete production-adjacent orchestration entrypoint for the recovery
    branch. It intentionally does not perform paid provider calls or runtime TESTED_PASS
    execution. Those remain behind runtime_validation approval boundaries.
    """

    repos = tuple(repo.strip() for repo in configured_repos if repo and repo.strip())
    if not repos:
        raise ValueError("at least one configured repository is required")

    root = Path(state_dir)
    root.mkdir(parents=True, exist_ok=True)
    source = issue_source or GitHubIssueSource()
    writer = callback_writer or GitHubIssueCommentWriter()
    issues = source.list_open_issues(repos)

    queue = PersistentRequestQueue(root / "request_queue.sqlite3")
    evidence_store = DurableEvidenceStore(root / "request_evidence.sqlite3")
    ledger = DeliveryLedger(root / "model_delivery.sqlite3")
    results = run_scout_cycle(
        issues=issues,
        configured_repos=repos,
        queue=queue,
        evidence_store=evidence_store,
        scout_runner=run_scout_core,
        callback_writer=writer,
        limit=limit,
    )
    for item in queue.snapshot():
        fingerprint = str(item["fingerprint"])
        owner = str(item.get("callback_repo") or item.get("source_repo") or "MODEL_SCOUT_AUTOMATION")
        record = ledger.request(fingerprint, owner=owner, next_action="discover license-compatible candidate")
        if item["state"] in {"EVIDENCE_READY", "DELIVERED"} and record.state == DeliveryState.REQUESTED:
            evidence = evidence_store.get(fingerprint) or {}
            ledger.advance(
                fingerprint,
                DeliveryState.FOUND,
                owner=owner,
                next_action="download selected candidate and run minimum runtime validation",
                evidence=evidence,
            )
    return results
