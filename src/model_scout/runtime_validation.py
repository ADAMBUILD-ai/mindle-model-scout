from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .request_queue import QueueState, RequestEnvelope


RuntimeRunner = Callable[[RequestEnvelope], Mapping[str, Any]]


class RuntimeQueue(Protocol):
    def get(self, fingerprint: str) -> RequestEnvelope | None: ...

    def set_state(self, fingerprint: str, target: QueueState) -> RequestEnvelope: ...


@dataclass(frozen=True)
class ExecutionRequirements:
    """Irreversible or privileged requirements that must stop automatic execution."""

    login: bool = False
    additional_permission: bool = False
    paid_cost: bool = False
    secret_access_or_rotation: bool = False
    production_deployment: bool = False
    external_publication: bool = False
    destructive_change: bool = False
    other_irreversible: bool = False

    def approval_reasons(self) -> tuple[str, ...]:
        labels = (
            ("login", self.login),
            ("additional_permission", self.additional_permission),
            ("paid_cost", self.paid_cost),
            ("secret_access_or_rotation", self.secret_access_or_rotation),
            ("production_deployment", self.production_deployment),
            ("external_publication", self.external_publication),
            ("destructive_change", self.destructive_change),
            ("other_irreversible", self.other_irreversible),
        )
        return tuple(name for name, enabled in labels if enabled)


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_runtime_evidence(evidence: Mapping[str, Any]) -> list[str]:
    """Validate the minimum proof required before a TESTED_PASS claim is allowed.

    A scout result, download, model-card check, or CI status is intentionally insufficient.
    The validator requires a real output file and verifies its size and SHA-256 on disk.
    """

    errors: list[str] = []

    for key in ("model_id", "model_revision", "source", "license", "input", "log"):
        if not _nonempty_text(evidence.get(key)):
            errors.append(f"missing_or_empty:{key}")

    if evidence.get("validation_scope") != "request":
        errors.append("validation_scope_not_request_complete")
    acceptance_checks = evidence.get("acceptance_checks")
    if not isinstance(acceptance_checks, Mapping) or not acceptance_checks:
        errors.append("missing_or_invalid:acceptance_checks")
    elif any(value is not True for value in acceptance_checks.values()):
        errors.append("acceptance_check_failed")

    settings = evidence.get("settings")
    if not isinstance(settings, Mapping):
        errors.append("missing_or_invalid:settings")

    runtime = evidence.get("runtime")
    if not isinstance(runtime, Mapping) or not runtime:
        errors.append("missing_or_invalid:runtime")

    hardware = evidence.get("hardware")
    if not isinstance(hardware, Mapping) or not hardware:
        errors.append("missing_or_invalid:hardware")

    output_path_raw = evidence.get("output_path")
    if not _nonempty_text(output_path_raw):
        errors.append("missing_or_empty:output_path")
        return errors

    output_path = Path(str(output_path_raw))
    if not output_path.is_file():
        errors.append("output_file_missing")
        return errors

    actual_size = output_path.stat().st_size
    if actual_size <= 0:
        errors.append("output_file_empty")

    declared_size = evidence.get("output_size")
    if not isinstance(declared_size, int) or declared_size <= 0:
        errors.append("missing_or_invalid:output_size")
    elif declared_size != actual_size:
        errors.append("output_size_mismatch")

    declared_sha = evidence.get("sha256")
    if not _nonempty_text(declared_sha):
        errors.append("missing_or_empty:sha256")
    else:
        normalized_sha = str(declared_sha).strip().lower()
        if len(normalized_sha) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_sha):
            errors.append("invalid_sha256")
        elif _sha256_file(output_path) != normalized_sha:
            errors.append("sha256_mismatch")

    downloads = evidence.get("downloaded_files")
    if not isinstance(downloads, list) or not downloads:
        errors.append("missing_or_invalid:downloaded_files")
    else:
        for index, item in enumerate(downloads):
            if not isinstance(item, Mapping):
                errors.append(f"invalid_download:{index}")
                continue
            path_value = item.get("path")
            if not _nonempty_text(path_value):
                errors.append(f"missing_download_path:{index}")
                continue
            path = Path(str(path_value))
            if not path.is_file():
                errors.append(f"download_file_missing:{index}")
                continue
            size = item.get("size")
            sha = str(item.get("sha256") or "").strip().lower()
            if size != path.stat().st_size:
                errors.append(f"download_size_mismatch:{index}")
            if len(sha) != 64 or _sha256_file(path) != sha:
                errors.append(f"download_sha256_mismatch:{index}")

    return errors


def run_runtime_validation(
    queue: RuntimeQueue,
    fingerprint: str,
    *,
    runner: RuntimeRunner,
    requirements: ExecutionRequirements | None = None,
) -> dict[str, Any]:
    """Run one approval-aware runtime validation request.

    Safe/free/local/non-destructive work may auto-run. Any declared privileged or
    irreversible requirement transitions the queue item to BLOCKED_APPROVAL without
    invoking the runner. TESTED_PASS is emitted only after real output-file evidence
    passes deterministic validation.
    """

    envelope = queue.get(fingerprint)
    if envelope is None:
        raise KeyError(f"unknown request fingerprint: {fingerprint}")
    if envelope.state != QueueState.QUEUED:
        raise ValueError(f"request is not runtime-dispatchable from state {envelope.state.value}")

    requirements = requirements or ExecutionRequirements()
    approval_reasons = requirements.approval_reasons()
    if approval_reasons:
        blocked = queue.set_state(fingerprint, QueueState.BLOCKED_APPROVAL)
        return {
            "fingerprint": blocked.fingerprint,
            "state": blocked.state.value,
            "status": QueueState.BLOCKED_APPROVAL.value,
            "approval_reasons": list(approval_reasons),
            "runner_invoked": False,
        }

    running = queue.set_state(fingerprint, QueueState.RUNNING)
    try:
        runtime_evidence = dict(runner(running))
    except Exception as exc:
        failed = queue.set_state(fingerprint, QueueState.FAILED_RETRYABLE)
        return {
            "fingerprint": failed.fingerprint,
            "state": failed.state.value,
            "status": QueueState.FAILED_RETRYABLE.value,
            "runner_invoked": True,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    errors = validate_runtime_evidence(runtime_evidence)
    if errors:
        failed = queue.set_state(fingerprint, QueueState.FAILED_RETRYABLE)
        return {
            "fingerprint": failed.fingerprint,
            "state": failed.state.value,
            "status": QueueState.FAILED_RETRYABLE.value,
            "runner_invoked": True,
            "validation_errors": errors,
        }

    ready = queue.set_state(fingerprint, QueueState.EVIDENCE_READY)
    return {
        "fingerprint": ready.fingerprint,
        "state": ready.state.value,
        "status": "TESTED_PASS",
        "runner_invoked": True,
        "runtime_evidence": runtime_evidence,
        "callback": {
            "repo": ready.callback_repo,
            "issue": ready.callback_issue,
        },
    }
