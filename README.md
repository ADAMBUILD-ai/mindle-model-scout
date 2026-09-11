# MINDLE MODEL SCOUT

Hugging Face 기반 AI Model Scout Agent

## Mission
사용자가 필요한 AI 기능을 자연어로 입력하면 Hugging Face에서 적합한 모델·Dataset·Space 후보를 탐색하고,
조사 · 분류 · 평가 · 추천하여 근거가 남는 후보와 Model Card/Scout Report를 제시한다.

## Core Flow
Requirement
→ Requirement Profile
→ Resource Selection (`model|dataset|space|all`)
→ Hugging Face Search
→ Candidate Collection
→ Metadata Normalization / Deduplication
→ Requirement Filter
→ License Gate
→ Explainable Scoring
→ Ranking
→ Safe Recommendation
→ Model Card
→ JSON/Markdown Comparison Report

## Safety / Evidence Contract
- 라이선스가 확인되지 않은 후보는 `LICENSE_REVIEW_REQUIRED`로 유지한다.
- 상업용 요청에서 비상업용(`-nc` / non-commercial) 라이선스는 `LICENSE_NOT_PERMITTED`로 차단한다.
- `LICENSE_NOT_PERMITTED`, `LICENSE_REVIEW_REQUIRED`, `REJECT` 후보는 추천 대상으로 선택하지 않는다.
- 확인하지 않은 사실을 승인 상태로 승격하지 않는다.
- Hugging Face 응답이 비정상 구조이거나 네트워크 호출이 실패하면 fail-closed 오류로 처리한다.
- 검색 `limit`은 1~100 범위로 제한하여 불필요한 대량 호출을 방지한다.
- 결과에는 원문 요구, 실제 upstream search query/query plan, 후보 수, 리소스 종류, 점수/상태/이유, 비교표, Model Card가 포함된다.

## CLI
기본 Model JSON 결과:

```bash
python -m src.model_scout.scout "commercial TTS license downloads 1000" --limit 20 --format json
```

Markdown 보고서:

```bash
python -m src.model_scout.scout "상업용 TTS 라이선스 필요 다운로드 1000 이상" --limit 20 --format markdown --top-n 5
```

리소스 선택(모델·데이터셋·Space·전체):

```bash
python -m src.model_scout.scout "squad" --resource dataset --limit 10
python -m src.model_scout.scout "image generation" --resource space --limit 10
python -m src.model_scout.scout "document AI" --resource all --limit 10
```

반복 Watch / Snapshot 변화 감지:

```bash
python -m src.model_scout.scout "tts" --resource model --limit 20 --watch-snapshot ./artifacts/tts-snapshot.json
```

## Watch Behavior
Snapshot 기반 반복 실행에서 다음 변화를 구분한다.
- first run
- no change
- added candidate
- removed candidate
- materially changed candidate
- corrupt/invalid snapshot
- failed write without destroying the previous valid snapshot

Watch identity는 `(resource_type, model_id)` 기준이라 같은 ID가 Model/Dataset/Space에 존재해도 별도 후보로 관리한다.

## Development Principle
- Hugging Face 전담 독립 제품으로 먼저 완성한다.
- 다른 MINDLE 시스템과의 통합은 이후 단계에서 진행한다.
- 기존 SSOT와 승인사항을 최우선 기준으로 유지한다.
- 이미 검증된 기능은 재작성하지 않고, 부족한 부분만 보강한다.
- 완료는 코드가 아니라 `tests + live hf-e2e + cli-smoke + artifact + post-merge tests` Evidence로 판단한다.

## Current Phase
SCOUT-GATE-04 — Multi Resource Scout Expansion — **COMPLETED**

- PR #25 merged to `main`
- PR head tests / live hf-e2e / cli-smoke: SUCCESS
- post-merge main tests: SUCCESS
- detailed evidence: `CURRENT_EXECUTION_CONTROL.md`

## Command Structure
신작가님
→ 아키 사령관
→ MODEL SCOUT 개발·검수·통합
