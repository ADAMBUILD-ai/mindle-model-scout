"""Emit evidence for the required live Hugging Face model-search sequence."""

from __future__ import annotations

import json
from pathlib import Path

from src.model_scout.report import build_report
from src.model_scout.scout import scout


SEARCH_STAGES = (
    ("sam_2_1", "sam2"),
    ("whisper", "whisper"),
    ("real_esrgan", "Real-ESRGAN"),
    ("matting", "matting"),
)


def main() -> None:
    stages = []
    for stage, query in SEARCH_STAGES:
        result = scout(query, limit=10)
        report = build_report(result, top_n=3)
        comparison = report["comparison"]
        if not comparison:
            raise RuntimeError(f"{stage} returned no candidates")
        stages.append({"stage": stage, "query": query, "candidate_count": result["candidate_count"], "candidates": comparison})

    Path("model-scout-search-evidence.json").write_text(
        json.dumps({"stages": stages}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
