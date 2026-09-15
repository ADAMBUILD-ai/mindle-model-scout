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
                next_action TEXT NOT NULL, evidence_json TEXT NOT NULL, updated_at REAL NOT NULL
            )""")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DeliveryRecord:
        return DeliveryRecord(row["fingerprint"], DeliveryState(row["state"]), row["owner"], row["next_action"], json.loads(row["evidence_json"]), row["updated_at"])

    def request(self, fingerprint: str, *, owner: str, next_action: str) -> DeliveryRecord:
        if not fingerprint or not owner or not next_action:
            raise ValueError("fingerprint, owner, and next_action are required")
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM model_delivery WHERE fingerprint = ?", (fingerprint,)).fetchone()
            if row is not None:
                return self._from_row(row)
            connection.execute("INSERT INTO model_delivery VALUES (?, ?, ?, ?, ?, ?)", (fingerprint, DeliveryState.REQUESTED.value, owner, next_action, "{}", time.time()))
        return self.get(fingerprint)

    def get(self, fingerprint: str) -> DeliveryRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM model_delivery WHERE fingerprint = ?", (fingerprint,)).fetchone()
        return None if row is None else self._from_row(row)

    def advance(self, fingerprint: str, state: DeliveryState, *, owner: str, next_action: str, evidence: dict[str, Any]) -> DeliveryRecord:
        if not owner or not next_action:
            raise ValueError("owner and next_action are required for every delivery state")
        current = self.get(fingerprint)
        if current is None:
            raise KeyError(fingerprint)
        if state != current.state and state not in _TRANSITIONS[current.state]:
            raise ValueError(f"invalid delivery transition: {current.state.value} -> {state.value}")
        with self._connect() as connection:
            connection.execute("UPDATE model_delivery SET state = ?, owner = ?, next_action = ?, evidence_json = ?, updated_at = ? WHERE fingerprint = ?", (state.value, owner, next_action, json.dumps(evidence, sort_keys=True, default=str), time.time(), fingerprint))
        return self.get(fingerprint)
