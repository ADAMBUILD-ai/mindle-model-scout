# MODEL SCOUT 표준 요청 계약서
## Standard Request Contract v1.0 — 2026-09-23

목적: 모든 개발팀이 MODEL SCOUT에 같은 형식으로 요청하여, **누가 / 어느 제품에서 / 무엇을 / 왜 / 어떤 조건으로 요청했는지**와 **무엇이 확보·검증·납품되었는지**를 끝까지 추적 가능하게 한다.

이 문서는 신규 요청의 SSOT 형식이다.

---

# 1. 핵심 원칙

1. **요청팀 식별이 없는 요청은 금지한다.**
2. **제품/앱 식별이 없는 요청은 금지한다.**
3. 모델명이 정해져 있으면 정확한 Model ID를 적는다.
4. 모델명이 정해져 있지 않으면 빈칸으로 두지 말고 반드시:
   `SCOUT_SELECTION_REQUIRED`
   로 표기하고 필요한 기능을 상세히 적는다.
5. 기능만 요청하는 경우에도 입력/출력/환경/라이선스/검수기준을 반드시 적는다.
6. 모든 요청은 Source Repo + Source Issue로 원본 위치를 남긴다.
7. 모든 요청은 Delivery Callback 위치를 명시한다.
8. 동일 요청의 중복 생성은 금지하고 Request Fingerprint로 dedupe한다.
9. 요청 → 확보 → 검증 → 납품의 상태를 한 레지스트리에서 추적한다.
10. 모르는 정보는 추정하지 않고 `UNKNOWN`으로 남긴다.

---

# 2. 시스템 고유 Request ID

Issue 생성 후 MODEL SCOUT가 아래 정보를 이용해 고유 Request ID를 생성한다.

권장 형식:

`MSR::<SOURCE_REPO>#<ISSUE_NUMBER>::<PRODUCT>`

예:
`MSR::ADAMBUILD-ai/avora-engine#12::AVORA`

사람이 임의로 번호를 만들지 않는다.

---

# 3. 필수 요청 항목

## A. 요청 주체

- 요청 개발팀명
- 제품/앱명
- 요청 담당자 또는 Owner
- Source Repository
- Source Issue Number / URL
- 우선순위: P0 / P1 / P2 / P3
- 필요 시점 / 마감일

## B. 요청 목적

- 필요한 기능명
- 해결하려는 문제
- 실제 사용 시나리오
- 현재 막혀 있는 작업
- 이 모델이 없으면 진행 불가능한 기능인지 여부

## C. 요청 모델

### 모델이 이미 정해진 경우
- 정확한 Model ID
- 모델 Family
- 희망 Version / Revision
- 공식 Source URL

### 모델이 정해지지 않은 경우
반드시:
`SCOUT_SELECTION_REQUIRED`

그리고 아래를 구체적으로 기입:
- 필요한 Capability
- 입력 형식
- 출력 형식
- 최소 성능 기준
- 허용 가능한 대체 모델 조건

## D. Runtime 조건

- OS
- CPU
- GPU 사용 가능 여부
- GPU 모델
- VRAM
- RAM
- Python 버전
- 허용 모델 포맷: safetensors / ONNX / GGUF / 기타
- `trust_remote_code` 허용 여부
  - 기본값: NO
- 오프라인 실행 필요 여부
- Windows 실행 필요 여부

## E. 라이선스 / 사용권 조건

반드시 아래를 명시한다.

- 상업 사용 필요 여부
- 재배포 필요 여부
- 내부 사용만인지 여부
- 공식 License
- 해당 Revision의 사용권 지속성 근거 필요 여부

MINDLE 기본 채택 조건:

> 확보한 해당 버전에 대해 향후 원저작자가 라이선스·배포정책·접근정책을 변경하더라도, 이미 확보한 해당 버전의 사용권이 유지된다는 근거를 확인할 수 있어야 한다. 명확히 입증할 수 없으면 채택하지 않고 대체 모델을 찾는다.

## F. 확보 Artifact 조건

- 필요한 파일명
- 필요한 Weight 형식
- 모델 크기 제한
- SHA-256 필수 여부
- exact revision pin 필수 여부
- 공식 배포처만 허용 여부
- 외부 remote code 금지 여부

기본값:
- exact revision pin: REQUIRED
- SHA-256: REQUIRED
- official source: REQUIRED
- unreviewed remote code: FORBIDDEN

## G. 실제 검수 입력

- 실제 샘플 파일 제공 여부
- 샘플 위치
- 개인정보/보안자료 포함 여부
- 실제 E2E 테스트 가능 여부
- 대표 입력이 없으면 그 이유

## H. 완료 기준

요청팀이 정의한 실제 PASS 조건을 적는다.

최소:
- 어떤 입력을 넣었을 때
- 어떤 출력이 나와야 하는지
- 최소 품질/정확도/속도
- 결과 파일 형식
- 재현 가능 여부
- CPU/GPU 기준
- 실패로 간주할 조건

## I. 납품 위치

- Callback Repository
- Callback Issue
- 결과 보관 위치
- 저장소/Private model repo 위치
- 최종 Evidence 위치

---

# 4. 요청 상태 표준

각 요청은 다음 상태 중 하나를 가진다.

- `REQUESTED`
- `DISCOVERED`
- `LICENSE_OK`
- `REVISION_PINNED`
- `DOWNLOADED`
- `HASH_VERIFIED`
- `ACQUIRED_VERIFIED`
- `TESTED_PASS`
- `CALLBACK_SENT`
- `DELIVERED`
- `BLOCKED_INPUT`
- `BLOCKED_APPROVAL`
- `FAILED_RETRYABLE`
- `REJECTED_LICENSE`
- `REJECTED_RUNTIME`
- `REJECTED_POLICY`

`FOUND` 또는 검색 결과만으로 완료 처리하지 않는다.

---

# 5. 중앙 Request Registry 필수 컬럼

각 요청과 실제 확보 모델을 한 줄 또는 한 레코드로 연결한다.

필수 필드:

- request_id
- requesting_team
- product
- source_repo
- source_issue
- source_url
- request_owner
- priority
- requested_capability
- requested_model_id
- requested_model_family
- selection_mode
- selected_model_id
- selected_revision
- source
- license
- commercial_use
- rights_persistence_evidence
- artifact_files
- sha256
- runtime_target
- validation_input
- validation_output
- acceptance_criteria
- callback_repo
- callback_issue
- status
- evidence_paths
- delivered_at
- last_updated

---

# 6. 누가 무엇을 요청했는지 확인하는 기준

한 모델이 여러 팀에서 필요할 수 있다.

따라서 MODEL SCOUT는 모델 중심이 아니라 **요청 중심으로 추적**한다.

예:
- Request A — AVORA — OCR
- Request B — AURA — Visual Understanding
- Request C — MEDIA AI — STT

서로 같은 모델을 선택해도 Request ID는 각각 유지한다.

모델 레지스트리는 별도로:
- Model ID
- Revision
- License
- SHA
- Storage
를 한 번만 기록한다.

Request Registry가 어떤 요청이 어떤 Model Registry 항목을 사용했는지 연결한다.

---

# 7. 레거시 요청 정리 규칙

기존 요청은 삭제하지 않는다.

모든 과거 요청을 아래 순서로 역추적한다.

1. Source Repository
2. Source Issue / 문서
3. 요청 개발팀
4. 제품
5. 요청 기능
6. 요청 모델명 또는 기능 요청
7. 실제 선택 모델
8. 현재 상태
9. callback / delivery evidence

확인 불가능한 값은:
`UNKNOWN`

으로 남기고 추정하지 않는다.

레거시 요청도 표준 Request ID를 부여해 중앙 Registry에 편입한다.

---

# 8. 신규 요청 차단 규칙

신규 요청은 아래 4개가 없으면 실행 Queue로 올리지 않는다.

필수 식별 4종:
1. 요청 개발팀
2. 제품/앱
3. Source Repo/Issue
4. 요청 Capability 또는 정확한 Model ID

모델명이 없다는 이유만으로 차단하지 않는다.
대신 `SCOUT_SELECTION_REQUIRED` 상태로 접수한다.

---

# 9. 완료 정의

한 요청의 완료는 다음이 모두 있어야 한다.

`REQUEST → SELECTED MODEL → EXACT REVISION → LICENSE → ARTIFACT → SHA256 → RUNTIME TEST → CALLBACK → DELIVERED`

그리고 Request Registry에서:
- 누가 요청했는지
- 어떤 제품인지
- 어떤 모델이 선택됐는지
- 지금 상태가 무엇인지
- 어디에 납품됐는지

를 한 번에 확인할 수 있어야 한다.
