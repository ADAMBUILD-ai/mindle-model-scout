# Model Scout 전체 점검 및 복구 실행 기준

기준: 2026-10-13, 운영 main 3a7dd50b8834347e3e4fea02cca256282f9e9903.
관찰: Actions 38408956950 / job 115335911015. 현재 운영과 수정 후보를 구분한다.

## 운영 판정
runner 정상 작동, 10개 저장소 조회 성공. 실제 cycle results=0, idle=NO_ELIGIBLE_REQUESTS.
큐 61개 기록: MISROUTED15, FAILED_TERMINAL14, DELIVERED10, SUPERSEDED5, ACQUIRED_VERIFIED13, BLOCKED_INPUT4.
이는 큐 기록 수이며 모델 수/현재 파일 존재 수/제품 품질 합격 수가 아니다.

## 원인과 수정
1. #139 CONTROL 지시가 generic model request로 오접수. 금지 문구 embedding/OCR가 실행기 선택에 영향을 주고 650MB 제한으로 실패했다.
   중앙 [CONTROL] 이슈를 모델 접수에서 제외한다. 기존 quarantine 경로가 prior state/error를 보존하며 이전 실패를 격리한다. #136 실제 요청은 보존한다.
2. Actions 프로세스 성공이 미해결 제품 요청을 숨긴다.
   cycle operational_health와 Actions summary에 unresolved 요청/state/exact error/next action을 출력한다. acquired만으로 delivered 또는 product PASS를 만들지 않는다.
3. 설정 저장소 누락은 registry가 실제 보완하므로 접근 실패가 아니다. 이전 관제 설명을 정정한다.
4. AURA #136 classifier-only guard는 올바르다. 유지한다. 생성형 파일/runtime 및 실제 출처가 없는데 재시도해 성공으로 만들지 않는다.
5. 역사적 Linux 임시 weights와 현재 Windows 자산 인계가 끊겼다. 기존 전체 manifest를 사용한 offline verifier를 제공한다. 현재 존재/전달 성공은 별도 실제 evidence가 필요하다.

## 현재 파일 인계 절차
기존 asset owner가 실제 보관 호스트/경로/관찰시각을 기록한다. historical path를 current path로 쓰지 않는다.
manifest는 단일 modelId/revision에 대응해야 하며 전체 파일 path/bytes/SHA256/license snapshot을 포함한다.
실행: python scripts/verify_existing_model_asset.py --manifest EXISTING_MANIFEST.json --model-root EXISTING_ROOT --python-exe EXISTING_PYTHON --output NEW_RECEIPT.json
검증기는 네트워크/다운로드/설치/추론을 하지 않는다. missing/mismatch/unlisted/path escape 차단. Runtime probe는 기존 Python의 버전/설치된 package metadata만 읽는다.
FILES_VERIFIED_NOT_PRODUCT_PASS는 파일 검증만 뜻한다. approved runtime과 실제 inference는 다른 Gate다.
타호스트 전달은 승인된 기존 자산 복사 후 도착 전체 hash 대조가 필요하다. Python Linux 환경을 Windows executable로 복사해 사용하지 않는다.
생존 사본이 없으면 정확한 ASSET_UNAVAILABLE blocker를 반환한다. 새 검색/구매/secret 변경으로 은폐하지 않는다.

## 미해결 실행 책임
- #139: Model Scout control owner. B01 defcd851b16c795cc716dd34a562b36cfcbaf9fe 보존. 후보48 반복 정리 금지.
- #136: pinned causal 모델/runtime 및 실제 입력 확보 후 데스크탑 actual inference; source/언어/건축/schema/context 수동 검수까지 필요.
- #47/#115: actual GLB 및 verified render package/license/runtime 입력 필요. generic 모델 검색으로 대체하지 않는다.
- #118: exact AVORA geometry/masks/approved reference 필요. re-scout 금지.
- #133: 원래 runtime error stack을 보존, 실제 입력과 지원 pipeline 요구를 대조한 후 제한된 replay. 이번 #136 작업으로 수정하지 않는다.
- #134/#135 및 나머지 FAILED_TERMINAL: fingerprint별 full error/실제 요구사항/지원 executor/라이선스를 대조한다. 원인 수정 없이 retry counter reset 금지.
- ACQUIRED_VERIFIED13: current asset existence, full file manifest, runtime identity, consumer acceptance를 별도 확인한다. 대장 갱신만으로 model delivered를 만들지 않는다.

## 운영 적용 Gate
수정은 별도 branch/PR 후보다. main 직접 merge/production deploy/force push 없음.
CI 및 리뷰 후 승인된 기존 통합 경로로 반영해야 live runner가 이 코드를 실행할 수 있다.
적용 후 canonical cycle에서 #139 신규 검색0/기존 실패 보존 격리/operational_health를 실제 확인한다.
issue_comment arbitrary command 실행을 추가하지 않는다. CONTROL 문장은 실행 허가나 프로그램이 아니며 typed 승인 scope를 가진 명시적 executor가 필요하다.
파일 인계 receipt가 도착하면 current asset 확인 -> 승인된 desktop inference -> 제품 quality review -> callback exact readback 순으로 진행한다.
이번 수정 테스트는 모델 추론/제품 PASS/스케줄러 운영 정상화 증거가 아니다.
