"""Offline B01 executor. Reuses frozen history; never searches or invokes models."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/evidence/aura-136-final-real-analysis-delivery-20261010"
HISTORY = OUT / "history"

def read(name):
    return json.loads((HISTORY / name).read_text())

def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def main():
    directive = ROOT / "docs/commander/MODEL_SCOUT_AURA_136_FINAL_REAL_ANALYSIS_DELIVERY_DIRECTIVE_v1.0_20261010.md"
    assert directive.is_file()
    search = read("LIVE_SEARCH_FULL.json")
    rejected = read("SCOUT_136_CANDIDATE_REJECTION_TABLE.json")
    probes = read("MODEL_CANDIDATE_RESOURCE_PROBES.json")
    matrix = read("MODEL_CANDIDATE_BENCHMARK_MATRIX.json")
    run = read("RUN_38237793292_AUDIT_EXTRACT.json")
    candidates = {r["model_id"]: r for r in search["candidates"]}
    for r in rejected["records"]:
        candidates.setdefault(r["model_id"], r)
    reject_map = {r["model_id"]: r["reasons"] for r in rejected["records"]}
    probe_map = {r["modelId"]: r for r in probes["resourceProbes"]}
    p = probes["additionalQualifiedInstructCandidate"]
    probe_map[p["modelId"]] = p
    quality = {r["modelId"]: r for r in matrix["models"]}
    rows = []
    for model_id, c in sorted(candidates.items()):
        assert re.fullmatch("[0-9a-f]{40}", c["revision"])
        p = probe_map.get(model_id, {})
        q = quality.get(model_id)
        reasons = list(reject_map.get(model_id, []))
        if q:
            reasons.append("PRIOR_ARCHITECTURE_SEMANTIC_FAIL" if q["schemaCompletions"] == 10 else "PRIOR_SCHEMA_CONTENT_FAIL")
        if p.get("resourceVerdict") == "BLOCKED_SAFE_CPU_MEMORY_BUDGET":
            reasons.append("HISTORICAL_8GIB_CPU_RESOURCE_BLOCK")
        metadata = c.get("metadata_evidence", {})
        rows.append({
            "modelId": model_id,
            "immutableRevision": c["revision"],
            "licenseEvidenceState": {
                "metadataLicense": c.get("license"),
                "pinnedLicenseUrls": metadata.get("license_urls", []),
                "state": "PINNED_LICENSE_REFERENCE_PRESENT" if metadata.get("license_urls") else "MISSING_OR_NOT_APPROVED_SEE_REJECTION",
                "acquiredVersionRightsRevalidatedNow": False
            },
            "KoreanEnglishEvidenceState": {
                "historicalLanguageDocument": metadata.get("language_document"),
                "state": "PRIOR_METADATA_QUALIFIED" if metadata.get("language_document") else "NOT_REVALIDATED_SEE_PRIOR_REJECTION",
                "architecturalQuality": q["architectureSemanticGate"] if q else "NOT_BENCHMARKED"
            },
            "contextCapabilityEvidenceState": {
                "configMaxPositionEmbeddings": p.get("config", {}).get("max_position_embeddings"),
                "state": "PINNED_CONFIG_REUSED" if p.get("config") else "NOT_AVAILABLE_IN_REUSED_SUMMARY",
                "usable32768Measured": False
            },
            "weightBinaryEvidenceState": {
                "files": p.get("files", c.get("model_files", [])),
                "state": "PRIOR_CPU_EXECUTED_OFFICIAL_HASH_EVIDENCE" if q else ("PINNED_LFS_METADATA_ONLY" if p else "PRIOR_FILE_LIST_OR_UNVERIFIED"),
                "localBytesVerifiedNow": False
            },
            "priorRejectionReason": reasons,
            "realGenerativeExecutorEntry": {
                "canProceedNow": False,
                "reason": "B02_NOT_RELEASED; configured Scout executor is classifier-only; local weights/runtime not verified in this session",
                "historicalNativeGeneration": bool(q),
                "productPass": False
            },
            "historicalMetadataEvidence": metadata
        })
    input_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HISTORY.glob("*.json"))}
    write("00_REQUEST_AND_HISTORY_LOCK.json", {
        "status": "PASS_B01_LOCAL_VALIDATED_REMOTE_READBACK_REQUIRED",
        "primaryRequest": "ADAMBUILD-ai/mindle-model-scout#136",
        "executionControlOwner": "ADAMBUILD-ai/mindle-model-scout#139",
        "callback": "ADAMBUILD-ai/aura-engine#37",
        "directiveCommit": "3a7dd50b8834347e3e4fea02cca256282f9e9903",
        "directiveSha256": hashlib.sha256(directive.read_bytes()).hexdigest(),
        "historyRepository": "ADAMBUILD-ai/aura-engine",
        "historyCommit": "e8da02bd3ac47d219c614657338666b8f836e5c1",
        "historyHashes": input_hashes,
        "rootCause": "DIRECTIVE_HANDOFF_FAILURE",
        "verifiedCausalChain": [
            "#139 B01 comments do not trigger workflow: issue_comment is absent",
            "Scheduled/manual cycles run, but no directive/comment B01 consumer exists",
            "#136 remains BLOCKED_INPUT after 3 retries; latest cycle has zero eligible/results",
            "Classifier-only guard correctly blocks generative request; retrying it cannot create B01",
            "Workflow contents permission is read; no B01 commit/push step exists",
            "Actual configured discovery repositories omit central Scout and AURA"
        ],
        "auditRun": run,
        "checks": {
            "repoHealth": "READ_CLONE_PASS; archived=false; disabled=false",
            "connectedWritePermission": "GitHub permissions.push=true; actual write verified by branch publication",
            "runner": "RECENT_JOB_COMPLETED_SUCCESS_ON_SELF_HOSTED",
            "workflowConditionSkip": "NO; execution step completed success",
            "localUnpushedWork": "CURRENT_INITIAL_CHECKOUT_CLEAN; other executor disks not accessible",
            "B01Path": "LOCAL_WRITE_AND_JSON_PARSE_PASS; runner B01 path not executed",
            "directiveConsumption": "THIS_EXECUTOR_READ_AND_HASHED; legacy cycle does not read directive",
            "integrationOwner": "#139 retained; General Work directly executes B01; B02 requires Commander release"
        },
        "fix": {
            "scope": "B01 execution handoff repaired through explicit offline General Work executor",
            "command": "python scripts/run_aura_136_b01.py",
            "networkCalls": 0,
            "modelCalls": 0,
            "legacySchedulerChanged": False,
            "persistentSchedulerRepair": "NOT_CLAIMED; do not retry acquisition to execute B01",
            "nextTrigger": "Commander releases B02 only after exact remote B01 readback",
            "mainMerge": False
        },
        "B02Started": False,
        "TESTED_PASS": False,
        "DELIVERED": False
    })
    write("01_EXISTING_CANDIDATES_REUSE.json", {
        "status": "B01_EXISTING_HISTORY_REUSED",
        "broadSearchCalls": 0,
        "historicalSearchCount": search["searched_candidate_count"],
        "candidateCount": len(rows),
        "candidates": rows,
        "scope": "Union of frozen generative candidate list and rejection table; no new identities",
        "unknownEvidencePolicy": "Missing context/weight/rights evidence remains explicitly unverified",
        "B02Started": False,
        "productionPassed": 0
    })
    assert len(rows) == len(set(r["modelId"] for r in rows))
    for name in ("00_REQUEST_AND_HISTORY_LOCK.json", "01_EXISTING_CANDIDATES_REUSE.json"):
        json.loads((OUT / name).read_text())
    print(json.dumps({"status": "PASS_B01_LOCAL", "candidateCount": len(rows), "broadSearchCalls": 0}))

if __name__ == "__main__":
    main()

