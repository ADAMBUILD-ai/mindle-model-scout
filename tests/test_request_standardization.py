from src.model_scout.github_request_discovery import normalize_github_issue_request
from src.model_scout.request_registry import classify_request, export_request_registry


FORM = """### 요청 개발팀

AVORA 개발팀

### 제품 / 앱

AVORA

### 요청 Owner / 담당자

AVORA General Work

### 우선순위

P0

### 필요한 기능 / 해결할 문제

도면 OCR

### 요청 Model ID

{model_id}

### Model Family / 계열

{family}

### Resource Type

model

### PASS 기준

정확도 95% 이상

### Callback Repository

ADAMBUILD-ai/avora-engine

### Callback Issue

12
"""


def issue(body: str, number: int = 76) -> dict[str, object]:
    return {
        "repository_full_name": "ADAMBUILD-ai/mindle-model-scout",
        "number": number,
        "title": "[MODEL_SCOUT_REQUEST] OCR",
        "body": body,
        "state": "open",
    }


def test_standard_issue_form_preserves_contract_and_links():
    envelope = normalize_github_issue_request(
        issue(FORM.format(model_id="owner/ocr-model", family="OCR")),
        configured_repos=["ADAMBUILD-ai/mindle-model-scout"],
    )
    assert envelope is not None
    assert envelope.requesting_team == "AVORA 개발팀"
    assert envelope.product == "AVORA"
    assert envelope.request_owner == "AVORA General Work"
    assert envelope.requested_capability == "도면 OCR"
    assert envelope.requested_model_id == "owner/ocr-model"
    assert envelope.requested_model_family == "OCR"
    assert envelope.selection_mode == "EXACT_MODEL"
    assert envelope.acceptance_criteria == "정확도 95% 이상"
    assert (envelope.source_repo, envelope.source_issue) == (
        "ADAMBUILD-ai/mindle-model-scout",
        76,
    )
    assert (envelope.callback_repo, envelope.callback_issue) == (
        "ADAMBUILD-ai/avora-engine",
        12,
    )


def test_selection_required_and_stable_request_id():
    body = FORM.format(model_id="SCOUT_SELECTION_REQUIRED", family="UNKNOWN")
    first = normalize_github_issue_request(
        issue(body), configured_repos=["ADAMBUILD-ai/mindle-model-scout"]
    )
    second = normalize_github_issue_request(
        issue(body), configured_repos=["ADAMBUILD-ai/mindle-model-scout"]
    )
    assert first is not None and second is not None
    assert first.selection_mode == "SCOUT_SELECTION_REQUIRED"
    assert first.request_id == "MSR::ADAMBUILD-ai/mindle-model-scout#76::AVORA"
    assert first.request_id == second.request_id
    assert first.fingerprint == second.fingerprint


def test_legacy_freeform_preserves_unknowns():
    envelope = normalize_github_issue_request(
        issue("MODEL SCOUT에서 안전한 모델을 찾아 주세요.", 77),
        configured_repos=["ADAMBUILD-ai/mindle-model-scout"],
    )
    assert envelope is not None
    assert envelope.requesting_team == "UNKNOWN"
    assert envelope.product == "UNKNOWN"
    assert envelope.selection_mode == "UNKNOWN_LEGACY"
    assert envelope.request_id.endswith("#77::UNKNOWN")


def test_capability_family_and_resource_classification():
    assert classify_request({"requested_capability": "OCR"}) == "CAPABILITY_REQUEST"
    assert classify_request({"requested_model_family": "Whisper"}) == "FAMILY_REQUEST"
    assert classify_request({"resource_type": "tool"}) == "TOOL_REQUEST"
    assert classify_request({"resource_type": "dataset"}) == "DATASET_REQUEST"


def test_same_model_multiple_teams_and_deterministic_export():
    records = [
        {
            "request_id": "MSR::repo#2::AURA",
            "requesting_team": "AURA",
            "requested_model_id": "owner/shared",
        },
        {
            "request_id": "MSR::repo#1::AVORA",
            "requesting_team": "AVORA",
            "requested_model_id": "owner/shared",
        },
    ]
    first = export_request_registry(records)
    second = export_request_registry(reversed(records))
    assert first == second
    assert first["total_requests"] == 2
    assert [item["request_id"] for item in first["requests"]] == [
        "MSR::repo#1::AVORA",
        "MSR::repo#2::AURA",
    ]
