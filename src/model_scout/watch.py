from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable


class SnapshotError(RuntimeError):
    """Raised when a persisted watch snapshot cannot be safely consumed."""


def _sorted_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted((dict(item) for item in candidates), key=lambda item: str(item.get("model_id") or ""))


def diff_candidates(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> dict[str, list]:
    prev = {item.get("model_id"): item for item in previous if item.get("model_id")}
    curr = {item.get("model_id"): item for item in current if item.get("model_id")}

    added = [curr[key] for key in sorted(curr.keys() - prev.keys())]
    removed = [prev[key] for key in sorted(prev.keys() - curr.keys())]
    changed = []
    for key in sorted(curr.keys() & prev.keys()):
        before, after = prev[key], curr[key]
        fields = ("downloads", "likes", "license", "pipeline_tag", "status", "score")
        delta = {field: (before.get(field), after.get(field)) for field in fields if before.get(field) != after.get(field)}
        if delta:
            changed.append({"model_id": key, "changes": delta})

    return {"added": added, "removed": removed, "changed": changed}


def load_snapshot(path: str | Path) -> list[dict[str, Any]]:
    snapshot_path = Path(path)
    if not snapshot_path.exists():
        return []
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"cannot read watch snapshot: {snapshot_path}") from exc

    if not isinstance(payload, dict) or payload.get("version") != 1 or not isinstance(payload.get("candidates"), list):
        raise SnapshotError(f"invalid watch snapshot schema: {snapshot_path}")
    if any(not isinstance(item, dict) for item in payload["candidates"]):
        raise SnapshotError(f"invalid watch snapshot candidate entry: {snapshot_path}")
    return _sorted_candidates(payload["candidates"])


def save_snapshot(path: str | Path, candidates: list[dict[str, Any]]) -> None:
    snapshot_path = Path(path)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "candidates": _sorted_candidates(candidates)}
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=snapshot_path.parent,
            prefix=f".{snapshot_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        os.replace(temp_path, snapshot_path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def run_watch(
    query: str,
    snapshot_path: str | Path,
    limit: int = 10,
    scout_fn: Callable[[str, int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run one deterministic watch cycle and atomically persist its current candidates."""
    previous = load_snapshot(snapshot_path)
    first_run = not Path(snapshot_path).exists()

    if scout_fn is None:
        from .scout import scout

        scout_fn = scout

    result = scout_fn(query, limit)
    current = result.get("candidates")
    if not isinstance(current, list) or any(not isinstance(item, dict) for item in current):
        raise ValueError("scout result must contain a candidate list")

    current = _sorted_candidates(current)
    delta = diff_candidates(previous, current)
    save_snapshot(snapshot_path, current)

    return {
        "query": query,
        "snapshot_path": str(Path(snapshot_path)),
        "first_run": first_run,
        "previous_candidate_count": len(previous),
        "current_candidate_count": len(current),
        "delta": delta,
        "candidates": current,
    }
