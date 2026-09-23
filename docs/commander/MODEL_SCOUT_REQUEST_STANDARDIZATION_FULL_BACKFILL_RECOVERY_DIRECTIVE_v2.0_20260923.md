# MINDLE MODEL SCOUT
## REQUEST STANDARDIZATION FULL BACKFILL RECOVERY DIRECTIVE
### v2.0 — 2026-09-23

**Authority:** 신작가님 → MODEL SCOUT Commander → General Work Executor  
**Repository:** `ADAMBUILD-ai/mindle-model-scout`  
**Central Standardization Issue:** #75  
**Active PR:** #76  
**Work branch:** `standards/model-scout-request-contract-20260923`

---

# 1. COMMANDER REVIEW RESULT

Current PR #76 contains only the initial standardization documents:

- `.github/ISSUE_TEMPLATE/model-scout-request.yml`
- `docs/standards/MODEL_SCOUT_STANDARD_REQUEST_CONTRACT_v1.0_20260923.md`
- `docs/commander/MODEL_SCOUT_REQUEST_STANDARDIZATION_AND_LEGACY_BACKFILL_DIRECTIVE_v1.0_20260923.md`

The required execution outputs are still missing.

Therefore current verdict:

`REWORK_REQUIRED — TEMPLATE CREATED / BACKFILL NOT EXECUTED`

This is not a documentation task anymore.

---

# 2. DO NOT STOP AT TEMPLATE / PLAN

General Work must now execute the actual migration/backfill.

Required missing outputs:

1. `evidence/model-request-registry.json`
2. `evidence/model-request-unresolved-legacy-20260923.json`
3. parser/normalizer implementation for the standardized fields
4. tests for standardized request parsing and legacy fallback
5. full historical request backfill
6. `docs/inspection/MODEL_SCOUT_REQUEST_STANDARDIZATION_AND_LEGACY_BACKFILL_CLOSEOUT_20260923.md`

Do not stop before all six exist.

---

# 3. HISTORICAL REQUEST BACKFILL SCOPE

Audit all MODEL SCOUT request sources visible in the repository history and central Issues.

For each source request, extract only evidence-supported values:

- request_id
- requesting_team
- product
- source_repo
- source_issue
- source_url
- request_owner
- priority
- requested_capability
- requested_model_id
- requested_model_family
- selection_mode
- selected_model_id
- selected_revision
- license
- commercial_use
- rights_persistence_evidence
- status
- callback_repo
- callback_issue
- evidence_paths
- delivered_at
- last_updated

Never infer team/product/model from adjacent projects unless explicit evidence exists.

Use:
- `UNKNOWN`
- `UNKNOWN_LEGACY`
- `VERIFY_REQUIRED`

where evidence is incomplete.

---

# 4. REQUIRED REQUEST CLASSIFICATION

Every legacy request must be one of:

- `EXACT_MODEL_REQUEST`
- `CAPABILITY_REQUEST`
- `FAMILY_REQUEST`
- `TOOL_REQUEST`
- `DATASET_REQUEST`
- `UNKNOWN_LEGACY`

Do not leave classification blank.

---

# 5. REQUEST ↔ MODEL LINKAGE

Model Registry and Request Registry serve different purposes.

## Model Registry
One record per acquired model revision.

## Request Registry
One record per team/product request.

If 5 teams use one model:
- Model Registry = 1 model record
- Request Registry = 5 request records

Each Request record must link to its selected model revision where known.

Do not collapse different teams into one request.

---

# 6. STANDARD ISSUE FORM PARSER

Update request discovery/normalization so standardized Issue Form fields are preserved.

Mandatory normalized fields:

- requesting_team
- product
- request_owner
- requested_capability
- requested_model_id
- requested_model_family
- selection_mode
- acceptance_criteria

Preserve existing:
- source_repo
- source_issue
- callback_repo
- callback_issue
- priority
- fingerprint

Legacy free-form requests must continue to parse.

If a legacy field is unavailable:
store `UNKNOWN`, not guessed text.

---

# 7. REQUEST ID RULE

Stable format:

`MSR::<source_repo>#<source_issue>::<product>`

If product is unknown:
`MSR::<source_repo>#<source_issue>::UNKNOWN`

If one Issue contains multiple independent subrequests:
append a deterministic suffix:
`::R1`, `::R2`, etc.

Do not generate a new ID on each run.

---

# 8. MACHINE-READABLE REGISTRY

Create:

`evidence/model-request-registry.json`

Required root:

- schema_version
- generated_at
- requests

Required summary block:

- total_requests
- identified_team_count
- identified_product_count
- exact_model_request_count
- capability_request_count
- family_request_count
- tool_request_count
- dataset_request_count
- unknown_legacy_count
- delivered_count
- active_count

Also include aggregates:
- by_team
- by_product
- by_selected_model
- by_status

---

# 9. UNRESOLVED LEGACY FILE

Create:

`evidence/model-request-unresolved-legacy-20260923.json`

Include only requests with unresolved fields.

For each:
- request_id
- source_repo
- source_issue
- missing_fields
- exact_reason
- next_evidence_needed

Do not bury unresolved records inside prose.

---

# 10. TEST REQUIREMENTS

Add deterministic tests for:

1. standardized Issue Form parses all required fields
2. `SCOUT_SELECTION_REQUIRED` is preserved
3. exact model request is classified correctly
4. capability-only request is classified correctly
5. legacy free-form request remains supported
6. unknown legacy fields remain UNKNOWN
7. duplicate request keeps one stable Request ID
8. same model used by multiple teams produces multiple request records
9. callback/source linkage is preserved
10. registry export is deterministic

Then run:
- focused tests
- full tests
- cli-smoke
- hf-e2e

---

# 11. CLOSEOUT REPORT

Create:

`docs/inspection/MODEL_SCOUT_REQUEST_STANDARDIZATION_AND_LEGACY_BACKFILL_CLOSEOUT_20260923.md`

Must report exact counts:

- total legacy requests
- team identified
- team unknown
- product identified
- product unknown
- exact model requests
- capability-only requests
- family requests
- tool requests
- dataset requests
- unknown legacy
- delivered
- in progress
- blocked
- unresolved

Also list:
- requests by team
- requests by product
- selected models and linked request counts
- unresolved legacy records
- test/CI run IDs
- exact HEAD

Final verdict may be:

`MODEL_SCOUT_REQUEST_STANDARDIZATION_AND_LEGACY_BACKFILL: PASS`

only when registry, parser, tests, backfill, unresolved file, and inspection report all exist.

---

# 12. EXECUTION RULE

Execute continuously:

`DISCOVER → EXTRACT → CLASSIFY → LINK → BACKFILL → PARSE → TEST → EVIDENCE → CLOSEOUT`

Do not stop after partial backfill.

Do not stop because some legacy values are unknown.
Unknown is an acceptable explicit result; guessing is not.

Stop only at:
- FINAL PASS
- or one exact approval-only blocker.
