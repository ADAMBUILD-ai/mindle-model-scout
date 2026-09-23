# MINDLE MODEL SCOUT
## POST-MAIN LIVE PROOF RECOVERY + FINAL CLOSEOUT DIRECTIVE
### v7.0 — 2026-09-23

**Authority:** 신작가님 → MODEL SCOUT Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Central Issue:** #68  
**Merged throughput PR:** #69  
**Main activation commit:** `9bf3a3cde6ee1f25a462725a8b77e963346b8bbb`  
**Active post-main PR:** #70  
**Post-main work branch:** `post-main/model-scout-activation-closeout-20260923`

---

# 1. CURRENT VERIFIED STATE

PR #69 is merged to `main`.

PR #70 currently contains only the post-main directive commit:
`16714f282d846a4775cfe326c61caf674c56ac1f`

As of this inspection, the following required post-main Evidence files are **NOT yet present**:
- `evidence/immediate-trigger-main-proof-20260923.json`
- `evidence/runner-bootstrap-cache-main-proof-20260923.json`
- `docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_POST_MAIN_CLOSEOUT_20260923.md`

Therefore the post-main mission has **not yet been executed to Evidence completion**.

This directive is a recovery/continuation order. It is not another design phase.

---

# 2. START NOW — EXECUTE, DO NOT ONLY DOCUMENT

General Work must act immediately.

Do not stop after:
- reading the directive
- verifying the workflow file
- creating a test Issue
- seeing a queued run
- one cache run
- one failed attempt
- one successful sub-step

Continue until the final post-main closeout Evidence exists in GitHub.

---

# 3. FIRST ACTION — VERIFY MAIN ACTIVATION

Verify from `main`:

- main contains merge commit `9bf3a3cde6ee1f25a462725a8b77e963346b8bbb`
- `.github/workflows/autonomous-model-scout.yml` contains:
  - `issues` trigger
  - `repository_dispatch` trigger
  - schedule watchdog
  - dependency fingerprint cache
- self-hosted labels remain:
  - `self-hosted`
  - `model-scout`
- the cross-repo token reference is still present
- the existing durable state directory remains unchanged

Record this in the final Evidence, but do not stop here.

---

# 4. REAL ISSUE-EVENT TRIGGER PROOF — REQUIRED

Create one minimal non-destructive dedicated proof Issue in the MODEL SCOUT repository.

Recommended title:

`[P0][MODEL SCOUT][TRIGGER PROOF] post-main immediate trigger verification 20260923`

The Issue body must clearly contain a valid MODEL SCOUT request marker so the existing discovery logic recognizes it, but the requested action must be safe, free, and non-production.

Immediately after Issue creation:

1. capture Issue URL/number
2. capture Issue created_at
3. identify the workflow run caused by the `issues: opened` event
4. capture:
   - run ID
   - event type
   - run created_at
   - run started_at / first job start
   - event-to-start latency
5. verify the request is either:
   - newly fingerprinted and safely processed, or
   - deterministically deduped
6. verify no duplicate central Issue/callback is created

Save:

`evidence/immediate-trigger-main-proof-20260923.json`

## Trigger failure handling

If no run appears:
- do not substitute schedule/manual dispatch
- inspect:
  1. default-branch workflow presence
  2. YAML trigger syntax
  3. Actions enablement
  4. event filter
  5. concurrency key collision
  6. workflow permissions
- apply the smallest safe fix on PR #70
- test
- merge only the minimal fix if required and exact CI passes
- repeat the real Issue event

If the run is created but waits for a self-hosted runner:
- trigger proof may still show GitHub event recognition
- but do not claim full PASS until job execution starts
- continue with runner audit below

---

# 5. SELF-HOSTED RUNNER / CACHE PROOF — REQUIRED

The cache proof must use the same requirements fingerprint.

## Run A — first eligible post-main execution

Capture:
- workflow run ID
- runner name
- job ID
- requirements SHA-256
- whether marker existed
- whether dependency install executed
- bootstrap start/end timestamps
- bootstrap duration

## Run B — second eligible execution

Trigger a second safe execution using the same dependency fingerprint.

Capture:
- workflow run ID
- runner name
- same requirements SHA-256
- cache/marker hit
- whether dependency install was skipped
- bootstrap start/end timestamps
- bootstrap duration
- raw delta from Run A

Save:

`evidence/runner-bootstrap-cache-main-proof-20260923.json`

PASS requires:
- same fingerprint
- second run reuses the verified cache/marker
- no unnecessary reinstall

Do not delete the global cache just to manufacture a cold result.
If the first observed post-main run is already a cache hit, record the actual state and use the earliest available post-main run/log that shows creation of the same marker. If unavailable, classify exactly and instrument a **new non-destructive proof marker namespace** rather than deleting production cache.

---

# 6. SELF-HOSTED RUNNER FAILURE RECOVERY

If the `model-scout` self-hosted runner does not execute:

Run this audit immediately:
1. repository Actions status
2. workflow run/job state
3. required labels vs runner labels
4. runner online/offline visibility
5. runner service account and workspace reachability
6. Python/runtime availability
7. durable state directory write test
8. token/permission errors

Do not respond “runner unavailable” and stop.

Apply safe fixes where possible:
- workflow label correction
- path correction
- Python bootstrap correction
- non-destructive runner-state repair
- retry/requeue

Only stop if resolution requires:
- PC access not available to Work
- login/permission escalation
- secret change/rotation
- destructive service action requiring approval

If such a blocker is reached, preserve exact Evidence and state the one precise approval/action required.

---

# 7. POST-MAIN REGRESSION GATE

After the trigger/cache proof, verify:

- central request discovery
- durable queue state
- watchdog recovery
- Team Router path
- ACK behavior
- cross-repo callback
- delivery ledger
- callback idempotency
- model registry dedupe
- existing DELIVERED stability
- scheduled watchdog still configured

Do not create unnecessary duplicate deliveries merely to test.

Use existing route fingerprints and safe dedupe-aware paths.

Save machine-readable regression Evidence if useful:
`evidence/post-main-regression-proof-20260923.json`

---

# 8. FINAL INSPECTION REPORT

Create:

`docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_POST_MAIN_CLOSEOUT_20260923.md`

Required fields:
- main activation commit
- current main HEAD
- proof Issue number/URL
- issue event timestamp
- trigger workflow run ID
- event-to-start latency
- runner/job ID
- requirements fingerprint
- cold/miss and hit run IDs
- raw bootstrap timings
- install executed/skipped state
- regression results
- acquired model registry summary
- duplicate suppression result
- failures and fixes
- exact unresolved blocker, if any
- safety confirmation

Final verdict:
`MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_CLOSEOUT: PASS`

only if all post-main gates pass.

---

# 9. PR #70 CLOSEOUT

All new post-main Evidence must be committed to:

`post-main/model-scout-activation-closeout-20260923`

Update PR #70 with:
- exact HEAD
- exact run IDs
- Evidence paths
- final verdict

If only Evidence/docs are added and no executable code changes remain:
- mark PR #70 Ready for review
- do not merge automatically unless explicitly approved

If a minimal code fix was required:
- run exact-head tests / cli-smoke / hf-e2e before Ready status

---

# 10. CONTINUOUS EXECUTION RULE

Execute:

`MAIN VERIFY → PROOF ISSUE → ISSUE EVENT RUN → CACHE RUN A → CACHE RUN B → REGRESSION → FINAL REPORT`

without stopping between steps.

On failure:
`Evidence → Exact Cause → Safe Fix → Rerun → Continue`

Do not return a generic “cannot”.

---

# 11. FINAL STOP STATE

Stop only at one of:

`MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_CLOSEOUT: PASS`

or

`BLOCKED_APPROVAL: <one exact approval-only blocker>`
