from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Iterable

from .live_automation import run_live_cycle
from .persistent_queue import PersistentRequestQueue
from .runtime_executors import load_runtime_executor_registry


def validate_intake_coverage(configured_repos: Iterable[str], team_registry_path: str | Path | None) -> dict[str, Any]:
    configured = {str(value).strip().casefold() for value in configured_repos if str(value).strip()}
    configured.add("adambuild-ai/mindle-model-scout")
    required: set[str] = set()
    if team_registry_path:
        payload = json.loads(Path(team_registry_path).read_text(encoding="utf-8"))
        required = {
            str(item.get("repository_full_name") or "").strip().casefold()
            for item in payload.get("teams", [])
            if isinstance(item, dict) and str(item.get("repository_full_name") or "").strip()
        }
    missing = sorted(required - configured)
    effective = configured | required
    return {
        "status": "PASS" if not missing else "PASS_AUTO_COMPLETED_FROM_TEAM_REGISTRY",
        "configured_repositories": sorted(configured),
        "required_team_repositories": sorted(required),
        "missing_repositories": missing,
        "effective_repositories": sorted(effective),
        "auto_completed_repositories": missing,
    }


def run_autonomous_cycle(
    *,
    configured_repos: Iterable[str],
    state_dir: str | Path,
    stale_after_seconds: float = 1800,
    limit: int = 10,
    max_requests: int = 4,
    max_retries: int = 3,
    retry_backoff_seconds: float = 900.0,
    team_registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run watchdog recovery before one idempotent live cycle on durable storage."""
    root = Path(state_dir).resolve()
    if root == Path.cwd().resolve():
        raise ValueError("MODEL_SCOUT_STATE_DIR must be a dedicated durable directory")
    root.mkdir(parents=True, exist_ok=True)
    configured = tuple(configured_repos)
    intake_coverage = validate_intake_coverage(configured, team_registry_path)
    # The checked-in team registry is the intake SSOT.  Repository variables are
    # deployment configuration and can lag behind registry changes; do not stop
    # acquisition when that happens.  Complete the effective set from the SSOT
    # while preserving the drift in evidence for operators to repair.
    repos = tuple(intake_coverage["effective_repositories"])
    queue = PersistentRequestQueue(root / "request_queue.sqlite3")
    requeued = queue.requeue_stale(stale_after_seconds=stale_after_seconds, max_retries=max_retries)
    requeued.extend(queue.requeue_retryable(max_retries=max_retries, backoff_seconds=retry_backoff_seconds))
    executor_config = os.environ.get("MODEL_SCOUT_EXECUTOR_CONFIG")
    scoped_config = os.environ.get("MODEL_SCOUT_SCOPED_REQUESTS_CONFIG", "")
    scoped_requests = ()
    if scoped_config:
        scopes = json.loads(Path(scoped_config).read_text(encoding="utf-8"))
        if not isinstance(scopes, list) or any(not isinstance(item, dict) for item in scopes):
            raise ValueError("scoped requests config must be a list of mappings")
        scoped_requests = tuple(scopes)
    runtime_runner = load_runtime_executor_registry(
        executor_config,
        work_root=root / "runtime-work",
        model_registry_path=root / "model-registry.json",
    )
    event_repo = os.environ.get("MODEL_SCOUT_EVENT_REPOSITORY", "").strip()
    event_issue_raw = os.environ.get("MODEL_SCOUT_EVENT_ISSUE", "").strip()
    preferred_source = None
    if event_repo and event_issue_raw:
        try:
            preferred_source = (event_repo, int(event_issue_raw))
        except ValueError as exc:
            raise ValueError("MODEL_SCOUT_EVENT_ISSUE must be an integer") from exc
    results = run_live_cycle(
        configured_repos=repos,
        state_dir=root,
        limit=limit,
        runtime_runner=runtime_runner,
        preferred_source=preferred_source,
        max_requests=max_requests,
        scoped_requests=scoped_requests,
    )
    queue_snapshot = queue.snapshot()
    eligible = sum(item["state"] in {"QUEUED", "EVIDENCE_READY"} for item in queue_snapshot)
    return {
        "watchdog_requeued": requeued,
        "results": results,
        "queue": queue_snapshot,
        "idle_reason": "NO_ELIGIBLE_REQUESTS" if not results and not eligible else None,
        "eligible_request_count": eligible,
        "model_registry": str(root / "model-registry.json"),
        "intake_coverage": intake_coverage,
    }
