"""Record live Hugging Face search evidence without downloading weights."""

from __future__ import annotations

import json
from pathlib import Path

from src.model_scout.scout import search_huggingface


SEARCH_STAGES = (
    ("sam_2_1", "sam2"),
    ("whisper", "whisper"),
    ("real_esrgan", "Real-ESRGAN"),
    ("matting", "matting"),
)


def main() -> None:
    stages = []
    for stage, query in SEARCH_STAGES:
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
            raise RuntimeError(f"{stage} returned no candidates")
        stages.append({"stage": stage, "query": query, "candidate_count": len(models), "candidates": candidates})

    Path("model-scout-search-evidence.json").write_text(
        json.dumps({"stages": stages}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
