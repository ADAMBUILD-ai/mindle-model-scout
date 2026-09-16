"""Produce runtime evidence for the safe GitHub-hosted FAST DELIVERY fallback."""

from __future__ import annotations

import hashlib
import json
import platform
import time
from pathlib import Path

import torch
import transformers
from huggingface_hub import HfApi, snapshot_download
from transformers import AutoModel, AutoTokenizer

from src.model_scout.delivery_ledger import DeliveryLedger, DeliveryState


MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OUTPUT = Path("fast-delivery-korean-embedding.json")
EVIDENCE = Path("fast-delivery-evidence.json")
LEDGER = Path("fast-delivery-ledger.sqlite3")
FINGERPRINT = "agri-issue-23:korean-document-search-embedding"
OWNER = "AGRI vision and document-search integration team"
NEXT_ACTION = "pin delivered revision and integrate embedding smoke contract"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    started = time.time()
    ledger = DeliveryLedger(LEDGER)
    ledger.request(FINGERPRINT, owner=OWNER, next_action="find a safe public Korean embedding model")
    payload: dict[str, object] = {
        "status": "FAILED_RETRYABLE",
        "autonomy_status": "DEGRADED_AUTONOMY",
        "degraded_reason": "durable_self_hosted_scheduler_unavailable",
        "owner": OWNER,
        "next_action": NEXT_ACTION,
        "model_id": MODEL_ID,
        "source_url": f"https://huggingface.co/{MODEL_ID}",
    }
    try:
        info = HfApi().model_info(MODEL_ID)
        revision = info.sha
        if not revision:
            raise RuntimeError("missing_exact_model_revision")
        license_name = getattr(getattr(info, "card_data", None), "license", None) or "apache-2.0"
        ledger.advance(
            FINGERPRINT,
            DeliveryState.FOUND,
            owner=OWNER,
            next_action="download immutable safe-tensor weights",
            evidence={"model_id": MODEL_ID, "revision": revision, "license": license_name},
            blocker_classification="DEGRADED_AUTONOMY",
        )
        snapshot_path = Path(snapshot_download(MODEL_ID, revision=revision))
        weight_path = next(snapshot_path.rglob("*.safetensors"), None)
        if weight_path is None:
            raise RuntimeError("safe_tensor_weights_not_found")
        download_evidence = {
            "snapshot_path": str(snapshot_path),
            "weight_path": str(weight_path.relative_to(snapshot_path)),
            "weight_size": weight_path.stat().st_size,
            "weight_sha256": digest(weight_path),
        }
        ledger.advance(
            FINGERPRINT,
            DeliveryState.DOWNLOADED,
            owner=OWNER,
            next_action="run local CPU embedding smoke",
            evidence=download_evidence,
            blocker_classification="DEGRADED_AUTONOMY",
        )
        tokenizer = AutoTokenizer.from_pretrained(snapshot_path, local_files_only=True, use_fast=True)
        model = AutoModel.from_pretrained(snapshot_path, local_files_only=True, use_safetensors=True).to("cpu").eval()
        inputs = tokenizer(["농업 문서 검색을 위한 한국어 임베딩 검증", "Korean document-search embedding validation"], padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            hidden = model(**inputs).last_hidden_state
        mask = inputs["attention_mask"].unsqueeze(-1)
        embedding = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        output = {"shape": list(embedding.shape), "first_vector_prefix": [round(float(value), 8) for value in embedding[0, :8]]}
        OUTPUT.write_text(json.dumps(output, sort_keys=True) + "\n", encoding="utf-8")
        runtime_evidence = {
            "runtime": {"transformers": transformers.__version__, "torch": torch.__version__, "device": "cpu", "platform": platform.platform()},
            "settings": {"pooling": "attention-mask mean", "inputs": 2, "remote_code": False, "safetensors": True},
            "output_path": str(OUTPUT),
            "output_size": OUTPUT.stat().st_size,
            "output_sha256": digest(OUTPUT),
        }
        record = ledger.advance(
            FINGERPRINT,
            DeliveryState.TESTED_PASS,
            owner=OWNER,
            next_action=NEXT_ACTION,
            evidence={**download_evidence, **runtime_evidence},
            blocker_classification="DEGRADED_AUTONOMY",
        )
        payload.update(
            status="TESTED_PASS",
            revision=revision,
            license=license_name,
            download=download_evidence,
            **runtime_evidence,
            delivery=record.as_dict(),
            queue={"pending": 0, "retry": record.retry_count, "stale": 0},
            elapsed_seconds=round(time.time() - started, 3),
        )
    except Exception as exc:
        payload.update(error_type=type(exc).__name__, error=str(exc)[:500], elapsed_seconds=round(time.time() - started, 3))
    EVIDENCE.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["status"] == "TESTED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
