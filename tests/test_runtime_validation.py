import hashlib

from src.model_scout.request_queue import QueueState, RequestQueue, normalize_request
from src.model_scout.runtime_validation import (
    ExecutionRequirements,
    run_runtime_validation,
    validate_runtime_evidence,
)


def _queued_request():
    queue = RequestQueue()
    envelope = normalize_request(
        project="AURA",
        request_text="Run a real local inference and return TESTED_PASS evidence",
        resource="model",
        priority="P0",
        source_repo="ADAMBUILD-ai/aura-engine",
        source_issue=32,
    )
    queued, created = queue.enqueue(envelope)
    assert created is True
    return queue, queued


def _evidence_for(path):
    payload = path.read_bytes()
    return {
        "model_id": "example/model",
        "model_revision": "deadbeef",
        "source": "huggingface:example/model",
        "license": "apache-2.0",
        "input": "AURA architectural concept test input",
        "output_path": str(path),
        "output_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "settings": {"seed": 7, "steps": 4},
        "runtime": {"python": "3.11", "backend": "cpu-test"},
        "hardware": {"device": "cpu", "ram_mb": 1024},
        "log": "inference completed successfully",
        "validation_scope": "request",
        "acceptance_checks": {"requested_runtime_output_verified": True},
        "downloaded_files": [
            {
                "path": str(path),
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        ],
    }


def test_approval_gated_request_is_blocked_without_runner_call():
    queue, queued = _queued_request()
    calls = []

    def runner(_envelope):
        calls.append(True)
        return {}

    result = run_runtime_validation(
        queue,
        queued.fingerprint,
        runner=runner,
        requirements=ExecutionRequirements(paid_cost=True, production_deployment=True),
    )

    assert calls == []
    assert result["state"] == QueueState.BLOCKED_APPROVAL.value
    assert result["status"] == QueueState.BLOCKED_APPROVAL.value
    assert result["runner_invoked"] is False
    assert result["approval_reasons"] == ["paid_cost", "production_deployment"]
    assert queue.get(queued.fingerprint).state == QueueState.BLOCKED_APPROVAL


def test_missing_output_file_cannot_be_tested_pass(tmp_path):
    queue, queued = _queued_request()
    missing = tmp_path / "missing.bin"

    def runner(_envelope):
        evidence = _evidence_for(tmp_path / "placeholder.bin") if False else {
            "model_id": "example/model",
            "model_revision": "deadbeef",
            "source": "huggingface:example/model",
            "license": "apache-2.0",
            "input": "real input",
            "output_path": str(missing),
            "output_size": 1,
            "sha256": "0" * 64,
            "settings": {"seed": 7},
            "runtime": {"python": "3.11"},
            "hardware": {"device": "cpu"},
            "log": "runner returned without a real file",
            "validation_scope": "request",
            "acceptance_checks": {"requested_runtime_output_verified": True},
            "downloaded_files": [],
        }
        return evidence

    result = run_runtime_validation(queue, queued.fingerprint, runner=runner)

    assert result["status"] == QueueState.FAILED_RETRYABLE.value
    assert "output_file_missing" in result["validation_errors"]
    assert queue.get(queued.fingerprint).state == QueueState.FAILED_RETRYABLE


def test_hash_mismatch_cannot_be_tested_pass(tmp_path):
    queue, queued = _queued_request()
    output = tmp_path / "output.bin"
    output.write_bytes(b"real-runtime-output")
    evidence = _evidence_for(output)
    evidence["sha256"] = "f" * 64

    result = run_runtime_validation(queue, queued.fingerprint, runner=lambda _env: evidence)

    assert result["status"] == QueueState.FAILED_RETRYABLE.value
    assert "sha256_mismatch" in result["validation_errors"]
    assert queue.get(queued.fingerprint).state == QueueState.FAILED_RETRYABLE


def test_valid_real_output_evidence_reaches_tested_pass(tmp_path):
    queue, queued = _queued_request()
    output = tmp_path / "output.bin"
    output.write_bytes(b"verified-runtime-output")
    evidence = _evidence_for(output)

    result = run_runtime_validation(queue, queued.fingerprint, runner=lambda _env: evidence)

    assert result["status"] == "TESTED_PASS"
    assert result["state"] == QueueState.EVIDENCE_READY.value
    assert result["runner_invoked"] is True
    assert result["runtime_evidence"]["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert result["callback"] == {"repo": "ADAMBUILD-ai/aura-engine", "issue": 32}
    assert queue.get(queued.fingerprint).state == QueueState.EVIDENCE_READY


def test_component_output_reaches_acquired_verified_without_false_tested_pass(tmp_path):
    queue, queued = _queued_request()
    output = tmp_path / "component-output.bin"
    output.write_bytes(b"verified-component-output")
    evidence = _evidence_for(output)
    evidence["validation_scope"] = "component"
    evidence["acquisition_verified"] = True

    result = run_runtime_validation(queue, queued.fingerprint, runner=lambda _env: evidence)

    assert result["status"] == "ACQUIRED_VERIFIED"
    assert result["validation_pending"] is True
    assert queue.get(queued.fingerprint).state == QueueState.EVIDENCE_READY


def test_component_without_verified_model_cannot_claim_acquisition(tmp_path):
    queue, queued = _queued_request()
    output = tmp_path / "component-output.bin"
    output.write_bytes(b"component-only")
    evidence = _evidence_for(output)
    evidence["validation_scope"] = "component"
    evidence["acquisition_verified"] = False
    result = run_runtime_validation(queue, queued.fingerprint, runner=lambda _env: evidence)
    assert result["status"] == "FAILED_RETRYABLE"
    assert queue.get(queued.fingerprint).state == QueueState.FAILED_RETRYABLE


def test_runner_exception_is_retryable():
    queue, queued = _queued_request()

    def runner(_envelope):
        raise RuntimeError("temporary runtime failure")

    result = run_runtime_validation(queue, queued.fingerprint, runner=runner)

    assert result["status"] == QueueState.FAILED_RETRYABLE.value
    assert result["error_type"] == "RuntimeError"
    assert "temporary runtime failure" in result["error"]
    assert queue.get(queued.fingerprint).state == QueueState.FAILED_RETRYABLE


def test_validator_rejects_missing_runtime_metadata(tmp_path):
    output = tmp_path / "output.bin"
    output.write_bytes(b"output")
    evidence = _evidence_for(output)
    evidence.pop("settings")
    evidence["runtime"] = {}
    evidence["hardware"] = {}
    evidence["log"] = ""

    errors = validate_runtime_evidence(evidence)

    assert "missing_or_invalid:settings" in errors
    assert "missing_or_invalid:runtime" in errors
    assert "missing_or_invalid:hardware" in errors
    assert "missing_or_empty:log" in errors
