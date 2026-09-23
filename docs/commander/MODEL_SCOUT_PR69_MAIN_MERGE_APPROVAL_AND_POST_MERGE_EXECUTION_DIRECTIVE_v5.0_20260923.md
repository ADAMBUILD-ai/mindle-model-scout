# MINDLE MODEL SCOUT
## PR #69 MAIN MERGE APPROVAL GATE + POST-MERGE ACTIVATION EXECUTION DIRECTIVE
### v5.0 — 2026-09-23

**Authority:** 신작가님 → MODEL SCOUT Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Central Issue:** #68  
**Target PR:** #69  
**Reviewed PR HEAD:** `eeefd7a597e79b237f12aa7390d2d74c5f137de6`  
**Directive branch:** `commander/model-scout-post-merge-directive-20260923`  
**Execution condition:** explicit commander/user approval to merge PR #69

---

# 1. INSPECTION RESULT

The current inspection result is:

`PRE_MERGE_GATES_PASS / DEFAULT_BRANCH_ACTIVATION_REQUIRED`

Verified:
- PR #69 is OPEN / Ready for review / mergeable / unmerged
- 3 new models are `ACQUIRED_VERIFIED`
- real peak acquisition concurrency = 3
- duplicate acquisition suppression = PASS
- unnecessary redownloads = 0
- blocked Lane B isolation = PASS
- Issue #48 delivery = `ACQUIRED_VERIFIED → TESTED_PASS → CALLBACK_SENT → DELIVERED`
- callback duplicate suppression = PASS
- synchronized Evidence contains no stale DELIVERY_PENDING status
- reviewed exact-head CI:
  - tests `35825351785` — SUCCESS
  - cli-smoke `35825351804` — SUCCESS
  - hf-e2e `35825351844` — SUCCESS

No new code or Evidence change is required before merge approval.

---

# 2. DO NOT CHANGE PR #69 BEFORE APPROVAL

Until merge approval is received:

- do not add documentation commits to PR #69
- do not rebase unless required by a verified conflict
- do not force push
- do not change workflow logic
- do not alter Evidence
- do not regenerate hashes
- do not rerun acquisition merely to produce new timestamps
- do not change main

Preserve reviewed HEAD:
`eeefd7a597e79b237f12aa7390d2d74c5f137de6`

If the PR HEAD changes for any reason, re-run exact-head CI before merge.

---

# 3. ON EXPLICIT MERGE APPROVAL — START IMMEDIATELY

When the commander/user explicitly approves main merge:

## Step 1 — Re-verify merge target
Confirm immediately:
- PR #69 is still OPEN
- Ready for review
- mergeable
- head SHA still equals the reviewed SHA, or if changed, verify new exact-head CI is PASS

## Step 2 — Merge PR #69 to main
- use normal merge
- no force push
- no squash/rebase unless repository policy requires it
- record merge commit SHA
- confirm main HEAD equals the merge result

## Step 3 — Confirm main activation
Verify main now contains:
- Lane A / Lane B separation
- bounded parallel acquisition
- actual-candidate acquisition
- approved-license gate
- remote-code fail-closed gate
- model registry
- Issue trigger
- repository_dispatch trigger
- scheduled watchdog
- dependency fingerprint cache

---

# 4. REAL ISSUE-EVENT TRIGGER PROOF

Create/use the minimum valid non-destructive MODEL SCOUT request event after main activation.

The test must prove:
- event type = `issues` or equivalent configured immediate trigger
- source issue number
- event timestamp
- workflow run ID
- workflow start timestamp
- event-to-start latency
- request fingerprint
- dedupe behavior
- no duplicate Issue
- no duplicate callback

The proof is invalid if execution started from:
- schedule
- manual workflow_dispatch
- unrelated push

Save:
`evidence/immediate-trigger-main-proof-20260923.json`

---

# 5. SELF-HOSTED DEPENDENCY CACHE PROOF

Run the activated autonomous workflow twice on the same requirements fingerprint.

## First eligible run
Record:
- run ID
- runner
- requirements SHA-256
- dependency cache state
- whether pip install ran
- bootstrap start/end
- bootstrap duration

## Second eligible run
Record:
- run ID
- same requirements SHA-256
- cache hit
- whether pip install was skipped
- bootstrap start/end
- bootstrap duration
- raw time delta

Save:
`evidence/runner-bootstrap-cache-main-proof-20260923.json`

Do not claim percentage improvement unless directly measured.

---

# 6. POST-MERGE REGRESSION GATE

After activation verify:
- central request discovery still works
- durable queue still works
- Team Router still works
- ACK still works
- cross-repo callback still works
- delivery idempotency remains intact
- model registry remains deduplicated
- scheduled watchdog remains active
- no existing DELIVERED request is duplicated

If failure occurs:
1. preserve exact Evidence
2. classify exact root cause
3. apply smallest safe fix
4. rerun
5. continue until PASS or an approval-only blocker is reached

Do not stop at the first retryable failure.

---

# 7. FINAL POST-MAIN REPORT

Create:

`docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_POST_MAIN_CLOSEOUT_20260923.md`

Required contents:
- PR #69 merge commit SHA
- final main HEAD
- immediate-trigger Issue number
- immediate-trigger workflow run ID
- event-to-start latency
- cache cold/hit run IDs
- raw cache timing measurements
- regression verification result
- acquired-model registry summary
- callback/delivery result
- duplicate suppression result
- failures/fallbacks
- unresolved blockers
- safety confirmation

Final verdict may be:

`MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_CLOSEOUT: PASS`

only after:
- immediate trigger proof PASS
- dependency cache proof PASS
- no delivery/idempotency regression
- final report committed to main through an authorized branch/PR path or otherwise preserved in repository Evidence

---

# 8. CONTINUOUS EXECUTION RULE

After explicit merge approval:

`MERGE → VERIFY MAIN → ISSUE EVENT PROOF → CACHE PROOF → REGRESSION GATE → FINAL REPORT`

Run this sequence continuously without waiting for intermediate user approval.

Only stop for:
- new permission scope
- new secret or secret rotation
- paid action
- external publication
- production deployment
- destructive/irreversible action
- force push

---

# 9. CURRENT STOP STATE

Until merge approval:

`COMMANDER_MERGE_APPROVAL_REQUIRED`
