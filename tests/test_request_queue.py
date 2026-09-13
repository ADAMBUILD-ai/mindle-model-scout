import pytest

from src.model_scout.request_queue import (
    QueueState,
    RequestQueue,
    build_fingerprint,
    normalize_request,
    transition,
)


def test_fingerprint_is_stable_across_spacing_case_and_mirrors():
    left = build_fingerprint(
        project="AURA",
        request_text="  Find   architecture image models  ",
        resource="ALL",
    )
    right = build_fingerprint(
        project="aura",
        request_text="find architecture image models",
        resource="all",
    )
    assert left == right


def test_normalize_request_defaults_callback_to_source():
    envelope = normalize_request(
        project="AGRI",
        request_text="  Korean   embedding model  ",
        source_repo="ADAMBUILD-ai/agri-ai-business-platform",
        source_issue=33,
    )

    assert envelope.project == "AGRI"
    assert envelope.request_text == "Korean embedding model"
    assert envelope.resource == "all"
    assert envelope.priority == "P1"
    assert envelope.callback_repo == "ADAMBUILD-ai/agri-ai-business-platform"
    assert envelope.callback_issue == 33
    assert envelope.state == QueueState.NORMALIZED


def test_queue_dedupes_same_request_from_different_mirror_sources():
    queue = RequestQueue()
    first = normalize_request(
        project="ADAM",
        request_text="Find GLB render provider alternatives",
        source_repo="ADAMBUILD-ai/adam-build",
        source_issue=38,
    )
    mirrored = normalize_request(
        project="adam",
        request_text=" find  glb render provider alternatives ",
        source_repo="ADAMBUILD-ai/mindle-model-scout",
        source_issue=38,
    )

    queued, created = queue.enqueue(first)
    duplicate, duplicate_created = queue.enqueue(mirrored)

    assert created is True
    assert duplicate_created is False
    assert queued.state == QueueState.QUEUED
    assert duplicate.fingerprint == queued.fingerprint
    assert len(queue.snapshot()) == 1


def test_queue_state_flow_and_retry():
    queue = RequestQueue()
    envelope = normalize_request(project="AURA", request_text="R1 image scout")
    queued, _ = queue.enqueue(envelope)

    running = queue.set_state(queued.fingerprint, QueueState.RUNNING)
    failed = queue.set_state(running.fingerprint, QueueState.FAILED_RETRYABLE)
    requeued = queue.set_state(failed.fingerprint, QueueState.QUEUED)
    rerunning = queue.set_state(requeued.fingerprint, QueueState.RUNNING)
    evidence = queue.set_state(rerunning.fingerprint, QueueState.EVIDENCE_READY)
    delivered = queue.set_state(evidence.fingerprint, QueueState.DELIVERED)

    assert delivered.state == QueueState.DELIVERED


def test_invalid_transition_is_rejected():
    envelope = normalize_request(project="AURA", request_text="R1 image scout")

    with pytest.raises(ValueError, match="invalid queue transition"):
        transition(envelope, QueueState.RUNNING)


def test_invalid_issue_numbers_are_rejected():
    with pytest.raises(ValueError, match="source_issue"):
        normalize_request(project="AGRI", request_text="scout", source_issue=0)
