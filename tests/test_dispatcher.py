from src.model_scout.dispatcher import dispatch_one
from src.model_scout.request_queue import QueueState, RequestQueue, normalize_request


def _queued_request(*, resource: str = "model"):
    queue = RequestQueue()
    envelope = normalize_request(
        project="AURA",
        request_text="Find a free public image model for architectural concept generation",
        resource=resource,
        priority="P0",
        source_repo="ADAMBUILD-ai/aura-engine",
        source_issue=32,
    )
    queued, created = queue.enqueue(envelope)
    assert created is True
    return queue, queued


def test_dispatch_one_moves_queued_request_to_evidence_ready():
    queue, queued = _queued_request(resource="model")
    calls = []

    def fake_scout(query, limit, resource):
        calls.append((query, limit, resource))
        return {"candidate_count": 1, "candidates": [{"model_id": "example/model"}]}

    evidence = dispatch_one(queue, queued.fingerprint, scout_runner=fake_scout, limit=7)

    assert calls == [(queued.request_text, 7, "model")]
    assert evidence["state"] == QueueState.EVIDENCE_READY.value
    assert evidence["requested_resource"] == "model"
    assert evidence["dispatched_resource"] == "model"
    assert evidence["callback"] == {"repo": "ADAMBUILD-ai/aura-engine", "issue": 32}
    assert evidence["result"]["candidate_count"] == 1
    assert queue.get(queued.fingerprint).state == QueueState.EVIDENCE_READY


def test_dispatch_one_marks_runner_failure_retryable():
    queue, queued = _queued_request()

    def failing_scout(_query, _limit, _resource):
        raise RuntimeError("temporary upstream failure")

    evidence = dispatch_one(queue, queued.fingerprint, scout_runner=failing_scout)

    assert evidence["state"] == QueueState.FAILED_RETRYABLE.value
    assert evidence["error_type"] == "RuntimeError"
    assert "temporary upstream failure" in evidence["error"]
    assert queue.get(queued.fingerprint).state == QueueState.FAILED_RETRYABLE


def test_dispatch_one_rejects_non_queued_request():
    queue, queued = _queued_request()
    queue.set_state(queued.fingerprint, QueueState.RUNNING)

    try:
        dispatch_one(queue, queued.fingerprint, scout_runner=lambda *_args: {})
    except ValueError as exc:
        assert "not dispatchable" in str(exc)
    else:
        raise AssertionError("dispatch_one must reject non-QUEUED requests")


def test_dispatch_one_widens_tool_request_to_current_core_all_resource():
    queue, queued = _queued_request(resource="tool")
    calls = []

    def fake_scout(query, limit, resource):
        calls.append((query, limit, resource))
        return {"candidate_count": 0, "candidates": []}

    evidence = dispatch_one(queue, queued.fingerprint, scout_runner=fake_scout)

    assert calls[0][2] == "all"
    assert evidence["requested_resource"] == "tool"
    assert evidence["dispatched_resource"] == "all"
    assert evidence["state"] == QueueState.EVIDENCE_READY.value
