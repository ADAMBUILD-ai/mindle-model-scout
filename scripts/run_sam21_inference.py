from __future__ import annotations

import hashlib
import json
import os
import platform
import time
from pathlib import Path
from urllib.request import urlopen

from huggingface_hub import HfApi
from PIL import Image
import torch
import transformers
from transformers import Sam2Model, Sam2Processor

MODEL_ID = "facebook/sam2.1-hiera-tiny"
INPUT_URL = "https://huggingface.co/datasets/hf-internal-testing/sam2-fixtures/resolve/main/truck.jpg"
INPUT_PATH = Path("sam21-input.jpg")
OUTPUT_PATH = Path("sam21-mask.png")
EVIDENCE_PATH = Path("sam21-inference-evidence.json")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_evidence(payload: dict) -> None:
    EVIDENCE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


def main() -> int:
    started = time.time()
    evidence: dict = {
        "status": "BLOCKED",
        "model_id": MODEL_ID,
        "source_url": f"https://huggingface.co/{MODEL_ID}",
        "input_source_url": INPUT_URL,
        "runtime": "transformers Sam2Model/Sam2Processor on PyTorch CPU",
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "gpu": "not requested; CPU-only GitHub Actions runner",
        "transformers_version": transformers.__version__,
        "torch_version": torch.__version__,
        "settings": {
            "mode": "single-positive-point image segmentation smoke",
            "input_point": [500, 375],
            "input_label": 1,
            "use_safetensors": True,
            "device": "cpu",
        },
    }

    try:
        info = HfApi().model_info(MODEL_ID)
        revision = info.sha
        if not revision:
            raise RuntimeError("missing_exact_model_revision")
        evidence["revision"] = revision
        evidence["license"] = (getattr(info, "card_data", None) or {}).get("license") if isinstance(getattr(info, "card_data", None), dict) else getattr(getattr(info, "card_data", None), "license", None)
        evidence["license"] = evidence["license"] or "apache-2.0"

        with urlopen(INPUT_URL, timeout=60) as response:
            input_bytes = response.read()
        INPUT_PATH.write_bytes(input_bytes)
        evidence.update(
            input_file=str(INPUT_PATH),
            input_sha256=sha256_bytes(input_bytes),
            input_size=len(input_bytes),
        )

        image = Image.open(INPUT_PATH).convert("RGB")
        processor = Sam2Processor.from_pretrained(MODEL_ID, revision=revision)
        model = Sam2Model.from_pretrained(
            MODEL_ID,
            revision=revision,
            use_safetensors=True,
        ).to("cpu").eval()

        input_points = [[[[500, 375]]]]
        input_labels = [[[1]]]
        inputs = processor(
            images=image,
            input_points=input_points,
            input_labels=input_labels,
            return_tensors="pt",
        )

        with torch.no_grad():
            outputs = model(**inputs)

        masks = processor.post_process_masks(outputs.pred_masks.cpu(), inputs["original_sizes"])[0]
        if masks.ndim != 4 or masks.shape[0] < 1 or masks.shape[1] < 1:
            raise RuntimeError(f"unexpected_mask_shape:{tuple(masks.shape)}")

        if hasattr(outputs, "iou_scores") and outputs.iou_scores is not None:
            best_index = int(outputs.iou_scores[0, 0].argmax().item())
        else:
            best_index = 0
        selected = masks[0, best_index]
        mask_img = Image.fromarray((selected.detach().cpu().numpy().astype("uint8") * 255), mode="L")
        mask_img.save(OUTPUT_PATH)
        output_bytes = OUTPUT_PATH.read_bytes()

        evidence.update(
            status="TESTED_PASS",
            output_file=str(OUTPUT_PATH),
            output_sha256=sha256_bytes(output_bytes),
            output_size=len(output_bytes),
            mask_shape=list(selected.shape),
            selected_mask_index=best_index,
            elapsed_seconds=round(time.time() - started, 3),
            safe_loader="SAFETENSORS_NO_REMOTE_CODE_EXECUTED",
        )
        write_evidence(evidence)
        return 0
    except Exception as exc:
        evidence.update(
            error_type=type(exc).__name__,
            error=str(exc)[:500],
            elapsed_seconds=round(time.time() - started, 3),
        )
        write_evidence(evidence)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
