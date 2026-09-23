# MINDLE MODEL SCOUT
## POST-MAIN ACTIVATION + FINAL CLOSEOUT EXECUTION DIRECTIVE
### v6.0 — 2026-09-23

**Authority:** 신작가님 → MODEL SCOUT Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Central Issue:** #68  
**Merged PR:** #69  
**Main merge commit:** `9bf3a3cde6ee1f25a462725a8b77e963346b8bbb`  
**Post-main work branch:** `post-main/model-scout-activation-closeout-20260923`

---

# 1. MERGE STATUS — COMPLETED

PR #69 has been merged to `main`.

The throughput changes are now active on the default branch.

This includes:
- Lane A acquisition / Lane B validation separation
- bounded parallel acquisition
- actual Scout-selected candidate acquisition
- immutable revision requirement
- license fail-closed gate
- remote-code fail-closed gate
- registry and duplicate suppression
- Issue trigger
- repository_dispatch trigger
- scheduled watchdog fallback
- dependency fingerprint cache

Do not repeat pre-merge validation as if PR #69 were still pending.

---

# 2. CURRENT MISSION

Now execute the default-branch-only proof that could not be completed before merge.

Required sequence:

`VERIFY MAIN → REAL ISSUE EVENT → CACHE COLD/HIT → REGRESSION CHECK → FINAL REPORT`

Do not interrupt this sequence for small issues.

---

# 3. VERIFY MAIN

Confirm first:
- main HEAD includes merge commit `9bf3a3cde6ee1f25a462725a8b77e963346b8bbb`
- `.github/workflows/autonomous-model-scout.yml` on main contains:
  - `issues`
  - `repository_dispatch:model-scout-request`
  - schedule watchdog
  - dependency fingerprint cache
- acquisition registry code exists
- no accidental rollback of PR #64 delivery closeout behavior

Record exact Evidence.

---

# 4. REAL IMMEDIATE ISSUE-EVENT TRIGGER PROOF

Create or reuse the smallest valid non-destructive MODEL SCOUT request event.

The event must be a genuine GitHub Issue event recognized by the default-branch workflow.

Required proof:
- issue number
- event action
- issue event timestamp
- workflow run ID
- workflow run created/start timestamp
- event-to-start latency
- request fingerprint
- whether the request was new or deduped
- no duplicate issue
- no duplicate callback

Save:

`evidence/immediate-trigger-main-proof-20260923.json`

PASS condition:
- execution starts from the Issue event, not schedule/manual dispatch
- valid request is recognized or deterministically deduped
- no duplicate execution side effect

If the first event does not start the workflow:
1. capture exact Evidence
2. inspect workflow trigger/default-branch syntax
3. apply smallest safe fix on this post-main branch
4. PR the fix
5. merge only if safe and authorized by this directive scope
6. rerun the Issue-event proof

No force push.

---

# 5. DEPENDENCY CACHE COLD/HIT PROOF

Use the self-hosted MODEL SCOUT workflow.

Run at least two eligible executions with the same requirements fingerprint.

## Run A
Capture:
- run ID
- runner name
- requirements SHA-256
- cache miss/cold state
- whether pip install ran
- bootstrap start/end
- bootstrap duration

## Run B
Capture:
- run ID
- same requirements SHA-256
- cache hit state
- whether pip install was skipped
- bootstrap start/end
- bootstrap duration
- raw elapsed-time delta

Save:

`evidence/runner-bootstrap-cache-main-proof-20260923.json`

PASS condition:
- same requirements fingerprint
- second run reuses cache/marker
- unnecessary reinstall avoided

Do not claim percentage improvement unless directly measured.

---

# 6. POST-MAIN REGRESSION CHECK

Verify that main activation did not break:

- central request discovery
- persistent queue
- watchdog recovery
- Team Router
- ACK path
- cross-repo callback
- delivery ledger
- duplicate suppression
- model registry integrity
- existing DELIVERED request stability
- scheduled watchdog

Where possible reuse existing verified paths instead of creating unnecessary duplicate work.

If regression occurs:
`Evidence → Cause → Minimal Fix → Rerun → Continue`

Do not stop at first failure when a safe fix exists.

---

# 7. FINAL POST-MAIN INSPECTION

Create:

`docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_POST_MAIN_CLOSEOUT_20260923.md`

Must contain:
- PR #69 merge commit
- final main HEAD
- real Issue-event proof
- event-to-start latency
- cache cold/hit evidence
- raw timings
- regression checks
- acquired model registry summary
- delivery/callback regression result
- duplicate suppression result
- failures and fallback actions
- exact unresolved blocker, if any
- safety confirmation

Final verdict:

`MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_CLOSEOUT: PASS`

only if all post-main gates pass.

---

# 8. CONTINUOUS EXECUTION RULE

Do not stop after:
- trigger proof only
- cache proof only
- one successful workflow
- one failed first attempt

Continue until:
- Issue event proof PASS
- dependency cache proof PASS
- regression check PASS
- final inspection committed

Only stop for:
- new permission scope
- secret creation/rotation
- paid resource
- external publication
- production deployment
- destructive/irreversible action
- force push

---

# 9. GITHUB OUTPUT REQUIREMENTS

All Evidence must be committed to this post-main branch.

Required artifacts:
- `evidence/immediate-trigger-main-proof-20260923.json`
- `evidence/runner-bootstrap-cache-main-proof-20260923.json`
- any regression evidence
- final inspection report

Maintain one post-main closeout PR to `main`.

Do not merge that PR automatically unless the change is evidence-only or a minimal non-destructive fix already allowed by this directive and exact CI is PASS.

If code changes are needed, preserve exact reason and test proof.

---

# 10. FINAL STOP CONDITION

Stop only when either:

`MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_CLOSEOUT: PASS`

or an exact approval-only blocker is reached.

Do not return a generic “cannot”.
