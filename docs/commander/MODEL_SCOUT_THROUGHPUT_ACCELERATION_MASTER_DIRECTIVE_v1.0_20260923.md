# MINDLE MODEL SCOUT
## THROUGHPUT ACCELERATION MASTER EXECUTION DIRECTIVE
### v1.0 — 2026-09-23

**Authority:** 신작가님 → MODEL SCOUT Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Central execution issue:** `#68 [P0][EXECUTION] MODEL SCOUT throughput acceleration full-chain closeout`  
**Base:** `main @ 9d342e3bc8d5950b2513cb847a568fedbdd6ddc9`  
**Work branch:** `improvement/model-scout-throughput-20260923`  
**Target PR:** this branch → `main`, Draft until all gates pass  
**Mode:** GENERAL WORK / long-running continuous execution  
**PC Work:** not required for this improvement scope unless an exact local-PC-only hardware proof is later separately required.

---

# 0. COMMANDER INTENT

This is **not a rebuild** of MODEL SCOUT.

The current system already has verified foundations:
- central request intake and durable queue
- runtime execution path
- cross-repository token scope
- Team Router / ACK
- request-level TESTED_PASS
- callback
- DELIVERED
- duplicate suppression / idempotent closeout
- PR #64 merged to main

The problem is **throughput**.

MODEL SCOUT currently behaves more like a strict request-validation/delivery system than a high-speed model acquisition system. Development-team Work sessions can often acquire individual models faster because they go directly from need → official source → download → run. MODEL SCOUT currently serializes too much work behind final product validation.

The mission is therefore:

> **Preserve all existing safety and Evidence gates, but separate model acquisition from product validation, parallelize acquisition, execute new requests immediately, and make the actual scouted candidate—not only a fixed fallback executor—the object being acquired and verified.**

Do not weaken Evidence standards.  
Do not delete the existing runtime/delivery system.  
Do not redesign unrelated product architecture.

---

# 1. NON-NEGOTIABLE WORK BEHAVIOR

General Work must execute from start to finish without stopping for small decisions.

## 1.1 PLAN → EXECUTE → VERIFY → FIX → CONTINUE
Repeat this loop until the closeout gates are met.

## 1.2 “CAN’T” IS NOT A COMPLETION STATE
Do not terminate work with:
- “not possible”
- “environment issue”
- “model failed”
- “dependency issue”
- “download failed”
- “runner limitation”

For every failure:
1. preserve exact Evidence
2. classify exact cause
3. choose a safe allowed fallback
4. modify the smallest necessary layer
5. rerun
6. continue the mission

## 1.3 SAFE BYPASS IS REQUIRED
Allowed bypass examples:
- alternate official mirror/source
- alternate compatible model revision
- ONNX / safetensors / CPU-compatible build
- smaller/quantized model
- cache reuse
- worker-local package install
- alternate fixture with documented provenance
- test split preserving request semantics
- independent acquisition even if product fixture is blocked

A single failed candidate must never stop the lane if a safe alternative exists.

## 1.4 ONLY STOP FOR APPROVAL WHEN REQUIRED
Stop and request user approval only for:
- paid resource / billable API / GPU spend
- new login / new account access
- new repository permission or scope expansion
- secret creation / secret rotation / revealing a secret
- external publication
- production deployment
- destructive or irreversible action
- force push
- main merge

Everything else: proceed.

## 1.5 DO NOT DESTROY VERIFIED HISTORY
Do not:
- overwrite prior PASS Evidence
- reclassify historical PASS without contradictory Evidence
- delete existing model cache merely to retest
- recreate already-DELIVERED requests
- duplicate callbacks
- duplicate central issues
- rewrite product SSOT outside this repository

---

# 2. VERIFIED ROOT CAUSE OF LOW SPEED

The improvement must explicitly address all of these:

### RC-1 — Acquisition and final product validation are coupled
A model can be fully downloaded, revision-pinned, license-verified and SHA-verified but still be prevented from becoming a useful inventory asset because the consuming team lacks a real production fixture.

**Fix:** introduce a first-class acquisition completion state independent of product E2E.

### RC-2 — Runtime execution is effectively serial
Requests are processed one-by-one through the runtime loop.

**Fix:** bounded parallel acquisition with deterministic concurrency and independent failure handling.

### RC-3 — New work waits on scheduled execution
Current autonomous workflow has a 15-minute cadence.

**Fix:** new request event should trigger immediate work. Schedule remains watchdog/recovery fallback, not the primary start mechanism.

### RC-4 — Fixed executor models can diverge from the actual scouted candidate
Current executor configuration includes preselected models such as MiniLM, TrOCR, Whisper-tiny, etc. The search result may identify another preferred model, while runtime executes a fixed class adapter.

**Fix:** dynamic acquisition/execution must bind to the actual selected candidate when technically safe.

### RC-5 — Repeated runner bootstrap overhead
Python/pip/dependency preparation repeats too much.

**Fix:** environment fingerprint + dependency/cache reuse. Install only when requirements change or a needed package is missing.

### RC-6 — SSOT/control is stale
`CURRENT_EXECUTION_CONTROL.md` does not reflect current main and merged closeout state.

**Fix:** refresh from real GitHub state and make future updates ledger-derived or automatically generated where feasible.

### RC-7 — Intake coverage and team routing are narrower than the actual MINDLE development surface
Do not limit automatic routing/registry to only the three historical Team Router teams.

**Fix:** expand intake/registry coverage to all valid configured development repos without breaking existing routes.

---

# 3. TARGET ARCHITECTURE — TWO INDEPENDENT LANES

## LANE A — HIGH-SPEED MODEL ACQUISITION

Lifecycle:

`DISCOVERED → LICENSE_OK → REVISION_PINNED → DOWNLOADED → HASH_VERIFIED → ACQUIRED_VERIFIED`

### ACQUIRED_VERIFIED definition
This state requires:
- exact model/program ID
- exact immutable revision/commit where supported
- official/authoritative source
- license evidence
- commercial-use classification
- downloaded exact files
- file sizes
- SHA-256
- storage/cache location
- acquisition timestamp
- no unapproved remote-code execution

It **does not require a consuming team's real production input**.

A team lacking a photo/video/audio/drawing fixture must not block Lane A.

## LANE B — PRODUCT VALIDATION / DELIVERY

Lifecycle:

`ACQUIRED_VERIFIED → TESTED_PASS → CALLBACK_SENT → DELIVERED`

This lane requires request-specific Evidence:
- real/approved representative input
- actual output
- runtime/hardware
- command/settings
- output SHA-256
- acceptance checks
- callback URL
- delivery ledger
- idempotent rerun

A blocked Lane B must not stall unrelated Lane A acquisitions.

---

# 4. REQUIRED STATE / DATA MODEL CHANGES

Implement the smallest durable change necessary.

The system must be able to represent at minimum:
- `DISCOVERED`
- `LICENSE_OK`
- `REVISION_PINNED`
- `DOWNLOADED`
- `HASH_VERIFIED`
- `ACQUIRED_VERIFIED`
- `TESTED_PASS`
- `CALLBACK_SENT`
- `DELIVERED`
- `BLOCKED_INPUT`
- `BLOCKED_CONFIG`
- `BLOCKED_APPROVAL`
- `FAILED_RETRYABLE`
- `REJECTED_LICENSE`
- `REJECTED_RUNTIME`

Do not fake linear progress.  
A request may have multiple candidate models with separate acquisition states.

---

# 5. MODEL REGISTRY — REQUIRED

Create a durable registry under repository-controlled Evidence/state.

Recommended canonical tracked export:

`evidence/model-registry.json`

If the durable runtime store remains SQLite, also create/update a deterministic human-readable export.

Each acquired asset must include:
- model_id
- revision
- source_url/source
- license
- commercial_use_status
- trust_remote_code_required
- file list
- size
- SHA-256
- acquired_at
- acquisition_runner
- cache/storage location
- acquisition_status
- validation_status
- consuming_team(s)
- originating request(s)
- rejection reason if rejected

The registry must prevent silent duplicate acquisition.

---

# 6. DYNAMIC EXECUTOR / ACQUISITION POLICY

## 6.1 Bind to actual selected candidate
When scout selects a candidate, Lane A must try to acquire **that exact candidate**, not silently substitute a fixed executor model.

## 6.2 Safe artifact policy
Preferred:
1. safetensors
2. ONNX
3. official binary/model artifacts
4. standard transformers models with no remote-code requirement

## 6.3 Remote code
If `trust_remote_code=True` or equivalent unreviewed remote execution is required:
- do not auto-execute
- record `BLOCKED_APPROVAL` or `REVIEW_REQUIRED`
- continue scouting/acquiring alternate safe candidates

## 6.4 Failure fallback order
For the same requested capability:
1. same official model, alternate safe format
2. smaller official variant
3. quantized/ONNX/OpenVINO compatible variant with clear source/license
4. alternate official model
5. established compatible open-source alternative
6. only then mark lane blocked if no valid safe candidate exists

---

# 7. PARALLELISM — REQUIRED

Implement bounded parallel acquisition.

Target:
- default concurrency: **3**
- configurable to **4**
- never unbounded
- one candidate failure must not cancel sibling acquisitions
- deterministic Evidence per job

Required Evidence:
- job start timestamps
- job end timestamps
- model ID
- result
- overlapping execution timestamps proving real concurrency

Do not parallelize writes to the same state record unsafely.

---

# 8. IMMEDIATE TRIGGER — REQUIRED

Current scheduled 15-minute cycle must remain only as watchdog/fallback.

Add an immediate execution path for a newly created/updated valid MODEL SCOUT request.

Acceptable mechanisms include:
- issue event workflow
- repository_dispatch
- reusable workflow called by request-router
- another deterministic GitHub-native trigger

Requirements:
- no duplicate cycle storms
- concurrency guard
- request fingerprint dedupe
- event Evidence with request/issue ID
- scheduled recovery remains enabled

---

# 9. RUNNER BOOTSTRAP ACCELERATION

Do not reinstall the same environment every cycle when unchanged.

Implement:
- requirements/environment fingerprint
- cache marker
- reuse of runner-local Python
- dependency presence verification
- install only missing/changed requirements
- preserve reproducibility

Record before/after bootstrap duration.

---

# 10. INTAKE / TEAM COVERAGE

Preserve incoming-request-first priority.

Expand configured intake/routing so valid MODEL SCOUT requests from the MINDLE development repos can be centrally detected.

Do not hardcode only historical:
- mindle-media-ai
- kimserv-core
- arcos-engine

The implementation may use:
- configured repo variable
- checked registry
- approved allow-list

But it must support the actual current development ecosystem.

Do not discover random external repositories.

---

# 11. SSOT REPAIR

Update `CURRENT_EXECUTION_CONTROL.md`.

It must no longer claim:
- main is `7040dd9...`
- PR #59/older closeout state is the current integration authority

New SSOT must reflect:
- main baseline inherited from `9d342e3...`
- PR #62/#64 closeout history as completed historical evidence
- Issue #68 as current active P0 improvement gate
- two-lane acquisition/validation model
- exact current blockers only
- no stale future-work entries for already-completed lanes

Where feasible, generate the volatile status section from registry/ledger data instead of manually duplicating state.

---

# 12. ACTUAL PROOF — DO NOT STOP AT UNIT TESTS

This mission is not complete with code-only PASS.

## Gate A — New acquisitions
Acquire **at least 3 NEW unique model IDs** not already counted as the existing core acquired set.

Existing core set that does NOT count toward the +3:
- `facebook/sam2.1-hiera-tiny`
- `PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx`
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- `google/siglip-base-patch16-224`

The new models must each reach `ACQUIRED_VERIFIED` with:
- revision
- license
- file size
- SHA-256
- registry entry

Use current team requests as demand signals. Good candidate families may include those already requested by teams, but selection must be based on actual license/runtime/source evidence, not this directive alone.

## Gate B — Parallel execution proof
At least 3 acquisition jobs must show overlapping timestamps.

## Gate C — Request delivery proof
At least 1 request must proceed:
`ACQUIRED_VERIFIED → TESTED_PASS → CALLBACK_SENT → DELIVERED`

Use an existing valid pending request or create only the minimum deterministic test request when needed. Do not fake production success.

## Gate D — Blocked fixture isolation
Demonstrate that one request blocked on missing real input does not prevent another model from reaching `ACQUIRED_VERIFIED`.

## Gate E — Idempotency
Rerun once:
- no duplicate registry entry
- no duplicate callback
- no duplicate Issue
- no unnecessary redownload when verified cache is valid

---

# 13. TEST REQUIREMENTS

Add deterministic tests for:
- acquisition state transitions
- invalid license rejection
- pinned revision requirement
- SHA mismatch rejection
- duplicate registry suppression
- dynamic selected-candidate binding
- remote-code safety block
- parallel worker isolation
- event-trigger dedupe
- acquisition success despite product-input blocker
- acquisition → validation handoff
- callback/delivery idempotency
- stale SSOT regression guard if practical

Preserve all existing tests.

Required closeout:
- full relevant pytest suite PASS
- cli-smoke PASS
- hf-e2e PASS
- new exact-head acquisition E2E PASS

---

# 14. PERFORMANCE EVIDENCE

Create:

`evidence/throughput-benchmark-20260923.json`

and summarize in:

`docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_CLOSEOUT_20260923.md`

Include:
- old architecture description
- new architecture description
- runner bootstrap before/after
- acquisition concurrency
- acquisition elapsed time per model
- total elapsed time for >=3 acquisitions
- event-to-start latency
- cache hit behavior
- redownload avoidance
- request delivery latency
- failures/fallbacks

Do not invent “X% faster” unless measured.

---

# 15. GITHUB WORKFLOW / BRANCH / PR RULES

Work only on:

`improvement/model-scout-throughput-20260923`

Do not modify main directly.

Push meaningful commits continuously.  
Do not keep important work only local.

Commit style examples:
- `feat: split acquisition and product validation lanes`
- `feat: add bounded parallel acquisition registry`
- `perf: reuse runner bootstrap dependencies`
- `feat: trigger model scout immediately on request events`
- `test: prove parallel acquisition and delivery isolation`
- `docs: refresh model scout execution control and closeout evidence`

Open/maintain one PR to main.

PR must remain Draft until all acceptance gates pass.  
When all gates pass:
- update PR body with exact Evidence
- attach run IDs/artifact IDs
- save final inspection report
- mark Ready for review
- STOP FOR COMMANDER REVIEW
- do **not** merge main without explicit owner approval

---

# 16. REQUIRED FINAL INSPECTION MATERIAL

At the end, commit:

`docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_CLOSEOUT_20260923.md`

It must contain:
- final verdict
- exact branch
- exact HEAD
- changed files
- architecture delta
- tests and commands
- CI run IDs
- new acquired models
- exact revisions
- licenses
- sizes/SHA-256
- registry paths
- concurrency Evidence
- event-trigger Evidence
- delivered request Evidence
- callback URL
- duplicate suppression result
- before/after benchmark
- unresolved blockers
- confirmation of no main merge / no production deploy / no secret exposure

Also preserve machine-readable artifacts under `evidence/`.

---

# 17. EXECUTION ORDER — START NOW AND CONTINUE

1. Checkout `improvement/model-scout-throughput-20260923`.
2. Read Issue #68 and this directive completely.
3. Verify baseline and preserve existing PASS Evidence.
4. Repair CURRENT_EXECUTION_CONTROL.
5. Implement acquisition registry/state.
6. Split acquisition from product validation.
7. Add bounded parallel acquisition.
8. Bind acquisition to actual scout candidate.
9. Add safe remote-code/license guards.
10. Add immediate request trigger.
11. Add runner bootstrap caching.
12. Expand configured team intake safely.
13. Add/modify tests.
14. Run local/unit integration tests.
15. Execute real new-model acquisition proof for >=3 unique models.
16. Execute at least one request through TESTED_PASS→DELIVERED.
17. Rerun for idempotency.
18. Run exact-head CI/E2E.
19. Fix any failure and rerun; do not stop at first failure.
20. Commit all Evidence and final inspection.
21. Update PR with exact Evidence.
22. Mark PR Ready for review only after all gates pass.
23. STOP FOR COMMANDER REVIEW.

**Do not break this sequence into repeated user approvals.**
**Do not stop at partial success when a safe allowed path remains.**
**Do not answer “cannot” without exhausting the fallback chain and preserving Evidence.**

---

# 18. COMPLETION DEFINITION

The mission is complete only when:

`FAST INTAKE + PARALLEL ACQUISITION + ACQUIRED_VERIFIED REGISTRY + INDEPENDENT PRODUCT VALIDATION + TESTED_PASS→DELIVERED + IDEMPOTENT RERUN + EXACT-HEAD CI + GITHUB CLOSEOUT EVIDENCE`

are all demonstrated on the branch.

Anything less is PARTIAL / VERIFY_REQUIRED.
