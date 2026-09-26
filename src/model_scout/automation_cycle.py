from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any, Protocol

from .callback_delivery import deliver_evidence
from .dispatcher import ScoutRunner, dispatch_one
from .delivery_ledger import DeliveryLedger, DeliveryState
from .github_request_discovery import discover_github_issue_requests
from .request_queue import QueueState, RequestEnvelope
from .runtime_validation import run_runtime_validation


CallbackWriter = Callable[[str, int, str], Any]
RuntimeRunner = Callable[[RequestEnvelope, Mapping[str, Any]], Mapping[str, Any]]


class QueueLike(Protocol):
    def enqueue(self, envelope: RequestEnvelope) -> tuple[RequestEnvelope, bool]: ...

    def get(self, fingerprint: str) -> RequestEnvelope | None: ...

    def set_state(self, fingerprint: str, target: QueueState) -> RequestEnvelope: ...


class DurableEvidenceStore:
    """Persist dispatcher evidence so callback retries survive process restarts.

    Queue state alone is insufficient for durable delivery: an EVIDENCE_READY item also
    needs the exact dispatcher payload that must be written back to the originating issue.
    This store keeps that payload separately and idempotently by request fingerprint.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS request_evidence (
                    fingerprint TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def put(self, fingerprint: str, evidence: Mapping[str, Any]) -> None:
        if not fingerprint:
            raise ValueError("fingerprint is required")
        payload = json.dumps(dict(evidence), ensure_ascii=False, sort_keys=True, default=str)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO request_evidence (fingerprint, payload_json)
                VALUES (?, ?)
                ON CONFLICT(fingerprint) DO UPDATE SET payload_json = excluded.payload_json
                """,
                (fingerprint, payload),
            )

    def get(self, fingerprint: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM request_evidence WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload_json"])
        if not isinstance(payload, dict):
            raise ValueError("stored evidence payload must be a mapping")
        return payload


def run_scout_cycle(
    *,
    issues: Iterable[Mapping[str, object]],
    configured_repos: Iterable[str],
    queue: QueueLike,
    evidence_store: DurableEvidenceStore,
    scout_runner: ScoutRunner,
    callback_writer: CallbackWriter,
    limit: int = 10,
    preferred_source: tuple[str, int] | None = None,
    max_requests: int = 4,
) -> list[dict[str, Any]]:
    """Run one deterministic cross-repo discovery -> scout -> callback cycle.

    The cycle is restart-safe at the delivery boundary: successful dispatcher evidence is
    persisted before callback delivery. If callback transport fails, the queue remains
    EVIDENCE_READY and the exact stored payload is reused on the next cycle instead of
    rerunning the scout core.
    """

    discovered = discover_github_issue_requests(issues, configured_repos=configured_repos)
    if max_requests < 1:
        raise ValueError("max_requests must be positive")
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    preferred_key = (preferred_source[0].casefold(), preferred_source[1]) if preferred_source else None
    discovered.sort(key=lambda item: (
        0 if preferred_key and (str(item.source_repo).casefold(), item.source_issue) == preferred_key else 1,
        priority_rank.get(item.priority, 4),
        str(item.source_repo),
        item.source_issue or 0,
    ))
    fingerprints: list[str] = []
    for envelope in discovered:
        queued, _created = queue.enqueue(envelope)
        fingerprints.append(queued.fingerprint)

    eligible = [
        fingerprint for fingerprint in fingerprints
        if (queue.get(fingerprint) is not None and queue.get(fingerprint).state in {QueueState.QUEUED, QueueState.EVIDENCE_READY})
    ][:max_requests]
    results: list[dict[str, Any]] = []
    for fingerprint in eligible:
        envelope = queue.get(fingerprint)
        if envelope is None:
            continue

        if envelope.state == QueueState.QUEUED:
            evidence = dispatch_one(
                queue,
                fingerprint,
                scout_runner=scout_runner,
                limit=limit,
            )
            results.append(dict(evidence))
            if evidence.get("state") != QueueState.EVIDENCE_READY.value:
                continue
            evidence_store.put(fingerprint, evidence)
            envelope = queue.get(fingerprint)

        if envelope is not None and envelope.state == QueueState.EVIDENCE_READY:
            evidence = evidence_store.get(fingerprint)
            if evidence is None:
                results.append(
                    {
                        "fingerprint": fingerprint,
                        "state": QueueState.EVIDENCE_READY.value,
                        "delivered": False,
                        "error": "durable_evidence_missing",
                    }
                )
                continue
            delivery = deliver_evidence(
                queue,
                fingerprint,
                evidence,
                writer=callback_writer,
            )
            results.append(dict(delivery))

    return results


def run_runtime_cycle(
    *,
    issues: Iterable[Mapping[str, object]],
    configured_repos: Iterable[str],
    queue: QueueLike,
    evidence_store: DurableEvidenceStore,
    delivery_ledger: DeliveryLedger,
    scout_runner: ScoutRunner,
    runtime_runner: RuntimeRunner,
    callback_writer: CallbackWriter,
    limit: int = 10,
    preferred_source: tuple[str, int] | None = None,
    max_requests: int = 4,
) -> list[dict[str, Any]]:
    """Run discovery, search, runtime validation, and callback as one durable cycle."""

    discovered = discover_github_issue_requests(issues, configured_repos=configured_repos)
    if max_requests < 1:
        raise ValueError("max_requests must be positive")
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    preferred_key = (preferred_source[0].casefold(), preferred_source[1]) if preferred_source else None
    discovered.sort(key=lambda item: (
        0 if preferred_key and (str(item.source_repo).casefold(), item.source_issue) == preferred_key else 1,
        priority_rank.get(item.priority, 4),
        str(item.source_repo),
        item.source_issue or 0,
    ))
    fingerprints: list[str] = []
    for envelope in discovered:
        queued, _created = queue.enqueue(envelope)
        fingerprints.append(queued.fingerprint)
        delivery_ledger.request(
            queued.fingerprint,
            owner=str(queued.callback_repo or queued.source_repo or "MODEL_SCOUT_AUTOMATION"),
            next_action="search for a license-compatible executable candidate",
        )

    eligible = [
        fingerprint for fingerprint in fingerprints
        if (queue.get(fingerprint) is not None and queue.get(fingerprint).state in {QueueState.QUEUED, QueueState.EVIDENCE_READY})
    ][:max_requests]
    results: list[dict[str, Any]] = []
    for fingerprint in eligible:
        envelope = queue.get(fingerprint)
        if envelope is None:
            continue

        if envelope.state == QueueState.QUEUED:
            owner = str(envelope.callback_repo or envelope.source_repo or "MODEL_SCOUT_AUTOMATION")
            try:
                scout_result = scout_runner(envelope.request_text, limit, envelope.resource)
                if not isinstance(scout_result, Mapping):
                    raise TypeError("scout runner must return a mapping")
                candidates = scout_result.get("candidates")
                if not isinstance(candidates, list) or not candidates:
                    raise ValueError("search produced no executable candidates")
            except Exception as exc:
                failed = queue.set_state(fingerprint, QueueState.FAILED_RETRYABLE)
                record_failure = getattr(queue, "record_failure", None)
                if callable(record_failure):
                    record_failure(fingerprint, f"search:{type(exc).__name__}: {exc}")
                results.append({
                    "fingerprint": fingerprint,
                    "state": failed.state.value,
                    "stage": "search",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                })
                continue

            delivery_ledger.advance(
                fingerprint,
                DeliveryState.FOUND,
                owner=owner,
                next_action="download candidate and execute runtime adapter",
                evidence={"scout_result": dict(scout_result)},
            )
            runtime_result = run_runtime_validation(
                queue,
                fingerprint,
                runner=lambda current: runtime_runner(current, scout_result),
            )
            results.append(dict(runtime_result))
            if runtime_result.get("status") == "FAILED_RETRYABLE":
                record_failure = getattr(queue, "record_failure", None)
                if callable(record_failure):
                    detail = runtime_result.get("error") or runtime_result.get("validation_errors") or "runtime failure"
                    record_failure(fingerprint, f"runtime:{runtime_result.get('error_type', 'validation')}: {detail}")
            if runtime_result.get("status") not in {"TESTED_PASS", "ACQUIRED_VERIFIED"}:
                continue

            runtime_evidence = dict(runtime_result["runtime_evidence"])
            delivery_ledger.advance(
                fingerprint,
                DeliveryState.DOWNLOADED,
                owner=owner,
                next_action="validate runtime output and evidence hashes",
                evidence=runtime_evidence,
            )
            if runtime_result.get("status") == "TESTED_PASS":
                delivery_ledger.advance(
                    fingerprint,
                    DeliveryState.TESTED_PASS,
                    owner=owner,
                    next_action="deliver validated evidence callback",
                    evidence=runtime_evidence,
                )
                marker = getattr(runtime_runner, "mark_tested_pass", None)
                if callable(marker):
                    marker(runtime_evidence)
            callback_evidence = {
                **runtime_result,
                "result": {"scout": dict(scout_result), "runtime": runtime_evidence},
            }
            evidence_store.put(fingerprint, callback_evidence)
            envelope = queue.get(fingerprint)

        if envelope is not None and envelope.state == QueueState.EVIDENCE_READY:
            evidence = evidence_store.get(fingerprint)
            if evidence is None:
                results.append({
                    "fingerprint": fingerprint,
                    "state": QueueState.EVIDENCE_READY.value,
                    "delivered": False,
                    "error": "durable_evidence_missing",
                })
                continue
            delivery = deliver_evidence(queue, fingerprint, evidence, writer=callback_writer)
            results.append(dict(delivery))
            if delivery.get("delivered"):
                current = delivery_ledger.get(fingerprint)
                if current is not None and current.state == DeliveryState.TESTED_PASS:
                    delivery_ledger.advance(
                        fingerprint,
                        DeliveryState.DELIVERED,
                        owner=current.owner,
                        next_action="monitor durable state on the next watchdog cycle",
                        evidence=evidence,
                    )

    return results
