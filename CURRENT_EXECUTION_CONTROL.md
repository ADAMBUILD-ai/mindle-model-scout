# CURRENT EXECUTION CONTROL

Status source: GitHub Evidence only. This file is the executor-facing SSOT for the current MODEL SCOUT gate.

## Integrated baseline on `main`
- Repository: `ADAMBUILD-ai/mindle-model-scout`
- Default branch: `main`
- Current main: `7040dd9b7e2e8ffea8e0a6d147904f18dfb8c014`
- SCOUT-GATE-02A / 02B / 03 / 04: merged and previously CI-verified.
- Common FastAPI layer: merged.
- UI/API validation recovery: merged.
- WARREN–BUFFETT Issue #28 / PR #30: completed and merged.

## Evidence audit checkpoint — 2026-09-16 16:12 KST
This checkpoint supersedes older operational-status lines when they conflict with fresh GitHub Evidence.

1. Repository health / permission: repository active, default branch `main`; connected authority reports `admin=true`, `maintain=true`, `push=true`, `pull=true`.
2. Remote branch / PR / commit state: `main` remains `7040dd9b7e2e8ffea8e0a6d147904f18dfb8c014`; no newer remote main commit was verified during this checkpoint. PR #44 remains OPEN at `7d88788d5ed45676588afd8e8c416bb70645a457` and is `mergeable=false`, `mergeable_state=dirty`. Local-only work is UNVERIFIED until pushed.
3. Actions / CI: manual `autonomous-model-scout` workflow run `35067189916` on `7040dd9...` completed SUCCESS. All recovery-cycle steps succeeded and artifact `10435295017` (`model-scout-autonomous-evidence`, 3602 bytes, digest `sha256:2d8b755ed5b893cbe60f698d473f8bc4dee53ed509e39cd2446cb699bc80226a`) was created. Repository-wide `event=schedule` run count is still 0. Therefore runner/runtime/manual dispatch are verified healthy, while scheduled event creation is not verified.
4. SSOT / handoff reachability: this file was reachable but its prior `Current main` value was stale (`e04f169...`). This branch refresh is the immediate safe corrective action; do not claim it is integrated until the PR is merged.
5. Integration owner / next-action trigger: Issue #36 remains OPEN and assigned to `ADAMBUILD-ai`; execution ownership exists. Exact current blocker is `SCHEDULE EVENT CREATION GAP` at the GitHub schedule-trigger layer, not runner/Python/runtime.
6. Remote push / integration path: repository write path is verified available. No force push, production deployment, secret change, destructive operation, or main merge is authorized by this checkpoint.

Current scheduler classification:
- `MANUAL AUTONOMOUS CYCLE = VERIFIED PASS`
- `SELF-HOSTED RUNNER/RUNTIME = VERIFIED PASS`
- `SCHEDULED AUTONOMY = BLOCKED / event=schedule total_count=0`
- Underlying schedule-event-generation cause remains `UNKNOWN` pending platform-layer Evidence.

## Parallel active gate A — AURA TESTED_PASS delivery
Authoritative sources:
- Issue #32: `AURA P0 — Approved Model Shopping / Deliver TESTED_PASS Assets`
- PR #31: `feat: add AURA execution order for MODEL SCOUT handoff`
- Branch: `feat/aura-execution-order-20260913`
- Current PR #31 head: `2dfa006fedd92f21a62b7897b4c19f706daf6de6`

Verified boundary:
- No `AURA_MODEL_SCOUT_DELIVERY_20260913` package with real inference output/log/settings/runtime/hash has been verified yet.
- Code search on current main finds that package name only in this execution-control document, not as a verified delivery package.
- Scout results, downloads, model-card checks, or CI alone are not `TESTED_PASS`.
- `TESTED_PASS` requires real input/output + model ID/revision/license/source + settings + runtime/HW/VRAM + log + file SHA-256.
- Issue #32 remains OPEN; PR #31 remains OPEN and its body still states AURA P03~P11 artifact generation is not started.

Execution authority:
- Safe/free/public scouting, download, local execution testing, re-scouting, Evidence generation, branch/PR/test/document updates are authorized without another user prompt.
- Approval is required only for login/additional permission, cost/paid GPU, external publication, destructive or hard-to-reverse change, secret rotation/access, production deployment, or another irreversible action.

## Parallel active gate B — P0 complete automation recovery
Authoritative sources:
- Issue #36: `[P0 RECOVERY] Request ingestion + execution dispatcher + TESTED_PASS runner`
- Historical implementation PR #37: `feat: complete MODEL SCOUT P0 automation recovery foundation`
- Historical branch: `recovery/request-ingestion-gate-20260913`

### Verified implemented Evidence
The following recovery slices were implemented and MUST NOT be listed as future work:
1. Deterministic request normalization + fingerprint dedupe + queue state contract.
2. Configured GitHub Issue request discovery + callback metadata normalization.
3. Dispatcher: `QUEUED -> RUNNING -> existing scout core -> EVIDENCE_READY`, with retryable failure state.
4. Retry-safe callback-delivery state contract: `EVIDENCE_READY -> DELIVERED`; callback failure leaves the item at `EVIDENCE_READY` and does not rerun scout core.
5. SQLite persistent queue + restart-safe state recovery + persisted source/callback metadata/evidence pointer.
6. Watchdog stale-request recovery for `QUEUED`/`RUNNING`, with retry counter/error/attempt metadata; `EVIDENCE_READY` is excluded from scout rerun.
7. Concrete GitHub Issue-comment callback transport with injected token/API boundary, sanitized non-2xx/network failures, and deterministic success/failure/retry integration tests.
8. Approval-aware runtime validation boundary: safe/free/local/non-destructive work may run automatically; login/additional permission, paid cost, secret access/rotation, production deployment, external publication, destructive or other irreversible work transitions to `BLOCKED_APPROVAL`. `TESTED_PASS` requires a real output file and deterministic metadata/size/SHA-256 verification.

Historical implementation commits:
- `0d916c92050a134e6f73aabac0afd02cdf8929bf` — approval-aware runtime TESTED_PASS validation boundary.
- `a7099309cb18ba01c43d0470914e9167ed2d5c75` — deterministic runtime Evidence / approval-boundary tests.
- `1ab1d1092ea371cade6d436e335f5627929a5834` — concrete GitHub Issue-comment callback transport.
- `d77d9251db199f3a0d98e1b2fe31dee460546e01` — transport boundary + delivery retry tests.
- `b5c69519bed7fad7f00daf6cb08d019074d1590b` — SQLite persistent queue and stale requeue implementation.
- `ef102ea996df0c199db93e03b653aa2ec5e24a3d` — persistence/restart/watchdog deterministic tests.

Historical CI on `a7099309cb18ba01c43d0470914e9167ed2d5c75`:
- tests `34864857252` — SUCCESS; pytest `81 passed, 1 warning`
- hf-e2e `34864857262` — SUCCESS
- cli-smoke `34864857600` — SUCCESS

### Current exact next executable work
1. Do not repeat runner/Python recovery while manual autonomous cycles continue to PASS. Isolate the remaining scheduled-autonomy failure to GitHub default-branch workflow registration / schedule-event generation and collect platform-layer Evidence.
2. Preserve degraded safe execution via verified manual `workflow_dispatch` only as a fallback; do not misreport it as scheduled autonomy.
3. Resolve PR #44 only through a conflict-safe update/rebase path with fresh CI Evidence; no force push or main merge without separate authorization.
4. Keep AURA Issue #32 active in parallel; do not claim AURA `TESTED_PASS` without the real delivery package and actual runtime output asset.
5. Continue real cross-repo lifecycle proof and preserve exact source issue, fingerprint, queue states, callback Evidence, commit/PR/CI identifiers.

### Closeout definition
MODEL SCOUT is NOT complete until a development team can place a valid request in its own configured repository and receive verified scout/runtime Evidence back without manual mirroring, manual assignment, manual requeue, or user intervention for safe/free work.

Required closeout Evidence:
- code commits
- deterministic persistence/watchdog/callback/approval/E2E tests
- `tests + hf-e2e + cli-smoke` PASS on the final PR head
- real cross-repo lifecycle Evidence from at least two project requests
- duplicate-request and retryable-failure recovery Evidence
- verified scheduled autonomous trigger Evidence, or an explicitly accepted replacement trigger architecture
- AURA runtime output Evidence for any `TESTED_PASS` claim

## Evidence-first operating rule
- Never report progress without a commit, PR, CI/test result, artifact, or exact verified blocker.
- If meaningful development Evidence is unchanged for two consecutive checks, audit in this order: repository/write permission -> remote branch/PR/commit and possible local-only work -> Actions/CI -> SSOT/handoff reachability -> integration owner/next-action trigger -> remote push/integration path.
- Classify the exact verified cause and execute the smallest safe corrective action immediately when approval is not required.
- Local-only work is `UNVERIFIED` until pushed.
- Do not merge `main`, deploy Production, incur cost, rotate/access secrets, publish externally, or perform destructive changes without explicit user approval.
