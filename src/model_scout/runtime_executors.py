from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .request_queue import RequestEnvelope


EXECUTOR_KINDS = (
    "huggingface-model",
    "embedding-reranker",
    "ocr-vision",
    "stt-tts",
    "geometry-tool",
)


class RuntimeExecutorUnavailable(RuntimeError):
    pass


def classify_executor_kind(envelope: RequestEnvelope) -> str:
    text = f"{envelope.project} {envelope.request_text}".casefold()
    if any(value in text for value in ("embedding", "rerank", "임베딩", "리랭")):
        return "embedding-reranker"
    if any(value in text for value in ("ocr", "vision", "image", "이미지", "도면", "비전")):
        return "ocr-vision"
    if any(value in text for value in ("stt", "tts", "speech", "whisper", "음성")):
        return "stt-tts"
    if any(value in text for value in ("geometry", "cad", "mesh", "glb", "gltf", "dxf", "svg", "3d", "2d")):
        return "geometry-tool"
    return "huggingface-model"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class LocalCommandAdapter:
    kind: str
    model_id: str
    model_revision: str
    source: str
    license: str
    command: tuple[str, ...]
    downloaded_files: tuple[Path, ...]
    timeout_seconds: float = 900.0

    def __post_init__(self) -> None:
        if self.kind not in EXECUTOR_KINDS:
            raise ValueError(f"unsupported executor kind: {self.kind}")
        if not self.command:
            raise ValueError("executor command is required")
        if self.timeout_seconds <= 0:
            raise ValueError("executor timeout must be positive")

    def run(
        self,
        envelope: RequestEnvelope,
        scout_result: Mapping[str, Any],
        *,
        work_root: Path,
    ) -> dict[str, Any]:
        workspace = work_root / envelope.fingerprint
        workspace.mkdir(parents=True, exist_ok=True)
        input_path = workspace / "input.json"
        output_path = workspace / "output.json"
        input_payload = {
            "request": envelope.as_dict(),
            "scout_result": dict(scout_result),
        }
        input_path.write_text(
            json.dumps(input_payload, ensure_ascii=False, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )

        placeholders = {
            "input": str(input_path),
            "output": str(output_path),
            "workspace": str(workspace),
            "python": sys.executable,
            "package_root": str(Path(__file__).resolve().parents[2]),
        }
        command = [part.format_map(placeholders) for part in self.command]
        completed = subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
            shell=False,
            env=os.environ.copy(),
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip()[-2000:]
            raise RuntimeError(f"executor exited {completed.returncode}: {stderr}")
        if not output_path.is_file() or output_path.stat().st_size <= 0:
            raise RuntimeError("executor did not create a non-empty output file")

        reported_downloads: tuple[Path, ...] = ()
        output_payload: Mapping[str, Any] = {}
        try:
            output_payload = json.loads(output_path.read_text(encoding="utf-8"))
            if isinstance(output_payload, Mapping):
                values = output_payload.get("_downloaded_files", ())
                if isinstance(values, list):
                    reported_downloads = tuple(Path(str(value)) for value in values)
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass

        downloads = []
        for raw_path in (*self.downloaded_files, *reported_downloads):
            path = raw_path.resolve()
            if not path.is_file() or path.stat().st_size <= 0:
                raise RuntimeError(f"downloaded artifact is missing or empty: {path}")
            downloads.append({
                "path": str(path),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            })

        return {
            "model_id": str(output_payload.get("model_id") or self.model_id),
            "model_revision": str(output_payload.get("revision") or self.model_revision),
            "source": str(output_payload.get("source") or self.source),
            "validation_scope": str(output_payload.get("validation_scope") or "component"),
            "acceptance_checks": dict(output_payload.get("acceptance_checks") or {}),
            "license": str(output_payload.get("license") or self.license),
            "input": str(input_path),
            "output_path": str(output_path),
            "output_size": output_path.stat().st_size,
            "sha256": _sha256(output_path),
            "downloaded_files": downloads,
            "settings": {
                "executor_kind": self.kind,
                "command": command,
                "timeout_seconds": self.timeout_seconds,
            },
            "runtime": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "returncode": completed.returncode,
            },
            "hardware": {
                "machine": platform.machine(),
                "processor": platform.processor() or "unknown",
            },
            "log": (completed.stdout.strip() or "executor completed successfully")[-4000:],
            "result": {
                key: value
                for key, value in output_payload.items()
                if key != "_downloaded_files"
            },
        }


class RuntimeExecutorRegistry:
    def __init__(self, adapters: Mapping[str, LocalCommandAdapter], *, work_root: str | Path):
        self.adapters = dict(adapters)
        self.work_root = Path(work_root)

    def __call__(
        self,
        envelope: RequestEnvelope,
        scout_result: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        kind = classify_executor_kind(envelope)
        adapter = self.adapters.get(kind)
        if adapter is None:
            raise RuntimeExecutorUnavailable(f"no configured local executor for {kind}")
        return adapter.run(envelope, scout_result, work_root=self.work_root)


def load_runtime_executor_registry(
    config_path: str | Path | None,
    *,
    work_root: str | Path,
) -> RuntimeExecutorRegistry:
    if config_path is None:
        return RuntimeExecutorRegistry({}, work_root=work_root)
    path = Path(config_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("runtime executor config must be a mapping")
    adapters: dict[str, LocalCommandAdapter] = {}
    for kind, raw in payload.items():
        if not isinstance(raw, Mapping):
            raise ValueError(f"executor config for {kind} must be a mapping")
        downloads = tuple(
            (path.parent / str(value)).resolve()
            for value in raw.get("downloaded_files", ())
        )
        adapters[str(kind)] = LocalCommandAdapter(
            kind=str(kind),
            model_id=str(raw.get("model_id") or ""),
            model_revision=str(raw.get("model_revision") or ""),
            source=str(raw.get("source") or ""),
            license=str(raw.get("license") or ""),
            command=tuple(str(value) for value in raw.get("command", ())),
            downloaded_files=downloads,
            timeout_seconds=float(raw.get("timeout_seconds", 900)),
        )
    return RuntimeExecutorRegistry(adapters, work_root=work_root)
