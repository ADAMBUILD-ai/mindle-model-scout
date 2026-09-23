from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import torch


def output_hash(tensor: torch.Tensor) -> str:
    return hashlib.sha256(tensor.detach().cpu().numpy().tobytes()).hexdigest()


def validate(model_id: str, root: Path) -> dict[str, object]:
    folder = root / model_id.replace("/", "--")
    revisions = [item for item in folder.iterdir() if item.is_dir()]
    if len(revisions) != 1:
        raise RuntimeError(f"expected one revision for {model_id}, found {len(revisions)}")
    path = revisions[0]
    started = time.time()
    torch.set_grad_enabled(False)
    if "granite-timeseries-ttm" in model_id:
        from tsfm_public.models.tinytimemixer import TinyTimeMixerForPrediction

        model = TinyTimeMixerForPrediction.from_pretrained(
            path, local_files_only=True, trust_remote_code=False
        ).eval()
        output = model(past_values=torch.linspace(0, 1, 512).reshape(1, 512, 1))
        tensor = output.prediction_outputs
        kind = "time-series-forecasting"
    elif model_id == "amazon/chronos-t5-small":
        from transformers import T5ForConditionalGeneration

        model = T5ForConditionalGeneration.from_pretrained(
            path, local_files_only=True
        ).eval()
        output = model(input_ids=torch.tensor([[1, 2, 3, 4]]), decoder_input_ids=torch.tensor([[0]]))
        tensor = output.logits
        kind = "time-series-token-forecasting"
    elif model_id == "microsoft/table-transformer-detection":
        from transformers import TableTransformerForObjectDetection

        model = TableTransformerForObjectDetection.from_pretrained(
            path, local_files_only=True
        ).eval()
        output = model(pixel_values=torch.zeros(1, 3, 64, 64))
        tensor = output.logits
        kind = "table-object-detection"
    elif model_id == "BAAI/bge-m3":
        from transformers import AutoModel, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        model = AutoModel.from_pretrained(
            path, local_files_only=True, trust_remote_code=False
        ).eval()
        output = model(**tokenizer("financial evidence", return_tensors="pt"))
        tensor = output.last_hidden_state
        kind = "embedding"
    else:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(
            path, local_files_only=True, trust_remote_code=False
        ).eval()
        output = model(**tokenizer("The earnings outlook improved.", return_tensors="pt"))
        tensor = output.logits
        kind = "classification-or-reranking"
    return {
        "model_id": model_id,
        "revision": path.name,
        "runtime_status": "TESTED_PASS",
        "runtime": "CPU / torch / trust_remote_code=False",
        "task": kind,
        "output_shape": list(tensor.shape),
        "output_sha256": output_hash(tensor),
        "duration_seconds": round(time.time() - started, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.model_id, args.cache_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
