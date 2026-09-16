from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .live_automation import run_live_cycle
from .persistent_queue import PersistentRequestQueue


def run_autonomous_cycle(*, configured_repos: Iterable[str], state_dir: str | Path, stale_after_seconds: float = 1800, limit: int = 10) -> dict[str, Any]:
    """Run watchdog recovery before one idempotent live cycle on durable storage."""
    root = Path(state_dir).resolve()
    if root == Path.cwd().resolve():
        raise ValueError("MODEL_SCOUT_STATE_DIR must be a dedicated durable directory")
    root.mkdir(parents=True, exist_ok=True)
    queue = PersistentRequestQueue(root / "request_queue.sqlite3")
    requeued = queue.requeue_stale(stale_after_seconds=stale_after_seconds)
    results = run_live_cycle(configured_repos=configured_repos, state_dir=root, limit=limit)
    return {"watchdog_requeued": requeued, "results": results, "queue": queue.snapshot()}
