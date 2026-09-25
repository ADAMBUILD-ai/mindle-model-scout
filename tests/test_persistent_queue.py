from src.model_scout.persistent_queue import PersistentRequestQueue
from src.model_scout.request_queue import QueueState, normalize_request


def test_persistent_queue_survives_reopen(tmp_path):
    db = tmp_path / "model-scout-queue.sqlite3"
    queue = PersistentRequestQueue(db)
    envelope = normalize_request(
        project="AGRI",
        request_text="Find Korean crop disease vision model",
        source_repo="ADAMBUILD-ai/agri-ai-business-platform",
        source_issue=33,
    )

    queued, created = queue.enqueue(envelope)
    assert created is True
    assert queued.state == QueueState.QUEUED

    reopened = PersistentRequestQueue(db)
    restored = reopened.get(queued.fingerprint)
    assert restored is not None
    assert restored.state == QueueState.QUEUED
    assert restored.source_repo == "ADAMBUILD-ai/agri-ai-business-platform"
    assert restored.source_issue == 33
    assert restored.callback_repo == "ADAMBUILD-ai/agri-ai-business-platform"
    assert restored.callback_issue == 33


def test_persistent_queue_preserves_evidence_pointer_and_runtime_state(tmp_path):
    now = [1000.0]
    db = tmp_path / "model-scout-queue.sqlite3"
    queue = PersistentRequestQueue(db, clock=lambda: now[0])
    envelope = normalize_request(project="AURA", request_text="Run R1 model validation")
    queued, _ = queue.enqueue(envelope)

    now[0] = 1010.0
    running = queue.set_state(queued.fingerprint, QueueState.RUNNING)
    assert running.state == QueueState.RUNNING

    now[0] = 1020.0
    ready = queue.set_state(queued.fingerprint, QueueState.EVIDENCE_READY)
    queue.set_evidence_pointer(ready.fingerprint, "evidence/aura/r1.json")

    reopened = PersistentRequestQueue(db, clock=lambda: now[0])
    snapshot = reopened.snapshot()[0]
    assert snapshot["state"] == QueueState.EVIDENCE_READY.value
    assert snapshot["evidence_pointer"] == "evidence/aura/r1.json"
    assert snapshot["last_attempt_at"] == 1010.0


def test_watchdog_requeues_stale_queued_and_running_but_not_evidence_ready(tmp_path):
    now = [1000.0]
    db = tmp_path / "model-scout-queue.sqlite3"
    queue = PersistentRequestQueue(db, clock=lambda: now[0])

    queued_env = normalize_request(project="ADAM", request_text="Find rendering model")
    running_env = normalize_request(project="AGRI", request_text="Find crop classifier")
    ready_env = normalize_request(project="AURA", request_text="Find image enhancement model")

    queued, _ = queue.enqueue(queued_env)
    running, _ = queue.enqueue(running_env)
    ready, _ = queue.enqueue(ready_env)

    queue.set_state(running.fingerprint, QueueState.RUNNING)
    queue.set_state(ready.fingerprint, QueueState.RUNNING)
    queue.set_state(ready.fingerprint, QueueState.EVIDENCE_READY)

    now[0] = 1201.0
    requeued = queue.requeue_stale(stale_after_seconds=200.0)

    assert set(requeued) == {queued.fingerprint, running.fingerprint}
    assert queue.get(queued.fingerprint).state == QueueState.QUEUED
    assert queue.get(running.fingerprint).state == QueueState.QUEUED
    assert queue.get(ready.fingerprint).state == QueueState.EVIDENCE_READY

    rows = {item["fingerprint"]: item for item in queue.snapshot()}
    assert rows[queued.fingerprint]["retry_count"] == 1
    assert rows[running.fingerprint]["retry_count"] == 1
    assert rows[ready.fingerprint]["retry_count"] == 0
    assert "watchdog stale" in rows[queued.fingerprint]["last_error"]


def test_watchdog_does_not_requeue_fresh_items(tmp_path):
    now = [1000.0]
    queue = PersistentRequestQueue(tmp_path / "queue.sqlite3", clock=lambda: now[0])
    envelope = normalize_request(project="AURA", request_text="Fresh request")
    queued, _ = queue.enqueue(envelope)

    now[0] = 1050.0
    assert queue.requeue_stale(stale_after_seconds=60.0) == []
    assert queue.get(queued.fingerprint).state == QueueState.QUEUED


def test_watchdog_rejects_non_positive_timeout(tmp_path):
    queue = PersistentRequestQueue(tmp_path / "queue.sqlite3")
    try:
        queue.requeue_stale(stale_after_seconds=0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_failed_retryable_is_requeued_on_next_cycle(tmp_path):
    queue = PersistentRequestQueue(tmp_path / "queue.sqlite3")
    envelope = normalize_request(project="TEST", request_text="retry me")
    queued, _ = queue.enqueue(envelope)
    queue.set_state(queued.fingerprint, QueueState.FAILED_RETRYABLE)

    requeued = queue.requeue_retryable(backoff_seconds=0)

    assert requeued == [queued.fingerprint]
    assert queue.get(queued.fingerprint).state == QueueState.QUEUED
    assert queue.snapshot()[0]["retry_count"] == 1


def test_retryable_uses_backoff_and_moves_to_terminal_after_limit(tmp_path):
    now = [1000.0]
    queue = PersistentRequestQueue(tmp_path / "queue.sqlite3", clock=lambda: now[0])
    queued, _ = queue.enqueue(normalize_request(project="TEST", request_text="bounded retry"))
    queue.set_state(queued.fingerprint, QueueState.FAILED_RETRYABLE)

    assert queue.requeue_retryable(max_retries=1, backoff_seconds=60, now=1059) == []
    assert queue.requeue_retryable(max_retries=1, backoff_seconds=60, now=1060) == [queued.fingerprint]
    queue.set_state(queued.fingerprint, QueueState.FAILED_RETRYABLE)
    assert queue.requeue_retryable(max_retries=1, backoff_seconds=0, now=1061) == []
    assert queue.get(queued.fingerprint).state == QueueState.FAILED_TERMINAL
