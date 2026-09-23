# MINDLE MODEL SCOUT
## REQUEST STANDARDIZATION — FINAL CLOSEOUT DIRECTIVE
### v3.0 FINAL — 2026-09-23

**Authority:** 신작가님 → MODEL SCOUT Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Central Issue:** #75  
**Active PR:** #76  
**Work branch:** `standards/model-scout-request-contract-20260923`

---

# 1. FINAL MISSION

이번 단계는 MODEL SCOUT 요청 표준화 작업의 **최종 마감 단계**다.

추가 설계, 범위 확대, 새로운 검수 항목 추가를 금지한다.

이번 작업에서 완료해야 할 범위는 딱 다음으로 고정한다.

1. 표준 요청서
2. 중앙 Request Registry
3. 기존 요청 Backfill
4. UNKNOWN_LEGACY 분리
5. Parser/Normalizer 반영
6. 테스트
7. 최종 검수서
8. PR #76 Ready for review

이 범위 외 신규 기능은 만들지 않는다.

---

# 2. COST / BUDGET BOUNDARY

사용자는 필요 시 **최대 20,000,000 KRW 규모까지 검토 가능 범위**로 열어두었다.

이 금액은 **검토 상한**이며 자동 집행 승인이 아니다.

규칙:
- 무료/기존 자원 우선
- 비용이 필요한 경우 먼저:
  - 목적
  - 최소 실행 단위
  - 예상 금액
  - 대체 무료안
  - 필요 이유
  를 보고한다.
- 실제 유료 집행은 별도 명시 승인 전까지 금지한다.
- 20,000,000 KRW를 초과하는 검토/집행은 금지한다.

이번 Request Standardization 작업은 원칙적으로 기존 GitHub/저장소 자원 안에서 완료한다.

---

# 3. SCOPE FREEZE

앞으로 이 작업에서 새로 추가할 수 있는 검수는 아래 두 경우뿐이다.

1. 현재 변경으로 기존 기능이 실제로 깨진 Evidence가 나온 경우
2. Request Registry 무결성을 깨는 직접적인 데이터 결함이 확인된 경우

그 외:
- 추가 아이디어
- 구조 개선
- UI 개선
- 새로운 모델 확보
- 새로운 자동화
- 별도 성능 최적화

는 이번 Closeout에서 제외한다.

---

# 4. REQUIRED OUTPUT — MUST EXIST BEFORE CLOSEOUT

반드시 생성/갱신:

## A. Request Registry
`evidence/model-request-registry.json`

필수:
- 모든 확인 가능한 요청 레코드
- 요청팀
- 제품
- Source Repo/Issue
- Capability
- 요청 모델 또는 `SCOUT_SELECTION_REQUIRED`
- 실제 선택 모델
- Revision
- License
- Status
- Callback
- Evidence
- Delivered 여부

## B. Unresolved Legacy
`evidence/model-request-unresolved-legacy-20260923.json`

확인 불가 항목만 포함:
- request_id
- missing_fields
- reason
- next_evidence_needed

추정 금지.

## C. Parser / Normalizer
표준 Issue Form에서 최소 다음을 보존:
- requesting_team
- product
- request_owner
- requested_capability
- requested_model_id
- requested_model_family
- selection_mode
- acceptance_criteria

기존 source/callback/fingerprint 계약은 유지.

## D. Tests
필수:
- 표준 Issue Form parse
- exact-model request
- capability-only request
- `SCOUT_SELECTION_REQUIRED`
- legacy free-form
- UNKNOWN preservation
- stable Request ID
- same model / multiple team requests
- callback/source linkage
- deterministic registry export

## E. Final Inspection
`docs/inspection/MODEL_SCOUT_REQUEST_STANDARDIZATION_AND_LEGACY_BACKFILL_CLOSEOUT_20260923.md`

---

# 5. LEGACY BACKFILL RULE

모든 기존 요청은 가능한 범위에서 Source Evidence로 재정리한다.

분류:
- `EXACT_MODEL_REQUEST`
- `CAPABILITY_REQUEST`
- `FAMILY_REQUEST`
- `TOOL_REQUEST`
- `DATASET_REQUEST`
- `UNKNOWN_LEGACY`

모델명만 있다고 팀을 추정하지 않는다.

팀/제품을 확인할 수 없으면:
- `UNKNOWN`
- `UNKNOWN_LEGACY`

로 유지한다.

이것은 실패가 아니라 **정확한 데이터 상태**다.

---

# 6. REQUEST ID

기본 형식:

`MSR::<source_repo>#<source_issue>::<product>`

제품 불명:
`MSR::<source_repo>#<source_issue>::UNKNOWN`

한 Issue 안에 독립 요청이 여러 개면:
`::R1`, `::R2`

동일 요청은 매 실행마다 동일 ID를 유지한다.

---

# 7. MODEL / REQUEST 분리 원칙

절대 다시 섞지 않는다.

## Model Registry
모델 revision 기준 1건.

## Request Registry
요청팀/제품/Source Issue 기준 각각 1건.

예:
동일 모델을 AVORA와 AURA가 사용해도:
- Model = 1
- Requests = 2

이 구조를 최종 기준으로 고정한다.

---

# 8. FINAL TEST GATE

변경 완료 후 순서:

1. focused tests
2. full tests
3. cli-smoke
4. hf-e2e
5. exact-head CI

HEAD가 바뀌면 다시 exact-head CI 실행.

PASS 없는 이전 run 재사용 금지.

---

# 9. FINAL INSPECTION CONTENT

최종 검수서에 반드시 정확한 수치 기록:

- total_requests
- identified_team_count
- unknown_team_count
- identified_product_count
- unknown_product_count
- exact_model_request_count
- capability_request_count
- family_request_count
- tool_request_count
- dataset_request_count
- unknown_legacy_count
- delivered_count
- active_count
- blocked_count
- unresolved_count

그리고:
- by_team
- by_product
- by_selected_model
- by_status

를 포함한다.

---

# 10. FINAL PASS CONDITION

아래가 모두 충족되면:

`MODEL_SCOUT_REQUEST_STANDARDIZATION_AND_LEGACY_BACKFILL: PASS`

- 표준 요청 계약서 존재
- 표준 Issue Form 존재
- Request Registry 존재
- Legacy backfill 완료
- UNKNOWN 분리 완료
- Parser/Normalizer 반영
- Tests PASS
- cli-smoke PASS
- hf-e2e PASS
- exact-head CI PASS
- 최종 검수서 존재

---

# 11. PR #76 CLOSEOUT

모든 Gate PASS 후:

1. PR #76 body를 실제 결과로 갱신
2. exact HEAD 기록
3. CI run IDs 기록
4. 검수서 경로 기록
5. PR #76을 Ready for review로 전환
6. Issue #75에 최종 Closeout comment 작성

그 후 상태:

`COMMANDER_MERGE_APPROVAL_REQUIRED`

main 병합은 사용자 명시 승인 전까지 금지한다.

---

# 12. NO MORE SCOPE EXPANSION

이번 지시서 이후 이 작업에는 **새로운 마무리 항목을 추가하지 않는다.**

발견된 UNKNOWN은 UNKNOWN으로 닫는다.
외부 자료가 없으면 VERIFY_REQUIRED로 닫는다.
추가 개선 아이디어는 별도 Future Work로만 기록하고 현재 Closeout에 넣지 않는다.

---

# 13. EXECUTION ORDER

`BACKFILL → REGISTRY → PARSER → TEST → CI → INSPECTION → PR READY`

중간 보고 때문에 멈추지 않는다.

완료 시:
- 결과
- 검수자료
- exact HEAD
- CI
를 저장소에 남긴다.

최종 정지 상태는 둘 중 하나뿐이다.

1. `MODEL_SCOUT_REQUEST_STANDARDIZATION_AND_LEGACY_BACKFILL: PASS`
2. `BLOCKED_APPROVAL: <one exact approval-only blocker>`
