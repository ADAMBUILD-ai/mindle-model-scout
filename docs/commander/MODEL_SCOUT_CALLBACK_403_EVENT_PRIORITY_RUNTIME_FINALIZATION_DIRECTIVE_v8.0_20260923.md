# MINDLE MODEL SCOUT
## CALLBACK 403 RECOVERY + EVENT PRIORITY + RUNTIME DEPENDENCY FINALIZATION DIRECTIVE
### v8.0 — 2026-09-23

**Authority:** 신작가님 → AKI Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Central Issue:** #68  
**Post-main PR:** #70  
**Work branch:** `post-main/model-scout-activation-closeout-20260923`  
**Current inspected HEAD before this directive:** `9d8fea531a53e9c01d4f5d1ee5643982f037aa2f`

---

# 1. COMMANDER INSPECTION RESULT

Post-main validation is substantially successful.

Verified PASS:
- default-branch `issues: opened` trigger recognized in 3 seconds
- self-hosted runner executed the event workflow
- dependency fingerprint cache cold/hit proof PASS
- second and confirming runs skipped unnecessary pip install
- scheduled watchdog PASS
- durable queue/watchdog state persisted
- 3 acquired models remain `ACQUIRED_VERIFIED`
- exact-head tests / cli-smoke / hf-e2e PASS

Current exact blockers:
1. callback comment writes return HTTP 403
2. dedicated proof Issue #71 did not reach request execution/callback in the triggered cycle
3. geometry worker lacks `scipy`
4. Hugging Face search has intermittent HTTP 500 retryable failures

The mission is now **final defect cleanup**, not more architecture work.

---

# 2. IMPORTANT ROOT-CAUSE CORRECTION — TOKEN ROLE COLLISION

Current workflow sets:

`GITHUB_TOKEN = secrets.MODEL_SCOUT_CROSS_REPO_TOKEN`

This overwrites the GitHub Actions built-in repository token for the entire runner process.

The workflow itself already declares:
`permissions: issues: write`

Therefore the built-in GitHub Actions repository token has same-repository Issue write permission, while the cross-repo secret is intended for cross-repository discovery/routing.

Observed callback 403s affect central MODEL SCOUT callback Issues. Before requesting any permission expansion, General Work MUST first remove this token-role collision.

**Do not rotate or broaden the secret first.**

---

# 3. SAFE FIX A — SPLIT LOCAL WRITE TOKEN FROM CROSS-REPO TOKEN

Implement explicit credential roles.

Recommended workflow environment:
- `MODEL_SCOUT_LOCAL_GITHUB_TOKEN: github.token`
- `MODEL_SCOUT_CROSS_REPO_TOKEN: secrets.MODEL_SCOUT_CROSS_REPO_TOKEN`

Do not export the cross-repo secret as generic `GITHUB_TOKEN`.

## Required transport behavior

### Discovery/read path
Use `MODEL_SCOUT_CROSS_REPO_TOKEN` for configured cross-repository Issue discovery.

### Same-repository callback path
When callback repo is:
`ADAMBUILD-ai/mindle-model-scout`

use `MODEL_SCOUT_LOCAL_GITHUB_TOKEN`.

### External callback path
When callback repo differs from the central repository:
use `MODEL_SCOUT_CROSS_REPO_TOKEN`.

If an external callback still returns 403 after this separation:
- record exact repository
- do not expose token
- do not rotate token
- classify only that external repo as `BLOCKED_APPROVAL`
- produce a least-privilege repository permission matrix for approval

Do not classify the whole system as blocked if local callbacks pass.

---

# 4. REQUIRED CODE SHAPE

Implement the smallest safe change.

Acceptable pattern:
- extend `GitHubIssueCommentWriter` to support:
  - local token
  - cross-repo token
  - local repository identity
  - token selection by callback repository
- or add a small routing writer wrapper

Required fail-closed behavior:
- local callback with missing local token → exact configuration error
- external callback with missing cross-repo token → exact configuration error
- no fallback from failed external permission to an unrelated credential
- no token value in logs/Evidence/errors

Add deterministic tests:
- same repo selects local token
- external repo selects cross-repo token
- local write succeeds with mocked 201
- external 403 is classified without credential leakage
- callback retry remains idempotent

---

# 5. SAFE FIX B — PROOF ISSUE PRIORITY / CURRENT EVENT FIRST

The operating rule already states:
**new incoming development-team request preempts background/re-scout/history work.**

Issue #71 triggered the workflow but did not produce request-processing Evidence.

Do not solve this by blindly increasing `MODEL_SCOUT_LIMIT`.

First trace:
- Issue #71 discovery
- normalized project/resource/priority
- fingerprint
- enqueue result
- whether it deduped to an existing fingerprint
- queue state before execution
- cycle iteration order
- whether callback 403 on earlier requests affected observable results

Then implement **current event first** semantics.

Recommended approach:
- workflow exports current event repository / Issue number
- discovery identifies the corresponding normalized envelope/fingerprint
- runtime cycle processes the event-origin fingerprint first
- older/requeued work resumes afterward
- scheduled watchdog behavior remains unchanged

If the event request is a true duplicate:
- record `DUPLICATE_SUPPRESSED`
- record the existing fingerprint
- do not execute it twice
- for trigger proof, use one unique safe proof request so processing Evidence can be observed

Add tests:
- new P0 event request runs before older requeued P0
- background work continues after event request
- duplicate event does not double-execute
- no starvation of retryable backlog across later watchdog cycles

---

# 6. SAFE FIX C — GEOMETRY WORKER SCIPY DEPENDENCY

Current regression Evidence:
`ModuleNotFoundError: No module named 'scipy'`

Resolve without guessing a version.

Required process:
1. inspect current Python and NumPy versions on runner
2. resolve an officially compatible SciPy version from package metadata
3. pin that compatible version in dependency control
4. update dependency fingerprint
5. run focused geometry worker test
6. run full relevant tests

Do not force an incompatible SciPy wheel.

Required PASS:
- geometry worker starts
- no `ModuleNotFoundError`
- existing geometry output contract remains unchanged
- no unrelated model/runtime regression

---

# 7. SAFE FIX D — HUGGING FACE HTTP 500 RETRY HARDENING

HTTP 500 is retryable upstream behavior.

Implement bounded retry only for retryable upstream failures:
- 500
- 502
- 503
- 504
- transient connection reset/timeouts

Requirements:
- bounded attempts
- short exponential/backoff delay
- no infinite retry
- exact retry count in Evidence
- 4xx license/auth/client errors are not blindly retried

Preserve `FAILED_RETRYABLE` if attempts exhaust.

---

# 8. EXECUTION ORDER — DO NOT STOP MIDWAY

Execute in this order:

1. split token roles
2. test local callback transport
3. fix current-event-first processing
4. fix/pin SciPy
5. add bounded HF retry handling
6. run focused tests
7. run full tests / cli-smoke / hf-e2e
8. create one NEW unique proof Issue
9. verify:
   - issues trigger
   - event request selected in that cycle
   - runtime result
   - callback comment successfully written
10. rerun same request/dedupe path
11. verify duplicate suppression
12. verify external callback path on an already authorized configured repo where safe
13. update regression Evidence
14. update final inspection report

Do not stop after the first local callback success.

---

# 9. PERMISSION APPROVAL BOUNDARY

Only after token-role separation is verified:

If external callbacks still return 403, create:

`evidence/cross-repo-callback-permission-matrix-20260923.json`

For each configured callback repo record only:
- repository
- read discovery PASS/FAIL
- Issue comment write PASS/FAIL
- HTTP status
- required minimum permission

Then stop at:

`BLOCKED_APPROVAL: <exact repositories requiring Issues write>`

Do not request account-wide write.
Do not request token rotation unless the existing credential cannot be safely extended and the user explicitly approves replacement.

---

# 10. FINAL EVIDENCE UPDATE

Update:

- `evidence/immediate-trigger-main-proof-20260923.json`
- `evidence/post-main-regression-proof-20260923.json`
- `evidence/runner-bootstrap-cache-main-proof-20260923.json`
- optional `evidence/cross-repo-callback-permission-matrix-20260923.json`
- `docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_POST_MAIN_CLOSEOUT_20260923.md`

Final report must distinguish:
- local callback PASS
- external callback PASS or exact permission blocker
- Issue event processing PASS
- SciPy geometry PASS
- HF retry behavior PASS
- cache proof PASS
- exact-head CI PASS

---

# 11. FINAL PASS GATE

Final verdict may be:

`MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_CLOSEOUT: PASS`

only when:
- real Issue event starts immediately
- event request is processed in its cycle or deterministically deduped with proof
- callback succeeds
- callback rerun is idempotent
- geometry worker PASS
- dependency cache proof PASS
- exact-head tests / cli-smoke / hf-e2e PASS
- no unresolved approval blocker remains

If only external repo permission remains after local callback recovery:
do not overclaim PASS; return the exact least-privilege approval requirement.

---

# 12. CONTINUOUS EXECUTION RULE

Use:

`FIX → TEST → LIVE PROOF → RETEST → EVIDENCE → CLOSEOUT`

Do not end with “cannot” while a safe code/configuration fix remains.

Stop only at:
- FINAL PASS
- or one exact approval-only permission/secret blocker.
