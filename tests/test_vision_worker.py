from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

pytest.importorskip("torch")
from scripts import run_runtime_worker


def test_vision_worker_uses_builtin_cpu_pipeline_without_remote_code(tmp_path, monkeypatch):
    calls = []

    class Worker:
        model = SimpleNamespace(config=SimpleNamespace(_commit_hash="a" * 40))

        def __call__(self, image):
            calls.append(image)
            return [{"generated_text": "ROOM 101"}]

    def pipeline(task, *, model, revision, trust_remote_code, device):
        assert (task, model, revision, trust_remote_code, device) == (
            "image-to-text", "example/vision", "a" * 40, False, -1
        )
        return Worker()

    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(pipeline=pipeline))
    monkeypatch.setattr(run_runtime_worker, "_model_files", lambda model: ["model.safetensors"])
    result = run_runtime_worker._vision_understanding("example/vision", tmp_path, "a" * 40, "image-to-text")
    assert result["prediction"] == [{"generated_text": "ROOM 101"}]
    assert result["revision"] == "a" * 40
    assert len(calls) == 1
    assert (tmp_path / "vision-sample.png").is_file()


def test_vision_worker_rejects_unsupported_model_family_before_loading(tmp_path):
    with pytest.raises(ValueError, match="no safe built-in vision adapter"):
        run_runtime_worker._vision_understanding("example/unsupported", tmp_path, "a" * 40, "image-text-to-text")
