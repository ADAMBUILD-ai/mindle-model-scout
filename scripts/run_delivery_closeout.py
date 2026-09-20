from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",required=True)
    p.add_argument("--artifact",default="delivery-closeout-evidence.json")
    p.add_argument("--ledger",default="delivery-ledger.json")
    args=p.parse_args()
    evidence=json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    target=str(evidence.get("callback_target") or "").strip()
    record={
        "central_issue": evidence.get("central_issue"),
        "source_repository": evidence.get("source_repository"),
        "source_issue": evidence.get("source_issue"),
        "route_fingerprint": evidence.get("route_fingerprint"),
        "model_id": evidence.get("model_id"),
        "revision": evidence.get("revision"),
        "license": evidence.get("license"),
        "input_sha256": evidence.get("input_sha256"),
        "output_sha256": evidence.get("output_sha256"),
        "output_path": evidence.get("output_path"),
        "output_size": evidence.get("output_size"),
        "exact_commit": evidence.get("exact_commit"),
        "workflow_run_id": evidence.get("workflow_run_id"),
        "artifact_id": evidence.get("artifact_id"),
        "state_before": "TESTED_PASS",
        "state_after": "BLOCKED_CONFIG" if not target else "CALLBACK_PENDING",
        "blocker": "missing authoritative AVORA source-team callback target" if not target else None
    }
    Path(args.artifact).write_text(json.dumps(record,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(record,ensure_ascii=False,sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
