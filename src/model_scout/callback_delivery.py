from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from .request_queue import QueueState, RequestQueue


CallbackWriter = Callable[[str, int, str], Any]


def render_callback_markdown(evidence: Mapping[str, Any]) -> str:
    """Render deterministic delivery evidence for the originating GitHub request.

    The callback body intentionally contains only verified dispatcher output. It does not
    promote a scout result to TESTED_PASS; runtime validation remains a separate gate.
    """

    fingerprint = str(evidence.get("fingerprint") or "").strip()
    state = str(evidence.get("state") or "").strip()
    if not fingerprint:
        raise ValueError("evidence fingerprint is required")
    if state != QueueState.EVIDENCE_READY.value:
        raise ValueError("callback evidence must be in EVIDENCE_READY state")

    callback = evidence.get("callback")
    if not isinstance(callback, Mapping):
        raise ValueError("callback metadata is required")

    result = evidence.get("result")
    if not isinstance(result, Mapping):
        raise ValueError("dispatcher result mapping is required")
    if int(result.get("candidate_count") or 0) <= 0:
        raise ValueError("callback requires at least one candidate")
    if str(result.get("semantic_match") or "PASS").upper() != "PASS":
        raise ValueError("callback requires semantic_match PASS")

    requested_resource = str(evidence.get("requested_resource") or "all")
    dispatched_resource = str(evidence.get("dispatched_resource") or "all")
    result_json = json.dumps(dict(result), ensure_ascii=False, sort_keys=True, default=str)

    return (
        "## MODEL SCOUT Evidence Callback\n\n"
        f"- fingerprint: `{fingerprint}`\n"
        f"- queue_state: `{state}`\n"
        f"- requested_resource: `{requested_resource}`\n"
        f"- dispatched_resource: `{dispatched_resource}`\n"
        "- success_gate: `candidate_count > 0 + semantic_match PASS + Evidence + source callback`\n"
        "- evidence_class: `SCOUT_RESULT` (not TESTED_PASS unless separate runtime evidence exists)\n\n"
        "```json\n"
        f"{result_json}\n"
        "```"
    )


def deliver_evidence(
    queue: RequestQueue,
    fingerprint: str,
    evidence: Mapping[str, Any],
    *,
    writer: CallbackWriter,
) -> dict[str, Any]:
    """Write EVIDENCE_READY output back to the source request and mark it DELIVERED.

    Callback transport failures are retry-safe: the queue remains EVIDENCE_READY so a
    later delivery attempt does not need to rerun the scout core.
    """

    envelope = queue.get(fingerprint)
    if envelope is None:
        raise KeyError(f"unknown request fingerprint: {fingerprint}")
    if envelope.state != QueueState.EVIDENCE_READY:
        raise ValueError(f"request is not deliverable from state {envelope.state.value}")
    if str(evidence.get("fingerprint") or "") != fingerprint:
        raise ValueError("evidence fingerprint does not match queue item")
    if not envelope.callback_repo or not envelope.callback_issue:
        raise ValueError("callback repository and issue are required")

    body = render_callback_markdown(evidence)
    try:
        callback_result = writer(envelope.callback_repo, envelope.callback_issue, body)
    except Exception as exc:
        return {
            "fingerprint": fingerprint,
            "state": QueueState.EVIDENCE_READY.value,
            "delivered": False,
            "callback": {
                "repo": envelope.callback_repo,
                "issue": envelope.callback_issue,
            },
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    delivered = queue.set_state(fingerprint, QueueState.DELIVERED)
    callback = {
        "repo": delivered.callback_repo,
        "issue": delivered.callback_issue,
    }
    if isinstance(callback_result, Mapping):
        if callback_result.get("id") is not None:
            callback["comment_id"] = callback_result["id"]
        if callback_result.get("html_url"):
            callback["url"] = callback_result["html_url"]
    return {
        "fingerprint": delivered.fingerprint,
        "state": delivered.state.value,
        "delivered": True,
        "callback": callback,
    }
