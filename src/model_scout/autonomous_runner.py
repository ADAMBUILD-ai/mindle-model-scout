from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from .live_automation import run_live_cycle
from .persistent_queue import PersistentRequestQueue
from .runtime_executors import load_runtime_executor_registry


def run_autonomous_cycle(*, configured_repos: Iterable[str], state_dir: str | Path, stale_after_seconds: float = 1800, limit: int = 10) -> dict[str, Any]:
    """Run watchdog recovery before one idempotent live cycle on durable storage."""
    root = Path(state_dir).resolve()
    if root == Path.cwd().resolve():
        raise ValueError("MODEL_SCOUT_STATE_DIR must be a dedicated durable directory")
    root.mkdir(parents=True, exist_ok=True)
    queue = PersistentRequestQueue(root / "request_queue.sqlite3")
    requeued = queue.requeue_stale(stale_after_seconds=stale_after_seconds)
    requeued.extend(queue.requeue_retryable())
    executor_config = os.environ.get("MODEL_SCOUT_EXECUTOR_CONFIG")
    runtime_runner = load_runtime_executor_registry(
        executor_config,
        work_root=root / "runtime-work",
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
        configured_repos=configured_repos,
        state_dir=root,
        limit=limit,
        runtime_runner=runtime_runner,
        preferred_source=preferred_source,
    )
    return {"watchdog_requeued": requeued, "results": results, "queue": queue.snapshot()}
