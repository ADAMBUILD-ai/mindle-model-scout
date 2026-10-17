from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import time
import wave
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model_scout.request_profiles import run_request_profile
from src.model_scout.runtime_samples import _embedding_sample_sentences
from src.model_scout.aura136_contract import ANALYSIS_FIELDS, real_sources, sha256_text, validate_source_citations


def _model_files(model) -> list[str]:
    from huggingface_hub import snapshot_download

    revision = getattr(model.config, "_commit_hash", None)
    root = Path(snapshot_download(model.name_or_path, revision=revision, local_files_only=True))
    preferred = ("*.safetensors", "*.bin", "config.json", "tokenizer.json", "*.model")
    files: list[str] = []
    for pattern in preferred:
        files.extend(str(path) for path in root.glob(pattern) if path.is_file())
    return sorted(dict.fromkeys(files))


def _license_snapshot_files(model_id: str, revision: str | None) -> list[str]:
    """Persist model-card/license evidence at the same immutable revision."""

    from huggingface_hub import hf_hub_download

    files: list[str] = []
    for name in ("README.md", "LICENSE", "LICENSE.txt", "NOTICE", "NOTICE.txt"):
        try:
            files.append(hf_hub_download(model_id, name, revision=revision))
        except Exception:
            continue
    if not files:
        raise RuntimeError("exact-revision model card or license evidence is unavailable")
    return sorted(dict.fromkeys(files))


def _embedding_reranker(model_id: str, revision: str | None = None, *, request: dict | None = None) -> dict:
    import torch
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, trust_remote_code=False)
    model = AutoModel.from_pretrained(model_id, revision=revision, trust_remote_code=False)
    sentences = _embedding_sample_sentences(request or {})
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
        "sample_provenance": "deterministic_generated_component_probe_not_actual_product_input",
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


def _huggingface_model(model_id: str, revision: str | None = None) -> dict:
    from transformers import pipeline

    classifier = pipeline("text-classification", model=model_id, revision=revision, trust_remote_code=False)
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


def _generative_text(model_id: str, revision: str, input_payload: dict) -> dict:
    """Run source-bound causal generation; never accepts a synthetic benchmark."""
    sources = real_sources(input_payload)
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, trust_remote_code=False)
    source_tokens = {
        source["source_id"]: len(tokenizer.encode(source["verifiedContent"], add_special_tokens=False))
        for source in sources
    }
    undersized = {source_id: count for source_id, count in source_tokens.items() if count < 1000}
    if undersized:
        raise RuntimeError(
            "AURA_136_REAL_BENCHMARK_INPUT_INCOMPLETE: each source requires >=1000 tokens; "
            f"undersized={undersized}"
        )
    corpus = "\n\n".join(
        f"[SOURCE {source['source_id']}]\n{source['verifiedContent']}" for source in sources
    )
    schema = ", ".join(ANALYSIS_FIELDS)
    prompt = (
        "Return JSON only. Analyze the verified Korean and global architectural sources below. "
        "Every inferential claim must cite only source_id values supplied below. "
        f"Required top-level fields: {schema}.\n\n{corpus}"
    )
    encoded = tokenizer(prompt, return_tensors="pt", truncation=False)
    context_limit = int(getattr(model.config, "max_position_embeddings", 0) or 0)
    if context_limit < 32768:
        raise RuntimeError(f"AURA_136_RUNTIME_EXECUTOR_NOT_AVAILABLE: model context={context_limit}, require >=32768")
    input_tokens = int(encoded["input_ids"].shape[-1])
    output_budget = 2048
    if input_tokens + output_budget > context_limit:
        raise RuntimeError(
            f"AURA_136_REAL_BENCHMARK_INPUT_INCOMPLETE: context overflow input={input_tokens} output_budget={output_budget} limit={context_limit}; no silent truncation"
        )
    started = time.perf_counter()
    with torch.no_grad():
        generated = model.generate(**encoded, max_new_tokens=output_budget, do_sample=False, pad_token_id=tokenizer.eos_token_id)
    output = tokenizer.decode(generated[0][input_tokens:], skip_special_tokens=True).strip()
    try:
        analysis = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"AURA_136_MODEL_QUALITY_FAILED: malformed JSON: {exc.msg}") from exc
    missing = [name for name in ANALYSIS_FIELDS if name not in analysis]
    if missing:
        raise RuntimeError(f"AURA_136_MODEL_QUALITY_FAILED: missing output fields={missing}")
    allowed_ids = {source["source_id"] for source in sources}
    cited_ids = validate_source_citations(analysis, allowed_ids)
    return {
        "task": "generative-text",
        "providerId": "transformers-local-cpu",
        "invocationId": str(uuid.uuid4()),
        "analysis": analysis,
        "prompt_sha256": sha256_text(prompt),
        "output_sha256": sha256_text(output),
        "input_tokens": input_tokens,
        "output_tokens": int(generated.shape[-1] - input_tokens),
        "truncation": {"occurred": False, "reason": "input+output budget verified before generation"},
        "wait_ms": round((time.perf_counter() - started) * 1000),
        "source_ids": sorted(allowed_ids),
        "source_token_counts": source_tokens,
        "cited_source_ids": sorted(cited_ids),
        "zero_invented_source_ids": True,
        "revision": getattr(model.config, "_commit_hash", None),
        "_downloaded_files": _model_files(model),
    }


def _ocr_vision(model_id: str, workspace: Path, revision: str | None = None) -> dict:
    from PIL import Image, ImageDraw
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

    sample = workspace / "ocr-sample.png"
    image = Image.new("RGB", (640, 120), "white")
    ImageDraw.Draw(image).text((30, 35), "ROOM 101  3500 mm", fill="black")
    image.save(sample)
    processor = TrOCRProcessor.from_pretrained(model_id, revision=revision, trust_remote_code=False)
    model = VisionEncoderDecoderModel.from_pretrained(model_id, revision=revision, trust_remote_code=False)
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


def _vision_understanding(model_id: str, workspace: Path, revision: str, pipeline_tag: str) -> dict:
    """Use a built-in Transformers task for visual candidates, without remote code."""
    supported = {"image-to-text", "visual-question-answering", "document-question-answering"}
    if pipeline_tag not in supported:
        raise ValueError(f"no safe built-in vision adapter for pipeline tag: {pipeline_tag}")
    from PIL import Image, ImageDraw
    from transformers import pipeline
    sample = workspace / "vision-sample.png"
    image = Image.new("RGB", (640, 160), "white")
    ImageDraw.Draw(image).text((30, 35), "ROOM 101  3500 mm", fill="black")
    image.save(sample)
    worker = pipeline(pipeline_tag, model=model_id, revision=revision, trust_remote_code=False, device=-1)
    started = time.perf_counter()
    if pipeline_tag == "image-to-text":
        output = worker(image)
    else:
        output = worker(image=image, question="What does the drawing say?")
    return {
        "task": pipeline_tag,
        "input_image": str(sample),
        "prediction": output,
        "latency_seconds": time.perf_counter() - started,
        "revision": getattr(worker.model.config, "_commit_hash", None),
        "_downloaded_files": _model_files(worker.model),
    }


def _speech(model_id: str, workspace: Path, revision: str | None = None) -> dict:
    import numpy as np
    from transformers import pipeline

    sample = workspace / "speech-sample.wav"
    rate = 16000
    frames = [int(12000 * math.sin(2 * math.pi * 440 * index / rate)) for index in range(rate)]
    with wave.open(str(sample), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"".join(struct.pack("<h", value) for value in frames))
    recognizer = pipeline("automatic-speech-recognition", model=model_id, revision=revision, trust_remote_code=False)
    started = time.perf_counter()
    # Supply decoded PCM samples: the Windows service does not install ffmpeg.
    audio = np.asarray(frames, dtype=np.float32) / 32768.0
    result = recognizer({"raw": audio, "sampling_rate": rate})
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
    parser.add_argument("--revision")
    parser.add_argument("--pipeline-tag", default="")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    workspace = Path(args.output).resolve().parent
    input_payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = None if args.model_id else run_request_profile(input_payload, workspace)
    if result is not None:
        pass
    elif args.kind == "huggingface-model":
        result = _huggingface_model(args.model_id or "distilbert/distilbert-base-uncased-finetuned-sst-2-english", args.revision)
    elif args.kind == "generative-text":
        result = _generative_text(args.model_id, args.revision, input_payload)
    elif args.kind == "embedding-reranker":
        result = _embedding_reranker(args.model_id or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", args.revision,
                                     request=input_payload.get("request") if isinstance(input_payload.get("request"), dict) else {})
    elif args.kind == "ocr-vision":
        if "trocr" in (args.model_id or "microsoft/trocr-small-printed").casefold():
            result = _ocr_vision(args.model_id or "microsoft/trocr-small-printed", workspace, args.revision)
        else:
            result = _vision_understanding(args.model_id, workspace, args.revision, args.pipeline_tag)
    elif args.kind == "stt-tts":
        result = _speech(args.model_id or "openai/whisper-tiny", workspace, args.revision)
    elif args.kind == "geometry-tool":
        result = _geometry(workspace)
    else:
        raise SystemExit(f"unsupported runtime worker kind: {args.kind}")
    if args.model_id:
        snapshots = _license_snapshot_files(args.model_id, args.revision)
        result["_downloaded_files"] = sorted(dict.fromkeys([*result.get("_downloaded_files", []), *snapshots]))
        result["license_evidence_files"] = snapshots
    result["request_input"] = str(Path(args.input).resolve())
    result.setdefault("validation_scope", "component")
    result.setdefault("acceptance_checks", {"runtime_component_executed": True})
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{args.kind} completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
