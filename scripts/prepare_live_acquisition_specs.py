from __future__ import annotations

import json
import urllib.request
from pathlib import Path


TARGETS = [
    {
        "model_id": "openai/whisper-tiny",
        "originating_requests": ["ADAMBUILD-ai/mindle-model-scout#51"],
        "consuming_teams": ["kimseobang", "mindle-media-ai"],
    },
    {
        "model_id": "BAAI/bge-small-en-v1.5",
        "originating_requests": [
            "ADAMBUILD-ai/mindle-model-scout#52",
            "ADAMBUILD-ai/mindle-model-scout#57",
        ],
        "consuming_teams": ["nas-knowledge-ai", "warren-buffett"],
    },
    {
        "model_id": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "originating_requests": [
            "ADAMBUILD-ai/mindle-model-scout#52",
            "ADAMBUILD-ai/mindle-model-scout#54",
            "ADAMBUILD-ai/mindle-model-scout#57",
        ],
        "consuming_teams": ["nas-knowledge-ai", "axiom", "warren-buffett"],
    },
]

WEIGHT_PRIORITY = ("model.safetensors", "pytorch_model.bin")


def fetch(model_id: str) -> dict:
    request = urllib.request.Request(
        f"https://huggingface.co/api/models/{model_id}",
        headers={"User-Agent": "mindle-model-scout/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise RuntimeError(f"invalid metadata payload for {model_id}")
    return payload


def license_from(payload: dict) -> str:
    for tag in payload.get("tags") or ():
        if isinstance(tag, str) and tag.startswith("license:"):
            return tag.split(":", 1)[1].casefold()
    card = payload.get("cardData") or {}
    return str(card.get("license") or "").casefold()


def select_weight(payload: dict) -> str:
    names = {str(item.get("rfilename")) for item in payload.get("siblings") or ()}
    for name in WEIGHT_PRIORITY:
        if name in names:
            return name
    raise RuntimeError("no allowlisted root weight artifact found")


def main() -> int:
    specs = []
    selection = []
    for target in TARGETS:
        payload = fetch(target["model_id"])
        revision = str(payload.get("sha") or "")
        license_id = license_from(payload)
        tags = {str(value).casefold() for value in payload.get("tags") or ()}
        if "custom_code" in tags:
            raise RuntimeError(f"remote code required: {target['model_id']}")
        weight = select_weight(payload)
        specs.append(
            {
                **target,
                "revision": revision,
                "source_url": f"https://huggingface.co/{target['model_id']}",
                "license": license_id,
                "files": [weight],
                "trust_remote_code_required": False,
            }
        )
        selection.append(
            {
                "model_id": target["model_id"],
                "revision": revision,
                "license": license_id,
                "selected_file": weight,
                "demand_signals": target["originating_requests"],
                "source": "live Hugging Face model metadata",
            }
        )
    Path("live-acquisition-specs.json").write_text(
        json.dumps(specs, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    Path("evidence/live-candidate-selection-20260923.json").write_text(
        json.dumps({"candidates": selection}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
