# MINDLE MODEL SCOUT
## REAL ACQUISITION + THROUGHPUT CLOSEOUT EXECUTION DIRECTIVE
### v2.0 — 2026-09-23

**Authority:** 신작가님 → MODEL SCOUT Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Central Issue:** #68  
**Active PR:** #69  
**Work branch:** `improvement/model-scout-throughput-20260923`  
**Current verified HEAD at directive issue time:** `d75cf93e58157a2698ff691a81bbe26021d85074`

---

# 1. CURRENT VERIFIED STATE

The structural throughput improvement has started and exact-head CI is currently healthy:
- tests: PASS
- cli-smoke: PASS
- hf-e2e: PASS

Already implemented on PR #69:
- Lane A acquisition / Lane B validation split
- bounded parallel acquisition code
- immediate issue/repository-dispatch trigger
- dependency fingerprint cache
- refreshed CURRENT_EXECUTION_CONTROL
- model registry schema
- throughput benchmark skeleton

**But the mission is NOT complete.**

Verified remaining gap:
- `evidence/model-registry.json` is still empty
- no real >=3 new unique `ACQUIRED_VERIFIED` model entries exist yet
- no measured live parallel acquisition Evidence has been committed
- final inspection report is not yet present

Therefore this directive orders the **live acquisition proof and final closeout**, not more architecture-only work.

---

# 2. START NOW — DO NOT STOP AT CODE PASS

General Work must continue immediately on the same branch.

Do not stop at:
- unit tests
- mock parallelism
- empty registry
- candidate search result
- model card review
- download URL list
- one failed candidate
- one successful model

The work is complete only after real model bytes are acquired and Evidence is committed.

---

# 3. LIVE MODEL ACQUISITION TARGET

Acquire **at least 3 NEW unique model IDs** that are not part of the existing core acquired set.

Existing core set — DOES NOT COUNT:
- `facebook/sam2.1-hiera-tiny`
- `PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx`
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- `google/siglip-base-patch16-224`

Candidate selection must come from:
1. current open MODEL SCOUT team requests
2. current Scout ranking/search result
3. exact license/source/runtime checks

Do not select arbitrary models just to satisfy the count.

Preferred demand signals include currently requested capability families such as:
- image edit / inpaint / visual understanding
- STT/TTS
- geospatial / OCR / embedding / reranker
- rendering / geometry / CAD support
- multimodal classification/search

But the chosen model must pass the actual acquisition safety gate.

---

# 4. ACQUIRED_VERIFIED GATE — STRICT

Each of the 3+ new models must contain:

- exact model ID
- exact immutable revision/commit
- authoritative source
- verified license
- commercial-use classification
- trust_remote_code status
- actual downloaded file list
- exact byte size
- SHA-256 for every acquired artifact
- acquisition start timestamp
- acquisition end timestamp
- cache/storage location
- originating request(s)
- consuming team(s)
- `acquisition_status = ACQUIRED_VERIFIED`

No candidate may be counted if any required field is missing.

Do not count:
- SOURCE_ONLY
- FOUND
- APPROVED
- model-card only
- partial download
- unpinned revision
- unknown license
- remote-code-required model without explicit approval

---

# 5. REAL PARALLELISM PROOF

Use the implemented bounded acquisition runner.

Required:
- concurrency default = 3
- run at least 3 real acquisition jobs in the same live execution window
- preserve overlapping timestamps
- one job failure must not cancel siblings
- if one candidate fails, replace that candidate and continue until >=3 succeed

Required machine-readable Evidence:
`evidence/parallel-acquisition-evidence-20260923.json`

Must include:
- model ID
- revision
- started_at
- ended_at
- duration
- result
- overlap proof / peak concurrency
- failure/fallback history

---

# 6. MODEL REGISTRY — MUST BE POPULATED

Update:
`evidence/model-registry.json`

It must contain the new verified models.

Do not leave the tracked registry empty after live acquisition.

If runtime durable registry is separate from repository export:
- preserve runtime registry
- export deterministic sanitized registry to GitHub
- ensure values match actual acquired files

No fake or manually invented hashes.

---

# 7. BLOCKED PRODUCT INPUT MUST NOT STOP ACQUISITION

Select at least one team request whose Lane B is blocked on missing product fixture/input.

Demonstrate:
- that request remains correctly BLOCKED_INPUT / VERIFY_REQUIRED in Lane B
- unrelated model acquisition continues
- at least one other model reaches ACQUIRED_VERIFIED during that same overall execution period

Record this isolation proof in:
`evidence/acquisition-validation-isolation-20260923.json`

---

# 8. COMPLETE AT LEAST ONE DELIVERY LANE

At least one valid request must complete:

`ACQUIRED_VERIFIED → TESTED_PASS → CALLBACK_SENT → DELIVERED`

Requirements:
- request-specific input/output
- runtime/hardware/settings/log
- output SHA-256
- callback URL
- delivery ledger transition
- exact Evidence
- no fake production acceptance

If the first selected request is blocked, choose another valid request that can be completed safely and continue.

---

# 9. IDEMPOTENCY / CACHE PROOF

After successful acquisition and delivery:
- rerun once

Required:
- verified cache reused
- no unnecessary redownload of valid model bytes
- no duplicate registry record
- no duplicate central Issue
- no duplicate callback
- no duplicate DELIVERED transition

Save:
`evidence/throughput-idempotency-20260923.json`

---

# 10. BENCHMARK MUST BECOME MEASURED, NOT PENDING

Update:
`evidence/throughput-benchmark-20260923.json`

Replace `PENDING_EXACT_HEAD_LIVE_E2E` with actual measurements.

Record:
- event-to-start latency
- bootstrap duration
- cache-hit bootstrap duration
- acquisition duration per model
- total elapsed for >=3 acquisitions
- peak acquisition concurrency
- cache-hit redownload avoidance
- request delivery elapsed time
- failures and fallback substitutions

Do not claim percentage improvement without measured baseline comparison.

---

# 11. RUNNER / TRIGGER PROOF

The immediate trigger must be proven with real GitHub Evidence.

Required:
- valid request event
- workflow start without waiting for the next 15-minute scheduled slot
- exact workflow run ID
- event type
- request/Issue ID
- start timestamp

Schedule remains enabled only as watchdog/fallback.

---

# 12. FAILURE RULE — CONTINUE

For any failed model:
1. capture exact error
2. classify:
   - LICENSE_REJECTED
   - REVISION_UNRESOLVED
   - ARTIFACT_NOT_FOUND
   - HASH_MISMATCH
   - REMOTE_CODE_REQUIRED
   - RUNTIME_INCOMPATIBLE
   - NETWORK_RETRYABLE
   - OTHER_EXACT_CLASSIFICATION
3. choose safe fallback
4. rerun
5. continue until >=3 ACQUIRED_VERIFIED

Do not finish the task with fewer than 3 because one candidate failed.

---

# 13. FINAL CI / TEST GATE

After all live Evidence is committed:

Run exact-head:
- full relevant tests
- cli-smoke
- hf-e2e
- acquisition tests
- real acquisition workflow/E2E

All must PASS.

If exact-head changes after CI:
- rerun CI on the new exact HEAD

Do not reuse older CI for a newer commit.

---

# 14. FINAL INSPECTION REPORT — REQUIRED

Create and commit:

`docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_CLOSEOUT_20260923.md`

Must include:
- final verdict
- branch
- exact HEAD
- changed files
- tests
- exact CI run IDs
- acquired model table
- exact revisions
- licenses
- file sizes
- SHA-256
- registry path
- parallelism proof
- immediate-trigger proof
- isolation proof
- delivered request proof
- callback URL
- idempotency result
- benchmark before/after
- failed candidates and fallback history
- unresolved blockers
- explicit confirmation:
  - no main merge
  - no production deployment
  - no secret exposure
  - no force push
  - no paid action

---

# 15. PR #69 CLOSEOUT

When ALL gates are satisfied:

1. Push all code and Evidence to `improvement/model-scout-throughput-20260923`
2. Update PR #69 body with exact Evidence
3. Add final closeout comment
4. Mark PR #69 **Ready for review**
5. STOP FOR COMMANDER REVIEW

Do not merge main.

---

# 16. HARD COMPLETION GATE

Do not stop until all are true:

- [ ] >=3 NEW unique models are `ACQUIRED_VERIFIED`
- [ ] real model registry populated
- [ ] actual SHA-256 and byte sizes recorded
- [ ] >=3 overlapping real acquisition jobs proven
- [ ] immediate trigger proven
- [ ] blocked Lane B does not block Lane A proof
- [ ] >=1 request `TESTED_PASS → CALLBACK_SENT → DELIVERED`
- [ ] idempotent rerun proven
- [ ] benchmark contains real measured values
- [ ] exact-head tests PASS
- [ ] exact-head cli-smoke PASS
- [ ] exact-head hf-e2e PASS
- [ ] final inspection report committed
- [ ] PR #69 Ready for review

Anything less is:
`PARTIAL / VERIFY_REQUIRED`

**Execute continuously. Do not stop at intermediate progress.**
