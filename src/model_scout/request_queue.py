from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Iterable, Mapping


class QueueState(str, Enum):
    DISCOVERED = "DISCOVERED"
    NORMALIZED = "NORMALIZED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    EVIDENCE_READY = "EVIDENCE_READY"
    DELIVERED = "DELIVERED"
    BLOCKED_APPROVAL = "BLOCKED_APPROVAL"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"


_ALLOWED_TRANSITIONS: dict[QueueState, set[QueueState]] = {
    QueueState.DISCOVERED: {QueueState.NORMALIZED},
    QueueState.NORMALIZED: {QueueState.QUEUED},
    QueueState.QUEUED: {
        QueueState.RUNNING,
        QueueState.BLOCKED_APPROVAL,
        QueueState.FAILED_RETRYABLE,
    },
    QueueState.RUNNING: {
        QueueState.EVIDENCE_READY,
        QueueState.BLOCKED_APPROVAL,
        QueueState.FAILED_RETRYABLE,
    },
    QueueState.EVIDENCE_READY: {QueueState.DELIVERED},
    QueueState.DELIVERED: set(),
    QueueState.BLOCKED_APPROVAL: {QueueState.QUEUED},
    QueueState.FAILED_RETRYABLE: {QueueState.QUEUED},
}


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", value).strip()


def _normalize_key(value: str) -> str:
    return _normalize_text(value).casefold()


def build_fingerprint(*, project: str, request_text: str, resource: str = "all") -> str:
    """Return a stable content fingerprint used to dedupe mirrored requests.

    Source repository/issue identity is intentionally excluded so the same request mirrored
    through multiple project repositories resolves to one central execution item.
    """

    canonical = {
        "project": _normalize_key(project),
        "request_text": _normalize_key(request_text),
        "resource": _normalize_key(resource or "all"),
    }
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RequestEnvelope:
    project: str
    request_text: str
    resource: str
    priority: str
    source_repo: str | None
    source_issue: int | None
    callback_repo: str | None
    callback_issue: int | None
    fingerprint: str
    state: QueueState = QueueState.NORMALIZED

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["state"] = self.state.value
        return payload


def normalize_request(
    *,
    project: str,
    request_text: str,
    resource: str = "all",
    priority: str = "P1",
    source_repo: str | None = None,
    source_issue: int | None = None,
    callback_repo: str | None = None,
    callback_issue: int | None = None,
) -> RequestEnvelope:
    project_n = _normalize_text(project)
    request_n = _normalize_text(request_text)
    resource_n = _normalize_key(resource or "all")
    priority_n = _normalize_text(priority).upper() or "P1"

    if not project_n:
        raise ValueError("project must not be empty")
    if not request_n:
        raise ValueError("request_text must not be empty")
    if source_issue is not None and source_issue <= 0:
        raise ValueError("source_issue must be positive")
    if callback_issue is not None and callback_issue <= 0:
        raise ValueError("callback_issue must be positive")

    source_repo_n = _normalize_text(source_repo) or None
    callback_repo_n = _normalize_text(callback_repo) or source_repo_n
    callback_issue_n = callback_issue if callback_issue is not None else source_issue

    return RequestEnvelope(
        project=project_n,
        request_text=request_n,
        resource=resource_n,
        priority=priority_n,
        source_repo=source_repo_n,
        source_issue=source_issue,
        callback_repo=callback_repo_n,
        callback_issue=callback_issue_n,
        fingerprint=build_fingerprint(
            project=project_n,
            request_text=request_n,
            resource=resource_n,
        ),
    )


def transition(envelope: RequestEnvelope, target: QueueState) -> RequestEnvelope:
    if target == envelope.state:
        return envelope
    allowed = _ALLOWED_TRANSITIONS[envelope.state]
    if target not in allowed:
        raise ValueError(f"invalid queue transition: {envelope.state.value} -> {target.value}")
    return replace(envelope, state=target)


class RequestQueue:
    """Deterministic central queue with fingerprint dedupe.

    This first recovery slice keeps storage in-memory by design. It establishes the queue
    contract and transition rules; the persistence adapter can be added without changing
    the envelope/fingerprint semantics.
    """

    def __init__(self, items: Iterable[RequestEnvelope] | None = None):
        self._items: dict[str, RequestEnvelope] = {}
        if items:
            for item in items:
                self._items[item.fingerprint] = item

    def enqueue(self, envelope: RequestEnvelope) -> tuple[RequestEnvelope, bool]:
        existing = self._items.get(envelope.fingerprint)
        if existing is not None:
            return existing, False
        queued = transition(envelope, QueueState.QUEUED)
        self._items[queued.fingerprint] = queued
        return queued, True

    def get(self, fingerprint: str) -> RequestEnvelope | None:
        return self._items.get(fingerprint)

    def set_state(self, fingerprint: str, target: QueueState) -> RequestEnvelope:
        current = self._items[fingerprint]
        updated = transition(current, target)
        self._items[fingerprint] = updated
        return updated

    def snapshot(self) -> list[Mapping[str, object]]:
        return [self._items[key].as_dict() for key in sorted(self._items)]
