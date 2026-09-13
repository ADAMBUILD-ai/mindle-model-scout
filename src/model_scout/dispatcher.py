from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .request_queue import QueueState, RequestQueue
from .scout import scout as run_scout_core


ScoutRunner = Callable[[str, int, str], Mapping[str, Any]]


def _core_resource(resource: str) -> str:
    """Map request-envelope resources onto the currently supported scout core contract."""
    normalized = (resource or "all").strip().casefold()
    if normalized in {"model", "dataset", "space", "all"}:
        return normalized
    # The request envelope may contain `tool`; the current core does not expose a
    # dedicated tool resource. Preserve execution by widening discovery to `all`
    # and expose the originally requested resource in dispatch evidence.
    return "all"


def dispatch_one(
    queue: RequestQueue,
    fingerprint: str,
    *,
    scout_runner: ScoutRunner = run_scout_core,
    limit: int = 10,
) -> dict[str, Any]:
    """Claim one QUEUED request and run it through the existing MODEL SCOUT core.

    This recovery slice is intentionally synchronous and deterministic. It establishes
    the dispatcher state contract before persistence/scheduling and callback writers are
    added. Successful core execution stops at EVIDENCE_READY; delivery is a separate gate.
    """

    envelope = queue.get(fingerprint)
    if envelope is None:
        raise KeyError(f"unknown request fingerprint: {fingerprint}")
    if envelope.state != QueueState.QUEUED:
        raise ValueError(f"request is not dispatchable from state {envelope.state.value}")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

    running = queue.set_state(fingerprint, QueueState.RUNNING)
    resource = _core_resource(running.resource)

    try:
        result = scout_runner(running.request_text, limit, resource)
        if not isinstance(result, Mapping):
            raise TypeError("scout runner must return a mapping")
    except Exception as exc:
        failed = queue.set_state(fingerprint, QueueState.FAILED_RETRYABLE)
        return {
            "fingerprint": failed.fingerprint,
            "state": failed.state.value,
            "requested_resource": failed.resource,
            "dispatched_resource": resource,
            "callback": {
                "repo": failed.callback_repo,
                "issue": failed.callback_issue,
            },
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    ready = queue.set_state(fingerprint, QueueState.EVIDENCE_READY)
    return {
        "fingerprint": ready.fingerprint,
        "state": ready.state.value,
        "requested_resource": ready.resource,
        "dispatched_resource": resource,
        "callback": {
            "repo": ready.callback_repo,
            "issue": ready.callback_issue,
        },
        "result": dict(result),
    }
