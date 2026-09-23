# MODEL SCOUT Throughput Acceleration — Final Post-Main Closeout

Date: 2026-09-23  
Repository: `ADAMBUILD-ai/mindle-model-scout`  
Post-main PR: #70  
Directive: `MODEL_SCOUT_POST_MAIN_LIVE_PROOF_RECOVERY_AND_FINAL_CLOSEOUT_DIRECTIVE_v7.0_20260923.md`

## Verdict

`BLOCKED_APPROVAL: MODEL_SCOUT_CROSS_REPO_TOKEN requires least-privilege Issue comment write permission review/update for configured callback repositories.`

`MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_CLOSEOUT: NOT_PASS`

The default-branch trigger and dependency-cache gates passed. Final PASS is prohibited because live callback writes repeatedly return HTTP 403 and the dedicated proof request was not processed within its triggered cycle.

## Main activation

- PR #69 merge commit / current verified main HEAD: `9bf3a3cde6ee1f25a462725a8b77e963346b8bbb`
- Workflow on main contains Issue events, `repository_dispatch:model-scout-request`, the scheduled watchdog, self-hosted labels, durable state, and dependency fingerprint marker reuse.
- Main tests: run `35826071156` — SUCCESS.
- Scheduled watchdog: run `35827603171` — SUCCESS.

## Real Issue-event proof

- Proof Issue: [#71](https://github.com/ADAMBUILD-ai/mindle-model-scout/issues/71)
- Action: `issues: opened`
- Issue created: `2026-09-23T06:57:58Z`
- Workflow run: [35829269974](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/35829269974)
- Workflow created: `2026-09-23T06:58:01Z`
- Event-to-workflow latency: **3 seconds**
- Job: `107077876004`
- Runner job start: `2026-09-23T07:03:20Z`
- Event-to-job-start latency: **322 seconds**
- Runner: `mindle-model-scout`
- Completion: SUCCESS at `2026-09-23T07:08:16Z`
- Artifact: `10736467457`
- Artifact digest: `sha256:7071bbaac64858807c2e01488ae2d10bd49cf925b44da31ee6456d1c942a9a88`

GitHub recognized the Issue event immediately. The additional 319 seconds was self-hosted runner queue time behind an already-running recovery cycle, not trigger latency.

No duplicate proof Issue or duplicate callback was created. However, Issue #71 did not appear in the cycle output because `MODEL_SCOUT_LIMIT=10` was consumed by older/requeued P0 work. Therefore request-processing proof is incomplete even though event activation and job execution succeeded.

## Dependency cache cold/hit proof

Requirements SHA-256:

`E8C26DC508B9EBFB962597DECB3264AC3A8F366453020B7C57E5FB70B5F0BC03`

Persistent runner marker:

`e9500cb9-2a91-4f8e-893b-6646609e1f87`

| Run | Event | Job | Marker | pip install | Dependency step |
|---|---|---:|---|---|---:|
| 35826071143 | push | 107067956610 | absent | executed | 9 s |
| 35826198513 | issues | 107068349449 | hit | skipped | 2 s |
| 35829269974 | issues | 107077876004 | hit | skipped | 1 s |

Measured Run A→Run B dependency-step delta: **7 seconds**. No percentage claim is made.

The GitHub `actions/cache` key reported a miss, but the durable absolute runner cache contained the exact SHA-256 marker. The install script used that marker and skipped unnecessary pip installation in both later runs.

## Registry summary

Three unique models remain `ACQUIRED_VERIFIED`:

1. `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` — MIT
2. `cross-encoder/ms-marco-MiniLM-L-6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a` — Apache-2.0
3. `openai/whisper-tiny@169d4a4341b33bc18d8881c4b69c2e104e1cc0af` — Apache-2.0

Each registry record contains exact revision, file SHA-256, byte size, source URL, cache location, consuming teams, and `trust_remote_code_required:false`.

## Regression results

Passed:

- default-branch Issue trigger
- self-hosted runner execution
- durable state/persistence marker
- persistent queue and retry counters
- watchdog requeue output
- schedule watchdog
- registry integrity
- no proof-Issue duplication
- no duplicate proof callback
- existing DELIVERED state not demoted
- dependency reinstall suppression

Failed or incomplete:

1. **Callback transport — FAIL**
   - Live cycle output repeatedly reports `GitHub callback rejected with HTTP 403`.
   - Observed for existing callback Issues #47, #52, #53, #54, and #56.
   - This prevents the callback/DELIVERED regression gate from passing.

2. **Dedicated proof request processing — INCOMPLETE**
   - Issue #71 triggered the workflow but was not selected inside the 10-request cycle limit.
   - Backlog/retry ordering must be corrected or the proof request must be allowed to reach a later cycle.

3. **Geometry worker — FAIL**
   - `ModuleNotFoundError: No module named 'scipy'`.
   - Safe code follow-up: pin a compatible scipy dependency and rerun focused geometry tests.

4. **Hugging Face search — RETRYABLE**
   - HTTP 500 occurred for several queued searches in the proof cycle.
   - These are correctly classified `FAILED_RETRYABLE`; no false PASS was issued.

## Exact approval-only blocker

The workflow assigns `GITHUB_TOKEN` from the `MODEL_SCOUT_CROSS_REPO_TOKEN` secret. Discovery succeeds, but Issue callback comment writes return HTTP 403.

Required approval/action:

- inspect the token’s repository access without exposing it;
- grant only the minimum Issue comment write permission required on configured callback repositories, or replace it with an equivalently least-privileged project token;
- rerun Issue #71 processing and confirm one callback receipt plus idempotent repeat;
- do not rotate, broaden, or disclose the secret without explicit approval.

## Safety confirmation

No force push, deletion, production deployment, external publication, paid compute, secret disclosure, secret rotation, or permission expansion was performed. Existing main and DELIVERED records were not overwritten.

## Evidence paths

- `evidence/immediate-trigger-main-proof-20260923.json`
- `evidence/runner-bootstrap-cache-main-proof-20260923.json`
- `evidence/post-main-regression-proof-20260923.json`
- `docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_POST_MAIN_CLOSEOUT_20260923.md`
