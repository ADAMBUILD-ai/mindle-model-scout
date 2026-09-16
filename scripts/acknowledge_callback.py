from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model_scout.delivery_ledger import DeliveryLedger, DeliveryState
from src.model_scout.persistent_queue import PersistentRequestQueue
from src.model_scout.request_queue import QueueState


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--callback-url", required=True)
    args = parser.parse_args()

    state_dir = Path(args.state_dir).resolve()
    queue = PersistentRequestQueue(state_dir / "request_queue.sqlite3")
    ledger = DeliveryLedger(state_dir / "model_delivery.sqlite3")
    queued = queue.get(args.fingerprint)
    record = ledger.get(args.fingerprint)
    if queued is None or record is None:
        raise SystemExit("fingerprint is missing from the durable queue or ledger")
    if queued.state != QueueState.EVIDENCE_READY or record.state != DeliveryState.TESTED_PASS:
        raise SystemExit(
            f"callback cannot be acknowledged from queue={queued.state.value}, ledger={record.state.value}"
        )

    evidence = dict(record.evidence)
    evidence["callback_url"] = args.callback_url
    ledger.advance(
        args.fingerprint,
        DeliveryState.DELIVERED,
        owner="model-scout",
        next_action="none",
        evidence=evidence,
    )
    queue.set_evidence_pointer(args.fingerprint, args.callback_url)
    delivered = queue.set_state(args.fingerprint, QueueState.DELIVERED)

    receipt_dir = state_dir / "callback-receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "fingerprint": args.fingerprint,
        "queue_state": delivered.state.value,
        "ledger_state": DeliveryState.DELIVERED.value,
        "callback_url": args.callback_url,
    }
    (receipt_dir / f"{args.fingerprint}.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
