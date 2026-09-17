from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model_scout.github_issue_source import GitHubIssueSource
from src.model_scout.live_automation import run_live_cycle
from src.model_scout.persistent_queue import PersistentRequestQueue
from src.model_scout.runtime_executors import load_runtime_executor_registry


class FilteredIssueSource:
    def __init__(self, source: GitHubIssueSource, issue_numbers: set[int]):
        self.source = source
        self.issue_numbers = issue_numbers

    def list_open_issues(self, repos):
        return [
            issue
            for issue in self.source.list_open_issues(repos)
            if issue.get("repository_full_name") == "ADAMBUILD-ai/mindle-model-scout"
            and issue.get("number") in self.issue_numbers
        ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--issues", default="52,54,56")
    parser.add_argument("--executor-config", default="config/runtime-executors.json")
    args = parser.parse_args()
    issue_numbers = {int(value) for value in args.issues.split(",") if value.strip()}
    if not issue_numbers:
        raise SystemExit("at least one issue number is required")
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")
    state_dir = Path(args.state_dir).resolve()
    queue = PersistentRequestQueue(state_dir / "request_queue.sqlite3")
    requeued = queue.requeue_retryable()
    source = FilteredIssueSource(GitHubIssueSource(token=token), issue_numbers)
    runner = load_runtime_executor_registry(
        args.executor_config,
        work_root=state_dir / "runtime-work",
    )
    results = run_live_cycle(
        configured_repos=["ADAMBUILD-ai/mindle-model-scout"],
        state_dir=state_dir,
        issue_source=source,
        runtime_runner=runner,
        limit=10,
    )
    print(json.dumps({"issues": sorted(issue_numbers), "requeued": requeued, "results": results, "queue": queue.snapshot()}, ensure_ascii=True, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
