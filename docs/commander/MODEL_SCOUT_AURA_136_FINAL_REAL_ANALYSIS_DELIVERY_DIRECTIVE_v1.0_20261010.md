# MODEL SCOUT — AURA #136 FINAL REAL ANALYSIS DELIVERY DIRECTIVE v1.0

Date: 2026-10-10
Owner: 신작가님
Commander: AURA Commander
Executor: MODEL_SCOUT
Priority: P0

Repository:
ADAMBUILD-ai/mindle-model-scout

Branch:
main

Primary request:
Issue #136
[AURA] AURA_GENERATIVE_ARCHITECTURAL_CORPUS_ANALYSIS_MODEL

Callback:
ADAMBUILD-ai/aura-engine issue #37

Consumer:
ADAMBUILD-ai/aura-engine
branch: research/aura-reference-warehouse-20260923

## 0. PURPOSE

Close AURA Model Scout request #136 with one real generative analysis model delivery.

Do not restart the broad candidate-search cycle.
Do not substitute text-classification, embedding, reranker, OCR, or vision-only models.
Do not report ACQUIRED_VERIFIED as product PASS.

Required lifecycle:

TESTED_PASS -> CALLBACK_SENT -> DELIVERED

The delivered result must be directly usable by AURA's existing createAnalysisModelProvider / approved compatible local runtime contract.

## 1. ACCEPTED HISTORY — DO NOT REPEAT

Preserve prior work already merged on main:
- text-search routing correction
- classifier substitution prevention
- pinned metadata hydration
- Korean/English language metadata recovery
- immutable revision/license evidence gathering
- bounded generative candidate discovery

Relevant merged heads include:
- 3ccfee255eaf05e0be7aca9efe0ba50992189f62
- 3ff82d9b9daa3f155e7cfb1ab58c01a070a068ff

Current known defect:
src/model_scout/runtime_executors.py explicitly blocks AURA #136 because the configured generic Hugging Face worker is a text-classification executor, not a causal/generative LLM.

That block is correct. Do not remove it by pretending the classifier is suitable.

## 2. REQUIRED EXECUTION STRATEGY

Use the already discovered/pinned candidate set first.

Select the smallest approved CPU-capable generative text model that can satisfy:
- Korean and English architectural reasoning
- structured JSON output
- source-bound synthesis
- >=32768 usable context tokens OR a measured bounded context strategy that truthfully accounts for truncation
- local/OpenAI-compatible serving path preferred
- no new paid API
- no new GPU purchase
- immutable model revision
- exact weight hashes
- persistent license snapshot / acquired-version usage evidence

If no existing candidate can meet the contract on approved CPU resources, stop with a precise terminal. Do not restart endless search.

## 3. REAL EXECUTOR REQUIREMENT

Implement or bind a true generative-text executor for #136.

Allowed:
- existing approved local OpenAI-compatible endpoint
- existing approved Ollama-compatible path
- Transformers causal/text-generation runtime if already supportable within current approved environment

Forbidden:
- generic text-classification worker
- synthetic-only inference
- mocked generation as PASS
- hidden remote paid API
- unpinned model revision
- silent model substitution

The runtime record must include:
- providerId
- modelId
- immutable model revision
- runtime/software versions
- invocationId
- prompt SHA256
- output SHA256
- input token accounting
- output token accounting
- truncation accounting
- wait_ms
- endpoint/runtime health
- raw artifactRef

## 4. BENCHMARK — REAL AURA INPUT

Use the already frozen AURA v14.30 qualified corpus as the benchmark source pool.

Consumer evidence:
ADAMBUILD-ai/aura-engine
docs/evidence/aura-v14_31r5-no-repeat-closeout-20261010/05_PILOT10_EXISTING_CORPUS_SELECTION.json

Use real source-bound records from that accepted corpus.

Minimum benchmark:
- KR >= 10 and GLOBAL >= 10 if the existing source-bound benchmark dataset is available
- otherwise execute the maximum currently persisted real corpus and report BLOCKED_INPUT for the missing remainder
- no synthetic replacement
- no invented source IDs

Required AURA output fields:
- patternClusters
- positiveCases
- negativeMismatchCases
- contradictions
- constraints
- risks
- unresolvedGaps
- nextSearchTargets
- competingDesignHypotheses
- rejectedStrategies
- sourceBoundDesignInference
- drawingProofRequirements
- coverageMatrix
- confidence
- applicability

All inferential claims must cite actual input source IDs.

## 5. QUALITY GATES

PASS requires:
- real generation, not classification
- Korean and English input handled
- JSON parses to expected schema
- zero invented source IDs
- no accepted claim without source binding
- model/revision/hash/license evidence complete
- repeated invocation produces valid source-bound output
- no hidden paid service
- benchmark artifacts preserved

Record failures separately:
- context overflow
- malformed JSON
- invented source IDs
- missing fields
- runtime crash
- CPU timeout
- unsupported language
- license failure

## 6. CALLBACK CONTRACT

On TESTED_PASS, write callback artifact to AURA:

Repository:
ADAMBUILD-ai/aura-engine

Branch:
research/aura-reference-warehouse-20260923

Path:
docs/evidence/aura-live-runtime-service-binding-v5-20261001/MODEL_SCOUT_DELIVERY.json

Callback issue:
AURA #37

The callback must include:
- status TESTED_PASS / CALLBACK_SENT / DELIVERED
- providerId
- modelId
- immutable revision
- weight hashes
- license evidence
- runtime endpoint/binding contract
- health result
- benchmark input hashes
- inference receipt hashes
- invocation IDs
- token/context accounting
- zero-invented-source assertion with measured evidence
- exact Model Scout source commit
- exact callback commit in aura-engine

Do not mark DELIVERED until AURA callback bytes are remotely read back.

## 7. EVIDENCE

Create:
docs/evidence/aura-136-final-real-analysis-delivery-20261010/

Required:
00_REQUEST_AND_HISTORY_LOCK.json
01_EXISTING_CANDIDATES_REUSE.json
02_SELECTED_MODEL_IDENTITY_LICENSE.json
03_REAL_GENERATIVE_EXECUTOR_BINDING.json
04_RUNTIME_HEALTH.json
05_REAL_AURA_BENCHMARK_INPUT.json
06_REAL_INFERENCE_RECEIPTS.json
07_SCHEMA_SOURCE_BINDING_QUALITY.json
08_CALLBACK_DELIVERY.json
09_FINAL_VERDICT.json
REMOTE_EVIDENCE_READBACK.json

## 8. TERMINALS

Preferred:
PASS_MODEL_SCOUT_AURA_136_TESTED_DELIVERED

Allowed blockers:
AURA_136_NO_APPROVED_CPU_GENERATIVE_MODEL
AURA_136_REAL_BENCHMARK_INPUT_INCOMPLETE
AURA_136_RUNTIME_EXECUTOR_NOT_AVAILABLE
AURA_136_LICENSE_OR_IMMUTABLE_IDENTITY_BLOCKED
AURA_136_MODEL_QUALITY_FAILED

No generic DONE.

## 9. STOP

After one terminal:
STOP_FOR_AURA_COMMANDER_REVIEW

Do not start AURA Pilot-10.
Do not touch #133 in this directive.
Do not start broad search again.

Final marker:
ONE_REAL_GENERATIVE_MODEL_OR_ONE_PRECISE_BLOCKER_NO_MORE_SEARCH_LOOP
