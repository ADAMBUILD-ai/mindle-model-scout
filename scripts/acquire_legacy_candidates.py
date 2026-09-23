from __future__ import annotations

import argparse
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from huggingface_hub import snapshot_download


CANDIDATES = (
    "peyterho/financial-roberta-large-macro-sentiment",
    "ENTUM-AI/FinBERT-Multi",
    "BAAI/bge-m3",
    "BAAI/bge-reranker-v2-m3",
    "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
    "ibm-granite/granite-timeseries-ttm-r1",
    "amazon/chronos-t5-small",
    "microsoft/table-transformer-detection",
    "Copycats/koelectra-base-v3-generalized-sentiment-analysis",
    "ibm-granite/granite-timeseries-ttm-r2",
)
ALLOWED_LICENSES = {"mit", "apache-2.0", "cc-by-4.0"}
INCLUDES = (
    "config.json", "tokenizer.json", "tokenizer_config.json",
    "special_tokens_map.json", "sentencepiece.bpe.model", "spiece.model",
    "vocab.*", "merges.txt",
    "preprocessor_config.json", "README.md", "LICENSE*", "NOTICE*",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def acquire(model_id: str, root: Path) -> dict[str, object]:
    started = time.time()
    response = requests.get(
        f"https://huggingface.co/api/models/{model_id}?blobs=true", timeout=60
    )
    response.raise_for_status()
    metadata = response.json()
    revision = metadata["sha"]
    license_name = next(
        (tag.split(":", 1)[1] for tag in metadata.get("tags", []) if tag.startswith("license:")),
        None,
    )
    if license_name not in ALLOWED_LICENSES:
        raise RuntimeError(f"license gate rejected {model_id}: {license_name}")
    sibling_names = {item["rfilename"] for item in metadata.get("siblings", [])}
    safe_weights = sorted(name for name in sibling_names if name.endswith(".safetensors"))
    bin_weights = sorted(
        name for name in sibling_names
        if name.endswith("pytorch_model.bin") or name == "pytorch_model.bin"
    )
    selected_weights = safe_weights or bin_weights
    if not selected_weights:
        raise RuntimeError(f"no safe static weight listed for {model_id}")
    local_dir = root / model_id.replace("/", "--") / revision
    snapshot_download(
        model_id,
        revision=revision,
        allow_patterns=(*INCLUDES, *selected_weights),
        local_dir=local_dir,
        max_workers=3,
    )
    files = []
    for path in sorted(local_dir.rglob("*")):
        if path.is_file() and ".cache" not in path.parts:
            files.append(
                {
                    "path": str(path.relative_to(local_dir)),
                    "size": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    weights = [
        item for item in files
        if str(item["path"]).endswith((".safetensors", "pytorch_model.bin"))
    ]
    if not weights:
        raise RuntimeError(f"no static weight acquired for {model_id}")
    return {
        "model_id": model_id,
        "revision": revision,
        "license": license_name,
        "source": f"https://huggingface.co/{model_id}/tree/{revision}",
        "files": files,
        "weight_bytes": sum(int(item["size"]) for item in weights),
        "cache_location": str(local_dir),
        "acquisition_status": "ACQUIRED_VERIFIED",
        "runtime_status": "PENDING",
        "started_at": started,
        "ended_at": time.time(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=3)
    args = parser.parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        pending = {pool.submit(acquire, item, args.cache_dir): item for item in CANDIDATES}
        for future in as_completed(pending):
            model_id = pending[future]
            try:
                result = future.result()
                print(f"ACQUIRED {model_id} {result['weight_bytes']}", flush=True)
            except Exception as exc:
                result = {"model_id": model_id, "acquisition_status": "FAILED", "error": str(exc)}
                print(f"FAILED {model_id}: {exc}", flush=True)
            results.append(result)
    payload = {
        "schema_version": "1.0",
        "generated_at": time.time(),
        "candidate_count": len(CANDIDATES),
        "results": sorted(results, key=lambda item: str(item["model_id"])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if any(item["acquisition_status"] != "ACQUIRED_VERIFIED" for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
