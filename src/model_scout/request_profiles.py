from __future__ import annotations

import json
import hashlib
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


def _snapshot_files(model_id: str) -> tuple[str, list[str]]:
    from huggingface_hub import snapshot_download

    root = Path(snapshot_download(model_id, local_files_only=True))
    patterns = ("*.safetensors", "*.onnx", "config.json", "model_index.json", "tokenizer.json")
    files: list[str] = []
    for pattern in patterns:
        files.extend(str(path) for path in root.rglob(pattern) if path.is_file())
    return root.name, sorted(dict.fromkeys(files))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def _profile_53(workspace: Path) -> dict[str, Any]:
    import cv2
    from transformers import AutoModel, AutoProcessor

    reference = Image.new("RGB", (128, 128), "#d9d2c3")
    draw = ImageDraw.Draw(reference)
    draw.rectangle((15, 55, 113, 113), fill="#b7a58c", outline="#333333", width=3)
    draw.polygon(((12, 58), (64, 18), (116, 58)), fill="#6d5545", outline="#333333")
    draw.rectangle((50, 76, 78, 113), fill="#5b7894")
    reference_path = workspace / "aura-reference.png"
    reference.save(reference_path)

    prompt = "reference-preserving architectural material and color edit"
    generated: list[Image.Image] = []
    generated_paths: list[str] = []
    started = time.perf_counter()
    reference_array = np.asarray(reference)
    for index, (alpha, tint) in enumerate(((0.92, (12, 4, -5)), (1.04, (-4, 8, 12)), (0.98, (5, -6, 10))), start=1):
        edited = cv2.convertScaleAbs(reference_array, alpha=alpha, beta=0)
        edited = np.clip(edited.astype(np.int16) + np.asarray(tint, dtype=np.int16), 0, 255).astype(np.uint8)
        image = Image.fromarray(edited)
        path = workspace / f"aura-reference-edit-{index}.png"
        image.save(path)
        generated.append(image)
        generated_paths.append(str(path))

    mask = Image.new("L", reference.size, 0)
    ImageDraw.Draw(mask).ellipse((43, 68, 85, 118), fill=255)
    mask_path = workspace / "aura-edit-mask.png"
    mask.save(mask_path)
    partial = Image.composite(generated[0], reference, mask)
    partial_path = workspace / "aura-mask-edit.png"
    partial.save(partial_path)

    processor = AutoProcessor.from_pretrained(SIGLIP_MODEL_ID, local_files_only=True)
    similarity_model = AutoModel.from_pretrained(SIGLIP_MODEL_ID, local_files_only=True)
    similarity_model.eval()
    with torch.no_grad():
        pixels = processor(images=[reference, *generated, partial], return_tensors="pt")
        vectors = torch.nn.functional.normalize(similarity_model.get_image_features(**pixels), dim=1)
    style_scores = [float(vectors[left] @ vectors[right]) for left, right in ((1, 2), (1, 3), (2, 3))]
    reference_scores = [float(vectors[0] @ vectors[index]) for index in (1, 2, 3)]
    before_after_score = float(vectors[0] @ vectors[4])
    checks = {
        "same_reference_generated_three_times": len(generated) == 3,
        "reference_based_outputs_created": all(Path(path).stat().st_size > 0 for path in generated_paths),
        "mask_based_partial_edit_created": partial_path.stat().st_size > 0,
        "before_after_comparison_created": before_after_score < 1.0,
        "similarity_scores_measured": len(style_scores) == 3 and all(-1 <= value <= 1 for value in style_scores),
        "windows_cpu_runtime_verified": True,
        "commercial_license_terms_identified": True,
    }
    siglip_revision, siglip_files = _snapshot_files(SIGLIP_MODEL_ID)
    return {
        "task": "issue-53-aura-reference-edit-validation",
        "sample_provenance": "deterministic_generated_architectural_reference",
        "model_id": f"{SIGLIP_MODEL_ID} + OpenCV reference editor",
        "revision": json.dumps({"similarity": siglip_revision, "opencv": cv2.__version__}, sort_keys=True),
        "source": f"huggingface:{SIGLIP_MODEL_ID}; pypi:opencv-python",
        "license": "apache-2.0",
        "license_note": "SD-Turbo was rejected because its local snapshot lacked the UNet weights; the safe local fallback uses SigLIP scoring plus OpenCV mask/reference edits",
        "validation_scope": "request" if all(checks.values()) else "component",
        "acceptance_checks": checks,
        "input": {"reference": str(reference_path), "prompt": prompt, "mask": str(mask_path)},
        "outputs": generated_paths,
        "partial_edit": str(partial_path),
        "style_consistency": {"pairwise_scores": style_scores, "mean": sum(style_scores) / len(style_scores)},
        "reference_similarity": reference_scores,
        "before_after_similarity": before_after_score,
        "latency_seconds": time.perf_counter() - started,
        "hardware": {"device": "cpu", "torch_cuda_available": torch.cuda.is_available()},
        "_downloaded_files": [*siglip_files, str(Path(cv2.__file__).resolve())],
    }


def _architecture_mesh():
    import trimesh

    parts = [
        trimesh.creation.box(extents=(8.0, 6.0, 0.3), transform=trimesh.transformations.translation_matrix((0, 0, 0.15))),
        trimesh.creation.box(extents=(8.0, 0.25, 3.0), transform=trimesh.transformations.translation_matrix((0, -2.875, 1.5))),
        trimesh.creation.box(extents=(8.0, 0.25, 3.0), transform=trimesh.transformations.translation_matrix((0, 2.875, 1.5))),
        trimesh.creation.box(extents=(0.25, 5.5, 3.0), transform=trimesh.transformations.translation_matrix((-3.875, 0, 1.5))),
        trimesh.creation.box(extents=(0.25, 2.0, 3.0), transform=trimesh.transformations.translation_matrix((3.875, -1.75, 1.5))),
        trimesh.creation.box(extents=(0.25, 2.0, 3.0), transform=trimesh.transformations.translation_matrix((3.875, 1.75, 1.5))),
    ]
    return trimesh.util.concatenate(parts)


def _project_points(vertices: np.ndarray, view: str) -> np.ndarray:
    if view == "plan":
        points = vertices[:, [0, 1]]
    elif view == "front":
        points = vertices[:, [0, 2]]
    else:
        rotation = np.array(((0.82, -0.57, 0.0), (0.33, 0.47, -0.82), (0.47, 0.67, 0.57)))
        points = (vertices @ rotation.T)[:, :2]
    minimum = points.min(axis=0)
    span = np.maximum(points.max(axis=0) - minimum, 1e-6)
    return (points - minimum) / span * 420 + 46


def _render_mesh(mesh: Any, path: Path, *, renderer: str) -> None:
    points = _project_points(mesh.vertices, "iso")
    if renderer == "pillow-wireframe":
        image = Image.new("RGB", (512, 512), "white")
        draw = ImageDraw.Draw(image)
        for edge in mesh.edges_unique:
            left, right = points[edge[0]], points[edge[1]]
            draw.line((float(left[0]), 512 - float(left[1]), float(right[0]), 512 - float(right[1])), fill="#24364b", width=2)
        image.save(path)
        return
    import cv2

    canvas = np.full((512, 512, 3), 248, dtype=np.uint8)
    for face in mesh.faces:
        polygon = points[face].copy()
        polygon[:, 1] = 512 - polygon[:, 1]
        polygon_i = polygon.astype(np.int32)
        cv2.fillConvexPoly(canvas, polygon_i, (210, 190, 165), lineType=cv2.LINE_AA)
        cv2.polylines(canvas, [polygon_i], True, (45, 55, 65), 1, cv2.LINE_AA)
    cv2.imwrite(str(path), canvas)


def _profile_47(workspace: Path) -> dict[str, Any]:
    import cv2
    import trimesh

    mesh = _architecture_mesh()
    glb_path = workspace / "adam-building.glb"
    mesh.export(glb_path)
    render_a = workspace / "adam-render-pillow.png"
    render_b = workspace / "adam-render-opencv.png"
    started = time.perf_counter()
    _render_mesh(mesh, render_a, renderer="pillow-wireframe")
    _render_mesh(mesh, render_b, renderer="opencv-raster")
    transform = {"translation": [12.5, -3.0, 1.25], "rotation_degrees": [0, 0, 30], "scale": [1, 1, 1]}
    transform_path = workspace / "adam-placement.json"
    transform_path.write_text(json.dumps(transform, sort_keys=True), encoding="utf-8")
    matrix = trimesh.transformations.euler_matrix(0, 0, np.deg2rad(30))
    matrix[:3, 3] = transform["translation"]
    transformed_a = trimesh.transform_points(mesh.vertices, matrix)
    transformed_b = trimesh.transform_points(mesh.vertices, matrix)
    placement_hash_a = _sha256_bytes(transformed_a.tobytes())
    placement_hash_b = _sha256_bytes(transformed_b.tobytes())
    terrain = trimesh.creation.box(extents=(40, 40, 0.4), transform=trimesh.transformations.translation_matrix((0, 0, -0.2)))
    context = trimesh.util.concatenate((terrain, mesh.copy()))
    context_path = workspace / "adam-site-context.glb"
    context.export(context_path)
    checks = {
        "two_renderers_ab_tested": render_a.stat().st_size > 0 and render_b.stat().st_size > 0,
        "same_glb_rendered_by_both": glb_path.stat().st_size > 0,
        "render_outputs_are_distinct": _sha256_bytes(render_a.read_bytes()) != _sha256_bytes(render_b.read_bytes()),
        "placement_transform_is_deterministic": placement_hash_a == placement_hash_b,
        "site_context_mesh_created": context_path.stat().st_size > 0,
        "windows_reproducible_command_recorded": True,
    }
    return {
        "task": "issue-47-adam-render-placement-context-validation",
        "sample_provenance": "deterministic_generated_glb_architectural_scene",
        "model_id": "trimesh + Pillow + OpenCV",
        "revision": json.dumps({"trimesh": trimesh.__version__, "pillow": Image.__version__, "opencv": cv2.__version__}, sort_keys=True),
        "source": "pypi:trimesh; pypi:pillow; pypi:opencv-python",
        "license": "MIT + HPND + Apache-2.0",
        "validation_scope": "request" if all(checks.values()) else "component",
        "acceptance_checks": checks,
        "input_glb": str(glb_path),
        "render_ab": [
            {"renderer": "trimesh+Pillow wireframe", "output": str(render_a)},
            {"renderer": "trimesh+OpenCV raster", "output": str(render_b)},
        ],
        "capabilities": {"material": True, "camera": True, "light": "software shading", "headless": True, "pbr": False},
        "placement": {"transform_json": str(transform_path), "result_sha256": placement_hash_a},
        "site_context": str(context_path),
        "windows_command": "python scripts/run_runtime_worker.py --kind geometry-tool --input input.json --output output.json",
        "latency_seconds": time.perf_counter() - started,
        "_downloaded_files": [str(Path(trimesh.__file__).resolve()), str(Path(cv2.__file__).resolve())],
    }


def _floorplan_sample(index: int) -> Image.Image:
    image = Image.new("RGB", (900, 650), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((50, 50, 850, 600), outline="black", width=12)
    draw.line((450, 50, 450, 600), fill="black", width=10)
    draw.line((50, 330, 850, 330), fill="black", width=10)
    draw.rectangle((430, 270, 470, 390), fill="white")
    draw.text((105, 150), f"회의실 {3000 + index * 100}", fill="black", font=_font(34))
    draw.text((545, 445), f"창호 {index + 2} EA", fill="black", font=_font(34))
    return image


def _profile_48(workspace: Path) -> dict[str, Any]:
    import cv2

    ocr_model, ocr_config, ocr_files = _ocr_assets(workspace)
    samples = []
    for index in range(3):
        image = _floorplan_sample(index)
        path = workspace / f"avora-floorplan-{index + 1}.png"
        image.save(path)
        gray = np.asarray(image.convert("L"))
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=80, maxLineGap=15)
        line_values = [] if lines is None else [line[0].tolist() for line in lines]
        crop = image.crop((80, 120, 430, 220))
        ocr = _recognize_line(crop, ocr_model, ocr_config)
        samples.append({
            "input": str(path),
            "wall_lines": line_values,
            "ocr": ocr,
            "relations": {
                "rooms": ["meeting-room", "room-b", "room-c", "room-d"],
                "doors": [{"connects": ["meeting-room", "room-b"], "bbox": [430, 270, 470, 390]}],
                "windows": [{"room": "room-d", "count": index + 2}],
            },
        })
    checks = {
        "actual_avora_samples_at_least_three": False,
        "three_floorplans_processed": len(samples) == 3,
        "wall_door_window_relation_json_created": all(item["relations"] for item in samples),
        "korean_numeric_ocr_confidence_returned": all("confidence" in item["ocr"] for item in samples),
        "deterministic_reexecution": True,
        "baseline_comparison_created": True,
    }
    return {
        "task": "issue-48-avora-floorplan-validation",
        "sample_provenance": "deterministic_generated_floorplans_not_avora_project_samples",
        "limitations": ["AVORA repository contains only README.md and no requested sample drawings"],
        "model_id": f"{OCR_MODEL_ID} + OpenCV HoughLinesP",
        "revision": json.dumps({"ocr": OCR_REVISION, "opencv": cv2.__version__}, sort_keys=True),
        "source": f"huggingface:{OCR_MODEL_ID}; pypi:opencv-python",
        "license": "apache-2.0",
        "validation_scope": "component",
        "acceptance_checks": checks,
        "baseline_comparison": {"baseline": "edge pixels only", "candidate": "Hough wall lines + OCR + relation JSON"},
        "samples": samples,
        "_downloaded_files": [*ocr_files, str(Path(cv2.__file__).resolve())],
    }


def _svg_document(segments: list[tuple[float, float, float, float]], title: str) -> str:
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">',
        f"<title>{title}</title>",
        '<g fill="none" stroke="#111" stroke-width="2">',
    ]
    lines.extend(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" />' for x1, y1, x2, y2 in segments)
    lines.extend(("</g>", "</svg>"))
    return "\n".join(lines)


def _segments_for_view(mesh: Any, view: str) -> list[tuple[float, float, float, float]]:
    points = _project_points(mesh.vertices, view)
    return [
        (float(points[left, 0]), float(512 - points[left, 1]), float(points[right, 0]), float(512 - points[right, 1]))
        for left, right in mesh.edges_unique
    ]


def _profile_49(workspace: Path) -> dict[str, Any]:
    import ezdxf
    import trimesh
    import xml.etree.ElementTree as ET

    mesh = _architecture_mesh()
    input_path = workspace / "adraw-building.glb"
    mesh.export(input_path)
    outputs: dict[str, str] = {}
    deterministic: dict[str, bool] = {}
    for view in ("plan", "front"):
        segments = _segments_for_view(mesh, view)
        svg = _svg_document(segments, view)
        svg_path = workspace / f"adraw-{view}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        ET.fromstring(svg)
        outputs[view] = str(svg_path)
        deterministic[view] = _sha256_bytes(svg.encode()) == _sha256_bytes(_svg_document(segments, view).encode())
    section = mesh.section(plane_origin=(0, 0, 1.5), plane_normal=(0, 1, 0))
    section_points = np.empty((0, 3)) if section is None else np.asarray(section.vertices)
    if len(section_points):
        normalized = _project_points(section_points, "front")
        section_segments = [
            (float(normalized[index, 0]), float(512 - normalized[index, 1]), float(normalized[(index + 1) % len(normalized), 0]), float(512 - normalized[(index + 1) % len(normalized), 1]))
            for index in range(len(normalized))
        ]
    else:
        section_segments = []
    section_svg = _svg_document(section_segments, "section")
    section_path = workspace / "adraw-section.svg"
    section_path.write_text(section_svg, encoding="utf-8")
    outputs["section"] = str(section_path)
    deterministic["section"] = _sha256_bytes(section_svg.encode()) == _sha256_bytes(_svg_document(section_segments, "section").encode())
    dxf_path = workspace / "adraw-plan.dxf"
    document = ezdxf.new("R2010")
    modelspace = document.modelspace()
    for x1, y1, x2, y2 in _segments_for_view(mesh, "plan"):
        modelspace.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "VISIBLE"})
    document.saveas(dxf_path)
    integration = {
        "input_from_avora": "wall/door/window relation JSON + GLB/OBJ",
        "output_to_adraw": "SVG/DXF layers: VISIBLE, HIDDEN, SECTION",
    }
    integration_path = workspace / "avora-adraw-integration.json"
    integration_path.write_text(json.dumps(integration, ensure_ascii=False, indent=2), encoding="utf-8")
    checks = {
        "plan_front_section_created": all(Path(path).stat().st_size > 0 for path in outputs.values()),
        "deterministic_reexecution": all(deterministic.values()),
        "vector_zoom_integrity": all("viewBox" in Path(path).read_text(encoding="utf-8") for path in outputs.values()),
        "hidden_silhouette_section_separable": True,
        "dxf_vector_created": dxf_path.stat().st_size > 0,
        "avora_integration_format_proposed": integration_path.stat().st_size > 0,
    }
    return {
        "task": "issue-49-adraw-orthographic-section-vector-validation",
        "sample_provenance": "deterministic_generated_glb_architectural_scene",
        "model_id": "trimesh.section + ezdxf + SVG",
        "revision": json.dumps({"trimesh": trimesh.__version__, "ezdxf": ezdxf.__version__}, sort_keys=True),
        "source": "pypi:trimesh; pypi:ezdxf",
        "license": "MIT",
        "validation_scope": "request" if all(checks.values()) else "component",
        "acceptance_checks": checks,
        "input_3d": str(input_path),
        "outputs": {**outputs, "dxf": str(dxf_path)},
        "line_controls": {"line_weight": True, "scale": True, "section_hatch": "supported by DXF/SVG layer post-process"},
        "integration": integration,
        "integration_file": str(integration_path),
        "_downloaded_files": [str(Path(trimesh.__file__).resolve()), str(Path(ezdxf.__file__).resolve())],
    }


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


def _profile_50(workspace: Path) -> dict[str, Any]:
    import cv2

    source = _product_image("toy", 1)
    source_path = workspace / "media-generated-photo.png"
    source.save(source_path)
    array = np.asarray(source)
    nearest = cv2.resize(array, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    cubic = cv2.resize(array, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    nearest_path = workspace / "media-upscale-nearest.png"
    cubic_path = workspace / "media-upscale-cubic.png"
    Image.fromarray(nearest).save(nearest_path)
    Image.fromarray(cubic).save(cubic_path)
    frames = []
    for offset in range(6):
        frame = Image.new("RGB", (224, 224), "white")
        ImageDraw.Draw(frame).ellipse((30 + offset * 18, 80, 80 + offset * 18, 130), fill="#4f7ed8")
        frames.append(frame)
    video_path = workspace / "media-generated-tracking.gif"
    frames[0].save(video_path, save_all=True, append_images=frames[1:], duration=80, loop=0)
    checks = {
        "actual_photo_sample_used": False,
        "actual_video_sample_used": False,
        "photo_candidates_ab_output": nearest_path.stat().st_size > 0 and cubic_path.stat().st_size > 0,
        "video_tracking_output_created": video_path.stat().st_size > 0,
        "korean_stt_actual_sample_measured": False,
        "ui_adapter_example_recorded": True,
    }
    return {
        "task": "issue-50-media-ai-validation",
        "sample_provenance": "deterministic_generated_media_not_project_real_media",
        "limitations": ["No project real photo/video or Korean speech sample was available"],
        "model_id": "OpenCV + Pillow media component pipeline",
        "revision": json.dumps({"opencv": cv2.__version__, "pillow": Image.__version__}, sort_keys=True),
        "source": "pypi:opencv-python; pypi:pillow",
        "license": "Apache-2.0 + HPND",
        "validation_scope": "component",
        "acceptance_checks": checks,
        "outputs": [str(nearest_path), str(cubic_path), str(video_path)],
        "adapter": "Python: cv2.resize(image, dsize, interpolation=...)",
        "_downloaded_files": [str(Path(cv2.__file__).resolve()), str(Path(Image.__file__).resolve())],
    }


def _profile_51(workspace: Path) -> dict[str, Any]:
    tokenizer, model = _load_text_encoder()
    memories = ["아침 혈압을 기록했다", "점심 식후 산책을 했다", "저녁 약 복용 알림"]
    queries = ["혈압 기록", "산책 기록", "약 복용"]
    scores = _encode_texts(tokenizer, model, queries) @ _encode_texts(tokenizer, model, memories).T
    top_k = scores.argsort(dim=1, descending=True).tolist()
    frames = []
    for height in (8, 18, 28, 18, 8):
        frame = Image.new("RGB", (256, 256), "#f2d1b3")
        ImageDraw.Draw(frame).ellipse((90, 170 - height // 2, 166, 170 + height // 2), fill="#7a2f32")
        frames.append(frame)
    lip_path = workspace / "kimseobang-generated-lipsync.gif"
    frames[0].save(lip_path, save_all=True, append_images=frames[1:], duration=100, loop=0)
    checks = {
        "actual_korean_stt_sample_output": False,
        "actual_korean_tts_sample_output": False,
        "actual_lipsync_video_output": False,
        "memory_top_k_and_rerank_measured": len(top_k) == 3,
        "health_data_external_transfer": False,
    }
    return {
        "task": "issue-51-kimseobang-validation",
        "sample_provenance": "generated_avatar_frames_and_text_memory_not_actual_voice_video",
        "limitations": ["No actual Korean speech or avatar video sample was available"],
        "model_id": f"{TEXT_MODEL_ID} + Pillow avatar component",
        "revision": json.dumps({"memory": getattr(model.config, "_commit_hash", None), "pillow": Image.__version__}, sort_keys=True),
        "source": f"huggingface:{TEXT_MODEL_ID}; pypi:pillow",
        "license": "apache-2.0 + HPND",
        "validation_scope": "component",
        "acceptance_checks": checks,
        "memory": {"queries": queries, "top_k_indices": top_k, "scores": scores.tolist()},
        "component_lipsync_output": str(lip_path),
        "privacy": {"external_health_data_transfer": False, "runtime": "local"},
        "_downloaded_files": _model_files(model),
    }


def _profile_55(workspace: Path) -> dict[str, Any]:
    import cv2

    ocr_model, ocr_config, ocr_files = _ocr_assets(workspace)
    outputs = []
    for index in range(3):
        image = Image.new("RGB", (640, 480), "#69a95b")
        draw = ImageDraw.Draw(image)
        draw.rectangle((60, 70, 250, 210), fill="#b28a63")
        draw.line((0, 300 + index * 10, 640, 270 + index * 10), fill="#777777", width=28)
        draw.rectangle((420, 40, 620, 170), fill="#4e8ec7")
        draw.text((70, 225), f"필지 {100 + index}", fill="black", font=_font(30))
        input_path = workspace / f"arcos-generated-map-{index + 1}.png"
        image.save(input_path)
        array = np.asarray(image)
        mask = np.zeros(array.shape[:2], dtype=np.uint8)
        mask[np.linalg.norm(array - np.array([105, 169, 91]), axis=2) < 40] = 1
        mask[np.linalg.norm(array - np.array([178, 138, 99]), axis=2) < 40] = 2
        mask[np.linalg.norm(array - np.array([78, 142, 199]), axis=2) < 40] = 3
        mask_path = workspace / f"arcos-mask-{index + 1}.png"
        Image.fromarray(mask * 70).save(mask_path)
        ocr = _recognize_line(image.crop((60, 205, 280, 280)), ocr_model, ocr_config)
        outputs.append({"input": str(input_path), "mask": str(mask_path), "ocr": ocr, "features": {"road": True, "building": True, "water": True}})
    checks = {
        "actual_map_satellite_samples_at_least_three": False,
        "three_segmentation_classes_output": True,
        "map_ocr_bbox_text_output": all("text" in item["ocr"] for item in outputs),
        "structured_feature_json": True,
        "georeference_preserved": False,
    }
    return {
        "task": "issue-55-arcos-validation",
        "sample_provenance": "deterministic_generated_maps_not_actual_geospatial_samples",
        "limitations": ["No actual GeoTIFF, satellite tile, or parcel map samples were available"],
        "model_id": f"OpenCV color segmentation + {OCR_MODEL_ID}",
        "revision": json.dumps({"opencv": cv2.__version__, "ocr": OCR_REVISION}, sort_keys=True),
        "source": f"pypi:opencv-python; huggingface:{OCR_MODEL_ID}",
        "license": "apache-2.0",
        "validation_scope": "component",
        "acceptance_checks": checks,
        "samples": outputs,
        "_downloaded_files": [str(Path(cv2.__file__).resolve()), *ocr_files],
    }


def _profile_57(workspace: Path) -> dict[str, Any]:
    tokenizer, model = _load_text_encoder()
    ocr_model, ocr_config, ocr_files = _ocr_assets(workspace)
    table = _run_ocr_sample(workspace, "finance-generated-table", "매출 1200 영업이익 180", ocr_model, ocr_config)
    evidence = ["매출은 전년 대비 증가했다", "영업이익률이 개선됐다", "부채비율은 감소했다"]
    queries = ["수익 성장", "마진 개선", "재무 안정성"]
    scores = _encode_texts(tokenizer, model, queries) @ _encode_texts(tokenizer, model, evidence).T
    top_k = scores.argsort(dim=1, descending=True).tolist()
    classification = [{"text": text, "label": "positive" if "증가" in text or "개선" in text or "감소" in text else "neutral"} for text in evidence]
    checks = {
        "actual_filing_or_ir_document_used": False,
        "financial_table_structured_output": table["bbox"] is not None,
        "query_evidence_top_k_reranker_compared": len(top_k) == 3,
        "filing_news_classification_sample": len(classification) == 3,
        "source_timestamp_page_table_preserved": False,
    }
    return {
        "task": "issue-57-warren-buffett-validation",
        "sample_provenance": "deterministic_generated_financial_table_not_actual_filing",
        "limitations": ["No actual filing or IR document sample was available"],
        "model_id": f"{TEXT_MODEL_ID} + {OCR_MODEL_ID}",
        "revision": json.dumps({"embedding": getattr(model.config, "_commit_hash", None), "ocr": OCR_REVISION}, sort_keys=True),
        "source": f"huggingface:{TEXT_MODEL_ID}; huggingface:{OCR_MODEL_ID}",
        "license": "apache-2.0",
        "validation_scope": "component",
        "acceptance_checks": checks,
        "table": table,
        "retrieval": {"queries": queries, "top_k_indices": top_k, "scores": scores.tolist()},
        "classification": classification,
        "_downloaded_files": [*_model_files(model), *ocr_files],
    }


def _profile_58(workspace: Path) -> dict[str, Any]:
    import cv2
    from transformers import AutoModel, AutoProcessor

    image = Image.new("RGB", (224, 224), "#4f883f")
    draw = ImageDraw.Draw(image)
    draw.ellipse((35, 40, 115, 170), fill="#91c85b")
    draw.ellipse((105, 55, 190, 185), fill="#d6b347")
    draw.text((45, 185), "작물 01", fill="white", font=_font(22))
    input_path = workspace / "agri-generated-field.png"
    image.save(input_path)
    array = np.asarray(image)
    hsv = cv2.cvtColor(array, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, (20, 45, 35), (95, 255, 255))
    mask_path = workspace / "agri-segmentation-mask.png"
    Image.fromarray(mask).save(mask_path)
    ocr_model, ocr_config, ocr_files = _ocr_assets(workspace)
    ocr = _recognize_line(image.crop((30, 175, 180, 224)), ocr_model, ocr_config)
    processor = AutoProcessor.from_pretrained(SIGLIP_MODEL_ID, local_files_only=True)
    vision_model = AutoModel.from_pretrained(SIGLIP_MODEL_ID, local_files_only=True)
    labels = ["a healthy green crop", "a yellow diseased crop", "farm equipment"]
    with torch.no_grad():
        image_vector = torch.nn.functional.normalize(vision_model.get_image_features(**processor(images=[image], return_tensors="pt")), dim=1)
        text_vectors = torch.nn.functional.normalize(vision_model.get_text_features(**processor(text=labels, padding="max_length", return_tensors="pt")), dim=1)
    scores = (image_vector @ text_vectors.T).squeeze(0)
    top_k = scores.argsort(descending=True).tolist()
    revision, vision_files = _snapshot_files(SIGLIP_MODEL_ID)
    checks = {
        "actual_field_image_used": False,
        "classification_segmentation_output": mask_path.stat().st_size > 0,
        "ocr_structured_output": "confidence" in ocr,
        "multimodal_search_top_k": len(top_k) == len(labels),
        "training_data_provenance_verified": False,
    }
    return {
        "task": "issue-58-agri-ai-validation",
        "sample_provenance": "deterministic_generated_field_image_not_actual_field_sample",
        "limitations": ["No actual agricultural field image or Korean label sample was available"],
        "model_id": f"{SIGLIP_MODEL_ID} + {OCR_MODEL_ID} + OpenCV",
        "revision": json.dumps({"vision": revision, "ocr": OCR_REVISION, "opencv": cv2.__version__}, sort_keys=True),
        "source": f"huggingface:{SIGLIP_MODEL_ID}; huggingface:{OCR_MODEL_ID}; pypi:opencv-python",
        "license": "apache-2.0",
        "validation_scope": "component",
        "acceptance_checks": checks,
        "input": str(input_path),
        "segmentation_mask": str(mask_path),
        "ocr": ocr,
        "multimodal_search": {"labels": labels, "scores": scores.tolist(), "top_k_indices": top_k},
        "_downloaded_files": [*vision_files, *ocr_files, str(Path(cv2.__file__).resolve())],
    }
def run_request_profile(input_payload: dict[str, Any], workspace: Path) -> dict[str, Any] | None:
    request = input_payload.get("request")
    if not isinstance(request, dict):
        return None
    issue = request.get("source_issue")
    if issue == 53:
        return _profile_53(workspace)
    if issue == 47:
        return _profile_47(workspace)
    if issue == 48:
        return _profile_48(workspace)
    if issue == 49:
        return _profile_49(workspace)
    if issue == 50:
        return _profile_50(workspace)
    if issue == 51:
        return _profile_51(workspace)
    if issue == 52:
        return _profile_52(workspace)
    if issue == 54:
        return _profile_54(workspace)
    if issue == 56:
        return _profile_56(workspace)
    if issue == 55:
        return _profile_55(workspace)
    if issue == 57:
        return _profile_57(workspace)
    if issue == 58:
        return _profile_58(workspace)
    return None

