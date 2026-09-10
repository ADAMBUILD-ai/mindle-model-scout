import json
from pathlib import Path

import pytest

from src.model_scout.watch import SnapshotError, diff_candidates, load_snapshot, run_watch, save_snapshot


def candidate(model_id: str, *, downloads: int = 10, likes: int = 1, status: str = "TEST", score: int = 75):
    return {
        "model_id": model_id,
        "pipeline_tag": "text-classification",
        "downloads": downloads,
        "likes": likes,
        "library_name": "transformers",
        "license": "apache-2.0",
        "score": score,
        "status": status,
        "reason": "license:apache-2.0",
    }


def fake_scout(candidates):
    def _run(query: str, limit: int):
        return {"query": query, "candidate_count": len(candidates), "candidates": candidates[:limit]}

    return _run


def test_diff_candidates_detects_added_removed_and_changed():
    previous = [
        candidate("a", downloads=10),
        {**candidate("b", downloads=20, score=70), "license": None, "status": "LICENSE_REVIEW_REQUIRED"},
    ]
    current = [
        candidate("a", downloads=30, status="APPROVED", score=82),
        {**candidate("c", downloads=5, likes=0, status="HOLD", score=65), "license": "mit"},
    ]
    result = diff_candidates(previous, current)
    assert [item["model_id"] for item in result["added"]] == ["c"]
    assert [item["model_id"] for item in result["removed"]] == ["b"]
    assert result["changed"][0]["model_id"] == "a"
    assert "downloads" in result["changed"][0]["changes"]


def test_watch_first_run_persists_snapshot_and_reports_added(tmp_path: Path):
    snapshot = tmp_path / "watch.json"
    result = run_watch("bert", snapshot, 10, fake_scout([candidate("b"), candidate("a")]))

    assert result["first_run"] is True
    assert result["previous_candidate_count"] == 0
    assert [item["model_id"] for item in result["delta"]["added"]] == ["a", "b"]
    assert [item["model_id"] for item in load_snapshot(snapshot)] == ["a", "b"]


def test_watch_no_change_emits_empty_delta(tmp_path: Path):
    snapshot = tmp_path / "watch.json"
    current = [candidate("a")]
    save_snapshot(snapshot, current)

    result = run_watch("bert", snapshot, 10, fake_scout(current))

    assert result["first_run"] is False
    assert result["delta"] == {"added": [], "removed": [], "changed": []}


def test_watch_repeat_run_detects_added_removed_and_changed(tmp_path: Path):
    snapshot = tmp_path / "watch.json"
    save_snapshot(snapshot, [candidate("a", downloads=10), candidate("b")])

    result = run_watch(
        "bert",
        snapshot,
        10,
        fake_scout([candidate("a", downloads=99, status="APPROVED", score=85), candidate("c")]),
    )

    assert [item["model_id"] for item in result["delta"]["added"]] == ["c"]
    assert [item["model_id"] for item in result["delta"]["removed"]] == ["b"]
    assert result["delta"]["changed"] == [
        {
            "model_id": "a",
            "changes": {"downloads": (10, 99), "status": ("TEST", "APPROVED"), "score": (75, 85)},
        }
    ]
    assert [item["model_id"] for item in load_snapshot(snapshot)] == ["a", "c"]


def test_corrupt_snapshot_fails_closed_without_overwrite(tmp_path: Path):
    snapshot = tmp_path / "watch.json"
    original = "{not-json\n"
    snapshot.write_text(original, encoding="utf-8")

    with pytest.raises(SnapshotError):
        run_watch("bert", snapshot, 10, fake_scout([candidate("a")]))

    assert snapshot.read_text(encoding="utf-8") == original


def test_invalid_snapshot_schema_fails_closed(tmp_path: Path):
    snapshot = tmp_path / "watch.json"
    snapshot.write_text(json.dumps({"version": 2, "candidates": []}), encoding="utf-8")

    with pytest.raises(SnapshotError):
        load_snapshot(snapshot)


def test_failed_serialization_does_not_damage_existing_snapshot(tmp_path: Path):
    snapshot = tmp_path / "watch.json"
    save_snapshot(snapshot, [candidate("a")])
    original = snapshot.read_text(encoding="utf-8")

    with pytest.raises(TypeError):
        save_snapshot(snapshot, [{"model_id": "bad", "not_json": {1, 2, 3}}])

    assert snapshot.read_text(encoding="utf-8") == original
