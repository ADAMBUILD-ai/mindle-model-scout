"""Record public Hugging Face search, license, and download-availability evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import quote

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from model_scout.scout import search_huggingface

SEARCH_STAGES = (
    ("sam_2_1", "sam2"),
    ("whisper", "whisper"),
    ("real_esrgan", "realesrgan"),
    ("matting", "BiRefNet"),
)
WEIGHT_SUFFIXES = (".onnx", ".safetensors", ".bin", ".pt", ".pth")


def download_availability(candidate: dict[str, object]) -> dict[str, object]:
    model_id = str(candidate["model_id"])
    source_url = str(candidate["source_url"])
    result = dict(candidate)
    try:
        metadata = requests.get(
            f"https://huggingface.co/api/models/{model_id}", timeout=30
        )
        metadata.raise_for_status()
        details = metadata.json()
        revision = details.get("sha")
        siblings = details.get("siblings", [])
        filename = next(
            (
                item.get("rfilename")
                for item in siblings
                if str(item.get("rfilename", "")).lower().endswith(WEIGHT_SUFFIXES)
            ),
            None,
        )
        if not revision or not filename:
            result["download_status"] = "NO_SAFE_WEIGHT_LISTED"
            return result
        resolve_url = (
            f"{source_url}/resolve/{revision}/{quote(str(filename), safe='/')}"
        )
        response = requests.get(
            resolve_url,
            headers={"Range": "bytes=0-0"},
            stream=True,
            timeout=30,
        )
        total_size = response.headers.get("Content-Range", "").partition("/")[2]
        response.close()
        result.update(
            {
                "revision": revision,
                "license": details.get("cardData", {}).get("license") or result.get("license"),
                "weight_filename": filename,
                "file_size": int(total_size) if total_size.isdigit() else None,
                "download_status": "PUBLIC_WEIGHT_RANGE_AVAILABLE"
                if response.status_code in (200, 206)
                else f"PUBLIC_RESOLVE_HTTP_{response.status_code}",
            }
        )
    except requests.RequestException as exc:
        result.update(
            {
                "download_status": "AVAILABILITY_CHECK_FAILED",
                "availability_error_type": type(exc).__name__,
            }
        )
    return result


def main() -> None:
    stages = []
    failed_stages = []
    for stage, query in SEARCH_STAGES:
        try:
            models = search_huggingface(query, limit=10, timeout=30)
            candidates = [
                download_availability(
                    {
                        "model_id": model["model_id"],
                        "license": model["license"],
                        "source_url": model["source_url"],
                    }
                )
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
