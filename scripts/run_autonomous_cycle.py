from __future__ import annotations

import json
import os

from src.model_scout.autonomous_runner import run_autonomous_cycle


def main() -> int:
    state_dir = os.environ.get("MODEL_SCOUT_STATE_DIR")
    if not state_dir:
        raise SystemExit("MODEL_SCOUT_STATE_DIR must point to durable runner storage")
    repos = [value.strip() for value in os.environ.get("MODEL_SCOUT_CONFIGURED_REPOS", "").split(",") if value.strip()]
    if not repos:
        raise SystemExit("MODEL_SCOUT_CONFIGURED_REPOS is required")
    result = run_autonomous_cycle(configured_repos=repos, state_dir=state_dir, stale_after_seconds=float(os.environ.get("MODEL_SCOUT_STALE_AFTER_SECONDS", "1800")), limit=int(os.environ.get("MODEL_SCOUT_LIMIT", "10")))
    # Keep stdout ASCII-safe so the Windows self-hosted runner cannot fail on its
    # legacy cp949 console codec when evidence contains punctuation such as an em dash.
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
