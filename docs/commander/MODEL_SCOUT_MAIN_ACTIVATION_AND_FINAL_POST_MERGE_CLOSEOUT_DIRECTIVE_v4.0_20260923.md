# MINDLE MODEL SCOUT
## MAIN ACTIVATION + FINAL POST-MERGE CLOSEOUT DIRECTIVE
### v4.0 — 2026-09-23

**Authority:** 신작가님 → MODEL SCOUT Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Central Issue:** #68  
**Active PR:** #69  
**Work branch:** `improvement/model-scout-throughput-20260923`  
**Pre-merge verified HEAD before this directive commit:** `e9b8b59535a844e4030eb193e47a1af842f151d5`

---

# 1. VERIFIED PRE-MERGE RESULT

Current verified verdict:

`PRE_MERGE_GATES_PASS / DEFAULT_BRANCH_ACTIVATION_REQUIRED`

Verified:
- 3 new `ACQUIRED_VERIFIED` models
- peak acquisition concurrency 3
- 3 duplicate acquisitions suppressed
- zero unnecessary redownloads
- blocked Lane B isolation proven
- Issue #48 `ACQUIRED_VERIFIED → TESTED_PASS → CALLBACK_SENT → DELIVERED`
- callback duplicate suppression PASS
- synchronized benchmark/idempotency Evidence
- fresh exact-head CI on the prior reviewed HEAD:
  - tests `35824824472` SUCCESS
  - cli-smoke `35824824503` SUCCESS
  - hf-e2e `35824824513` SUCCESS

PR #69 is Ready for review and unmerged.

---

# 2. THIS DIRECTIVE'S PURPOSE

The remaining mission is to activate the already-reviewed throughput changes on `main` and prove the two default-branch-only behaviors:

1. real immediate Issue-event trigger latency
2. self-hosted dependency-cache cold/hit behavior

No redesign is authorized.
No new throughput architecture is required unless the post-merge proof exposes a real defect.

---

# 3. APPROVAL BOUNDARY

Do NOT merge PR #69 until explicit commander/user approval is given.

Before approval:
- preserve PR state
- keep Evidence intact
- do not rewrite history
- do not force push
- do not deploy production

After explicit merge approval:
- merge exact reviewed PR #69 to `main`
- immediately continue Phase B without waiting for another instruction

---

# 4. PHASE B — MAIN ACTIVATION

After merge approval:

## B-1. Merge exact PR
- verify PR #69 head SHA immediately before merge
- merge to main
- record merge commit SHA
- verify main contains the expected workflow and acquisition changes

## B-2. Immediate Issue-event proof
Use the minimum valid non-destructive MODEL SCOUT request event.

Required Evidence:
- source Issue number
- Issue-event timestamp
- workflow run ID
- workflow start timestamp
- event-to-start latency
- request fingerprint
- dedupe result
- no duplicate Issue
- no duplicate callback

Save:
`evidence/immediate-trigger-main-proof-20260923.json`

PASS requires the workflow to begin from the Issue event, not from schedule or manual dispatch.

## B-3. Self-hosted dependency cache proof
Run the updated autonomous workflow twice with the same requirements fingerprint.

Capture:
- run IDs
- runner name
- requirements SHA-256 fingerprint
- cold/miss bootstrap duration
- cache-hit bootstrap duration
- whether pip install executed or was skipped
- elapsed-time delta

Save:
`evidence/runner-bootstrap-cache-main-proof-20260923.json`

Do not invent percentage improvement.

## B-4. Regression gate
After main activation, verify:
- request ingestion still works
- Team Router still works
- cross-repo callback still works
- existing DELIVERED/idempotency behavior remains intact
- acquisition registry remains deduplicated
- scheduled watchdog remains active

If a regression appears:
Evidence → exact root cause → safe fix → rerun → continue.

---

# 5. FINAL POST-MAIN CLOSEOUT

Create/update:

`docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_POST_MAIN_CLOSEOUT_20260923.md`

Must include:
- PR #69 merge commit
- final main HEAD
- immediate Issue-event run ID
- event-to-start latency
- dependency-cache cold/hit run IDs and raw timings
- current acquired-model registry summary
- callback/delivery regression proof
- any fallback/failure history
- exact remaining blockers, if any

Final verdict may be:

`MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_CLOSEOUT: PASS`

only if:
- immediate event trigger PASS
- cache benchmark PASS
- no regression in delivery/idempotency
- exact main Evidence is preserved

---

# 6. WORK BEHAVIOR

After merge approval, do not stop between:
merge → trigger proof → cache proof → regression verification → final inspection.

Do not stop for small failures.
Use:
Evidence → cause → safe fallback → fix → rerun → continue.

Only stop again for:
- new permission scope
- new secret/rotation
- paid action
- external publication
- production deployment
- destructive/irreversible action

---

# 7. FINAL COMPLETION CHECKLIST

- [ ] PR #69 merged after explicit approval
- [ ] main contains immediate Issue/repository-dispatch trigger
- [ ] real Issue-event start proven
- [ ] event-to-start latency recorded
- [ ] dependency cache cold/hit proof recorded
- [ ] scheduled watchdog preserved
- [ ] Team Router/callback regression-free
- [ ] registry remains deduplicated
- [ ] final post-main inspection committed
- [ ] final verdict PASS or exact blocker

Until explicit merge approval:
`COMMANDER_MERGE_APPROVAL_REQUIRED`
