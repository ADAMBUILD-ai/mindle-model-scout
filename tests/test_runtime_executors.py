from __future__ import annotations

import json
import sys

import pytest

from src.model_scout.request_queue import normalize_request
from src.model_scout.runtime_executors import (
    LocalCommandAdapter,
    RuntimeExecutorRegistry,
    RuntimeExecutorUnavailable,
    classify_executor_kind,
    select_executable_candidate,
)


def _envelope(text: str):
    return normalize_request(project="TEST", request_text=text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("download a Hugging Face classifier", "huggingface-model"),
        ("Korean embedding and reranker", "embedding-reranker"),
        ("OCR document vision", "ocr-vision"),
        ("Korean STT and TTS", "stt-tts"),
        ("GLB geometry to SVG", "geometry-tool"),
    ],
)
def test_executor_kind_routing(text, expected):
    assert classify_executor_kind(_envelope(text)) == expected


def test_local_command_executor_captures_real_artifact_and_output(tmp_path):
    artifact = tmp_path / "weights.bin"
    artifact.write_bytes(b"real-downloaded-artifact")
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import json,sys\n"
        "source=json.load(open(sys.argv[1], encoding='utf-8'))\n"
        "json.dump({'ok': True, 'project': source['request']['project']}, open(sys.argv[2], 'w', encoding='utf-8'))\n"
        "print('runtime completed')\n",
        encoding="utf-8",
    )
    adapter = LocalCommandAdapter(
        kind="embedding-reranker",
        model_id="example/embedding",
        model_revision="abc123",
        source="huggingface:example/embedding",
        license="apache-2.0",
        command=(sys.executable, str(worker), "{input}", "{output}"),
        downloaded_files=(artifact,),
    )
    registry = RuntimeExecutorRegistry(
        {"embedding-reranker": adapter},
        work_root=tmp_path / "work",
    )

    evidence = registry(_envelope("embedding and reranker"), {"candidates": []})

    assert evidence["model_id"] == "example/embedding"
    assert evidence["downloaded_files"][0]["size"] == artifact.stat().st_size
    assert json.loads(open(evidence["output_path"], encoding="utf-8").read())["ok"] is True
    assert evidence["sha256"]
    assert evidence["validation_scope"] == "component"
    assert evidence["result"]["ok"] is True


def test_missing_executor_fails_without_false_tested_pass(tmp_path):
    registry = RuntimeExecutorRegistry({}, work_root=tmp_path)

    with pytest.raises(RuntimeExecutorUnavailable, match="ocr-vision"):
        registry(_envelope("OCR vision request"), {})


def test_selects_real_scout_candidate_only_with_revision_and_allowed_license():
    selected = select_executable_candidate({"candidates": [
        {"model_id": "bad/no-license", "revision": "abcdef123", "license": "unknown", "status": "TEST"},
        {"model_id": "good/model", "revision": "1234567890abcdef", "license": "apache-2.0", "status": "APPROVED"},
    ]})
    assert selected["model_id"] == "good/model"
    assert select_executable_candidate({"candidates": [
        {"model_id": "other/model", "revision": "a" * 40, "license": "mit", "status": "APPROVED"},
        {"model_id": "good/model", "revision": "b" * 40, "license": "mit", "status": "APPROVED"},
    ]}, "good/model")["model_id"] == "good/model"


def test_candidate_values_are_passed_to_executor_and_registry(tmp_path):
    revision = "a" * 40
    snapshot = tmp_path / "models--new--model" / "snapshots" / revision
    snapshot.mkdir(parents=True)
    (snapshot / "README.md").write_text("---\nlicense: apache-2.0\n---\n", encoding="utf-8")
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import json,pathlib,sys\n"
        "p=pathlib.Path(sys.argv[3]); p.write_bytes(b'weights')\n"
        "json.dump({'model_id':sys.argv[1],'revision':sys.argv[2],'license':'apache-2.0','_downloaded_files':[str(p),str(p.parent/'README.md')]},open(sys.argv[4],'w'))\n",
        encoding="utf-8",
    )
    adapter = LocalCommandAdapter(
        kind="huggingface-model", model_id="fallback/model", model_revision="fallback-rev",
        source="huggingface:fallback/model", license="apache-2.0",
        command=(sys.executable, str(worker), "{model_id}", "{revision}", str(snapshot / "model.safetensors"), "{output}"),
        downloaded_files=(),
    )
    from src.model_scout.acquisition import ModelRegistry
    model_registry = ModelRegistry(tmp_path / "registry.json")
    registry = RuntimeExecutorRegistry({"huggingface-model": adapter}, work_root=tmp_path / "work", model_registry=model_registry)
    scout = {"candidates": [{"model_id":"new/model","revision":revision,"license":"apache-2.0","status":"APPROVED","source_url":"https://huggingface.co/new/model"}]}
    evidence = registry(_envelope("classify text"), scout)
    assert evidence["model_id"] == "new/model"
    assert model_registry.snapshot()["models"][0]["validation_status"] == "PENDING"


def test_unrelated_site_package_cannot_be_registered_as_acquired_model(tmp_path):
    from src.model_scout.acquisition import ModelRegistry

    unrelated = tmp_path / "site-packages" / "trimesh" / "__init__.py"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("# unrelated library", encoding="utf-8")
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import json,sys\njson.dump({'revision':'4.12.2','_downloaded_files':[sys.argv[1]]},open(sys.argv[2],'w'))\n",
        encoding="utf-8",
    )
    registry_file = ModelRegistry(tmp_path / "registry.json")
    adapter = LocalCommandAdapter(
        kind="huggingface-model", model_id="fallback/model", model_revision="fallback",
        source="https://huggingface.co/fallback/model", license="mit",
        command=(sys.executable, str(worker), str(unrelated), "{output}"), downloaded_files=(),
    )
    registry = RuntimeExecutorRegistry({"huggingface-model": adapter}, work_root=tmp_path / "work", model_registry=registry_file)
    scout = {"candidates": [{"model_id": "pyannote/wespeaker-voxceleb-resnet34-LM", "revision": "b" * 40,
                             "license": "cc-by-4.0", "status": "APPROVED"}]}
    with pytest.raises(RuntimeExecutorUnavailable, match="no model weights"):
        registry(_envelope("classify text"), scout)
    assert registry_file.snapshot()["models"] == []


def test_fallback_component_does_not_create_acquisition(tmp_path):
    from src.model_scout.acquisition import ModelRegistry

    worker = tmp_path / "worker.py"
    worker.write_text("import json,sys\njson.dump({'ok':True},open(sys.argv[1],'w'))\n", encoding="utf-8")
    registry_file = ModelRegistry(tmp_path / "registry.json")
    adapter = LocalCommandAdapter(kind="geometry-tool", model_id="trimesh/trimesh", model_revision="resolved-at-runtime",
                                  source="pypi:trimesh", license="mit", command=(sys.executable, str(worker), "{output}"), downloaded_files=())
    registry = RuntimeExecutorRegistry({"geometry-tool": adapter}, work_root=tmp_path / "work", model_registry=registry_file)
    assert registry(_envelope("GLB geometry"), {"candidates": []})["selected_candidate"] is False
    assert registry_file.snapshot()["models"] == []


def test_legacy_pyannote_false_positive_is_demoted_without_deleting_evidence(tmp_path):
    from src.model_scout.acquisition import ModelRegistry

    model_registry = ModelRegistry(tmp_path / "registry.json")
    model_registry.upsert({
        "model_id": "pyannote/wespeaker-voxceleb-resnet34-LM", "revision": "4.12.2",
        "acquisition_runner": "candidate-aware-runtime-v2", "acquisition_status": "ACQUIRED_VERIFIED",
        "validation_status": "PENDING", "files": [{"path": "C:\\Python\\site-packages\\trimesh\\__init__.py", "size": 2433, "sha256": "abc"}],
        "runtime_evidence": "evidence/output.json",
    })
    RuntimeExecutorRegistry({}, work_root=tmp_path / "work", model_registry=model_registry)
    row = model_registry.snapshot()["models"][0]
    assert row["acquisition_status"] == "VERIFY_REQUIRED"
    assert row["runtime_evidence"] == "evidence/output.json"
