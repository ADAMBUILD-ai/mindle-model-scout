# AURA #136 실제 모델 파일 인계 — 2026-10-14
실제 확보 완료: Qwen/Qwen3-4B@1cfa9a7208912126459214e8b04321603b3df60c, 12개 파일, 8060925056 bytes.
실행 source main: 54e1cdfea0714102820626a8a19d9a366b439a72.
실제 성공 Actions: 38428438316 / job115403924678 / artifact11829742746.
Artifact ZIP SHA256: ac4bf3968d67d380d32410abb1c5f74dac2c6155c434ff9220ef4ef8e688d0f0.
12개 파일의 실제 크기/SHA256과 공식 Git/LFS 대조는 07 receipt에 모두 있다.

MODEL_ROOT:
C:\actions-runner\_work\_state\mindle-model-scout\aura136-pinned-models\Qwen--Qwen3-4B\1cfa9a7208912126459214e8b04321603b3df60c
PYTHON_EXE:
C:\actions-runner\_work\_tool\python311-service\python.exe
실제 실행 호스트: mindle-model-scout self-hosted Windows runner.
Python3.11.9 / torch2.14.0 / transformers4.56.2 설치 metadata 확인. 모델 실제 추론은 0회.

## 인계 책임
Model Scout General Work의 파일 확보·고정 버전·라이선스·전체 해시 검증은 완료.
Owner PC가 같은 호스트인지 단정하지 않는다. 같은 호스트라면 실제 owner 계정의 파일 접근을 검증하고, 다른 호스트라면 이 기존 파일을 승인된 경로로 전달한 후 도착 bytes/hash를 대조한다.
이력상 기존 소형 3개는 건축/schema FAIL이며 현재 bounded cache에는 config만 있었다. 그 파일들을 다시 받거나 같은 실패 시험을 반복하지 않는다.
이번 4B는 새로운 검색으로 찾은 모델이 아니라 기존 qualified 후보를 정확히 고정해 확보한 것이다. 품질 합격은 아직 아니다.

## Desktop 실행 입력
08_QWEN4B_DESKTOP_CANDIDATE_MANIFEST.json은 기존 AURA benchmark driver의 family/revision/files/license/runtime 필드를 맞춘 후보 자료다. approvedDesktopInference=false, resourceReviewRef=null을 유지한다.
40960은 configured context이며 실측 완료가 아니다. 실제 입력 token수/output reserve와 모델 config를 대조하여 usable context를 검수한다.
현재 승인된 AURA branch의 최신 scripts/run_aura_136_local_benchmark.py와 release contract를 먼저 읽고, 실제 owner 접근·RAM·runtime import·manifest/input/driver hashes를 확인한 다음 정확한 승인 범위의 release를 발행한다.
새로운 다운로드/설치/유상 API 없이 현재 준비된 파일 세트로 진행한다.
확인한 6277a78345ee0f6f7c54971be8d5e41b42583881 driver는 raw JSON prompt와 torch.float32를 사용한다. Qwen3 native chat-template 및 dtype/메모리 적합성을 검수한 뒤 실행한다. 잘못된 prompt나 부족한 RAM으로 인한 실패를 모델 품질 판정과 혼동하지 않는다.
실행 명령 구조: python scripts/run_aura_136_local_benchmark.py --release ACTUAL_RELEASE.json --manifest ACTUAL_APPROVED_MANIFEST.json --model-root CURRENT_VERIFIED_ROOT --input ACTUAL_INPUT.json --output NEW_RECEIPT_DIR
이 명령은 구조 안내다. actual release/input/owner 상태를 꾸며 생성하지 않는다.

## 실제 검수 순서
동일한 기존 architectural lexical set -> 한국어/영어·공간 의미·JSON 수동 검수 -> 합격하면 승인된 실제 KR10/GLOBAL10 source-bound 입력 -> context/원문 인용/전체 ANALYSIS_FIELDS 검수 -> 실제 inference receipt -> AURA Commander TESTED_PASS/callback 검수.
모든 runtime version, raw prompt/output, invocationId, token/time/hash/exit를 반환한다.
최초 실제 호출 전 current Python 실행파일·modelRoot와 전체 파일 일치를 재확인한다.
설치/UI/Windows 복구·Pilot10 및 product release 범위는 확대하지 않는다.
