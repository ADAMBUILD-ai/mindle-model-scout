from __future__ import annotations

from pathlib import Path

from src.model_scout.automation_cycle import DurableEvidenceStore, run_scout_cycle
from src.model_scout.persistent_queue import PersistentRequestQueue
from src.model_scout.request_queue import QueueState


def _issue() -> dict[str, object]:
    return {
        "repository_full_name": "ADAMBUILD-ai/example-project",
        "number": 7,
        "state": "open",
        "title": "[P0][EXAMPLE] MODEL SCOUT request",
        "body": "Find Hugging Face model candidates for Korean document classification.",
    }


def test_cross_repo_cycle_delivers_once_and_dedupes(tmp_path: Path) -> None:
    queue = PersistentRequestQueue(tmp_path / "queue.sqlite3")
    store = DurableEvidenceStore(tmp_path / "evidence.sqlite3")
    scout_calls: list[tuple[str, int, str]] = []
    callbacks: list[tuple[str, int, str]] = []

    def scout_runner(query: str, limit: int, resource: str):
        scout_calls.append((query, limit, resource))
        return {"query": query, "resource_type": resource, "candidate_count": 1, "semantic_match": "PASS", "candidates": [{"model_id": "example/model"}]}

    def callback_writer(repo: str, issue: int, body: str):
        callbacks.append((repo, issue, body))

    first = run_scout_cycle(
        issues=[_issue()],
        configured_repos=["ADAMBUILD-ai/example-project"],
        queue=queue,
        evidence_store=store,
        scout_runner=scout_runner,
        callback_writer=callback_writer,
    )

    snapshot = queue.snapshot()
    assert len(snapshot) == 1
    assert snapshot[0]["state"] == QueueState.DELIVERED.value
    assert len(scout_calls) == 1
    assert len(callbacks) == 1
    assert callbacks[0][0] == "ADAMBUILD-ai/example-project"
    assert callbacks[0][1] == 7
    assert any(item.get("delivered") is True for item in first)

    second = run_scout_cycle(
        issues=[_issue()],
        configured_repos=["ADAMBUILD-ai/example-project"],
        queue=queue,
        evidence_store=store,
        scout_runner=scout_runner,
        callback_writer=callback_writer,
    )

    assert second == []
    assert len(scout_calls) == 1
    assert len(callbacks) == 1


def test_callback_retry_uses_persisted_evidence_without_rerunning_scout(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.sqlite3"
    evidence_path = tmp_path / "evidence.sqlite3"
    queue = PersistentRequestQueue(queue_path)
    store = DurableEvidenceStore(evidence_path)
    scout_calls = 0
    callback_attempts = 0

    def scout_runner(query: str, limit: int, resource: str):
        nonlocal scout_calls
        scout_calls += 1
        return {"query": query, "resource_type": resource, "candidate_count": 1, "semantic_match": "PASS", "candidates": [{"model_id": "example/model"}]}

    def failing_writer(repo: str, issue: int, body: str):
        nonlocal callback_attempts
        callback_attempts += 1
        raise RuntimeError("temporary callback failure")

    first = run_scout_cycle(
        issues=[_issue()],
        configured_repos=["ADAMBUILD-ai/example-project"],
        queue=queue,
        evidence_store=store,
        scout_runner=scout_runner,
        callback_writer=failing_writer,
    )

    assert scout_calls == 1
    assert callback_attempts == 1
    assert queue.snapshot()[0]["state"] == QueueState.EVIDENCE_READY.value
    assert any(item.get("delivered") is False for item in first)

    # Simulate a process restart by reconstructing both SQLite-backed objects.
    queue = PersistentRequestQueue(queue_path)
    store = DurableEvidenceStore(evidence_path)
    delivered: list[tuple[str, int, str]] = []

    def success_writer(repo: str, issue: int, body: str):
        delivered.append((repo, issue, body))

    second = run_scout_cycle(
        issues=[_issue()],
        configured_repos=["ADAMBUILD-ai/example-project"],
        queue=queue,
        evidence_store=store,
        scout_runner=scout_runner,
        callback_writer=success_writer,
    )

    assert scout_calls == 1
    assert len(delivered) == 1
    assert queue.snapshot()[0]["state"] == QueueState.DELIVERED.value
    assert any(item.get("delivered") is True for item in second)
