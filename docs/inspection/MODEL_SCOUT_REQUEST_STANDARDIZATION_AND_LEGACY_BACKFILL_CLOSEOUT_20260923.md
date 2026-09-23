# MODEL SCOUT Request Standardization and Legacy Backfill Closeout

Date: 2026-09-23  
Central Issue: #75  
Pull Request: #76  
Directive: `MODEL_SCOUT_REQUEST_STANDARDIZATION_FINAL_CLOSEOUT_DIRECTIVE_v3.0_20260923.md`

## Result

The standard Issue Form, request-centric registry, legacy unresolved ledger, parser/normalizer, persistent queue migration, and deterministic registry export are complete. Model records remain revision-centric in `evidence/model-registry.json`; request records remain source Issue/product-centric in `evidence/model-request-registry.json`.

No missing legacy value was inferred. Eight operational legacy items without a confirmed requesting team are retained as `UNKNOWN` / `UNKNOWN_LEGACY`. The unresolved ledger records the evidence needed to improve every incomplete legacy record without blocking closeout.

## Exact counts

| Metric | Count |
|---|---:|
| total_requests | 27 |
| identified_team_count | 19 |
| unknown_team_count | 8 |
| identified_product_count | 27 |
| unknown_product_count | 0 |
| exact_model_request_count | 0 |
| capability_request_count | 14 |
| family_request_count | 0 |
| tool_request_count | 5 |
| dataset_request_count | 0 |
| unknown_legacy_count | 8 |
| delivered_count | 9 |
| active_count | 0 |
| blocked_count | 0 |
| unresolved_count | 27 |

## Aggregates

### by_team

`ADAM=2, ADAM_BUILD=4, ADRAW=1, AGRI=1, AGRI_AI=1, AGRI_AI_BUSINESS_PLATFORM=1, ARCOS=1, AURA=1, AVORA=1, AXIOM=1, G-DOG=1, MINDLE_MEDIA_AI=1, NAS_KNOWLEDGE_AI=1, UNKNOWN=8, WARREN_BUFFETT=1, 김서방=1`

### by_product

`ADAM=2, ADAM BUILD=4, ADRAW=1, AGRI=1, AGRI AI=1, AGRI AI BUSINESS PLATFORM=1, ARCOS=1, AURA=1, AVORA=1, AXIOM=1, G-DOG=1, MINDLE MEDIA AI=1, MODEL SCOUT=8, NAS KNOWLEDGE AI=1, WARREN BUFFETT=1, 김서방=1`

### by_selected_model

- `UNKNOWN`: 23
- `openai/whisper-tiny`: 1
- `cross-encoder/ms-marco-MiniLM-L-6-v2`: 1
- `BAAI/bge-small-en-v1.5; cross-encoder/ms-marco-MiniLM-L-6-v2`: 2

### by_status

- `DELIVERED`: 9
- `FAILED_RETRYABLE`: 18

## Validation

| Gate | Command / evidence | Result |
|---|---|---|
| Focused tests | `python -m pytest -q tests/test_request_standardization.py tests/test_github_request_discovery.py tests/test_persistent_queue.py` | PASS — 18 |
| Full tests | `python -m pytest -q` | PASS — 138 |
| CLI smoke | live JSON query and positive candidate assertion | PASS |
| HF E2E | `tests/test_hf_e2e.py tests/test_api_hf_e2e.py` | PASS — 3 |
| Delivery boundary | `tests/test_delivery_closeout.py` | PASS — 4 |
| Exact-head CI | GitHub checks `tests`, `cli-smoke`, and `hf-e2e` on the final PR #76 head; exact SHA and run IDs are recorded in the PR body | REQUIRED FINAL REMOTE GATE |

## Contract verification

- Standard Issue Form fields are preserved through normalization.
- Exact-model, capability-only, family, tool, dataset, selection-required, and unknown legacy classifications are explicit.
- Request IDs are stable: `MSR::<source_repo>#<source_issue>::<product>`.
- Source and callback identities remain separate and durable.
- Fingerprint semantics remain content-based for mirror deduplication.
- SQLite queues migrate in place and preserve new request metadata.
- Registry export is deterministic and does not collapse separate teams using the same model.

## Remaining risk

- Twenty-seven legacy records still lack at least one standard field; they are enumerated in `evidence/model-request-unresolved-legacy-20260923.json`.
- Twenty-three request records do not yet have a selected model. This is recorded as `UNKNOWN`, not promoted to completion.
- Eighteen requests remain retryable and are not represented as delivered.

## Verdict

`MODEL_SCOUT_REQUEST_STANDARDIZATION_AND_LEGACY_BACKFILL: PASS`

This verdict becomes merge-eligible only after all required GitHub checks succeed on the final PR #76 head. Until explicit user approval, the terminal state is:

`COMMANDER_MERGE_APPROVAL_REQUIRED`
