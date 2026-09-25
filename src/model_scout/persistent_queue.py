from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable, Mapping
from pathlib import Path

from .request_queue import QueueState, RequestEnvelope, transition


Clock = Callable[[], float]


class PersistentRequestQueue:
    """SQLite-backed MODEL SCOUT request queue.

    The public methods intentionally mirror ``RequestQueue`` so the existing dispatcher
    and callback delivery code can use this queue without changing their state contract.
    Each operation opens its own short-lived SQLite connection, which makes process
    restart recovery deterministic and avoids relying on in-memory state.
    """

    def __init__(self, path: str | Path, *, clock: Clock = time.time):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._clock = clock
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS request_queue (
                    fingerprint TEXT PRIMARY KEY,
                    project TEXT NOT NULL,
                    request_text TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    source_repo TEXT,
                    source_issue INTEGER,
                    callback_repo TEXT,
                    callback_issue INTEGER,
                    state TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    last_attempt_at REAL,
                    evidence_pointer TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(request_queue)")
            }
            for name in (
                "request_id", "requesting_team", "product", "request_owner",
                "requested_capability", "requested_model_id", "requested_model_family",
                "selection_mode", "acceptance_criteria",
            ):
                if name not in columns:
                    connection.execute(
                        f"ALTER TABLE request_queue ADD COLUMN {name} TEXT NOT NULL DEFAULT 'UNKNOWN'"
                    )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_request_queue_state_updated "
                "ON request_queue(state, updated_at)"
            )

    @staticmethod
    def _row_to_envelope(row: sqlite3.Row) -> RequestEnvelope:
        return RequestEnvelope(
            project=row["project"],
            request_text=row["request_text"],
            resource=row["resource"],
            priority=row["priority"],
            source_repo=row["source_repo"],
            source_issue=row["source_issue"],
            callback_repo=row["callback_repo"],
            callback_issue=row["callback_issue"],
            fingerprint=row["fingerprint"],
            request_id=row["request_id"],
            requesting_team=row["requesting_team"],
            product=row["product"],
            request_owner=row["request_owner"],
            requested_capability=row["requested_capability"],
            requested_model_id=row["requested_model_id"],
            requested_model_family=row["requested_model_family"],
            selection_mode=row["selection_mode"],
            acceptance_criteria=row["acceptance_criteria"],
            state=QueueState(row["state"]),
        )

    def enqueue(self, envelope: RequestEnvelope) -> tuple[RequestEnvelope, bool]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM request_queue WHERE fingerprint = ?",
                (envelope.fingerprint,),
            ).fetchone()
            if row is not None:
                return self._row_to_envelope(row), False

            queued = transition(envelope, QueueState.QUEUED)
            now = float(self._clock())
            connection.execute(
                """
                INSERT INTO request_queue (
                    fingerprint, project, request_text, resource, priority,
                    source_repo, source_issue, callback_repo, callback_issue,
                    request_id, requesting_team, product, request_owner,
                    requested_capability, requested_model_id, requested_model_family,
                    selection_mode, acceptance_criteria,
                    state, retry_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    queued.fingerprint,
                    queued.project,
                    queued.request_text,
                    queued.resource,
                    queued.priority,
                    queued.source_repo,
                    queued.source_issue,
                    queued.callback_repo,
                    queued.callback_issue,
                    queued.request_id,
                    queued.requesting_team,
                    queued.product,
                    queued.request_owner,
                    queued.requested_capability,
                    queued.requested_model_id,
                    queued.requested_model_family,
                    queued.selection_mode,
                    queued.acceptance_criteria,
                    queued.state.value,
                    now,
                    now,
                ),
            )
            return queued, True

    def get(self, fingerprint: str) -> RequestEnvelope | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM request_queue WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        return None if row is None else self._row_to_envelope(row)

    def set_state(self, fingerprint: str, target: QueueState) -> RequestEnvelope:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM request_queue WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
            if row is None:
                raise KeyError(fingerprint)

            current = self._row_to_envelope(row)
            updated = transition(current, target)
            now = float(self._clock())
            last_attempt_at = now if target == QueueState.RUNNING else row["last_attempt_at"]
            connection.execute(
                """
                UPDATE request_queue
                SET state = ?, updated_at = ?, last_attempt_at = ?
                WHERE fingerprint = ?
                """,
                (updated.state.value, now, last_attempt_at, fingerprint),
            )
            return updated

    def set_evidence_pointer(self, fingerprint: str, pointer: str | None) -> None:
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM request_queue WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
            if exists is None:
                raise KeyError(fingerprint)
            connection.execute(
                "UPDATE request_queue SET evidence_pointer = ?, updated_at = ? WHERE fingerprint = ?",
                (pointer, float(self._clock()), fingerprint),
            )

    def snapshot(self) -> list[Mapping[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM request_queue ORDER BY fingerprint"
            ).fetchall()
        result: list[Mapping[str, object]] = []
        for row in rows:
            envelope = self._row_to_envelope(row)
            payload = envelope.as_dict()
            payload.update(
                {
                    "retry_count": row["retry_count"],
                    "last_error": row["last_error"],
                    "last_attempt_at": row["last_attempt_at"],
                    "evidence_pointer": row["evidence_pointer"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )
            result.append(payload)
        return result

    def requeue_stale(
        self,
        *,
        stale_after_seconds: float,
        now: float | None = None,
    ) -> list[str]:
        """Requeue stale QUEUED/RUNNING items without touching ready evidence.

        Items are moved through FAILED_RETRYABLE before returning to QUEUED so the
        existing transition contract remains authoritative. EVIDENCE_READY items are
        intentionally excluded to prevent duplicate scout execution when only delivery
        needs retrying.
        """

        if stale_after_seconds <= 0:
            raise ValueError("stale_after_seconds must be positive")
        current_time = float(self._clock() if now is None else now)
        threshold = current_time - stale_after_seconds
        requeued: list[str] = []

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM request_queue
                WHERE state IN (?, ?) AND updated_at <= ?
                ORDER BY fingerprint
                """,
                (QueueState.QUEUED.value, QueueState.RUNNING.value, threshold),
            ).fetchall()

            for row in rows:
                current = self._row_to_envelope(row)
                failed = transition(current, QueueState.FAILED_RETRYABLE)
                queued = transition(failed, QueueState.QUEUED)
                error = f"watchdog stale {current.state.value.lower()} request"
                connection.execute(
                    """
                    UPDATE request_queue
                    SET state = ?, retry_count = retry_count + 1,
                        last_error = ?, last_attempt_at = ?, updated_at = ?
                    WHERE fingerprint = ?
                    """,
                    (
                        queued.state.value,
                        error,
                        current_time,
                        current_time,
                        queued.fingerprint,
                    ),
                )
                requeued.append(queued.fingerprint)

        return requeued

    def requeue_retryable(
        self,
        *,
        max_retries: int = 3,
        backoff_seconds: float = 900.0,
        now: float | None = None,
    ) -> list[str]:
        """Requeue due failures with exponential backoff and terminal isolation."""

        if max_retries < 1:
            raise ValueError("max_retries must be positive")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds must not be negative")

        requeued: list[str] = []
        current_time = float(self._clock() if now is None else now)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM request_queue WHERE state = ? ORDER BY fingerprint",
                (QueueState.FAILED_RETRYABLE.value,),
            ).fetchall()
            for row in rows:
                current = self._row_to_envelope(row)
                retry_count = int(row["retry_count"])
                if retry_count >= max_retries:
                    terminal = transition(current, QueueState.FAILED_TERMINAL)
                    connection.execute(
                        "UPDATE request_queue SET state = ?, last_error = ?, updated_at = ? WHERE fingerprint = ?",
                        (
                            terminal.state.value,
                            f"retry limit reached ({max_retries})",
                            current_time,
                            terminal.fingerprint,
                        ),
                    )
                    continue
                last_attempt = float(row["last_attempt_at"] or row["updated_at"] or 0.0)
                due_at = last_attempt + backoff_seconds * (2 ** retry_count)
                if current_time < due_at:
                    continue
                queued = transition(current, QueueState.QUEUED)
                connection.execute(
                    """
                    UPDATE request_queue
                    SET state = ?, retry_count = retry_count + 1, updated_at = ?
                    WHERE fingerprint = ?
                    """,
                    (queued.state.value, current_time, queued.fingerprint),
                )
                requeued.append(queued.fingerprint)
        return requeued
