"""Record live Hugging Face model-search evidence without downloading weights."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from model_scout.scout import search_huggingface


SEARCH_STAGES = (
    ("sam_2_1", "sam2"),
    ("whisper", "whisper"),
    ("real_esrgan", "realesrgan"),
    ("matting", "BiRefNet"),
)


def main() -> None:
    stages = []
    failed_stages = []

    for stage, query in SEARCH_STAGES:
        try:
            models = search_huggingface(query, limit=10, timeout=30)
            candidates = [
                {
                    "model_id": model["model_id"],
                    "license": model["license"],
                    "source_url": model["source_url"],
                    "download_status": "SOURCE_ONLY",
                }
                for model in models[:3]
            ]
            if not candidates:
                raise RuntimeError("no candidates")
            stages.append(
                {
                    "stage": stage,
                    "query": query,
                    "candidate_count": len(models),
                    "candidates": candidates,
                }
            )
        except Exception as exc:
            stages.append(
                {
                    "stage": stage,
                    "query": query,
                    "candidate_count": 0,
                    "candidates": [],
                    "error_type": type(exc).__name__,
                }
            )
            failed_stages.append(stage)

    Path("model-scout-search-evidence.json").write_text(
        json.dumps({"stages": stages}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if failed_stages:
        raise RuntimeError("live search failed for: " + ", ".join(failed_stages))


if __name__ == "__main__":
    main()
