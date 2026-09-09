from src.model_scout.watch import diff_candidates


def test_diff_candidates_detects_added_removed_and_changed():
    previous = [
        {"model_id": "a", "downloads": 10, "likes": 1, "license": "apache-2.0", "status": "TEST", "score": 75},
        {"model_id": "b", "downloads": 20, "likes": 2, "license": None, "status": "LICENSE_REVIEW_REQUIRED", "score": 70},
    ]
    current = [
        {"model_id": "a", "downloads": 30, "likes": 1, "license": "apache-2.0", "status": "APPROVED", "score": 82},
        {"model_id": "c", "downloads": 5, "likes": 0, "license": "mit", "status": "HOLD", "score": 65},
    ]
    result = diff_candidates(previous, current)
    assert [item["model_id"] for item in result["added"]] == ["c"]
    assert [item["model_id"] for item in result["removed"]] == ["b"]
    assert result["changed"][0]["model_id"] == "a"
    assert "downloads" in result["changed"][0]["changes"]
