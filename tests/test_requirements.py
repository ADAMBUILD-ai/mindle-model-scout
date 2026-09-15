from src.model_scout.requirements import parse_requirement


def test_parse_commercial_tts_requirement():
    profile = parse_requirement("상업용 TTS 모델, downloads 1000 이상, likes 20 이상")
    assert profile["task_hint"] == "text-to-speech"
    assert profile["commercial_use"] is True
    assert profile["license_required"] is True
    assert profile["min_downloads"] == 1000
    assert profile["min_likes"] == 20


def test_parse_generic_vision_requirement():
    profile = parse_requirement("commercial vision model with license")
    assert profile["task_hint"] == "image-classification"
