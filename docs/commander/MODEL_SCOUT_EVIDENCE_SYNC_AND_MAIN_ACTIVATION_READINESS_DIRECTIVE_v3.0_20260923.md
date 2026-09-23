# MINDLE MODEL SCOUT
## EVIDENCE SYNCHRONIZATION + MAIN ACTIVATION READINESS DIRECTIVE
### v3.0 — 2026-09-23

**Authority:** 신작가님 → MODEL SCOUT Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Central Issue:** #68  
**Active PR:** #69  
**Work branch:** `improvement/model-scout-throughput-20260923`  
**Current verified HEAD:** `22451bf5f4e08738b7c339f00d4a45429b39e7e9`  
**Current PR state:** OPEN / DRAFT / mergeable / unmerged

---

# 1. VERIFIED CURRENT STATE

The throughput architecture itself is substantially proven.

Verified completed Evidence:
- 3 new unique models reached `ACQUIRED_VERIFIED`
  - `openai/whisper-tiny`
  - `BAAI/bge-small-en-v1.5`
  - `cross-encoder/ms-marco-MiniLM-L-6-v2`
- exact revisions, licenses, file sizes and SHA-256 are recorded
- real parallel acquisition reached peak concurrency 3
- duplicate acquisition rerun suppressed all 3
- verified cache avoided redownloads
- blocked Issue #55 Lane B did not stop unrelated Lane A
- Issue #48 completed `TESTED_PASS → CALLBACK_SENT → DELIVERED`
- callback idempotency remained clean
- live acquisition workflow passed
- exact-head CI for current HEAD passed:
  - tests `35823504489` — SUCCESS
  - cli-smoke `35823504502` — SUCCESS
  - hf-e2e `35823504495` — SUCCESS

The remaining work is **closeout correctness and default-branch activation proof**, not another redesign.

---

# 2. VERIFIED REMAINING GAPS

## GAP-A — Evidence files are not fully synchronized

The current inspection/report set contains stale intermediate language.

Examples that must be corrected:
- `evidence/throughput-idempotency-20260923.json`
  still contains `PENDING_DELIVERY_LANE_PROOF` although delivery idempotency is now proven.
- `evidence/throughput-benchmark-20260923.json`
  still contains `PENDING_DELIVERY_LANE_PROOF` / `LIVE_ACQUISITION_PASS_DELIVERY_PENDING` despite successful delivery Evidence.
- `docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_CLOSEOUT_20260923.md`
  contains earlier implementation/evidence HEAD references and must be synchronized to the final pre-merge HEAD.

No final PASS may be claimed while machine-readable Evidence contradicts the narrative report.

## GAP-B — Immediate Issue-event trigger cannot be proven from an unmerged PR branch

GitHub evaluates `issues` / `repository_dispatch` workflow triggers from the default branch.

The improved trigger exists on PR #69 only.

Therefore:
- do not fake Issue-event latency proof on the branch
- do not directly modify main
- prepare merge-ready Evidence first
- main activation requires explicit commander approval

## GAP-C — Self-hosted dependency cache needs real default-branch execution

The new requirements-fingerprint cache is structurally implemented, but a valid cold-run vs cache-hit measurement requires the updated workflow to execute from default branch.

That measurement belongs to the **post-merge activation verification stage**, after explicit merge approval.

---

# 3. PHASE A — EXECUTE NOW WITHOUT FURTHER USER APPROVAL

General Work must complete all safe pre-merge work continuously.

## A-1. Synchronize idempotency Evidence

Update:
`evidence/throughput-idempotency-20260923.json`

Replace stale pending delivery language with exact verified values from current Evidence:
- delivery idempotency = PASS
- callback duplicate suppressed = true
- duplicate callback count = 0
- acquisition duplicate suppression = 3
- unnecessary redownloads = 0
- verified cache reused = true
- reference delivery run/artifact/callback URL exactly

Do not invent values. Reuse already verified Evidence.

## A-2. Synchronize throughput benchmark

Update:
`evidence/throughput-benchmark-20260923.json`

It must accurately reflect:
- 3 actual new model acquisitions
- peak concurrency 3
- measured acquisition durations
- measured delivery duration
- cache/idempotency result
- exact live acquisition workflow run
- exact delivery workflow run
- immediate trigger = `BLOCKED_BY_DEFAULT_BRANCH_ACTIVATION`, not PASS
- dependency cache benchmark = `PENDING_POST_MERGE_DEFAULT_BRANCH_PROOF`

Do not leave stale `DELIVERY_PENDING` values.

## A-3. Synchronize final inspection report

Update:
`docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_CLOSEOUT_20260923.md`

The report must reference the **new exact HEAD after the Evidence synchronization commit**.

Required verdict before default-branch activation:
`PRE_MERGE_GATES_PASS / DEFAULT_BRANCH_ACTIVATION_REQUIRED`

Do not use overall FINAL PASS yet.

The report must clearly separate:

### PRE-MERGE PASS
- acquisition architecture
- 3 new ACQUIRED_VERIFIED models
- real concurrency
- cache redownload suppression
- Lane isolation
- delivery proof
- callback idempotency
- exact-head CI

### POST-MERGE REQUIRED
- real Issue-event immediate-trigger latency
- real self-hosted dependency cache cold/hit benchmark

## A-4. Exact-head CI after final human-authored synchronization commit

After editing Evidence/report:
1. push one human-authored synchronization commit
2. run/verify fresh exact-head:
   - tests
   - cli-smoke
   - hf-e2e
3. if HEAD changes, rerun on the new HEAD
4. update PR #69 with exact run IDs

Do not reuse CI from an older HEAD for final readiness.

## A-5. PR #69 readiness state

When Phase A is fully PASS:
- update PR #69 body with synchronized Evidence
- add a concise closeout comment
- mark PR #69 **Ready for review**
- do not merge main
- stop only at `COMMANDER_MERGE_APPROVAL_REQUIRED`

---

# 4. PHASE B — EXECUTE ONLY AFTER EXPLICIT MAIN MERGE APPROVAL

This phase is already defined now so Work can continue immediately once approval exists.

## B-1. Merge PR #69 to main

Only after explicit commander/user approval.

Use exact expected HEAD.

No force push.

## B-2. Verify main contains expected workflow

Confirm main contains:
- `issues` trigger
- `repository_dispatch:model-scout-request`
- 15-minute schedule retained as watchdog/fallback
- dependency fingerprint cache
- Lane A / Lane B implementation
- registry/export logic

## B-3. Real immediate Issue-event trigger proof

Create or use the minimum valid non-destructive MODEL SCOUT request event.

Required Evidence:
- source Issue number
- issue event timestamp
- workflow run ID
- workflow start timestamp
- event-to-start latency
- request fingerprint
- dedupe behavior
- no duplicate issue/callback

Do not use schedule or manual dispatch as a substitute for this proof.

Save:
`evidence/immediate-trigger-main-proof-20260923.json`

## B-4. Self-hosted dependency cache benchmark

Run the updated autonomous workflow at least twice on the same dependency fingerprint:

Run 1:
- cold/miss or first eligible state
- bootstrap duration

Run 2:
- same requirements fingerprint
- cache/marker hit
- bootstrap duration
- dependency reinstall avoided

Save:
`evidence/runner-bootstrap-cache-main-proof-20260923.json`

Do not invent a speed percentage.
Report raw measured times and delta.

## B-5. Final post-main inspection

Create/update:
`docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_POST_MAIN_CLOSEOUT_20260923.md`

Required:
- main merge commit
- main HEAD
- Issue-event run ID
- event-to-start latency
- cache cold/hit results
- all previously verified acquisition/delivery Evidence
- any failures/fallbacks
- final unresolved blockers, if any

Final verdict may be `PASS` only if both immediate trigger and cache proof succeed.

---

# 5. FAILURE HANDLING

Do not stop at first failure.

For every failure:
1. preserve Evidence
2. classify exact root cause
3. apply safe fallback
4. rerun
5. continue

Allowed safe actions include:
- workflow correction on feature branch before merge
- test fixture correction
- cache-marker logic correction
- deterministic event/dedupe fix
- documentation/Evidence synchronization
- rerun failed non-paid workflows

Stop only for:
- main merge approval
- new permission scope
- secret creation/rotation
- paid resources
- external publication
- production deployment
- destructive/irreversible action
- force push

---

# 6. REQUIRED FINAL PRE-MERGE CHECKLIST

Before requesting merge approval, all must be true:

- [ ] throughput-idempotency Evidence synchronized
- [ ] throughput-benchmark Evidence synchronized
- [ ] inspection report synchronized to exact HEAD
- [ ] no stale `DELIVERY_PENDING` claims remain
- [ ] 3 ACQUIRED_VERIFIED models still present
- [ ] real concurrency Evidence intact
- [ ] delivery Evidence intact
- [ ] callback idempotency Evidence intact
- [ ] exact-head tests PASS
- [ ] exact-head cli-smoke PASS
- [ ] exact-head hf-e2e PASS
- [ ] PR #69 body updated with exact Evidence
- [ ] PR #69 marked Ready for review
- [ ] no main merge performed

Then stop with exactly:
`COMMANDER_MERGE_APPROVAL_REQUIRED`

---

# 7. EXECUTION ORDER — START NOW

1. Read this directive.
2. Stay on `improvement/model-scout-throughput-20260923`.
3. Synchronize the two stale JSON Evidence files.
4. Synchronize the inspection report.
5. Commit and push.
6. Run fresh exact-head CI.
7. Fix and rerun any failures.
8. Update PR #69 body/comment with exact Evidence.
9. Mark Ready for review.
10. Stop at `COMMANDER_MERGE_APPROVAL_REQUIRED`.

Do not wait for another instruction before completing Phase A.
