"""Post a verified FAST DELIVERY callback using the already-approved cross-repo token."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from src.model_scout.delivery_ledger import DeliveryLedger, DeliveryState


LEDGER = Path("fast-delivery-ledger.sqlite3")
FINGERPRINT = "agri-issue-23:korean-document-search-embedding"


def main() -> int:
    evidence = json.loads(Path("fast-delivery-evidence.json").read_text(encoding="utf-8"))
    if evidence.get("status") != "TESTED_PASS":
        raise SystemExit("FAST DELIVERY evidence is not TESTED_PASS")
    download = evidence.get("download")
    if not isinstance(download, dict) or not download.get("weight_sha256") or not download.get("weight_size"):
        raise SystemExit("FAST DELIVERY evidence lacks downloaded weight hash and size")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required for callback delivery")
    ledger = DeliveryLedger(LEDGER)
    record = ledger.get(FINGERPRINT)
    if record is None or record.state != DeliveryState.TESTED_PASS:
        raise SystemExit("FAST DELIVERY ledger is not TESTED_PASS")
    body = "## MODEL SCOUT FAST DELIVERY — DELIVERED\n\n"
    body += "`REQUESTED -> FOUND -> DOWNLOADED -> TESTED_PASS -> DELIVERED`\n\n"
    body += "```json\n" + json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n```\n"
    request = urllib.request.Request(
        "https://api.github.com/repos/ADAMBUILD-ai/agri-ai-business-platform/issues/23/comments",
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "Content-Type": "application/json", "User-Agent": "mindle-model-scout"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        callback = json.load(response)
    delivered = ledger.advance(
        FINGERPRINT,
        DeliveryState.DELIVERED,
        owner=record.owner,
        next_action="handoff complete; integration owner pins the tested revision",
        evidence={**record.evidence, "callback_url": callback["html_url"], "callback_comment_id": callback["id"]},
        blocker_classification="DEGRADED_AUTONOMY",
    )
    evidence["delivery"] = delivered.as_dict()
    evidence["queue"] = {"pending": 0, "retry": delivered.retry_count, "stale": 0}
    Path("fast-delivery-evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    Path("fast-delivery-callback.json").write_text(json.dumps({"issue_comment_url": callback["html_url"], "comment_id": callback["id"], "delivery": delivered.as_dict()}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"delivered": True, "issue_comment_url": callback["html_url"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
