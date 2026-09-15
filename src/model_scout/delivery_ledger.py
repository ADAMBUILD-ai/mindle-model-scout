from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class DeliveryState(str, Enum):
    REQUESTED = "REQUESTED"
    FOUND = "FOUND"
    DOWNLOADED = "DOWNLOADED"
    TESTED_PASS = "TESTED_PASS"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"


_TRANSITIONS = {
    DeliveryState.REQUESTED: {DeliveryState.FOUND, DeliveryState.REJECTED},
    DeliveryState.FOUND: {DeliveryState.DOWNLOADED, DeliveryState.REJECTED},
    DeliveryState.DOWNLOADED: {DeliveryState.TESTED_PASS, DeliveryState.REJECTED},
    DeliveryState.TESTED_PASS: {DeliveryState.DELIVERED, DeliveryState.REJECTED},
    DeliveryState.DELIVERED: set(),
    DeliveryState.REJECTED: set(),
}


@dataclass(frozen=True)
class DeliveryRecord:
    fingerprint: str
    state: DeliveryState
    owner: str
    next_action: str
    evidence: dict[str, Any]
    updated_at: float
    last_evidence_at: float | None
    retry_count: int
    blocker_classification: str | None

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["state"] = self.state.value
        return value


class DeliveryLedger:
    """The durable SSOT for model-supply progress and operational ownership."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS model_delivery (
                fingerprint TEXT PRIMARY KEY, state TEXT NOT NULL, owner TEXT NOT NULL,
                next_action TEXT NOT NULL, evidence_json TEXT NOT NULL, updated_at REAL NOT NULL,
                last_evidence_at REAL, retry_count INTEGER NOT NULL DEFAULT 0,
                blocker_classification TEXT
            )""")
            columns = {row[1] for row in connection.execute("PRAGMA table_info(model_delivery)")}
            if "last_evidence_at" not in columns:
                connection.execute("ALTER TABLE model_delivery ADD COLUMN last_evidence_at REAL")
            if "retry_count" not in columns:
                connection.execute("ALTER TABLE model_delivery ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0")
            if "blocker_classification" not in columns:
                connection.execute("ALTER TABLE model_delivery ADD COLUMN blocker_classification TEXT")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DeliveryRecord:
        return DeliveryRecord(
            row["fingerprint"], DeliveryState(row["state"]), row["owner"], row["next_action"],
            json.loads(row["evidence_json"]), row["updated_at"], row["last_evidence_at"],
            row["retry_count"], row["blocker_classification"],
        )

    def request(self, fingerprint: str, *, owner: str, next_action: str) -> DeliveryRecord:
        if not fingerprint or not owner or not next_action:
            raise ValueError("fingerprint, owner, and next_action are required")
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM model_delivery WHERE fingerprint = ?", (fingerprint,)).fetchone()
            if row is not None:
                return self._from_row(row)
            connection.execute(
                "INSERT INTO model_delivery (fingerprint, state, owner, next_action, evidence_json, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (fingerprint, DeliveryState.REQUESTED.value, owner, next_action, "{}", time.time()),
            )
        return self.get(fingerprint)

    def get(self, fingerprint: str) -> DeliveryRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM model_delivery WHERE fingerprint = ?", (fingerprint,)).fetchone()
        return None if row is None else self._from_row(row)

    def advance(self, fingerprint: str, state: DeliveryState, *, owner: str, next_action: str, evidence: dict[str, Any], blocker_classification: str | None = None) -> DeliveryRecord:
        if not owner or not next_action:
            raise ValueError("owner and next_action are required for every delivery state")
        current = self.get(fingerprint)
        if current is None:
            raise KeyError(fingerprint)
        if state != current.state and state not in _TRANSITIONS[current.state]:
            raise ValueError(f"invalid delivery transition: {current.state.value} -> {state.value}")
        with self._connect() as connection:
            now = time.time()
            connection.execute(
                "UPDATE model_delivery SET state = ?, owner = ?, next_action = ?, evidence_json = ?, updated_at = ?, last_evidence_at = ?, blocker_classification = ? WHERE fingerprint = ?",
                (state.value, owner, next_action, json.dumps(evidence, sort_keys=True, default=str), now, now, blocker_classification, fingerprint),
            )
        return self.get(fingerprint)
