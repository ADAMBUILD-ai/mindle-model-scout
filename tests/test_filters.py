from src.model_scout.filters import filter_candidates


def test_filter_candidates_applies_task_license_and_popularity():
    candidates = [
        {"model_id": "a", "pipeline_tag": "text-to-speech", "license": "apache-2.0", "downloads": 5000, "likes": 40},
        {"model_id": "b", "pipeline_tag": "text-to-speech", "license": None, "downloads": 9000, "likes": 80},
        {"model_id": "c", "pipeline_tag": "text-generation", "license": "apache-2.0", "downloads": 12000, "likes": 90},
    ]
    profile = {"task_hint": "text-to-speech", "license_required": True, "min_downloads": 1000, "min_likes": 20}
    result = filter_candidates(candidates, profile)
    assert [item["model_id"] for item in result] == ["a"]
