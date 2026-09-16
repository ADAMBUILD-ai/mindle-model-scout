# MODEL SCOUT execution reopen directive — 2026-09-16

Status: **REOPENED / NOT FINAL**

Owner: ADAMBUILD-ai

## Immediate execution gates
1. Verify current value/effective members of `MODEL_SCOUT_CONFIGURED_REPOS` and ensure `ADAMBUILD-ai/mindle-model-scout` is included so Issues #47-#58 can be discovered, or implement direct central-issue ingestion.
2. Re-run the autonomous cycle and require the artifact queue to contain new fingerprints sourced from Issues #47-#58. If absent, stop and fix discovery before any scheduler work.
3. Integrate `runtime_validation.run_runtime_validation()` into the autonomous live path. Current `run_live_cycle()` must no longer stop at FOUND for requests that require actual runtime proof.
4. Implement generic safe executors/adapters by request class. Do not hard-code one model/request.
5. For at least three heterogeneous actual team requests, prove `REQUESTED -> FOUND -> DOWNLOADED -> TESTED_PASS -> DELIVERED` with exact revision/commit, file hash, runtime/hardware/settings, output file, license, and source-issue callback.
6. Mark privileged/cost/login/secret/production/destructive operations `BLOCKED_APPROVAL`; continue all safe work automatically.
7. Scheduler/watchdog success is supporting infrastructure evidence only; it is not business-work completion evidence.

## Prohibited closeout shortcuts
- workflow SUCCESS with `results=[]`
- idle queue containing only legacy requests
- artifact existence without a new team-request lifecycle
- one-off `run_fast_delivery.py` AGRI result generalized to all request types
- FOUND or callback-only result represented as TESTED_PASS

## Final acceptance
FINAL only after new real team requests #47-#58 are visibly consumed and at least three heterogeneous requests complete with real TESTED_PASS evidence and callbacks. Until then: `VERIFY_REQUIRED`.
