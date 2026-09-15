from __future__ import annotations

import json
import os
from pathlib import Path

from src.model_scout.live_automation import run_live_cycle


def main() -> int:
    raw = os.environ.get("MODEL_SCOUT_CONFIGURED_REPOS", "")
    repos = [item.strip() for item in raw.split(",") if item.strip()]
    if not repos:
        raise SystemExit("MODEL_SCOUT_CONFIGURED_REPOS is required")
    state_dir = Path(os.environ.get("MODEL_SCOUT_STATE_DIR", ".model-scout-state"))
    limit = int(os.environ.get("MODEL_SCOUT_LIMIT", "10"))
    results = run_live_cycle(configured_repos=repos, state_dir=state_dir, limit=limit)
    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
