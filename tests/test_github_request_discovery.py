from src.model_scout.github_request_discovery import (
    discover_github_issue_requests,
    infer_priority,
    infer_project,
    infer_resource,
    is_model_scout_request,
    normalize_github_issue_request,
    request_discovery_repositories,
)


CONFIGURED = {
    "ADAMBUILD-ai/agri-ai-business-platform",
    "ADAMBUILD-ai/adam-build",
}


def test_detects_explicit_model_scout_marker():
    assert is_model_scout_request("[MODEL SCOUT 요청] P0", "농산물 모델 검색") is True


def test_detects_huggingface_with_request_intent():
    assert is_model_scout_request("Stage 4", "Find Hugging Face model alternatives") is True
    assert is_model_scout_request("Stage 4", "Hugging Face notes only") is False


def test_normalizes_configured_agri_issue_with_callback_metadata():
    envelope = normalize_github_issue_request(
        {
            "repository_full_name": "ADAMBUILD-ai/agri-ai-business-platform",
            "number": 33,
            "state": "open",
            "title": "[P0][AGRI] MODEL SCOUT 요청",
            "body": "model / dataset / space / tool 전체 범위에서 한국어 농산물 후보를 찾아줘",
        },
        configured_repos=CONFIGURED,
    )

    assert envelope is not None
    assert envelope.project == "AGRI"
    assert envelope.priority == "P0"
    assert envelope.resource == "all"
    assert envelope.source_repo == "ADAMBUILD-ai/agri-ai-business-platform"
    assert envelope.source_issue == 33
    assert envelope.callback_repo == envelope.source_repo
    assert envelope.callback_issue == 33


def test_ignores_closed_or_unconfigured_or_irrelevant_issue():
    closed = normalize_github_issue_request(
        {
            "repository_full_name": "ADAMBUILD-ai/adam-build",
            "number": 38,
            "state": "closed",
            "title": "MODEL SCOUT render provider",
            "body": "Find alternatives",
        },
        configured_repos=CONFIGURED,
    )
    unconfigured = normalize_github_issue_request(
        {
            "repository_full_name": "outside/example",
            "number": 1,
            "state": "open",
            "title": "MODEL SCOUT",
            "body": "Find model",
        },
        configured_repos=CONFIGURED,
    )
    irrelevant = normalize_github_issue_request(
        {
            "repository_full_name": "ADAMBUILD-ai/adam-build",
            "number": 39,
            "state": "open",
            "title": "Stage 3 geometry",
            "body": "No external model request here",
        },
        configured_repos=CONFIGURED,
    )

    assert closed is None
    assert unconfigured is None
    assert irrelevant is None


def test_discovery_dedupes_mirrored_identical_requests():
    issues = [
        {
            "repository_full_name": "ADAMBUILD-ai/adam-build",
            "number": 38,
            "state": "open",
            "title": "MODEL SCOUT",
            "body": "Find GLB render provider alternatives",
        },
        {
            "repository_full_name": "ADAMBUILD-ai/adam-build",
            "number": 40,
            "state": "open",
            "title": "MODEL SCOUT",
            "body": "  Find   GLB render provider alternatives  ",
        },
    ]

    discovered = discover_github_issue_requests(issues, configured_repos=CONFIGURED)

    assert len(discovered) == 1
    assert discovered[0].callback_issue == 38


def test_priority_and_resource_inference_are_fail_safe():
    assert infer_priority("normal request", "") == "P1"
    assert infer_priority("[P0] urgent", "") == "P0"
    assert infer_resource("model request", "find one model") == "model"
    assert infer_resource("mixed request", "model dataset space tool") == "all"
    assert infer_project("owner/repo", "[P0][NAS Knowledge AI] request", "") == "NAS_KNOWLEDGE_AI"


def test_central_request_repository_is_always_discovered():
    repos = request_discovery_repositories(["ADAMBUILD-ai/adam-build"])

    assert repos == (
        "ADAMBUILD-ai/adam-build",
        "ADAMBUILD-ai/mindle-model-scout",
    )


def test_central_execution_and_binary_handoff_use_dedicated_workers():
    for number, title in ((68, "[P0][EXECUTION] MODEL SCOUT throughput acceleration"),
                          (82, "[P0][AURA] Binary handoff required before model benchmark")):
        assert normalize_github_issue_request(
            {"repository_full_name": "ADAMBUILD-ai/mindle-model-scout", "number": number,
             "state": "open", "title": title, "body": "Model Scout actual binary package required"},
            configured_repos=["ADAMBUILD-ai/mindle-model-scout"],
        ) is None
