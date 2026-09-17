from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model_scout.automation_cycle import DurableEvidenceStore, run_runtime_cycle
from src.model_scout.delivery_ledger import DeliveryLedger
from src.model_scout.github_issue_source import GitHubIssueSource
from src.model_scout.github_request_discovery import CENTRAL_REQUEST_REPOSITORY
from src.model_scout.persistent_queue import PersistentRequestQueue
from src.model_scout.runtime_executors import load_runtime_executor_registry
from src.model_scout.runtime_executors import classify_executor_kind


class EvidenceFileWriter:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def __call__(self, repo: str, issue: int, body: str):
        path = self.root / f"issue-{issue}-callback.md"
        path.write_text(body, encoding="utf-8")
        raise RuntimeError(f"callback staged for authenticated delivery: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issues", required=True, help="comma-separated central issue numbers")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--executor-config", default="config/runtime-executors.json")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    requested = {int(value.strip()) for value in args.issues.split(",") if value.strip()}
    state_dir = Path(args.state_dir).resolve()
    source = GitHubIssueSource(token="")
    issues = [
        issue
        for issue in source.list_open_issues([CENTRAL_REQUEST_REPOSITORY])
        if int(issue["number"]) in requested
    ]
    if {int(issue["number"]) for issue in issues} != requested:
        raise SystemExit("one or more requested open issues were not found")

    queue = PersistentRequestQueue(state_dir / "request_queue.sqlite3")
    store = DurableEvidenceStore(state_dir / "request_evidence.sqlite3")
    ledger = DeliveryLedger(state_dir / "model_delivery.sqlite3")
    runtime = load_runtime_executor_registry(
        args.executor_config,
        work_root=state_dir / "runtime-work",
    )

    def targeted_scout(query: str, limit: int, resource: str):
        from huggingface_hub import HfApi

        envelope = next(item for item in queue.snapshot() if item["request_text"] == query)
        queued = queue.get(str(envelope["fingerprint"]))
        if queued is None:
            raise RuntimeError("queued request disappeared before search")
        kind = classify_executor_kind(queued)
        adapter = runtime.adapters.get(kind)
        if adapter is None:
            raise RuntimeError(f"no runtime adapter configured for {kind}")
        if not adapter.source.startswith("huggingface:"):
            return {
                "query": query,
                "resource_type": "tool",
                "candidate_count": 1,
                "candidates": [{
                    "model_id": adapter.model_id,
                    "revision": adapter.model_revision,
                    "license": adapter.license,
                    "source": adapter.source,
                }],
            }
        info = HfApi().model_info(adapter.model_id)
        return {
            "query": query,
            "resource_type": resource,
            "candidate_count": 1,
            "candidates": [{
                "model_id": info.id,
                "revision": info.sha,
                "license": adapter.license,
                "source": adapter.source,
                "downloads": info.downloads,
            }],
        }
    results = run_runtime_cycle(
        issues=issues,
        configured_repos=[CENTRAL_REQUEST_REPOSITORY],
        queue=queue,
        evidence_store=store,
        delivery_ledger=ledger,
        scout_runner=targeted_scout,
        runtime_runner=runtime,
        callback_writer=EvidenceFileWriter(state_dir / "callbacks"),
        limit=args.limit,
    )
    payload = {
        "issues": sorted(requested),
        "results": results,
        "queue": queue.snapshot(),
        "ledger": [
            record.as_dict()
            for item in queue.snapshot()
            if (record := ledger.get(str(item["fingerprint"]))) is not None
        ],
    }
    evidence_path = state_dir / "selected-e2e-evidence.json"
    evidence_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
