from __future__ import annotations

import argparse
import json
import math
import struct
import time
import wave
from pathlib import Path


def _model_files(model) -> list[str]:
    from huggingface_hub import snapshot_download

    revision = getattr(model.config, "_commit_hash", None)
    root = Path(snapshot_download(model.name_or_path, revision=revision, local_files_only=True))
    preferred = ("*.safetensors", "*.bin", "config.json", "tokenizer.json", "*.model")
    files: list[str] = []
    for pattern in preferred:
        files.extend(str(path) for path in root.glob(pattern) if path.is_file())
    return sorted(dict.fromkeys(files))


def _embedding_reranker(model_id: str) -> dict:
    import torch
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModel.from_pretrained(model_id)
    sentences = [
        "한국어 문서 의미 검색",
        "다국어 임베딩 모델",
        "건축 도면 OCR",
        "financial filing evidence retrieval",
    ]
    encoded = tokenizer(sentences, padding=True, truncation=True, return_tensors="pt")
    started = time.perf_counter()
    with torch.no_grad():
        hidden = model(**encoded).last_hidden_state
        mask = encoded["attention_mask"].unsqueeze(-1)
        vectors = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1)
        vectors = torch.nn.functional.normalize(vectors, dim=1)
        scores = (vectors[0:1] @ vectors[1:].T).squeeze(0).tolist()
    return {
        "task": "embedding-reranker",
        "sentences": sentences,
        "dimension": int(vectors.shape[1]),
        "ranked": sorted(
            ({"text": text, "score": float(score)} for text, score in zip(sentences[1:], scores)),
            key=lambda item: item["score"],
            reverse=True,
        ),
        "latency_seconds": time.perf_counter() - started,
        "revision": getattr(model.config, "_commit_hash", None),
        "_downloaded_files": _model_files(model),
    }


def _huggingface_model(model_id: str) -> dict:
    from transformers import pipeline

    classifier = pipeline("text-classification", model=model_id)
    started = time.perf_counter()
    result = classifier("MODEL SCOUT runtime validation completed with a real model.")
    model = classifier.model
    return {
        "task": "huggingface-model",
        "prediction": result,
        "latency_seconds": time.perf_counter() - started,
        "revision": getattr(model.config, "_commit_hash", None),
        "_downloaded_files": _model_files(model),
    }


def _ocr_vision(model_id: str, workspace: Path) -> dict:
    from PIL import Image, ImageDraw
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

    sample = workspace / "ocr-sample.png"
    image = Image.new("RGB", (640, 120), "white")
    ImageDraw.Draw(image).text((30, 35), "ROOM 101  3500 mm", fill="black")
    image.save(sample)
    processor = TrOCRProcessor.from_pretrained(model_id)
    model = VisionEncoderDecoderModel.from_pretrained(model_id)
    started = time.perf_counter()
    pixels = processor(images=image, return_tensors="pt").pixel_values
    generated = model.generate(pixels, max_new_tokens=32)
    text = processor.batch_decode(generated, skip_special_tokens=True)[0]
    return {
        "task": "ocr-vision",
        "input_image": str(sample),
        "expected_text": "ROOM 101 3500 mm",
        "recognized_text": text,
        "latency_seconds": time.perf_counter() - started,
        "revision": getattr(model.config, "_commit_hash", None),
        "_downloaded_files": _model_files(model),
    }


def _speech(model_id: str, workspace: Path) -> dict:
    from transformers import pipeline

    sample = workspace / "speech-sample.wav"
    rate = 16000
    frames = [int(12000 * math.sin(2 * math.pi * 440 * index / rate)) for index in range(rate)]
    with wave.open(str(sample), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"".join(struct.pack("<h", value) for value in frames))
    recognizer = pipeline("automatic-speech-recognition", model=model_id)
    started = time.perf_counter()
    result = recognizer(str(sample))
    model = recognizer.model
    return {
        "task": "stt-tts",
        "input_audio": str(sample),
        "transcript": result.get("text", ""),
        "latency_seconds": time.perf_counter() - started,
        "revision": getattr(model.config, "_commit_hash", None),
        "_downloaded_files": _model_files(model),
    }


def _geometry(workspace: Path) -> dict:
    import trimesh

    mesh = trimesh.creation.box(extents=(4.0, 3.0, 2.0))
    glb_path = workspace / "sample-box.glb"
    mesh.export(glb_path)
    projections = {}
    for name, axes in {"plan": (0, 1), "front": (0, 2), "side": (1, 2)}.items():
        points = mesh.vertices[:, axes]
        projections[name] = {
            "min": points.min(axis=0).tolist(),
            "max": points.max(axis=0).tolist(),
        }
    section = mesh.section(plane_origin=(0, 0, 0), plane_normal=(0, 0, 1))
    return {
        "task": "geometry-tool",
        "input_glb": str(glb_path),
        "projections": projections,
        "section_vertices": 0 if section is None else len(section.vertices),
        "trimesh_version": trimesh.__version__,
        "revision": trimesh.__version__,
        "_downloaded_files": [str(Path(trimesh.__file__).resolve())],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True)
    parser.add_argument("--model-id")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    workspace = Path(args.output).resolve().parent
    if args.kind == "huggingface-model":
        result = _huggingface_model(args.model_id or "distilbert/distilbert-base-uncased-finetuned-sst-2-english")
    elif args.kind == "embedding-reranker":
        result = _embedding_reranker(args.model_id or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    elif args.kind == "ocr-vision":
        result = _ocr_vision(args.model_id or "microsoft/trocr-small-printed", workspace)
    elif args.kind == "stt-tts":
        result = _speech(args.model_id or "openai/whisper-tiny", workspace)
    elif args.kind == "geometry-tool":
        result = _geometry(workspace)
    else:
        raise SystemExit(f"unsupported runtime worker kind: {args.kind}")
    result["request_input"] = str(Path(args.input).resolve())
    result["validation_scope"] = "component"
    result["acceptance_checks"] = {"runtime_component_executed": True}
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{args.kind} completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
