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


def test_exact_terminal_recovery_runs_once_and_preserves_prior_failure(tmp_path):
    import sqlite3

    db = tmp_path / "queue.sqlite3"
    queue = PersistentRequestQueue(db)
    aura, _ = queue.enqueue(normalize_request(project="AURA", request_text="visual image request",
                                                source_repo="ADAMBUILD-ai/aura-engine", source_issue=35))
    other, _ = queue.enqueue(normalize_request(project="AURA", request_text="license request",
                                                 source_repo="ADAMBUILD-ai/aura-engine", source_issue=36))
    for item, error in ((aura, "tokenization_gpt2.py failed"), (other, "license rejected")):
        queue.set_state(item.fingerprint, QueueState.FAILED_RETRYABLE)
        queue.set_state(item.fingerprint, QueueState.FAILED_TERMINAL)
        queue.record_failure(item.fingerprint, error)
    assert queue.reopen_terminal_once(recovery_id="adapter-v1", source_repo="ADAMBUILD-ai/aura-engine",
                                      source_issue=35, error_contains="different error") is None
    assert queue.reopen_terminal_once(recovery_id="adapter-v1", source_repo="ADAMBUILD-ai/aura-engine",
                                      source_issue=35, error_contains="tokenization_gpt2.py") == aura.fingerprint
    assert queue.get(aura.fingerprint).state == QueueState.QUEUED
    assert queue.get(other.fingerprint).state == QueueState.FAILED_TERMINAL
    queue.set_state(aura.fingerprint, QueueState.FAILED_RETRYABLE)
    queue.set_state(aura.fingerprint, QueueState.FAILED_TERMINAL)
    assert queue.reopen_terminal_once(recovery_id="adapter-v1", source_repo="ADAMBUILD-ai/aura-engine",
                                      source_issue=35, error_contains="tokenization_gpt2.py") is None
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT previous_error FROM terminal_recoveries WHERE recovery_id = 'adapter-v1'").fetchone()[0] == "tokenization_gpt2.py failed"


def test_exact_failure_replay_preserves_retry_count_and_runs_once(tmp_path):
    import sqlite3

    db = tmp_path / "queue.sqlite3"
    queue = PersistentRequestQueue(db)
    request, _ = queue.enqueue(normalize_request(project="AURA", request_text="visual model",
                                                   source_repo="ADAMBUILD-ai/aura-engine", source_issue=35))
    queue.set_state(request.fingerprint, QueueState.FAILED_RETRYABLE)
    queue.record_failure(request.fingerprint, "no runnable candidate with allowed license")
    with sqlite3.connect(db) as connection:
        connection.execute("UPDATE request_queue SET retry_count = 2 WHERE fingerprint = ?", (request.fingerprint,))
    assert queue.replay_failed_once(replay_id="task-search-v1", source_repo="ADAMBUILD-ai/aura-engine",
                                    source_issue=35, error_contains="no runnable candidate") == request.fingerprint
    row = queue.snapshot()[0]
    assert row["state"] == QueueState.QUEUED.value
    assert row["retry_count"] == 2
    queue.set_state(request.fingerprint, QueueState.RUNNING)
    queue.set_state(request.fingerprint, QueueState.FAILED_RETRYABLE)
    assert queue.replay_failed_once(replay_id="task-search-v1", source_repo="ADAMBUILD-ai/aura-engine",
                                    source_issue=35, error_contains="no runnable candidate") is None
    with sqlite3.connect(db) as connection:
        prior = connection.execute("SELECT previous_state, previous_error FROM failure_replays").fetchone()
    assert prior == (QueueState.FAILED_RETRYABLE.value, "no runnable candidate with allowed license")


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


def test_watchdog_terminates_exhausted_stale_item(tmp_path):
    now = [1000.0]
    queue = PersistentRequestQueue(tmp_path / "queue.sqlite3", clock=lambda: now[0])
    queued, _ = queue.enqueue(normalize_request(project="ADMIN", request_text="stale work order"))
    for _ in range(3):
        now[0] += 100.0
        assert queue.requeue_stale(stale_after_seconds=60, max_retries=3) == [queued.fingerprint]
    now[0] += 100.0
    assert queue.requeue_stale(stale_after_seconds=60, max_retries=3) == []
    row = queue.snapshot()[0]
    assert row["state"] == QueueState.FAILED_TERMINAL.value
    assert row["retry_count"] == 3


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
    queue.record_failure(queued.fingerprint, "runtime:OSError: pinned download unavailable")
    assert queue.requeue_retryable(max_retries=1, backoff_seconds=0, now=1061) == []
    assert queue.get(queued.fingerprint).state == QueueState.FAILED_TERMINAL
    assert "pinned download unavailable" in queue.snapshot()[0]["last_error"]
