# MINDLE MODEL SCOUT
## REQUEST STANDARDIZATION + LEGACY BACKFILL EXECUTION DIRECTIVE
### v1.0 — 2026-09-23

**Authority:** 신작가님 → MODEL SCOUT Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Purpose:** 모든 개발팀의 MODEL SCOUT 요청을 동일 양식으로 표준화하고, 기존 뒤섞인 요청을 역추적 가능한 중앙 Request Registry로 재정리한다.

---

# 1. 기준 문서

반드시 아래 문서를 SSOT로 사용한다.

`docs/standards/MODEL_SCOUT_STANDARD_REQUEST_CONTRACT_v1.0_20260923.md`

신규 GitHub Issue 요청은:

`.github/ISSUE_TEMPLATE/model-scout-request.yml`

양식을 사용한다.

---

# 2. 신규 요청 강제 규칙

신규 MODEL SCOUT 요청은 다음 4개가 없으면 실행 Queue에 올리지 않는다.

1. 요청 개발팀
2. 제품/앱
3. Source Repo / Issue
4. 요청 Capability 또는 정확한 Model ID

모델이 아직 정해지지 않은 요청은:
`SCOUT_SELECTION_REQUIRED`
로 접수한다.

빈칸 또는 출처 불명 요청은 자동 실행하지 않는다.

---

# 3. 반드시 보존해야 할 추적 관계

각 요청은 아래 연결관계를 끝까지 유지한다.

`REQUEST TEAM → PRODUCT → SOURCE ISSUE → CAPABILITY → SELECTED MODEL → REVISION → LICENSE → ARTIFACT/SHA → TEST → CALLBACK → DELIVERED`

어느 단계에서도 요청팀과 제품 정보를 잃지 않는다.

---

# 4. 중앙 Request Registry 생성

다음 파일을 생성한다.

`evidence/model-request-registry.json`

최소 스키마:

- schema_version
- generated_at
- requests[]

각 requests 레코드 필수:
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
- license
- commercial_use
- rights_persistence_evidence
- status
- callback_repo
- callback_issue
- evidence_paths
- delivered_at
- last_updated

모르는 값은 `UNKNOWN`.
추정 금지.

---

# 5. 기존 요청 전수 역추적

기존 중앙 Issue, project repo Issue, handoff 문서, callback Evidence를 확인해서 요청을 다시 묶는다.

각 기존 요청마다 반드시 확인:

1. 어느 개발팀 요청인지
2. 어느 제품인지
3. 원 Source Repo/Issue가 어디인지
4. 어떤 기능을 요청했는지
5. 정확한 모델명을 지정했는지 또는 기능만 요청했는지
6. 실제로 선택/확보된 모델은 무엇인지
7. 정확한 Revision / License / SHA가 있는지
8. 현재 상태가 무엇인지
9. 어느 팀/Issue로 callback 되었는지
10. DELIVERED인지 아직 진행 중인지

---

# 6. 레거시 요청 분류

기존 요청은 다음 중 하나로 명확히 분류한다.

- EXACT_MODEL_REQUEST
- CAPABILITY_REQUEST
- FAMILY_REQUEST
- TOOL_REQUEST
- DATASET_REQUEST
- UNKNOWN_LEGACY

모델명만 있고 요청 주체를 확인할 수 없으면:
`UNKNOWN_LEGACY`

로 남긴다.

절대 임의로 팀을 붙이지 않는다.

---

# 7. 한 모델을 여러 팀이 요청한 경우

중복 모델은 Model Registry에 한 번만 보관할 수 있다.

하지만 Request Registry에는 팀별 Request ID를 각각 유지한다.

예:
- AVORA → OCR → Model A
- AURA → OCR → Model A

Model A 자체는 한 번만 확보해도 되지만,
두 요청의 source/callback/delivery 상태는 별도로 추적한다.

---

# 8. 신규 자동화 보완

현재 request discovery / normalization 로직에 다음 필드가 보존되도록 보완한다.

- requesting_team
- product
- request_owner
- requested_capability
- requested_model_id
- requested_model_family
- selection_mode
- acceptance_criteria

기존 source_repo/source_issue/callback/fingerprint는 유지한다.

신규 표준 Issue Form 요청은 위 필드를 직접 파싱한다.

레거시 자유형 Issue는 기존 parser를 유지하되:
- 식별 불가 필드는 UNKNOWN
- 추정 금지
- legacy flag 기록

---

# 9. Request ID

신규/레거시 모든 요청에 안정적인 Request ID를 부여한다.

권장:
`MSR::<source_repo>#<source_issue>::<product>`

동일 Source Issue는 동일 Request ID를 유지한다.

한 Issue 안에 완전히 다른 복수 요청이 있으면 명시적 subrequest suffix를 사용한다.

---

# 10. 검수 자료

작업 완료 후 아래를 저장소에 커밋한다.

1. `evidence/model-request-registry.json`
2. `docs/inspection/MODEL_SCOUT_REQUEST_STANDARDIZATION_AND_LEGACY_BACKFILL_CLOSEOUT_20260923.md`
3. 필요 시 machine-readable unresolved list:
   `evidence/model-request-unresolved-legacy-20260923.json`

최종 검수서에는 반드시:
- 총 레거시 요청 수
- 요청팀 식별 완료 수
- 제품 식별 완료 수
- exact model 요청 수
- capability-only 요청 수
- UNKNOWN_LEGACY 수
- DELIVERED 수
- 진행 중 수
- 팀별 요청 개수
- 제품별 요청 개수
- 모델별 연결 요청 개수
를 적는다.

---

# 11. 완료 기준

완료는 단순히 양식 파일을 만든 것이 아니다.

다음이 모두 되어야 한다.

- 신규 표준 Issue Form 존재
- 표준 요청 계약서 존재
- 중앙 Request Registry 존재
- 기존 요청 backfill 완료
- UNKNOWN은 UNKNOWN으로 명확히 분리
- 요청팀/제품/모델/상태 연결 가능
- 어떤 팀이 무엇을 요청했고 결과가 어디까지 갔는지 한 번에 확인 가능
- 관련 테스트 PASS
- 검수자료 저장

---

# 12. 작업 원칙

`SOURCE → NORMALIZE → LINK → VERIFY → BACKFILL → TEST → EVIDENCE`

임의 추정 금지.

누락된 데이터가 있으면 숨기지 말고 `UNKNOWN` 또는 `VERIFY_REQUIRED`로 남긴다.

기존 DELIVERED Evidence를 덮어쓰지 않는다.
