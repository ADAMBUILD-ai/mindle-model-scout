# CURRENT EXECUTION CONTROL

Status source: GitHub Evidence only. This file is the executor-facing SSOT for the current MODEL SCOUT gate.

## Integrated baseline on `main`
- Repository: `ADAMBUILD-ai/mindle-model-scout`
- Default branch: `main`
- Current main: `e04f169f4bff6a77c9f9d34cefda8ce9e52c5aea`
- SCOUT-GATE-02A / 02B / 03 / 04: merged and previously CI-verified.
- Common FastAPI layer: merged.
- UI/API validation recovery: merged.
- WARREN–BUFFETT Issue #28 / PR #30: completed and merged.

## Parallel active gate A — AURA TESTED_PASS delivery
Authoritative sources:
- Issue #32: `AURA P0 — Approved Model Shopping / Deliver TESTED_PASS Assets`
- PR #31: `feat: add AURA execution order for MODEL SCOUT handoff`
- Branch: `feat/aura-execution-order-20260913`
- Current PR #31 head: `2dfa006fedd92f21a62b7897b4c19f706daf6de6`

Verified boundary:
- No `AURA_MODEL_SCOUT_DELIVERY_20260913` package with real inference output/log/settings/runtime/hash has been verified yet.
- Scout results, downloads, model-card checks, or CI alone are not `TESTED_PASS`.
- `TESTED_PASS` requires real input/output + model ID/revision/license/source + settings + runtime/HW/VRAM + log + file SHA-256.

Execution authority:
- Safe/free/public scouting, download, local execution testing, re-scouting, Evidence generation, branch/PR/test/document updates are authorized without another user prompt.
- Approval is required only for login/additional permission, cost/paid GPU, external publication, destructive or hard-to-reverse change, secret rotation, production deployment, or another irreversible action.

## Parallel active gate B — P0 complete automation recovery
Authoritative sources:
- Issue #36: `[P0 RECOVERY] Request ingestion + execution dispatcher + TESTED_PASS runner`
- PR #37: `feat: add P0 request queue normalization and dedupe recovery slice`
- Branch: `recovery/request-ingestion-gate-20260913`

### Verified implemented Evidence
The following recovery slices are already implemented on PR #37 and MUST NOT be listed as future work:
1. Deterministic request normalization + fingerprint dedupe + queue state contract.
2. Configured GitHub Issue request discovery + callback metadata normalization.
3. Dispatcher: `QUEUED -> RUNNING -> existing scout core -> EVIDENCE_READY`, with retryable failure state.
4. Retry-safe callback-delivery state contract: `EVIDENCE_READY -> DELIVERED`; callback failure leaves the item at `EVIDENCE_READY` and does not rerun scout core.
5. SQLite persistent queue + restart-safe state recovery + persisted source/callback metadata/evidence pointer.
6. Watchdog stale-request recovery for `QUEUED`/`RUNNING`, with retry counter/error/attempt metadata; `EVIDENCE_READY` is excluded from scout rerun.

Latest implementation commits:
- `1be5393da4de33c85d520f89e0bdff18cb71c087` — retry-safe source callback delivery.
- `08826d088cd195c026d8220de6036709afc4548a` — callback delivery/retry tests; prior CI all PASS.
- `b5c69519bed7fad7f00daf6cb08d019074d1590b` — SQLite persistent queue and stale requeue implementation.
- `ef102ea996df0c199db93e03b653aa2ec5e24a3d` — persistence/restart/watchdog deterministic tests.

Prior verified CI on `08826d088...`:
- tests `34791747433` — SUCCESS
- hf-e2e `34791747422` — SUCCESS
- cli-smoke `34791747413` — SUCCESS

Fresh CI for the persistence/watchdog head is REQUIRED before that slice is accepted. Do not claim PASS until GitHub Actions reports it.

### Current exact next executable work
1. Wire a concrete GitHub issue-comment callback transport adapter to the existing callback delivery contract; test callback success/failure/retry against the transport boundary.
2. Add runtime-validation runner boundary for requests explicitly requiring execution Evidence. Safe/free/local/non-destructive work may auto-run; approval-gated operations must transition to `BLOCKED_APPROVAL`.
3. Run a real cross-repo lifecycle proof using at least two project requests and record: source request -> discovery -> normalization/dedupe -> persistence -> queue -> dispatch -> evidence -> source callback -> `DELIVERED`.
4. Exercise one duplicate request and one retryable failure/recovery path.
5. Only after code Evidence exists, refresh this file again with exact commit/CI/lifecycle Evidence.

### Closeout definition
MODEL SCOUT is NOT complete until a development team can place a valid request in its own configured repository and receive verified scout/runtime Evidence back without manual mirroring, manual assignment, manual requeue, or user intervention for safe/free work.

Required closeout Evidence:
- code commits
- deterministic persistence/watchdog/callback/approval/E2E tests
- `tests + hf-e2e + cli-smoke` PASS on the final PR head
- real cross-repo lifecycle Evidence
- AURA runtime output Evidence for any `TESTED_PASS` claim

## Evidence-first operating rule
- Never report progress without a commit, PR, CI/test result, artifact, or exact verified blocker.
- If meaningful development Evidence is unchanged for two consecutive checks, audit in this order: repository/write permission -> remote branch/PR/commit and possible local-only work -> Actions/CI -> SSOT/handoff reachability -> integration owner/next-action trigger -> remote push/integration path.
- Classify the exact verified cause and execute the smallest safe corrective action immediately when approval is not required.
- Local-only work is `UNVERIFIED` until pushed.
- Do not merge `main`, deploy Production, incur cost, rotate secrets, publish externally, or perform destructive changes without explicit user approval.
