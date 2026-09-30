# MODEL SCOUT — AURA FINAL GAP RECOVERY DIRECTIVE v1.0

Date: 2026-09-30
Owner: 신작가님
Requester: AURA Commander
Repository: ADAMBUILD-ai/mindle-model-scout
Priority: P0
Execution mode: CONTINUE UNTIL TESTED_PASS + DELIVERED OR ALL ALLOWED CANDIDATES ARE EXHAUSTED WITH EVIDENCE

## 0. PURPOSE

AURA product mechanics A–F are already Commander PASS.

Final AURA closeout is blocked only by two unresolved Model Scout capability gaps:

1. Architectural Visual / Drawing Understanding
2. Geometry-Preserving Controlled Visual Generation / Edit

This directive is the execution order to close those two gaps.

Do NOT interpret:
- workflow success,
- issue closure,
- model download,
- ACQUIRED_VERIFIED,
- generic component inference

as AURA final delivery.

Required terminal path:
`REQUESTED -> FOUND -> DOWNLOADED -> PINNED_REVISION -> SHA256 -> LICENSE_SNAPSHOT -> ACQUIRED_VERSION_RIGHTS_PERSISTENCE -> RUNTIME -> AURA_PRODUCT_BENCHMARK -> TESTED_PASS -> CALLBACK -> DELIVERED`

If any candidate fails:
`FAILURE EVIDENCE -> ROOT CAUSE -> ALLOWED ALTERNATIVE -> FIX/RESCOUT -> RERUN -> CONTINUE`

No stopping after first failure while another allowed route remains.

---

## 1. GOVERNING AURA REQUESTS

Canonical source requests:

### #133 final-closeout request
`ADAMBUILD-ai/mindle-model-scout#133`

Capability:
`ARCHITECTURAL_VISUAL_UNDERSTANDING_REPLACEMENT`

Canonical AURA source:
`ADAMBUILD-ai/aura-engine#35`

Benchmark:
`requests/aura/benchmarks/AURA_ARCH_VISUAL_UNDERSTANDING_FIXTURE_v2.0_20260930.json`

### #134 final-closeout request
`ADAMBUILD-ai/mindle-model-scout#134`

Capability:
`GEOMETRY_PRESERVING_CONTROLLED_VISUAL_GENERATION_EDIT`

Canonical AURA source:
`ADAMBUILD-ai/aura-engine#36`

Benchmark:
`requests/aura/benchmarks/AURA_GEOMETRY_PRESERVING_EDIT_FIXTURE_v2.0_20260930.json`

---

## 2. OWNER TOP GATE — ACQUIRED VERSION RIGHTS PERSISTENCE

For every candidate, exact acquired-version evidence is mandatory.

Required:
- official/original source
- exact model ID
- exact immutable revision/commit
- exact files
- per-file SHA-256
- license snapshot
- model card/source snapshot
- evidence supporting continued use of the exact acquired version even if upstream policy/license changes later
- runtime environment
- actual product benchmark
- final adoption decision

If the acquired-version rights persistence cannot be evidenced:
`REJECT_AND_REPLACE`

Do not weaken this gate.

---

# PART A — #133 ARCHITECTURAL VISUAL / DRAWING UNDERSTANDING

## 3. VERIFIED CURRENT STATE

### 3.1 BLIP candidate already acquired

Candidate:
`Salesforce/blip-image-captioning-base`

Revision:
`82a37760796d32b1411fe092ab5d4e227313294b`

License:
`BSD-3-Clause`

Acquisition state:
`ACQUIRED_VERIFIED`

Current validation state:
`PENDING`

This candidate is NOT AURA TESTED_PASS.

Generic caption output does not satisfy architecture-specific understanding.

### 3.2 LayoutLM candidate runtime failure

Candidate:
`impira/layoutlm-document-qa`

Revision:
`beed3c4d02d86017ebca5bd0fdf210046b907aa6`

Observed failure:
document-QA pipeline attempted OCR and failed because `pytesseract` / OCR runtime dependency was unavailable on the runner.

Classification:
`FAILED_RETRYABLE_ENVIRONMENT_DEPENDENCY`

This is not a model-quality rejection.

---

## 4. #133 REQUIRED RECOVERY WORK

### 4.1 Fix the OCR runtime path

Allowed recovery options:

A. install/use Tesseract + pytesseract on the runner; or

B. bypass internal OCR by supplying explicit words/boxes from an approved OCR component; or

C. use another architecture/document model with a safe local runtime that does not require unavailable OCR dependencies.

Record:
- exact dependency/version
- exact command
- runtime log
- input/output hashes
- whether OCR came from internal pipeline or external preprocessor

### 4.2 Run BLIP through the actual six-class AURA benchmark

Required classes:

1. site plan
2. floor plan
3. section
4. elevation
5. aerial/perspective
6. proposal page

Required evaluation:

- grounded architectural facts
- programme interpretation
- circulation interpretation
- mass / footprint relationships
- level / section relationships
- open-space hierarchy
- page hierarchy
- cross-view consistency
- omissions
- contradictions
- hallucinations

BLIP must not PASS only because it generates captions.

If generic/repetitive/non-architectural:
`REJECT_QUALITY`
and continue scouting.

### 4.3 Continue architecture-specific candidate search

Use the canonical #35 request fields.

Do not degrade to generic phrases such as:
- image captioning
- OCR only
- QA only

Search lanes should include, where license/runtime gates permit:

- architectural/document VQA
- plan/drawing understanding
- document-layout reasoning
- technical drawing understanding
- cross-view multimodal reasoning

Candidates found in prior evidence may be re-evaluated only if exact revision/license/runtime is valid.

Florence-2 remains historical `REJECT_QUALITY` unless genuinely new evidence proves an architecture-specific quality improvement.

---

## 5. #133 PASS GATE

PASS only if at least one candidate reaches:

`TESTED_PASS -> CALLBACK_SENT -> DELIVERED`

Required delivery evidence:

- model ID
- pinned revision
- file list
- per-file SHA-256
- license snapshot
- acquired-version rights-persistence evidence
- Windows/runtime environment
- CPU/GPU/RAM/VRAM
- exact command/settings
- six-class raw outputs
- per-class scores
- hallucination report
- KEEP / SUPPORT_ONLY / REJECT
- AURA role placement
- AURA lifecycle state placement
- required Guardian
- fallback route

Required AURA role candidate:
- ANALYSIS_AI support and/or
- VISUAL_BRAIN understanding support and/or
- CROSS_ARTIFACT_PAGE_GUARDIAN support

No model receives architecture approval authority.

---

# PART B — #134 GEOMETRY-PRESERVING CONTROLLED VISUAL EDIT

## 6. VERIFIED CURRENT STATE

Latest run showed:

- `requested_capability = UNKNOWN`
- `selection_mode = UNKNOWN_LEGACY`
- broken query plan:
  - segmentation/safe-scope
  - QA/reference
  - generator/editor
- candidate_count = 0

Classification:
`FAILED_SEARCH_PLAN_NORMALIZATION`

This is not proof that no viable model exists.

---

## 7. #134 REQUIRED NORMALIZATION FIX

The #134 request must be normalized from the canonical structured AURA request:

`ADAMBUILD-ai/aura-engine#36`

Exact capability:
`GEOMETRY_PRESERVING_CONTROLLED_VISUAL_GENERATION_EDIT`

Do not parse the narrative body into generic phrase fragments.

The normalized request envelope must contain:

- requesting_team = AURA
- product = AURA
- priority = P0
- resource = model/tool as appropriate
- requested_capability = GEOMETRY_PRESERVING_CONTROLLED_VISUAL_GENERATION_EDIT
- callback_repo = ADAMBUILD-ai/aura-engine
- callback_issue = 36
- benchmark = AURA_GEOMETRY_PRESERVING_EDIT_FIXTURE
- hard_geometry_lock = true

Add deterministic normalization test:
#134 must never normalize to `UNKNOWN` or `UNKNOWN_LEGACY`.

---

## 8. #134 CANDIDATE SEARCH

Search exact capability candidates.

Potential families may include, subject to exact license/revision/runtime gates:

- Qwen Image Edit family
- SDXL Inpainting + ControlNet
- FLUX edit/inpaint/control family
- instruction-guided image editing
- mask-constrained local editors
- deterministic local visual-edit stacks

Family name alone is not adoption.

Prefer:
- local
- pinned
- reproducible
- low-VRAM / quantized when quality is sufficient
- safe file formats
- no arbitrary remote code

Paid/API path may be evaluated but must remain approval-gated and cannot substitute for missing local evidence.

---

## 9. #134 GEOMETRY LOCK BENCHMARK

Use exact AURA benchmark fixture.

Hard invariants:

- building count unchanged
- layout unchanged
- relative positions unchanged
- footprint topology unchanged
- central/common-space relationship unchanged
- protected edges unchanged
- protected pixels unchanged
- E1 outside-mask delta = 0
- edit/protected intersection = 0
- page frame/text outside edit scope unchanged

Any protected geometry drift:
`REJECT_GEOMETRY_DRIFT`

Required visual A/B:

- before
- edit mask
- protected mask
- after
- diff
- geometry metrics

A candidate must visibly improve at least one allowed visual layer:

- material
- landscape
- light
- atmosphere
- people/cars/furniture
- graphic emphasis

without changing protected architecture.

---

## 10. #134 PASS GATE

PASS only when one candidate reaches:

`TESTED_PASS -> CALLBACK_SENT -> DELIVERED`

Required:

- exact model/tool ID
- exact revision/commit
- files + SHA-256
- license/persistence evidence
- runtime environment
- source/mask/protected-mask SHA
- output SHA
- geometry fingerprint before/after
- outside-mask delta
- protected-region delta
- visual A/B
- latency/resources
- KEEP / SUPPORT_ONLY / REJECT
- AURA role/state placement
- Guardian/fallback

Expected role:
`VISUAL_BRAIN`

Required Guardians:
- GEOMETRY_GUARDIAN
- SCOPE_VERSION_GUARDIAN
- CROSS_ARTIFACT_PAGE_GUARDIAN

No model bypasses Geometry Lock.

---

# PART C — MODEL SCOUT SYSTEM CORRECTIONS

## 11. NORMALIZATION REGRESSION

Add tests so canonical structured requests from AURA #35/#36 remain structured.

Required regression tests:

1. #35 -> ARCHITECTURAL_VISUAL_UNDERSTANDING_REPLACEMENT
2. #36 -> GEOMETRY_PRESERVING_CONTROLLED_VISUAL_GENERATION_EDIT
3. #133 wrapper -> resolves to canonical #35 capability
4. #134 wrapper -> resolves to canonical #36 capability
5. narrative text may not overwrite structured capability
6. callback repo/issue preserved
7. benchmark path preserved
8. priority P0 preserved

Failure:
`HARD_FAIL_REQUEST_NORMALIZATION`

---

## 12. RUNTIME DEPENDENCY CHECK

Before model execution, inspect executor dependencies.

For OCR/document-QA candidates:
- pytesseract/Tesseract availability
- OCR preprocessing route
- tokenizer/processor compatibility
- transformers version compatibility

For image-edit candidates:
- torch/diffusers/transformers versions
- CUDA/CPU route
- image libraries
- safetensors/ONNX support
- memory feasibility

Dependency absence must become:
`FAILED_RETRYABLE_ENVIRONMENT_DEPENDENCY`

and trigger an allowed recovery path.

Do not waste retries on the same unchanged environment.

---

## 13. RETRY / RESCOUT RULE

For #133/#134:

`candidate fail -> classify -> repair or rescout -> run next candidate`

Do not terminate at retry-limit if:
- a safe alternate candidate remains;
- a different executor can satisfy the request;
- a missing local dependency can be repaired safely;
- a known acquired candidate still requires product benchmark.

Only terminal stop when:
- all allowed candidates exhausted;
- every failure has evidence;
- no authorized local/free route remains;
- remaining route requires explicit approval.

---

## 14. CALLBACK REQUIREMENTS

Callback to:

### #133
- central issue #133
- canonical AURA issue #35

### #134
- central issue #134
- canonical AURA issue #36

Callback must contain:

- exact candidate
- exact revision
- license
- SHA evidence
- runtime
- benchmark
- result
- role placement
- delivery state

No status-only callback.

---

## 15. AURA FINAL CLOSEOUT CONTRACT

AURA may not clear:

`VERIFY_REQUIRED_MODEL_SCOUT_INVENTORY_NOT_BOUND`

until both capability gaps have verified coverage.

Final AURA consumer:

`FINAL_MODEL_ROUTING_AND_MODEL_SCOUT_BINDING_GATE.json`

Required final state:

`PASS`

Only then may AURA final audit become:

`AURA_FINAL_SYSTEM_INTELLIGENCE_AUDIT = PASS`

---

## 16. REQUIRED EVIDENCE PACKAGE

Create under Model Scout:

`evidence/aura-final-gap-recovery-20260930/`

Required:

- AURA_133_NORMALIZED_REQUEST.json
- AURA_133_CANDIDATE_MATRIX.json
- AURA_133_RUNTIME_DEPENDENCY_CHECK.json
- AURA_133_SIX_CLASS_BENCHMARK.json
- AURA_133_DELIVERY_MANIFEST.json
- AURA_134_NORMALIZED_REQUEST.json
- AURA_134_CANDIDATE_MATRIX.json
- AURA_134_GEOMETRY_LOCK_BENCHMARK.json
- AURA_134_VISUAL_AB.json
- AURA_134_DELIVERY_MANIFEST.json
- AURA_FINAL_GAP_RECOVERY_TEST_RESULTS.md
- AURA_FINAL_GAP_RECOVERY_CLOSEOUT.md

Also preserve:
- exact workflow run IDs
- job IDs
- artifact IDs
- callback comment URLs
- exact commit SHA

---

## 17. COMPLETION RULE

Do not finish with:
- PLAN_ONLY
- SEARCH_ONLY
- ACQUIRED_VERIFIED_ONLY
- WORKFLOW_SUCCESS_ONLY
- FAILED_FIRST_CANDIDATE
- UNKNOWN_LEGACY
- NO_CANDIDATE after a broken query plan

Completion requires:

### #133
`TESTED_PASS + DELIVERED`

### #134
`TESTED_PASS + DELIVERED`

If either is incomplete:
`AURA_FINAL_MODEL_SCOUT_CLOSEOUT = BLOCKED`

If both are complete:
`AURA_FINAL_MODEL_SCOUT_CLOSEOUT = PASS_FOR_AURA_COMMANDER_REVIEW`

Final marker:
`STOP_ONLY_AFTER_AURA_133_AND_134_TESTED_PASS_DELIVERED_OR_TRUE_APPROVAL_BLOCKER`
