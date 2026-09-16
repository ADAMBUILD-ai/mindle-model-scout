from __future__ import annotations

from src.model_scout.callback_delivery import deliver_evidence, render_callback_markdown
from src.model_scout.request_queue import QueueState, RequestQueue, normalize_request


def _ready_queue():
    envelope = normalize_request(
        project="AGRI",
        request_text="Find Hugging Face models for Korean agricultural RAG",
        resource="model",
        priority="P0",
        source_repo="ADAMBUILD-ai/agri-ai-business-platform",
        source_issue=33,
    )
    queue = RequestQueue()
    queued, _ = queue.enqueue(envelope)
    queue.set_state(queued.fingerprint, QueueState.RUNNING)
    ready = queue.set_state(queued.fingerprint, QueueState.EVIDENCE_READY)
    evidence = {
        "fingerprint": ready.fingerprint,
        "state": ready.state.value,
        "requested_resource": "model",
        "dispatched_resource": "model",
        "callback": {"repo": ready.callback_repo, "issue": ready.callback_issue},
        "result": {"candidate_count": 2, "query": "agricultural RAG"},
    }
    return queue, ready, evidence


def test_render_callback_marks_scout_result_not_tested_pass():
    _queue, ready, evidence = _ready_queue()

    body = render_callback_markdown(evidence)

    assert ready.fingerprint in body
    assert "SCOUT_RESULT" in body
    assert "not TESTED_PASS" in body
    assert '"candidate_count": 2' in body


def test_deliver_evidence_writes_source_callback_and_marks_delivered():
    queue, ready, evidence = _ready_queue()
    calls = []

    def writer(repo, issue, body):
        calls.append((repo, issue, body))

    result = deliver_evidence(queue, ready.fingerprint, evidence, writer=writer)

    assert result["delivered"] is True
    assert result["state"] == QueueState.DELIVERED.value
    assert queue.get(ready.fingerprint).state == QueueState.DELIVERED
    assert calls[0][0] == "ADAMBUILD-ai/agri-ai-business-platform"
    assert calls[0][1] == 33
    assert "MODEL SCOUT Evidence Callback" in calls[0][2]


def test_callback_transport_failure_keeps_evidence_ready_for_retry():
    queue, ready, evidence = _ready_queue()

    def writer(_repo, _issue, _body):
        raise RuntimeError("temporary GitHub callback failure")

    result = deliver_evidence(queue, ready.fingerprint, evidence, writer=writer)

    assert result["delivered"] is False
    assert result["state"] == QueueState.EVIDENCE_READY.value
    assert result["error_type"] == "RuntimeError"
    assert queue.get(ready.fingerprint).state == QueueState.EVIDENCE_READY


def test_deliver_rejects_mismatched_fingerprint():
    queue, ready, evidence = _ready_queue()
    evidence = dict(evidence)
    evidence["fingerprint"] = "wrong"

    try:
        deliver_evidence(queue, ready.fingerprint, evidence, writer=lambda *_: None)
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("mismatched fingerprint must fail")


def test_stale_component_evidence_cannot_be_delivered(tmp_path):
    queue, ready, evidence = _ready_queue()
    output = tmp_path / "output.json"
    output.write_text("{}", encoding="utf-8")
    evidence = {
        **evidence,
        "status": "TESTED_PASS",
        "result": {"runtime": {"output_path": str(output)}},
    }
    calls = []

    result = deliver_evidence(
        queue,
        ready.fingerprint,
        evidence,
        writer=lambda *args: calls.append(args),
    )

    assert result["delivered"] is False
    assert result["error"] == "runtime_evidence_invalid"
    assert calls == []
    assert queue.get(ready.fingerprint).state == QueueState.EVIDENCE_READY
