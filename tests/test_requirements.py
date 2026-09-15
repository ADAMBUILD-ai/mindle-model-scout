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


def test_ner_requires_a_real_token_or_phrase_match():
    profile = parse_requirement("GLB render provider and deterministic local rendering")
    assert profile["task_hint"] is None
    assert profile["query"] == "3d"

    ner_profile = parse_requirement("NER model for named entity extraction")
    assert ner_profile["task_hint"] == "token-classification"


def test_adam_38_glb_render_work_order_uses_3d_query():
    profile = parse_requirement(
        "Stage 3/4 hardening + real asset integration + render provider shopping. "
        "Use the final GLB/GLTF scene and compare deterministic local rendering alternatives."
    )
    assert profile["task_hint"] is None
    assert profile["query"] == "3d"


def test_adam_39_placement_work_order_uses_3d_query():
    profile = parse_requirement(
        "Stage 1 building artifact + virtual site artifact -> footprint, placement drawing, transform assist."
    )
    assert profile["task_hint"] is None
    assert profile["query"] == "3d"


def test_adam_40_context_modeling_work_order_uses_3d_query():
    profile = parse_requirement(
        "Stage 3 placement + Stage 1 GLB/model -> surrounding buildings, terrain/context, "
        "GLB scene composition and rendering assist."
    )
    assert profile["task_hint"] is None
    assert profile["query"] == "3d"
