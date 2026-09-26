from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


SAFE_EXTENSIONS = {".safetensors", ".onnx", ".json", ".txt", ".model", ".bin"}
ALLOWED_LICENSES = {
    "apache-2.0", "mit", "bsd", "bsd-2-clause", "bsd-3-clause", "isc",
    "cc-by-4.0", "cc0-1.0", "mpl-2.0",
}


class AcquisitionRejected(RuntimeError):
    pass


@dataclass(frozen=True)
class AcquisitionSpec:
    model_id: str
    revision: str
    source_url: str
    license: str
    files: tuple[str, ...]
    trust_remote_code_required: bool = False
    originating_requests: tuple[str, ...] = ()
    consuming_teams: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AcquisitionSpec":
        return cls(
            model_id=str(value.get("model_id") or "").strip(),
            revision=str(value.get("revision") or "").strip(),
            source_url=str(value.get("source_url") or "").strip(),
            license=str(value.get("license") or "").strip().casefold(),
            files=tuple(str(item).strip() for item in value.get("files", ()) if str(item).strip()),
            trust_remote_code_required=bool(value.get("trust_remote_code_required", False)),
            originating_requests=tuple(str(item) for item in value.get("originating_requests", ())),
            consuming_teams=tuple(str(item) for item in value.get("consuming_teams", ())),
        )

    def validate(self) -> None:
        if not self.model_id or "/" not in self.model_id:
            raise AcquisitionRejected("model_id must be an explicit owner/name")
        if not self.revision or len(self.revision) < 7:
            raise AcquisitionRejected("an immutable exact revision is required")
        if self.license not in ALLOWED_LICENSES:
            raise AcquisitionRejected(f"license is not approved: {self.license or 'unknown'}")
        if self.trust_remote_code_required:
            raise AcquisitionRejected("unreviewed remote code is forbidden")
        if not self.files:
            raise AcquisitionRejected("at least one explicit artifact file is required")
        for name in self.files:
            if Path(name).suffix.casefold() not in SAFE_EXTENSIONS:
                raise AcquisitionRejected(f"artifact type is not allowlisted: {name}")
            if ".." in Path(name).parts or Path(name).is_absolute():
                raise AcquisitionRejected(f"unsafe artifact path: {name}")


class ModelRegistry:
    """Atomic, deterministic export of acquired assets with duplicate suppression."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        if not self.path.exists():
            self._write({"schema_version": 1, "models": []})

    def _read(self) -> dict[str, Any]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") not in {1, 2} or not isinstance(payload.get("models"), list):
            raise ValueError("invalid model registry")
        return payload

    def _write(self, payload: Mapping[str, Any]) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            temp = Path(handle.name)
        os.replace(temp, self.path)

    def key_exists(self, model_id: str, revision: str) -> bool:
        with self._lock:
            return any(row["model_id"] == model_id and row["revision"] == revision for row in self._read()["models"])

    def upsert(self, record: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
        with self._lock:
            payload = self._read(); rows = payload["models"]
            key = (record["model_id"], record["revision"])
            for row in rows:
                if (row["model_id"], row["revision"]) == key:
                    if row.get("acquisition_status") == record.get("acquisition_status") == "ACQUIRED_VERIFIED":
                        changed = False
                        for field in ("originating_requests", "consuming_teams"):
                            merged = list(dict.fromkeys([*(row.get(field) or []), *(record.get(field) or [])]))
                            if merged != (row.get(field) or []):
                                row[field] = merged
                                changed = True
                        if changed:
                            self._write(payload)
                    return dict(row), False
            rows.append(dict(record)); rows.sort(key=lambda row: (row["model_id"], row["revision"]))
            self._write(payload)
            return dict(record), True

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._read()

    def mark_validation(self, model_id: str, revision: str, *, status: str, evidence: str) -> dict[str, Any]:
        with self._lock:
            payload = self._read()
            for row in payload["models"]:
                if row.get("model_id") == model_id and row.get("revision") == revision:
                    row["validation_status"] = status
                    row["runtime_evidence"] = evidence
                    self._write(payload)
                    return dict(row)
        raise KeyError((model_id, revision))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class AcquisitionRunner:
    def __init__(self, *, cache_root: str | Path, registry: ModelRegistry, timeout: float = 900):
        self.cache_root = Path(cache_root); self.cache_root.mkdir(parents=True, exist_ok=True)
        self.registry = registry; self.timeout = timeout
        self._keys: set[tuple[str, str]] = set(); self._keys_lock = threading.Lock()

    def acquire(self, spec: AcquisitionSpec) -> dict[str, Any]:
        started = time.time(); spec.validate(); key = (spec.model_id, spec.revision)
        with self._keys_lock:
            if key in self._keys or self.registry.key_exists(*key):
                return {"model_id": spec.model_id, "revision": spec.revision, "status": "DUPLICATE_SUPPRESSED", "started_at": started, "ended_at": time.time()}
            self._keys.add(key)
        try:
            root = self.cache_root / spec.model_id.replace("/", "--") / spec.revision
            root.mkdir(parents=True, exist_ok=True); artifacts = []
            for name in spec.files:
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
                if not target.is_file() or target.stat().st_size == 0:
                    url = f"https://huggingface.co/{spec.model_id}/resolve/{spec.revision}/{name}"
                    request = urllib.request.Request(url, headers={"User-Agent": "mindle-model-scout/1.0"})
                    with urllib.request.urlopen(request, timeout=self.timeout) as response, tempfile.NamedTemporaryFile("wb", dir=target.parent, delete=False) as handle:
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk: break
                            handle.write(chunk)
                        temp = Path(handle.name)
                    if temp.stat().st_size == 0: raise RuntimeError(f"empty artifact: {name}")
                    os.replace(temp, target)
                artifacts.append({"path": name, "size": target.stat().st_size, "sha256": _sha256(target)})
            ended = time.time()
            record = {**asdict(spec), "files": artifacts, "acquired_at": ended, "started_at": started, "ended_at": ended, "duration_seconds": round(ended-started, 3), "cache_location": str(root), "acquisition_runner": "safe-http-v1", "acquisition_status": "ACQUIRED_VERIFIED", "validation_status": "PENDING"}
            stored, created = self.registry.upsert(record)
            return {**stored, "created": created, "status": "ACQUIRED_VERIFIED"}
        finally:
            with self._keys_lock: self._keys.discard(key)

    def acquire_many(self, specs: Iterable[AcquisitionSpec], *, concurrency: int = 3) -> list[dict[str, Any]]:
        if concurrency < 1 or concurrency > 4: raise ValueError("concurrency must be between 1 and 4")
        values = list(specs); results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="model-acquire") as pool:
            futures = {pool.submit(self.acquire, spec): spec for spec in values}
            for future in as_completed(futures):
                spec = futures[future]
                try: results.append(future.result())
                except Exception as exc: results.append({"model_id": spec.model_id, "revision": spec.revision, "status": "FAILED_RETRYABLE", "error_type": type(exc).__name__, "error": str(exc)})
        return sorted(results, key=lambda row: (row["model_id"], row["revision"]))
