import hashlib
import json
import os
import platform
import sys
import urllib.request
from pathlib import Path

import torch
import transformers
from huggingface_hub import model_info
from transformers import pipeline

MODEL_ID = "facebook/sam2.1-hiera-tiny"
INPUT_URL = "https://huggingface.co/datasets/hf-internal-testing/sam2-fixtures/resolve/main/truck.jpg"
INPUT_PATH = Path("sam21-input.jpg")
OUTPUT_PATH = Path("sam21-mask.png")
EVIDENCE_PATH = Path("sam21-inference-evidence.json")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cpu_name():
    if Path("/proc/cpuinfo").exists():
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


evidence = {
    "status": "BLOCKED",
    "model_id": MODEL_ID,
    "license": "apache-2.0",
    "source_url": f"https://huggingface.co/{MODEL_ID}",
    "input_source_url": INPUT_URL,
    "runtime": f"transformers@{transformers.__version__}; torch@{torch.__version__}; CPU",
    "platform": sys.platform,
    "architecture": platform.machine(),
    "cpu": cpu_name(),
    "cpu_count": os.cpu_count(),
    "gpu": "not requested; CPU-only GitHub Actions runner",
    "inference_backend": "Transformers Python CPU fallback; the downloaded SAM 2.1 ONNX graph remains separately verified",
}
try:
    revision = model_info(MODEL_ID).sha
    evidence["revision"] = revision
    with urllib.request.urlopen(INPUT_URL, timeout=60) as response:
        INPUT_PATH.write_bytes(response.read())
    evidence["input_file"] = str(INPUT_PATH)
    evidence["input_sha256"] = digest(INPUT_PATH)
    evidence["input_size"] = INPUT_PATH.stat().st_size
    generator = pipeline("mask-generation", model=MODEL_ID, revision=revision, device=-1)
    result = generator(str(INPUT_PATH), points_per_batch=16)
    masks = result["masks"]
    if not masks:
        raise RuntimeError("mask_output_unavailable")
    masks[0].save(OUTPUT_PATH)
    evidence.update({
        "status": "TESTED_PASS",
        "mask_count": len(masks),
        "output_file": str(OUTPUT_PATH),
        "output_sha256": digest(OUTPUT_PATH),
        "output_size": OUTPUT_PATH.stat().st_size,
    })
except Exception as error:
    evidence["error_type"] = type(error).__name__
    evidence["error"] = str(error)[:240]
EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps(evidence))
raise SystemExit(0 if evidence["status"] == "TESTED_PASS" else 1)
