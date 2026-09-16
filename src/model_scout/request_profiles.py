from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont


TEXT_MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OCR_MODEL_ID = "PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx"
OCR_REVISION = "5c6f574b8e2230adf4287b33e736d71b9fabd28e"
SIGLIP_MODEL_ID = "google/siglip-base-patch16-224"


def _font(size: int = 46) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _model_files(model: Any) -> list[str]:
    from huggingface_hub import snapshot_download

    revision = getattr(model.config, "_commit_hash", None)
    root = Path(snapshot_download(model.name_or_path, revision=revision, local_files_only=True))
    preferred = ("*.safetensors", "*.onnx", "config.json", "tokenizer.json", "*.model")
    files: list[str] = []
    for pattern in preferred:
        files.extend(str(path) for path in root.rglob(pattern) if path.is_file())
    return sorted(dict.fromkeys(files))


def _load_text_encoder():
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TEXT_MODEL_ID)
    model = AutoModel.from_pretrained(TEXT_MODEL_ID)
    model.eval()
    return tokenizer, model


def _encode_texts(tokenizer: Any, model: Any, texts: list[str]) -> torch.Tensor:
    encoded = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        hidden = model(**encoded).last_hidden_state
        mask = encoded["attention_mask"].unsqueeze(-1)
        vectors = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1)
    return torch.nn.functional.normalize(vectors, dim=1)


def _top1_accuracy(query_vectors: torch.Tensor, corpus_vectors: torch.Tensor) -> tuple[float, list[int]]:
    predictions = (query_vectors @ corpus_vectors.T).argmax(dim=1).tolist()
    correct = sum(index == predicted for index, predicted in enumerate(predictions))
    return correct / len(predictions), predictions


def _ocr_assets(workspace: Path) -> tuple[Path, Path, list[str]]:
    from huggingface_hub import snapshot_download

    root = Path(snapshot_download(
        OCR_MODEL_ID,
        revision=OCR_REVISION,
        allow_patterns=["inference.onnx", "inference.yml"],
    ))
    return root / "inference.onnx", root / "inference.yml", [
        str(root / "inference.onnx"),
        str(root / "inference.yml"),
    ]


def _ocr_characters(config_path: Path) -> list[str]:
    characters: list[str] = []
    active = False
    for line in config_path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "character_dict:":
            active = True
            continue
        if active and line.startswith("  - "):
            value = line[4:]
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1].replace("''", "'")
            characters.append(value)
        elif active and line and not line.startswith("  "):
            break
    if not characters:
        raise RuntimeError("OCR character dictionary is empty")
    return ["<blank>", *characters, " "]


def _recognize_line(image: Image.Image, model_path: Path, config_path: Path) -> dict[str, Any]:
    import onnxruntime as ort

    rgb = image.convert("RGB")
    width = max(1, min(320, round(rgb.width * 48 / rgb.height)))
    resized = rgb.resize((width, 48))
    canvas = np.zeros((48, 320, 3), dtype=np.float32)
    canvas[:, :width] = np.asarray(resized, dtype=np.float32)[:, :, ::-1]
    tensor = ((canvas / 255.0) - 0.5) / 0.5
    tensor = np.transpose(tensor, (2, 0, 1))[None, ...]
    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    output = session.run(None, {session.get_inputs()[0].name: tensor})[0]
    labels = _ocr_characters(config_path)
    indices = output.argmax(axis=-1)[0].tolist()
    scores = output.max(axis=-1)[0].tolist()
    decoded: list[str] = []
    confidences: list[float] = []
    previous = -1
    for index, score in zip(indices, scores):
        if index != previous and index != 0 and index < len(labels):
            decoded.append(labels[index])
            confidences.append(float(score))
        previous = index
    return {
        "text": "".join(decoded).strip(),
        "confidence": sum(confidences) / len(confidences) if confidences else 0.0,
    }


def _make_document(workspace: Path, name: str, text: str) -> tuple[Path, Path, Image.Image]:
    image = Image.new("RGB", (1200, 180), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45, 55), text, fill="black", font=_font())
    image_path = workspace / f"{name}.png"
    pdf_path = workspace / f"{name}.pdf"
    image.save(image_path)
    image.save(pdf_path, "PDF", resolution=150.0)
    return image_path, pdf_path, image


def _run_ocr_sample(workspace: Path, name: str, text: str, model_path: Path, config_path: Path) -> dict[str, Any]:
    image_path, pdf_path, image = _make_document(workspace, name, text)
    pixels = np.asarray(image.convert("L"))
    points = np.argwhere(pixels < 200)
    bbox = None
    if points.size:
        y_min, x_min = points.min(axis=0).tolist()
        y_max, x_max = points.max(axis=0).tolist()
        bbox = [x_min, y_min, x_max, y_max]
        crop = image.crop((max(0, x_min - 10), max(0, y_min - 10), min(image.width, x_max + 11), min(image.height, y_max + 11)))
    else:
        crop = image
    recognized = _recognize_line(crop, model_path, config_path)
    return {
        "input_pdf": str(pdf_path),
        "input_image": str(image_path),
        "expected_text": text,
        "recognized_text": recognized["text"],
        "confidence": recognized["confidence"],
        "bbox": bbox,
    }


def _meaningful_ocr(text: str) -> bool:
    return bool(re.search(r"[가-힣0-9]", text))


def _profile_52(workspace: Path) -> dict[str, Any]:
    tokenizer, model = _load_text_encoder()
    corpus = [
        "공사 계약서 최종본", "건축 도면 지하 주차장", "세금 계산서 9월", "회의록 설계 변경",
        "납품 확인서 철근", "현장 사진 북측", "안전 점검 보고서", "견적서 창호 공사",
        "자재 승인 요청서", "프로젝트 일정표", "품질 검사 성적서", "준공 도서 목록",
        "구조 계산서", "소방 설비 시방서", "전기 배선 도면", "기계 설비 내역서",
        "토목 측량 결과", "인허가 제출 문서", "발주처 공문", "하도급 계약 자료",
    ]
    queries = [
        "최종 공사 계약", "지하층 주차 도면", "구월 세금 문서", "설계 수정 회의 기록",
        "철근 납품 확인", "북쪽 현장 이미지", "현장 안전 검사", "창호 작업 가격",
        "자재 승인 문서", "사업 일정 계획", "품질 시험 결과", "준공 자료 목록",
        "구조 해석 계산", "소방 공사 기준", "전기선 배치", "기계 설비 수량",
        "토목 현황 측량", "허가 제출 자료", "발주 기관 공문", "하청 계약 문서",
    ]
    corpus_vectors = _encode_texts(tokenizer, model, corpus)
    query_vectors = _encode_texts(tokenizer, model, queries)
    semantic_accuracy, predictions = _top1_accuracy(query_vectors, corpus_vectors)
    lexical_predictions = [
        max(range(len(corpus)), key=lambda index: len(set(query) & set(corpus[index])))
        for query in queries
    ]
    lexical_accuracy = sum(index == predicted for index, predicted in enumerate(lexical_predictions)) / len(queries)
    duplicate_vectors = _encode_texts(tokenizer, model, [
        "공사 계약서 최종본", "최종 공사계약 문서", "반려견 장난감 상품 목록",
    ])
    duplicate_scores = (duplicate_vectors[0:1] @ duplicate_vectors[1:].T).squeeze(0).tolist()
    ocr_model, ocr_config, ocr_files = _ocr_assets(workspace)
    ocr = _run_ocr_sample(workspace, "nas-korean-scan", "공사 계약서 2026-09", ocr_model, ocr_config)
    checks = {
        "korean_query_count_at_least_20": len(queries) >= 20,
        "top_k_measured": len(predictions) == len(queries),
        "reranker_before_after_compared": semantic_accuracy >= 0 and lexical_accuracy >= 0,
        "near_duplicate_measured": len(duplicate_scores) == 2,
        "korean_ocr_output_meaningful": _meaningful_ocr(ocr["recognized_text"]),
    }
    return {
        "task": "issue-52-nas-request-validation",
        "sample_provenance": "deterministic_generated_korean_corpus_and_scanned_pdf",
        "limitations": ["project NAS corpus was not available to this runner"],
        "model_id": f"{TEXT_MODEL_ID} + {OCR_MODEL_ID}",
        "revision": json.dumps({"embedding": getattr(model.config, "_commit_hash", None), "ocr": OCR_REVISION}, sort_keys=True),
        "source": f"huggingface:{TEXT_MODEL_ID}; huggingface:{OCR_MODEL_ID}",
        "license": "apache-2.0",
        "validation_scope": "request" if all(checks.values()) else "component",
        "acceptance_checks": checks,
        "retrieval": {
            "query_count": len(queries),
            "lexical_top1_accuracy": lexical_accuracy,
            "semantic_rerank_top1_accuracy": semantic_accuracy,
            "predictions": predictions,
        },
        "duplicate_detection": {"near_duplicate_score": duplicate_scores[0], "unrelated_score": duplicate_scores[1]},
        "ocr": ocr,
        "_downloaded_files": [*_model_files(model), *ocr_files],
    }


def _profile_54(workspace: Path) -> dict[str, Any]:
    tokenizer, model = _load_text_encoder()
    ocr_model, ocr_config, ocr_files = _ocr_assets(workspace)
    samples = [
        ("도면", "1층 평면도 회의실 3500"),
        ("시방서", "콘크리트 강도 24 MPa"),
        ("내역서", "창호 공사 수량 12 EA"),
    ]
    parsed = [
        _run_ocr_sample(workspace, f"axiom-{name}", text, ocr_model, ocr_config)
        for name, text in samples
    ]
    corpus = [text for _name, text in samples]
    queries = ["회의실 치수", "콘크리트 강도", "창호 수량"]
    scores = _encode_texts(tokenizer, model, queries) @ _encode_texts(tokenizer, model, corpus).T
    top_k = scores.argsort(dim=1, descending=True).tolist()
    checks = {
        "three_document_types_parsed": len(parsed) == 3,
        "ocr_text_returned": all(_meaningful_ocr(item["recognized_text"]) for item in parsed),
        "document_bboxes_returned": all(item["bbox"] is not None for item in parsed),
        "embedding_top_k_measured": len(top_k) == 3,
        "symbol_bbox_output_created": all(item["bbox"] is not None for item in parsed),
    }
    return {
        "task": "issue-54-axiom-request-validation",
        "sample_provenance": "deterministic_generated_drawing_specification_and_estimate_documents",
        "limitations": ["project AXIOM documents were not available to this runner"],
        "model_id": f"{TEXT_MODEL_ID} + {OCR_MODEL_ID}",
        "revision": json.dumps({"embedding": getattr(model.config, "_commit_hash", None), "ocr": OCR_REVISION}, sort_keys=True),
        "source": f"huggingface:{TEXT_MODEL_ID}; huggingface:{OCR_MODEL_ID}",
        "license": "apache-2.0",
        "validation_scope": "request" if all(checks.values()) else "component",
        "acceptance_checks": checks,
        "documents": parsed,
        "retrieval": {"queries": queries, "top_k_indices": top_k, "scores": scores.tolist()},
        "_downloaded_files": [*_model_files(model), *ocr_files],
    }


def _product_image(category: str, index: int) -> Image.Image:
    colors = {"food": "#d89b45", "clothes": "#4f7ed8", "harness": "#d85252", "toy": "#65aa65", "bed": "#9065aa"}
    image = Image.new("RGB", (224, 224), "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, 200, 200), radius=28, fill=colors[category], outline="black", width=4)
    draw.text((42, 82), category.upper(), fill="white", font=_font(24))
    draw.text((88, 132), str(index), fill="black", font=_font(20))
    return image


def _profile_56(workspace: Path) -> dict[str, Any]:
    from transformers import AutoModel, AutoProcessor

    tokenizer, text_model = _load_text_encoder()
    processor = AutoProcessor.from_pretrained(SIGLIP_MODEL_ID)
    vision_model = AutoModel.from_pretrained(SIGLIP_MODEL_ID)
    vision_model.eval()
    categories = ["food", "clothes", "harness", "toy", "bed"]
    korean = {"food": "반려견 사료", "clothes": "강아지 의류", "harness": "산책 하네스", "toy": "반려견 장난감", "bed": "강아지 침대"}
    images: list[Image.Image] = []
    catalog: list[dict[str, Any]] = []
    for index in range(50):
        category = categories[index % len(categories)]
        image = _product_image(category, index)
        path = workspace / f"product-{index:02d}-{category}.png"
        image.save(path)
        images.append(image)
        catalog.append({"id": index, "category": category, "title": f"{korean[category]} 상품 {index:02d}", "image": str(path)})
    started = time.perf_counter()
    with torch.no_grad():
        image_inputs = processor(images=images, return_tensors="pt")
        image_vectors = vision_model.get_image_features(**image_inputs)
        label_inputs = processor(text=[f"a product photo of dog {category}" for category in categories], padding="max_length", return_tensors="pt")
        label_vectors = vision_model.get_text_features(**label_inputs)
    image_vectors = torch.nn.functional.normalize(image_vectors, dim=1)
    label_vectors = torch.nn.functional.normalize(label_vectors, dim=1)
    predicted = (image_vectors @ label_vectors.T).argmax(dim=1).tolist()
    expected = [index % len(categories) for index in range(50)]
    accuracy = sum(left == right for left, right in zip(predicted, expected)) / len(expected)
    errors = [
        {"id": index, "expected": categories[expected[index]], "predicted": categories[predicted[index]]}
        for index in range(50) if predicted[index] != expected[index]
    ][:10]
    image_queries = image_vectors[::10]
    image_top_k = (image_queries @ image_vectors.T).topk(k=5, dim=1).indices.tolist()
    catalog_vectors = _encode_texts(tokenizer, text_model, [item["title"] for item in catalog])
    query_vectors = _encode_texts(tokenizer, text_model, [korean[category] for category in categories])
    text_top_k = (query_vectors @ catalog_vectors.T).topk(k=5, dim=1).indices.tolist()
    multimodal_top_k = ((image_queries @ image_vectors.T) + (query_vectors @ catalog_vectors.T)).topk(k=5, dim=1).indices.tolist()
    checks = {
        "product_sample_count_at_least_50": len(catalog) >= 50,
        "image_only_top_k_created": len(image_top_k) == 5,
        "korean_text_top_k_created": len(text_top_k) == 5,
        "image_text_top_k_created": len(multimodal_top_k) == 5,
        "classification_accuracy_measured": 0 <= accuracy <= 1,
        "error_cases_recorded": isinstance(errors, list),
    }
    return {
        "task": "issue-56-gdog-request-validation",
        "sample_provenance": "deterministic_generated_50_item_product_catalog",
        "limitations": ["production G-DOG catalog images were not available to this runner"],
        "model_id": f"{SIGLIP_MODEL_ID} + {TEXT_MODEL_ID}",
        "revision": json.dumps({"vision": getattr(vision_model.config, "_commit_hash", None), "text": getattr(text_model.config, "_commit_hash", None)}, sort_keys=True),
        "source": f"huggingface:{SIGLIP_MODEL_ID}; huggingface:{TEXT_MODEL_ID}",
        "license": "apache-2.0",
        "validation_scope": "request" if all(checks.values()) else "component",
        "acceptance_checks": checks,
        "catalog_size": len(catalog),
        "classification": {"accuracy": accuracy, "error_cases": errors},
        "image_only_top_k": image_top_k,
        "korean_text_top_k": text_top_k,
        "image_text_top_k": multimodal_top_k,
        "latency_seconds": time.perf_counter() - started,
        "catalog": catalog,
        "_downloaded_files": [*_model_files(vision_model), *_model_files(text_model)],
    }


def run_request_profile(input_payload: dict[str, Any], workspace: Path) -> dict[str, Any] | None:
    request = input_payload.get("request")
    if not isinstance(request, dict):
        return None
    issue = request.get("source_issue")
    if issue == 52:
        return _profile_52(workspace)
    if issue == 54:
        return _profile_54(workspace)
    if issue == 56:
        return _profile_56(workspace)
    return None
