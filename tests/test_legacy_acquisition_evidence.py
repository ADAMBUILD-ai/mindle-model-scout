import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_candidates_are_acquired_and_runtime_tested():
    evidence = json.loads(
        (ROOT / "evidence/legacy-scouted-model-acquisition-closeout-20260923.json")
        .read_text(encoding="utf-8")
    )
    assert evidence["result"] == "LEGACY_SCOUTED_MODEL_ACQUISITION: PASS"
    assert evidence["totals"]["legacy_models_processed"] == 10
    assert evidence["totals"]["acquired_verified"] == 10
    assert evidence["totals"]["tested_pass"] == 10
    assert evidence["totals"]["registry_total_models"] == 13
    assert len({item["model_id"] for item in evidence["models"]}) == 10
    assert all(item["acquisition_status"] == "ACQUIRED_VERIFIED" for item in evidence["models"])
    assert all(item["runtime"]["runtime_status"] == "TESTED_PASS" for item in evidence["models"])
    assert all(len(item["revision"]) == 40 for item in evidence["models"])
    assert all(len(item["runtime"]["output_sha256"]) == 64 for item in evidence["models"])


def test_rejected_candidates_have_permitted_replacements():
    evidence = json.loads(
        (ROOT / "evidence/legacy-scouted-model-acquisition-closeout-20260923.json")
        .read_text(encoding="utf-8")
    )
    rejected = {item["model_id"]: item for item in evidence["rejected"]}
    assert rejected["snunlp/KR-FinBert-SC"]["reason"] == "LICENSE_UNKNOWN"
    assert rejected["Salesforce/moirai-1.1-R-small"]["reason"] == "CC-BY-NC-4.0_NOT_PERMITTED"
    acquired = {item["model_id"] for item in evidence["models"]}
    assert {item["replacement"] for item in rejected.values()} <= acquired


def test_model_registry_contains_thirteen_acquired_models():
    registry = json.loads((ROOT / "evidence/model-registry.json").read_text(encoding="utf-8"))
    assert registry["summary"]["total_models"] == 13
    assert registry["summary"]["acquired_verified"] == 13
    assert len({item["model_id"] for item in registry["models"]}) == 13
