from __future__ import annotations

import hashlib
import json
import zipfile

import pytest

from scripts.package_verified_model import build, verify


def _fixture(tmp_path):
    revision = "a" * 40
    snapshot = tmp_path / "models--org--model" / "snapshots" / revision
    snapshot.mkdir(parents=True)
    (snapshot / "README.md").write_text("---\nlicense: mit\n---\n")
    (snapshot / "model.safetensors").write_bytes(b"real-model-weights")
    files = [{"path": str(path), "size": path.stat().st_size,
              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in snapshot.iterdir()]
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"models": [{"model_id": "org/model", "revision": revision,
        "source_url": "https://huggingface.co/org/model", "license": "mit", "files": files,
        "acquisition_status": "ACQUIRED_VERIFIED", "validation_status": "PENDING",
        "trust_remote_code_required": False}]}))
    return registry, snapshot


def test_packages_real_snapshot_and_verifies_independent_zip(tmp_path):
    registry, snapshot = _fixture(tmp_path)
    result = build(registry, "org/model", tmp_path / "handoff")
    package = tmp_path / "handoff" / result["package"]
    with zipfile.ZipFile(package) as z:
        manifest = json.loads(z.read("MODEL_HANDOFF_MANIFEST.json"))
        assert manifest["product_validation_status"] == "PENDING"
        assert z.read("snapshot/model.safetensors") == b"real-model-weights"
    downloaded = tmp_path / "downloaded.zip"
    downloaded.write_bytes(package.read_bytes())
    assert verify(downloaded, expected_sha256=result["package_sha256"])["status"] == "INDEPENDENT_DOWNLOAD_VERIFIED"
    (snapshot / "model.safetensors").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="registered file"):
        build(registry, "org/model", tmp_path / "handoff")


def test_rejects_false_acquisition_and_remote_code(tmp_path):
    registry, snapshot = _fixture(tmp_path)
    payload = json.loads(registry.read_text())
    payload["models"][0]["acquisition_status"] = "VERIFY_REQUIRED"
    registry.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="not verified"):
        build(registry, "org/model", tmp_path / "handoff")
    payload["models"][0]["acquisition_status"] = "ACQUIRED_VERIFIED"
    registry.write_text(json.dumps(payload))
    (snapshot / "modeling.py").write_text("raise RuntimeError('should never package remote code')")
    with pytest.raises(ValueError, match="unsafe snapshot file"):
        build(registry, "org/model", tmp_path / "handoff")
