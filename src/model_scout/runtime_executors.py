from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .acquisition import ALLOWED_LICENSES, ModelRegistry
from .request_queue import RequestEnvelope
from .runtime_validation import RuntimeInputUnavailable


EXECUTOR_KINDS = (
    "huggingface-model",
    "embedding-reranker",
    "ocr-vision",
    "stt-tts",
    "geometry-tool",
)


class RuntimeExecutorUnavailable(RuntimeError):
    pass


_IMMUTABLE_REVISION = re.compile(r"[0-9a-f]{40}\Z")
_MODEL_WEIGHTS = (".safetensors", ".bin", ".onnx", ".gguf", ".pt", ".pth", ".ckpt")


def _verified_hub_files(model_id: str, revision: str, files: list[dict[str, Any]]) -> None:
    """Require actual weights and a model card at the selected Hub snapshot."""
    if not _IMMUTABLE_REVISION.fullmatch(revision):
        raise RuntimeExecutorUnavailable("acquisition requires an immutable 40-character Hub revision")
    snapshot = f"models--{model_id.replace('/', '--')}/snapshots/{revision}/".casefold()
    names = []
    for entry in files:
        path = str(entry["path"]).replace("\\", "/").casefold()
        if snapshot not in path or not path.endswith(tuple(_MODEL_WEIGHTS) + ("/readme.md", "/license", "/license.txt")):
            continue
        names.append(path)
    if not any(name.endswith(_MODEL_WEIGHTS) for name in names):
        raise RuntimeExecutorUnavailable("no model weights from the selected pinned Hub snapshot")
    if not any(name.endswith(("/readme.md", "/license", "/license.txt")) for name in names):
        raise RuntimeExecutorUnavailable("no license/model-card snapshot for the selected revision")


def select_executable_candidate(scout_result: Mapping[str, Any], requested_model_id: str = "") -> Mapping[str, Any] | None:
    """Select the highest-ranked safe model with an immutable Hub revision."""

    candidates = scout_result.get("candidates", ())
    if not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        model_id = str(candidate.get("model_id") or candidate.get("id") or "").strip()
        if requested_model_id and model_id.casefold() != requested_model_id.casefold():
            continue
        revision = str(candidate.get("revision") or "").strip()
        license_name = str(candidate.get("license") or "").strip().casefold()
        status = str(candidate.get("status") or "").upper()
        resource_type = str(candidate.get("resource_type") or "model").casefold()
        if (
            resource_type == "model"
            and "/" in model_id
            and len(revision) >= 7
            and license_name in ALLOWED_LICENSES
            and status not in {"REJECT", "LICENSE_REVIEW_REQUIRED", "LICENSE_NOT_PERMITTED"}
        ):
            return candidate
    return None


def classify_executor_kind(envelope: RequestEnvelope) -> str:
    # Structured request identity outranks incidental benchmark/license prose.
    capability = envelope.requested_capability.casefold()
    family = envelope.requested_model_family.casefold()
    if capability == "aura_generative_architectural_corpus_analysis_model":
        return "huggingface-model"
    structured = f"{capability} {family}".replace("_", " ")
    task = re.search(r"(?im)^\s*(?:task|modality|requested modality)\s*:\s*([^\n;]+)", envelope.acceptance_criteria)
    if task:
        structured += " " + task.group(1).casefold()

    def route(text: str) -> str | None:
        # Token boundaries prevent revision/preview from matching vision/view.
        def has(values):
            return any(re.search(r"(?<![a-z0-9])" + re.escape(value) + r"(?![a-z0-9])", text)
                       for value in values)
        if envelope.resource == "tool" and has(("mapping", "render", "pbr", "texture")):
            return "geometry-tool"
        if has(("generative text reasoning", "text generation", "text-generation", "causal llm", "causal_llm")):
            return "huggingface-model"
        if has(("embedding", "reranker", "rerank", "임베딩", "리랭")):
            return "embedding-reranker"
        if has(("ocr", "vision", "visual", "image", "이미지", "도면", "비전")):
            return "ocr-vision"
        if has(("stt", "tts", "speech", "whisper", "음성")):
            return "stt-tts"
        if has(("geometry", "cad", "mesh", "glb", "gltf", "dxf", "svg", "3d", "2d")):
            return "geometry-tool"
        return None

    explicit = route(structured)
    if explicit is not None:
        return explicit
    # Legacy unstructured requests retain modality routing with token boundaries.
    return route(envelope.request_text.casefold()) or "huggingface-model"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _candidate_has_pinned_weights(model_id: str, revision: str) -> bool:
    """Check official Hub metadata before spending CPU time on a model loader."""
    from huggingface_hub import HfApi
    from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError, RevisionNotFoundError

    for attempt in range(3):
        try:
            info = HfApi().model_info(model_id, revision=revision)
            break
        except (RepositoryNotFoundError, RevisionNotFoundError):
            return False
        except HfHubHTTPError as exc:
            if getattr(getattr(exc, "response", None), "status_code", None) != 429 or attempt == 2:
                raise
            retry_after = getattr(exc.response, "headers", {}).get("Retry-After", "")
            delay = float(retry_after) if str(retry_after).isdigit() else 2 ** attempt
            time.sleep(min(10.0, max(1.0, delay)))
    if str(info.sha or "").casefold() != revision.casefold():
        return False
    return any(str(sibling.rfilename).casefold().endswith(_MODEL_WEIGHTS) for sibling in (info.siblings or []))


def _candidate_weight_bytes(model_id: str, revision: str) -> int | None:
    """Bound CPU acquisition using pinned official Hub file sizes before download."""
    from huggingface_hub import HfApi
    from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError, RevisionNotFoundError

    for attempt in range(3):
        try:
            info = HfApi().model_info(model_id, revision=revision, files_metadata=True)
            break
        except (RepositoryNotFoundError, RevisionNotFoundError):
            return None
        except HfHubHTTPError as exc:
            if getattr(getattr(exc, "response", None), "status_code", None) != 429 or attempt == 2:
                raise
            time.sleep(2 ** attempt)
    if str(info.sha or "").casefold() != revision.casefold():
        return None
    # Transformers loads one weight format. Counting both safetensors and legacy
    # PyTorch copies rejects otherwise viable CPU candidates before download.
    siblings = info.siblings or []
    weights = [item for item in siblings if str(item.rfilename).casefold().endswith(".safetensors")]
    if not weights:
        weights = [item for item in siblings if str(item.rfilename).casefold().endswith(".bin")]
    sizes = [getattr(sibling, "size", None) for sibling in weights]
    if not sizes or any(not isinstance(size, int) or size <= 0 for size in sizes):
        return None
    return sum(sizes)


def _candidate_has_safe_builtin_config(model_id: str, revision: str) -> tuple[bool, str]:
    """Reject candidates that require unsupported or repository-supplied Python code.

    This deliberately resolves only the pinned config with ``trust_remote_code``
    disabled. Network and Hub failures are not converted into an incompatibility:
    they must remain retryable infrastructure errors.
    """
    from transformers import AutoConfig

    try:
        AutoConfig.from_pretrained(model_id, revision=revision, trust_remote_code=False)
    except (KeyError, ValueError) as exc:
        summary = " ".join(str(exc).split())[:400]
        return False, f"unsupported_safe_transformers_config:{summary}"
    return True, ""


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
    preflight_weights: bool = False
    preflight_builtin_transformers: bool = False
    max_weight_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in EXECUTOR_KINDS:
            raise ValueError(f"unsupported executor kind: {self.kind}")
        if not self.command:
            raise ValueError("executor command is required")
        if self.timeout_seconds <= 0:
            raise ValueError("executor timeout must be positive")
        if self.max_weight_bytes is not None and self.max_weight_bytes <= 0:
            raise ValueError("max_weight_bytes must be positive")

    def run(
        self,
        envelope: RequestEnvelope,
        scout_result: Mapping[str, Any],
        *,
        work_root: Path,
    ) -> dict[str, Any]:
        workspace = work_root / envelope.fingerprint
        workspace.mkdir(parents=True, exist_ok=True)
        if envelope.resource == "tool":
            candidates = scout_result.get("candidates")
            names = [f"{item.get('model_id')}@{item.get('revision')}" for item in candidates[:5]
                     if isinstance(item, Mapping)] if isinstance(candidates, list) else []
            raise RuntimeInputUnavailable(
                f"render tool discovery candidates={names}; exact request GLB and a verified program "
                "package/license/runtime are required before CPU execution or ACQUIRED_VERIFIED"
            )
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

        requested_model_id = envelope.requested_model_id
        if requested_model_id in {"UNKNOWN", "SCOUT_SELECTION_REQUIRED"}:
            requested_model_id = ""
        selected = None
        raw_candidates = scout_result.get("candidates")
        selection_diagnostics: list[dict[str, str]] = []
        candidates = raw_candidates if isinstance(raw_candidates, list) else []
        for index in range(len(candidates)):
            candidate = select_executable_candidate({"candidates": [candidates[index]]}, requested_model_id)
            if candidate is None:
                continue
            candidate_id = str(candidate.get("model_id") or candidate.get("id"))
            candidate_revision = str(candidate.get("revision"))
            if self.kind == "ocr-vision" and "trocr" not in candidate_id.casefold() and str(candidate.get("pipeline_tag") or "") not in {
                "image-to-text", "visual-question-answering", "document-question-answering"
            }:
                selection_diagnostics.append({"model_id": candidate_id, "reason": "unsupported_safe_vision_pipeline"})
                continue
            listed_files = candidate.get("model_files")
            if self.preflight_weights and not (
                any(str(name).casefold().endswith(_MODEL_WEIGHTS) for name in listed_files)
                if isinstance(listed_files, list) else _candidate_has_pinned_weights(candidate_id, candidate_revision)
            ):
                selection_diagnostics.append({"model_id": candidate_id, "reason": "no_weights_at_exact_revision"})
                continue
            if self.preflight_builtin_transformers:
                compatible, reason = _candidate_has_safe_builtin_config(candidate_id, candidate_revision)
                if not compatible:
                    selection_diagnostics.append({"model_id": candidate_id, "reason": reason})
                    continue
            if self.max_weight_bytes is not None:
                weight_bytes = _candidate_weight_bytes(candidate_id, candidate_revision)
                if weight_bytes is None or weight_bytes > self.max_weight_bytes:
                    selection_diagnostics.append({
                        "model_id": candidate_id,
                        "reason": f"unknown_or_oversize_pinned_weights:{weight_bytes}:limit={self.max_weight_bytes}",
                    })
                    continue
            selected = candidate
            break
        if isinstance(raw_candidates, list) and raw_candidates and selected is None:
            raise RuntimeExecutorUnavailable(
                "scout returned no runnable candidate with allowed license, immutable revision, supported adapter, "
                f"and pinned weights; skipped={selection_diagnostics[:10]}"
            )
        selected_model_id = str(selected.get("model_id") or selected.get("id")) if selected else self.model_id
        selected_revision = str(selected.get("revision")) if selected else self.model_revision
        selected_license = str(selected.get("license")) if selected else self.license
        selected_source = str(selected.get("source_url") or f"https://huggingface.co/{selected_model_id}") if selected else self.source
        placeholders = {
            "input": str(input_path),
            "output": str(output_path),
            "workspace": str(workspace),
            "python": sys.executable,
            "package_root": str(Path(__file__).resolve().parents[2]),
            "model_id": selected_model_id,
            "revision": selected_revision,
            "pipeline_tag": str(selected.get("pipeline_tag") or "") if selected else "",
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
            pipeline_tag = str(selected.get("pipeline_tag") or "") if selected else ""
            raise RuntimeError(
                f"executor exited {completed.returncode} for model={selected_model_id}@{selected_revision} "
                f"pipeline={pipeline_tag or 'unspecified'}: {stderr}"
            )
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
            path = raw_path.absolute()
            if not path.is_file() or path.stat().st_size <= 0:
                raise RuntimeError(f"downloaded artifact is missing or empty: {path}")
            # Hub snapshots may symlink into their own blobs directory, but
            # never accept a symlink to an unrelated package or filesystem.
            lexical = str(path).replace("\\", "/").casefold()
            actual = str(path.resolve()).replace("\\", "/").casefold()
            if "/snapshots/" in lexical:
                repo_root = lexical.split("/snapshots/", 1)[0]
                if not (actual.startswith(repo_root + "/snapshots/") or actual.startswith(repo_root + "/blobs/")):
                    raise RuntimeExecutorUnavailable(f"snapshot file escapes its model repository: {path}")
            downloads.append({
                "path": str(path),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            })

        return {
            "model_id": selected_model_id,
            "model_revision": selected_revision,
            "source": selected_source,
            "validation_scope": str(output_payload.get("validation_scope") or "component"),
            "acceptance_checks": dict(output_payload.get("acceptance_checks") or {}),
            "license": selected_license,
            "selected_candidate": selected is not None,
            "selection_diagnostics": selection_diagnostics,
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
    def __init__(self, adapters: Mapping[str, LocalCommandAdapter], *, work_root: str | Path, model_registry: ModelRegistry | None = None):
        self.adapters = dict(adapters)
        self.work_root = Path(work_root)
        self.model_registry = model_registry
        if self.model_registry is not None:
            self._reconcile_prior_runtime_records()

    def _reconcile_prior_runtime_records(self) -> None:
        """Demote old runtime rows whose recorded files cannot prove acquisition."""
        assert self.model_registry is not None
        with self.model_registry._lock:
            payload = self.model_registry._read()
            changed = False
            for row in payload["models"]:
                # Run #593 acquired valid bytes, but the English-only model card
                # cannot satisfy AGRI #33's Korean embedding requirement. Preserve
                # acquisition proof while correcting the product suitability claim.
                if (row.get("model_id") == "BAAI/bge-small-en-v1.5"
                    and row.get("revision") == "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
                    and "ADAMBUILD-ai/mindle-model-scout#33" in (row.get("originating_requests") or [])):
                    if row.get("validation_status") != "REJECT_QUALITY":
                        row["validation_status"] = "REJECT_QUALITY"
                        row["product_review_reason"] = "English-only model card is incompatible with AGRI #33 Korean embedding requirement; autonomous run #593"
                        row["consuming_teams"] = [team for team in (row.get("consuming_teams") or []) if team != "AGRI"]
                        changed = True
                if row.get("acquisition_runner") != "candidate-aware-runtime-v2" or row.get("acquisition_status") != "ACQUIRED_VERIFIED":
                    continue
                try:
                    _verified_hub_files(str(row["model_id"]), str(row["revision"]), row.get("files", []))
                except (RuntimeExecutorUnavailable, KeyError, TypeError):
                    row["acquisition_status"] = "VERIFY_REQUIRED"
                    row["acquisition_review_reason"] = "missing pinned model bytes or model-card evidence"
                    changed = True
            if changed:
                self.model_registry._write(payload)

    def __call__(
        self,
        envelope: RequestEnvelope,
        scout_result: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        kind = classify_executor_kind(envelope)
        # The current generic worker is a sentiment classifier, not a causal LLM.
        # Never acquire/run it as proof of AURA's generative analysis contract.
        if envelope.requested_capability.casefold() == "aura_generative_architectural_corpus_analysis_model":
            raise RuntimeInputUnavailable(
                "AURA #136 requires a generative-text executor and real KR10+GLOBAL10 benchmark inputs; "
                "the configured generic huggingface-model worker only runs text-classification"
            )
        adapter = self.adapters.get(kind)
        if adapter is None:
            raise RuntimeExecutorUnavailable(f"no configured local executor for {kind}")
        evidence = adapter.run(envelope, scout_result, work_root=self.work_root)
        evidence["acquisition_verified"] = False
        if self.model_registry is not None and evidence["selected_candidate"]:
            _verified_hub_files(str(evidence["model_id"]), str(evidence["model_revision"]), evidence["downloaded_files"])
            record = {
                "model_id": evidence["model_id"],
                "revision": evidence["model_revision"],
                "source_url": evidence["source"],
                "license": evidence["license"],
                "files": evidence["downloaded_files"],
                "trust_remote_code_required": False,
                "originating_requests": [f"{envelope.source_repo}#{envelope.source_issue}"],
                "consuming_teams": [envelope.requesting_team],
                "cache_location": str(self.work_root),
                "acquisition_runner": "candidate-aware-runtime-v2",
                "acquisition_status": "ACQUIRED_VERIFIED",
                "validation_status": "PENDING",
                "runtime_evidence": evidence["output_path"],
            }
            persisted, _created = self.model_registry.upsert(record)
            evidence["acquisition_verified"] = persisted.get("acquisition_status") == "ACQUIRED_VERIFIED"
        return evidence

    def mark_tested_pass(self, evidence: Mapping[str, Any]) -> None:
        if self.model_registry is not None and evidence.get("selected_candidate"):
            self.model_registry.mark_validation(
                str(evidence["model_id"]),
                str(evidence["model_revision"]),
                status="TESTED_PASS",
                evidence=str(evidence["output_path"]),
            )


def load_runtime_executor_registry(
    config_path: str | Path | None,
    *,
    work_root: str | Path,
    model_registry_path: str | Path | None = None,
) -> RuntimeExecutorRegistry:
    if config_path is None:
        return RuntimeExecutorRegistry({}, work_root=work_root, model_registry=ModelRegistry(model_registry_path) if model_registry_path else None)
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
            preflight_weights=bool(raw.get("preflight_weights", False)),
            preflight_builtin_transformers=bool(raw.get("preflight_builtin_transformers", False)),
            max_weight_bytes=int(raw["max_weight_bytes"]) if raw.get("max_weight_bytes") is not None else None,
        )
    registry = ModelRegistry(model_registry_path) if model_registry_path else None
    return RuntimeExecutorRegistry(adapters, work_root=work_root, model_registry=registry)
