# MODEL SCOUT obsolete queue reconciliation — 2026-09-27

## Reproduced defect

Autonomous run #586 (`36297157319`) completed SUCCESS on main `747bc28181e0b0a65b4b6d1d5b8af32d94b666f6`, but its Evidence artifact `10923944181` reported `results=[]`, `eligible_request_count=1`. The one actionable record was central AVORA #115's obsolete `resource=model` fingerprint `2f6c0eae4fc054da510176eb1c057354af549db092b3cc97d06d562ebc567686`, retry_count=2. The current canonical #115 is a separate `resource=tool` fingerprint `8ecfe72289b5b8027e7b6348a4821125a6405eba167843a090b0f559e6ebfd92` in BLOCKED_INPUT. Discovery never returns the old fingerprint, so it cannot execute, yet the runner reports eligible work.

## Correction

- Add a terminal `SUPERSEDED` state for old, actionable normalizations of the *same fetched open GitHub Issue*.
- Reconcile against current raw Issue normalization before dispatch. Only old QUEUED, FAILED_RETRYABLE or BLOCKED_INPUT records are retired. Preserve retry count and prior failure in the `superseded_requests` audit table. Do not touch RUNNING, EVIDENCE_READY, DELIVERED, FAILED_TERMINAL or intentionally scoped subrequests.
- Publish retired fingerprints in autonomous discovery diagnostics. A truly empty queue now has eligible_request_count=0 and a truthful idle reason.
- No global retry reset, no deletion, no claim of newly acquired model or product PASS.

## Verification gate

Local targeted tests: 46 PASS, including exact Issue #115 duplicate normalization, idempotent reconciliation and preservation of delivered/scoped work. CI tests, cli-smoke, hf-e2e and the post-merge autonomous Evidence must be verified before this correction is accepted operationally.

Remaining product work: central #118 requires accessible exact AVORA assets, verified pre-existing SAM/SigLIP package bytes and a dedicated AVORA QA adapter. The accepted Blender renderer should not be reacquired. Historical FAILED_TERMINAL records are retained for case-specific audit, not globally reset.

Sources: [run #586](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36297157319), [AVORA #115](https://github.com/ADAMBUILD-ai/mindle-model-scout/issues/115), [reuse #118](https://github.com/ADAMBUILD-ai/mindle-model-scout/issues/118).

## Immediate execution trigger gap found after PR #121

PR #121 merged as `b8715603e208de4eb22b32e2efa104c767f824f4`, with exact-head tests #348, cli-smoke #224 and hf-e2e #229 SUCCESS. Its push ran the tests workflow but did **not** start the autonomous workflow, because the latter's push path filter omitted `persistent_queue.py`, `live_automation.py` and `request_queue.py`. This can make a corrected main appear operational while the worker waits for the next schedule. Follow-up fixes the filter to `src/model_scout/**`. A new autonomous run on the follow-up merge is required for post-merge queue proof; PR #121's CI alone is insufficient.
