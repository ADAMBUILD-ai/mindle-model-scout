# MODEL SCOUT P0 Request-Ingestion Recovery Gate

Date: 2026-09-13
Status: ACTIVE RECOVERY GATE

## 1. Verified problem
MODEL SCOUT core search/API functions exist and are healthy, but the current architecture is pull-based: a caller must explicitly invoke `/v1/scout` or create/maintain an execution issue/handoff. There is no verified repository-level mechanism that discovers MODEL SCOUT requests written in other project repositories and converts them into a central executable queue.

This causes asymmetric operation:
- AURA: central Issue #32 exists -> execution starts.
- WARREN–BUFFETT: central Issue #28 existed -> execution completed.
- Other teams may write valid MODEL SCOUT requests in their own repo/issue/handoff, but no central MODEL SCOUT execution record is created -> no execution trigger.

Therefore the verified failure class is REQUEST_INGESTION / HANDOFF FAILURE, not core HF search failure.

## 2. P0 objective
Make valid MODEL SCOUT requests executable regardless of which ADAMBUILD-ai project repository they originate from.

## 3. Minimal architecture
### 3.1 Request discovery
Add one safe discovery path that can enumerate configured project repositories and detect open Issues containing one of the approved request markers:
- `[MODEL SCOUT 요청]`
- `[MODEL_SCOUT_REQUEST]`
- `MODEL SCOUT`
- `Hugging Face` together with an explicit find/scout/shop/model request intent

Do not scan secrets or private issue bodies outside configured ADAMBUILD-ai repositories.

### 3.2 Normalization
Convert each discovered request into a deterministic request envelope:
- source_repo
- source_issue_number
- source_url
- project
- requested_capability/problem
- resource: model|dataset|space|tool|all
- constraints
- expected_result
- callback target
- request_fingerprint

Incomplete but actionable requests must be normalized from project context instead of silently ignored. Only irreversible/cost/auth requirements may block.

### 3.3 Central execution queue
Persist a central queue record in MODEL SCOUT. Minimum viable implementation may be a JSON state file plus GitHub Issue/PR evidence. Duplicate source requests must deduplicate by fingerprint.

Required states:
- DISCOVERED
- NORMALIZED
- QUEUED
- RUNNING
- EVIDENCE_READY
- DELIVERED
- BLOCKED_APPROVAL
- FAILED_RETRYABLE

### 3.4 Auto execution
For QUEUED requests, invoke existing MODEL SCOUT core/API flow without redesigning the scout engine. Existing license gate, ranking, report, watch, API and CLI stay authoritative.

### 3.5 Delivery
Write result evidence back to the source request location and central queue record. A request is not complete until delivery evidence exists.

## 4. Immediate compatibility rule
Until automated discovery code is merged, executors must manually mirror any verified external project MODEL SCOUT request into the central queue/Issue on detection. Do not wait for a user to repeat the request.

## 5. Acceptance tests
1. A valid request in a non-MODEL-SCOUT ADAMBUILD-ai repository is discovered.
2. It is normalized into a deterministic request envelope.
3. The same source request is not queued twice.
4. A partially specified but actionable request is accepted and normalized.
5. Cost/login/secret/production/destructive requirements become BLOCKED_APPROVAL, not silent failure.
6. An ordinary free/public HF request reaches QUEUED/RUNNING automatically.
7. Existing scout core is invoked and evidence is produced.
8. Result/evidence is written back to the originating project request.
9. Unit tests cover discovery, normalization, dedupe, status transitions and callback metadata.
10. Existing tests + hf-e2e + cli-smoke remain PASS.

## 6. Non-goals
- No rewrite of search/ranking/license/report core.
- No production deployment in this gate.
- No paid provider activation.
- No secret rotation.
- No cross-organization scanning.

## 7. Evidence rule
Progress is recognized only by code commit + tests + PR + CI or an exact verified blocker. Documents alone are not completion.

## 8. Immediate next action
Implement `request_ingestion` as a thin layer around the existing core, starting with deterministic normalization/deduplication tests and a configured GitHub request discovery adapter. Then connect QUEUED requests to the existing scout function/API and add source callback evidence.
