# MODEL SCOUT — AURA FINAL PRODUCT BENCHMARK + SEARCH EXECUTOR RECOVERY DIRECTIVE v2.0

Date: 2026-09-30
Owner: 신작가님
Requester: AURA Commander
Repository: ADAMBUILD-ai/mindle-model-scout
Priority: P0
Execution mode: CODE FIX + RERUN UNTIL PRODUCT TESTED_PASS/DELIVERED OR TRUE APPROVAL-ONLY BLOCKER

## 0. PURPOSE

Runs #783 and #784 proved that request normalization is improved, but final AURA delivery is still blocked.

Observed:
- #133: ACQUIRED_VERIFIED only, validation_pending=true, component-only synthetic input.
- #134: correctly normalized, but FAILED_RETRYABLE with candidate_count=0 after 30 searches.

This directive requires Model Scout CODE correction, not another unchanged rerun.

## 1. #133 — PRODUCT BENCHMARK STATE MACHINE

Implement an explicit state transition:

`ACQUIRED_VERIFIED -> PRODUCT_BENCHMARK_PENDING -> PRODUCT_BENCHMARK_RUNNING -> TESTED_PASS | REJECT_QUALITY | FAILED_RETRYABLE`

Do not emit final DELIVERED for ACQUIRED_VERIFIED-only evidence.

If callback evidence is sent before product validation, label it:
`ACQUISITION_EVIDENCE_CALLBACK`

Only product benchmark PASS may emit:
`TESTED_PASS -> CALLBACK_SENT -> DELIVERED`

## 2. #133 — AUTHORITATIVE AURA FIXTURE FETCHER

Source repository:
`ADAMBUILD-ai/aura-engine`

Source branch:
`research/aura-reference-warehouse-20260923`

Required six physical inputs:
- P03: `docs/proposal/final/gochang-stage2-corrected-control-v73_2/P03.png`
- P04: `docs/proposal/final/gochang-stage2-corrected-control-v73_2/P04.png`
- P07: `docs/proposal/final/gochang-stage2-corrected-control-v73_2/P07.png`
- P10: `docs/proposal/final/gochang-stage2-corrected-control-v73_2/P10.png`
- P11: `docs/proposal/final/gochang-stage2-corrected-control-v73_2/P11.png`
- P12: `docs/proposal/final/gochang-stage2-corrected-control-v73_2/P12.png`

Benchmark SSOT:
`requests/aura/benchmarks/AURA_ARCH_VISUAL_UNDERSTANDING_FIXTURE_v2.0_20260930.json`

Mandatory:
- fetch actual bytes;
- verify exact SHA-256 against benchmark;
- if any hash mismatch, STOP THAT FIXTURE and locate the authoritative matching artifact by hash;
- no synthetic white image;
- no generated substitute;
- no filename-only evidence.

Create a reusable cross-repo fixture fetcher with evidence:
- source repo
- branch
- path
- git blob sha
- byte sha256
- size
- fetched_at

## 3. #133 — SIX-CLASS BENCHMARK RUNNER

For each of the six classes run the candidate on the actual image.

Required scoring dimensions:
- groundedFactAccuracy
- relationshipReasoning
- crossViewConsistency
- hallucinationPenalty

Required evidence:
- raw model output per class;
- normalized assertions/facts;
- expected-grounded-fact comparison;
- forbidden-hallucination check;
- per-class score;
- aggregate score;
- failure reason.

BLIP generic captioning must not PASS simply because runtime returned 0.

If BLIP fails architecture-specific thresholds:
`REJECT_QUALITY`
then continue to next candidate automatically.

Candidates already surfaced by Model Scout may be evaluated if license/revision/runtime gates pass, including architecture/document VQA lanes. Florence-2 remains negative baseline unless new evidence legitimately exceeds the benchmark.

## 4. #133 — OCR/DOCUMENT DEPENDENCY RECOVERY

For LayoutLM/document-QA candidates:
- preflight Tesseract/pytesseract;
- or use explicit OCR words/boxes from approved OCR preprocessing;
- or choose a candidate without unavailable OCR dependency.

Do not burn retries on unchanged missing dependencies.

State:
`FAILED_RETRYABLE_ENVIRONMENT_DEPENDENCY`

must route to dependency fix or alternate candidate.

## 5. #134 — AUTHORITATIVE GEOMETRY FIXTURE FETCHER

Source repo:
`ADAMBUILD-ai/aura-engine`

Source branch:
`research/aura-reference-warehouse-20260923`

Required files:
- source: `docs/evidence/aura-pc-work-v56/P04_BEFORE.png`
- edit mask: `docs/evidence/aura-pc-work-v56/P04_MASK.png`
- protected mask: `docs/evidence/aura-pc-work-v56/P04_PROTECTED_MASK.png`
- geometry check: `docs/evidence/aura-pc-work-v56/P04_GEOMETRY_CHECK_RAW_v56_1.json`
- mask intersection: `docs/evidence/aura-pc-work-v56/P04_MASK_INTERSECTION_CHECK_RAW_v56_1.json`

Benchmark:
`requests/aura/benchmarks/AURA_GEOMETRY_PRESERVING_EDIT_FIXTURE_v2.0_20260930.json`

Verify source/mask/protected-mask SHA before any candidate runs.

## 6. #134 — SEARCH EXECUTOR CORRECTION

Current plan:
- controlnet inpainting
- image-to-image
- diffusers controlnet

searched 30, executable candidates 0.

This is not a terminal result.

Required changes:

1. Record WHY every discovered candidate was filtered:
   - no immutable revision
   - license unsupported
   - unsupported library/runtime
   - trust_remote_code required
   - insufficient metadata
   - resource mismatch
   - memory infeasible
   - other

2. If one query family yields zero executable candidates, automatically expand:
   - controlled image edit
   - masked inpainting
   - instruction image edit
   - ControlNet inpaint/edit
   - diffusers inpaint/control
   - local deterministic image-edit stack

3. Search both:
   - model resources
   - safe local tool/program resources

4. Allow official non-HF open-source tool routes where the existing Model Scout resource contract supports them.

5. Maintain exact license/revision/rights-persistence gates.

6. No zero-candidate terminal stop while an alternate safe query/source remains.

## 7. #134 — CANDIDATE COMPATIBILITY PREFLIGHT

Before full download/run, detect:
- diffusers/transformers compatibility
- safetensors availability
- required scheduler/control modules
- CPU/GPU path
- VRAM/RAM estimate
- Windows support
- mask input support
- local/offline feasibility

Classify unsupported candidates explicitly instead of silently removing them.

## 8. #134 — GEOMETRY LOCK RUNNER

For every runnable candidate:

Inputs:
- source
- edit mask
- protected mask

Required output:
- edited image
- diff image
- geometry metrics
- source/output hashes

Hard invariants:
- building count = 7
- central COMMON unchanged
- bbox equal
- centroid delta = 0
- protected pixel delta = 0
- outside-mask changed pixels = 0
- edit/protected intersection = 0
- no title/text/frame change

Any violation:
`REJECT_GEOMETRY_DRIFT`

Only after geometry PASS evaluate visual improvement.

## 9. CALLBACK SEMANTICS FIX

Current run #783 emitted a callback object with `delivered:true` while state remained `ACQUIRED_VERIFIED`.

This is ambiguous and must be fixed.

Required callback fields:
- delivery_class
- acquisition_state
- product_validation_state
- terminal_delivery

Allowed:
- `delivery_class=ACQUISITION_EVIDENCE`, terminal_delivery=false
- `delivery_class=PRODUCT_TESTED_PASS`, terminal_delivery=true

AURA final gate must consume only:
`terminal_delivery=true AND product_validation_state=TESTED_PASS`

## 10. REGRESSION TESTS

Add deterministic tests:

### #133
1. ACQUIRED_VERIFIED does not become terminal DELIVERED.
2. synthetic fixture is forbidden for AURA product benchmark.
3. all six AURA physical inputs fetched and SHA verified.
4. six-class scoring generated.
5. generic caption-only output fails architecture threshold.
6. failed candidate advances to next candidate.
7. OCR dependency failure routes to recovery.

### #134
8. structured capability remains preserved.
9. zero executable candidates records exclusion reasons.
10. zero candidate on first query expands alternate queries.
11. source/mask/protected-mask SHA verified.
12. geometry drift rejects candidate.
13. geometry PASS requires zero outside-mask/protected delta.
14. visual A/B created after geometry PASS.
15. safe tool route may be considered.
16. callback only terminal after TESTED_PASS.

## 11. REQUIRED EVIDENCE

Create:
`evidence/aura-final-gap-recovery-v2-20260930/`

Required:
- RUN_783_ROOT_CAUSE.json
- RUN_784_ROOT_CAUSE.json
- AURA_133_FIXTURE_FETCH_MANIFEST.json
- AURA_133_SIX_CLASS_BENCHMARK.json
- AURA_133_CANDIDATE_DECISIONS.json
- AURA_134_FIXTURE_FETCH_MANIFEST.json
- AURA_134_SEARCH_EXCLUSION_MATRIX.json
- AURA_134_CANDIDATE_MATRIX.json
- AURA_134_GEOMETRY_LOCK_RESULTS.json
- AURA_134_VISUAL_AB_MANIFEST.json
- CALLBACK_SEMANTICS_REGRESSION.json
- TEST_RESULTS.md
- CLOSEOUT.md

## 12. COMPLETION

Do not rerun unchanged code and call workflow success a result.

Required execution:
`CODE FIX -> TEST -> COMMIT -> PUSH -> RERUN #133/#134 -> PRODUCT BENCHMARK -> CALLBACK -> DELIVERED -> REMOTE EVIDENCE`

#133 complete only:
`TESTED_PASS + terminal_delivery=true`

#134 complete only:
`TESTED_PASS + terminal_delivery=true`

Otherwise:
`AURA_FINAL_MODEL_SCOUT_CLOSEOUT = BLOCKED`

Final marker:
`STOP_ONLY_AFTER_CODE_CORRECTION_AND_AURA_133_134_PRODUCT_DELIVERY`
