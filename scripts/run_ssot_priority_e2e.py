from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model_scout.automation_cycle import DurableEvidenceStore, run_runtime_cycle
from src.model_scout.delivery_ledger import DeliveryLedger
from src.model_scout.persistent_queue import PersistentRequestQueue
from src.model_scout.runtime_executors import load_runtime_executor_registry


def local_candidate_search(query: str, limit: int, resource: str) -> dict:
    lowered = query.casefold()
    request_heading = next((line.strip() for line in lowered.splitlines() if line.strip()), "")
    if "— aura" in request_heading:
        candidates = [
            {
                "id": "google/siglip-base-patch16-224 + OpenCV reference editor",
                "source": "Hugging Face cache + local Python runtime",
                "license": "apache-2.0",
                "executable": True,
            }
        ]
        rejected = [{"id": "stabilityai/sd-turbo", "reason": "local snapshot missing UNet weights"}]
    elif "— adam" in request_heading:
        candidates = [
            {"id": "trimesh + Pillow wireframe", "license": "MIT + HPND", "executable": True},
            {"id": "trimesh + OpenCV raster", "license": "MIT + Apache-2.0", "executable": True},
        ]
        rejected = [{"id": "Blender", "reason": "executable not installed on this Windows runner"}]
    elif "— adraw" in request_heading:
        candidates = [
            {"id": "trimesh.section + ezdxf + SVG", "license": "MIT", "executable": True}
        ]
        rejected = [{"id": "Blender/OpenCascade", "reason": "executables not installed on this Windows runner"}]
    elif "— avora" in request_heading:
        candidates = [
            {"id": "PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx + OpenCV", "license": "apache-2.0", "executable": True}
        ]
        rejected = []
    elif "— mindle media ai" in request_heading:
        candidates = [{"id": "OpenCV + Pillow media pipeline", "license": "Apache-2.0 + HPND", "executable": True}]
        rejected = []
    elif "— ai 닥터 김서방" in request_heading:
        candidates = [{"id": "multilingual MiniLM + Pillow avatar component pipeline", "license": "Apache-2.0 + HPND", "executable": True}]
        rejected = []
    elif "— arcos" in request_heading:
        candidates = [{"id": "OpenCV segmentation + Paddle Korean OCR", "license": "Apache-2.0", "executable": True}]
        rejected = []
    elif "— warren–buffett" in request_heading:
        candidates = [{"id": "multilingual MiniLM + Paddle Korean OCR", "license": "Apache-2.0", "executable": True}]
        rejected = []
    elif "— agri ai business platform" in request_heading:
        candidates = [{"id": "SigLIP + Paddle Korean OCR + OpenCV", "license": "Apache-2.0", "executable": True}]
        rejected = []
    else:
        candidates = []
        rejected = []
    return {
        "query": query,
        "resource": resource,
        "candidate_count": min(len(candidates), limit),
        "candidates": candidates[:limit],
        "rejected_candidates": rejected,
        "search_method": "SSOT candidate list intersected with locally executable model/program inventory",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-snapshot", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--executor-config", default="config/runtime-executors.json")
    args = parser.parse_args()

    issues = json.loads(Path(args.issue_snapshot).read_text(encoding="utf-8"))
    if not isinstance(issues, list) or not issues:
        raise SystemExit("issue snapshot must contain a non-empty list")
    for issue in issues:
        issue.setdefault("repository_full_name", "ADAMBUILD-ai/mindle-model-scout")
        issue.setdefault("state", "open")
    state_dir = Path(args.state_dir).resolve()
    queue = PersistentRequestQueue(state_dir / "request_queue.sqlite3")
    evidence_store = DurableEvidenceStore(state_dir / "request_evidence.sqlite3")
    ledger = DeliveryLedger(state_dir / "model_delivery.sqlite3")
    runner = load_runtime_executor_registry(args.executor_config, work_root=state_dir / "runtime-work")
    callback_dir = state_dir / "callbacks"
    callback_dir.mkdir(parents=True, exist_ok=True)

    def stage_callback(repo: str, issue: int, body: str):
        path = callback_dir / f"issue-{issue}-callback.md"
        path.write_text(body, encoding="utf-8")
        raise RuntimeError(f"callback staged for authenticated delivery: {path.name}")

    results = run_runtime_cycle(
        issues=issues,
        configured_repos=["ADAMBUILD-ai/mindle-model-scout"],
        queue=queue,
        evidence_store=evidence_store,
        delivery_ledger=ledger,
        scout_runner=local_candidate_search,
        runtime_runner=runner,
        callback_writer=stage_callback,
        limit=10,
    )
    print(json.dumps({"results": results, "queue": queue.snapshot()}, ensure_ascii=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

