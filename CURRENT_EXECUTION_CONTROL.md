# CURRENT EXECUTION CONTROL

Status source: GitHub Evidence only. This file is the executor-facing SSOT for the current MODEL SCOUT gate.

## Integrated baseline on `main`
- Repository: `ADAMBUILD-ai/mindle-model-scout`
- Default branch: `main`
- Current main: `7040dd9b7e2e8ffea8e0a6d147904f18dfb8c014`
- Do not claim PR/recovery branch work as integrated until merge Evidence exists.

## Active recovery gate — Team Router / ACK watchdog
- PR #61: `Recovery: Team Router and ACK watchdog`
- Branch: `recovery/team-router-ack-20260917`
- Pre-refresh head: `1ebf9c3e1eec29ccb08dd0d3851281f3cb6cfaa7`
- Scope: static team registry for MINDLE MEDIA AI, AI 닥터 김서방, ARCOS; idempotent child-issue routing; `REQUEST_SENT`; `ACK_RECEIVED`; 15-minute `EXECUTOR_UNREACHABLE` audit; real routing command and focused E2E tests.
- Verified code/CI boundary before this SSOT refresh: focused local suite `15 passed`; exact-head GitHub Actions `tests`, `cli-smoke`, `hf-e2e` previously verified SUCCESS.
- Runtime completion is NOT claimed until actual `REQUEST_SENT -> ACK_RECEIVED` Evidence exists, or an actual missing-ACK case produces `EXECUTOR_UNREACHABLE` Evidence.

## Runtime execution recovery gate
- PR #59: `Recovery: connect durable ingestion to runtime execution`
- Branch: `recovery/runtime-execution-core-20260916`
- Current remote head: `0e680b6225f9708cf3d951802f0339ea3ea9aa67`
- Delivered request lanes already evidenced: #47, #48, #49, #52, #53, #54, #56.
- Exact remaining blockers: #50 real project video/Korean speech sample absent; #51 real Korean STT/TTS sample/avatar video absent; #55 three actual georeferenced GeoTIFF/satellite/parcel-map samples absent; #57 actual filing/IR document provenance unavailable to local runtime and outbound CLI download blocked; #58 actual field image/Korean label sample and training-data provenance absent.
- Generated/component smoke results must not be promoted to request-complete `TESTED_PASS`.

## AURA TESTED_PASS gate
- Issue #32 and PR #31 remain authoritative for AURA delivery.
- Branch: `feat/aura-execution-order-20260913`
- Current remote branch head: `2dfa006fedd92f21a62b7897b4c19f706daf6de6`.
- No verified AURA delivery package with real inference input/output + model ID/revision/license/source + settings + runtime/HW/VRAM + log + output SHA-256 exists yet.
- Therefore `AURA TESTED_PASS = 0 / VERIFY_REQUIRED` until that exact Evidence exists.

## Current exact next executable work
1. On PR #61, obtain actual runtime routing Evidence: `REQUEST_SENT -> ACK_RECEIVED`; if ACK is absent past the configured threshold, preserve actual `EXECUTOR_UNREACHABLE` audit Evidence.
2. Do not re-run already delivered PR #59 lanes; execute only a remaining lane when its required real input/provenance becomes available.
3. Keep AURA at `VERIFY_REQUIRED` until the real TESTED_PASS package is verified.
4. For every new branch-head commit, require fresh exact-head `tests + cli-smoke + hf-e2e` Evidence before promotion.

## Evidence-first operating rule
- Never report progress without a commit, PR, CI/test result, artifact, or exact verified blocker.
- If meaningful development Evidence is unchanged for two consecutive checks, audit in this order: repository/write permission -> remote branch/PR/commit and possible local-only work -> Actions/CI -> SSOT/handoff reachability -> integration owner/next-action trigger -> remote push/integration path.
- Classify the exact verified cause and execute the smallest safe corrective action immediately when approval is not required.
- Local-only work is `UNVERIFIED` until pushed.
- Do not merge `main`, deploy Production, incur cost, rotate/access secrets, publish externally, or perform destructive changes without explicit user approval.
