from __future__ import annotations

import sys
from types import SimpleNamespace

import numpy as np

from scripts import run_runtime_worker


def test_speech_worker_supplies_decoded_audio_without_ffmpeg(tmp_path, monkeypatch):
    received = {}

    class Recognizer:
        model = SimpleNamespace(config=SimpleNamespace(_commit_hash="a" * 40))

        def __call__(self, audio):
            received.update(audio)
            return {"text": ""}

    def pipeline(task, *, model, revision, trust_remote_code):
        assert (task, model, revision, trust_remote_code) == (
            "automatic-speech-recognition", "example/whisper", "a" * 40, False
        )
        return Recognizer()

    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(pipeline=pipeline))
    monkeypatch.setattr(run_runtime_worker, "_model_files", lambda model: ["model.safetensors"])

    result = run_runtime_worker._speech("example/whisper", tmp_path, "a" * 40)

    assert received["sampling_rate"] == 16000
    assert isinstance(received["raw"], np.ndarray)
    assert received["raw"].dtype == np.float32
    assert len(received["raw"]) == 16000
    assert (tmp_path / "speech-sample.wav").is_file()
    assert result["revision"] == "a" * 40
