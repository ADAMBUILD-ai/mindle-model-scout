from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
TARGET_REPO = "ADAMBUILD-ai/avora-engine"
TARGET_ISSUE = 7

def github_json(method: str, url: str, token: str, payload: dict | None = None):
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urlopen(req, timeout=20) as response:
        return response.status, json.loads(response.read().decode("utf-8"))

def marker_for(route_fingerprint: str) -> str:
    return f"<!-- model-scout-route:{route_fingerprint} -->"

def find_existing_callback(token: str, marker: str):
    url = f"{API_ROOT}/repos/{TARGET_REPO}/issues/{TARGET_ISSUE}/comments?per_page=100"
    status, comments = github_json("GET", url, token)
    for comment in comments:
        if marker in str(comment.get("body", "")):
            return {
                "url": comment.get("html_url") or comment.get("url"),
                "comment_id": comment.get("id"),
                "duplicate_suppressed": True,
                "http_status": status,
            }
    return None

def callback_body(evidence: dict, marker: str) -> str:
    return (
        f"{marker}\n"
        "## MODEL SCOUT delivery callback\n\n"
        f"- Central request: ADAMBUILD-ai/mindle-model-scout#{evidence['central_issue']}\n"
        f"- Route fingerprint: {evidence['route_fingerprint']}\n"
        f"- Model: {evidence['model_id']}\n"
        f"- Revision: {evidence['revision']}\n"
        f"- License: {evidence['license']}\n"
        f"- Input SHA-256: {evidence['input_sha256']}\n"
        f"- Output SHA-256: {evidence['output_sha256']}\n"
        f"- Exact commit: {evidence['exact_commit']}\n"
        f"- Workflow run: {evidence['workflow_run_id']}\n"
        f"- Evidence artifact: {evidence['artifact_id']}\n"
        "- Source evidence state: TESTED_PASS\n\n"
        "This callback records delivery evidence only. It does not modify AVORA geometry, semantics, provenance, architecture, main, or production."
    )

def deliver_once(evidence: dict, token: str):
    marker = marker_for(evidence["route_fingerprint"])
    existing = find_existing_callback(token, marker)
    if existing:
        return existing
    body = callback_body(evidence, marker)
    url = f"{API_ROOT}/repos/{TARGET_REPO}/issues/{TARGET_ISSUE}/comments"
    status, created = github_json("POST", url, token, {"body": body})
    callback_url = created.get("html_url") or created.get("url")
    if not callback_url:
        raise RuntimeError("callback response did not contain a URL")
    return {
        "url": callback_url,
        "comment_id": created.get("id"),
        "duplicate_suppressed": False,
        "http_status": status,
    }

def write_ledger(path: Path, evidence: dict, result: dict, rerun: dict):
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    record = {
        "state_before": "TESTED_PASS",
        "state_after": "DELIVERED",
        "route_fingerprint": evidence["route_fingerprint"],
        "callback_target": evidence["callback_target"],
        "callback_url": result["url"],
        "callback_sent_at": now,
        "delivered_at": now,
        "duplicate_count": int(bool(result["duplicate_suppressed"])) + int(bool(rerun["duplicate_suppressed"])),
        "idempotent_rerun": {
            "performed": True,
            "duplicate_suppressed": bool(rerun["duplicate_suppressed"]),
            "callback_url": rerun["url"],
        },
        "evidence": evidence,
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--artifact", default="delivery-closeout-evidence.json")
    parser.add_argument("--ledger", default="delivery-ledger.json")
    args = parser.parse_args()
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    target = str(evidence.get("callback_target") or "").strip()
    token = os.environ.get("GITHUB_TOKEN", "")
    if target != f"{TARGET_REPO}#{TARGET_ISSUE}":
        raise SystemExit("BLOCKED_CONFIG: callback target is not the fixed AVORA target")
    if not token:
        raise SystemExit("BLOCKED_CONFIG: callback token unavailable")
    try:
        first = deliver_once(evidence, token)
        time.sleep(1)
        rerun = deliver_once(evidence, token)
    except HTTPError as exc:
        raise SystemExit(f"FAILED_RETRYABLE: callback failed: HTTP {exc.code} {exc.reason}") from exc
    except (URLError, TimeoutError, RuntimeError) as exc:
        raise SystemExit(f"FAILED_RETRYABLE: callback failed: {type(exc).__name__}") from exc
    ledger = write_ledger(Path(args.ledger), evidence, first, rerun)
    artifact = {
        **ledger,
        "callback_url": first["url"],
        "idempotent_rerun": ledger["idempotent_rerun"],
        "duplicate_count": ledger["duplicate_count"],
    }
    Path(args.artifact).write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(artifact, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
