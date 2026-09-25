import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _builder(tmp_path):
    # Exercise selection and binary integrity without contacting the Hub.
    hub = types.ModuleType("huggingface_hub")
    hub.HfApi = object
    hub.snapshot_download = lambda **kwargs: None
    sys.modules["huggingface_hub"] = hub
    path = Path(__file__).resolve().parents[1] / "scripts" / "build_aura_handoff_packages.py"
    spec = importlib.util.spec_from_file_location("aura_handoff_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HandoffSelectionTests(unittest.TestCase):
    def test_matrix_job_selects_only_its_model(self):
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as folder:
            builder = _builder(Path(folder))
            with patch.dict("os.environ", {"AURA_HANDOFF_ONLY": "ocr"}):
                self.assertEqual([item["key"] for item in builder.selected_candidates()], ["ocr"])
            with patch.dict("os.environ", {"AURA_HANDOFF_ONLY": "invalid"}):
                with self.assertRaisesRegex(ValueError, "unknown AURA_HANDOFF_ONLY"):
                    builder.selected_candidates()

    def test_snapshot_requires_card_binary_and_matching_hash(self):
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            builder = _builder(Path(folder))
            model = Path(folder) / "model"
            model.mkdir()
            candidate = {"required_files": {"inference.onnx": (4, builder.hashlib.sha256(b"real").hexdigest())}}
            with self.assertRaisesRegex(RuntimeError, "model card"):
                builder.verify_snapshot(model, candidate)
            (model / "README.md").write_text("Apache-2.0")
            with self.assertRaisesRegex(RuntimeError, "binary"):
                builder.verify_snapshot(model, candidate)
            (model / "inference.onnx").write_bytes(b"fake")
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                builder.verify_snapshot(model, candidate)
            (model / "inference.onnx").write_bytes(b"real")
            builder.verify_snapshot(model, candidate)
