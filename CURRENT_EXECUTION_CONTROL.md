# CURRENT EXECUTION CONTROL

Status source: GitHub Evidence only. This file is the executor-facing SSOT for the current MODEL SCOUT gate.

## Integrated baseline on `main`
- Repository: `ADAMBUILD-ai/mindle-model-scout`
- Default branch: `main`
- Current verified main: `7040dd9b7e2e8ffea8e0a6d147904f18dfb8c014`
- No PR #59 recovery work is claimed merged to main.

## Active recovery gate — PR #59
Authoritative source:
- PR #59: `Recovery: connect durable ingestion to runtime execution`
- Branch: `recovery/runtime-execution-core-20260916`
- Pre-refresh verified head: `6c0bcc3e18e1327f5e244c477f8c63c2309771a7`
- State at audit: OPEN / DRAFT / mergeable / unmerged.

### Verified validation on pre-refresh head
- Local offline suite: 113 passed.
- GitHub Actions: tests SUCCESS, cli-smoke SUCCESS, hf-e2e SUCCESS.
- Local live-only suite: 3 blocked by sandbox outbound-network policy; this is not promoted to PASS.

### Verified delivered lifecycle Evidence
The following request lanes have durable lifecycle Evidence recorded by PR #59 and MUST NOT be listed as future work:
- #47 DELIVERED
- #48 AVORA: actual project test-kit PDFs supplied 8 pages; 3 real pages passed PDF rendering, mask/vector output, OCR confidence, wall/door/window relation JSON, baseline comparison, deterministic rerun; FOUND -> DOWNLOADED -> TESTED_PASS -> callback -> DELIVERED; idempotent rerun results=[]
- #49 DELIVERED
- #52 DELIVERED
- #53 DELIVERED
- #54 DELIVERED
- #56 DELIVERED

Generated/component smoke results are not request-complete TESTED_PASS.

### Exact remaining blockers
- #50: no real project video or Korean speech sample; no local audio/video files found.
- #51: no actual Korean STT/TTS sample or avatar video.
- #55: no three actual GeoTIFF/satellite/parcel-map samples with georeference.
- #57: no actual filing/IR document with source/timestamp/page/table provenance available to local runtime; outbound CLI download blocked.
- #58: no actual field image/Korean label sample and training-data provenance Evidence.

### Current next-action trigger
1. Do not repeat already-delivered #47/#48/#49/#52/#53/#54/#56 work.
2. For #50/#51/#55/#57/#58, execute only when the required real input/provenance becomes reachable; preserve FAILED_RETRYABLE/VERIFY_REQUIRED boundaries until then.
3. Continue safe/free/public scouting and local verification where it can produce new Evidence without inventing production samples.
4. Keep PR #59 Draft/unmerged while exact blockers remain. Do not merge main without explicit user approval.
5. Keep AURA Issue #32 active in parallel; no AURA TESTED_PASS claim without the real delivery package.

## Parallel gate — AURA TESTED_PASS delivery
Authoritative sources:
- Issue #32: `AURA P0 — Approved Model Shopping / Deliver TESTED_PASS Assets`
- PR #31: `feat: add AURA execution order for MODEL SCOUT handoff`
- Branch: `feat/aura-execution-order-20260913`

Verified boundary:
- No `AURA_MODEL_SCOUT_DELIVERY_20260913` package with real inference output/log/settings/runtime/hash has been verified.
- Scout results, downloads, model-card checks, or CI alone are not TESTED_PASS.
- TESTED_PASS requires real input/output + model ID/revision/license/source + settings + runtime/HW/VRAM + log + file SHA-256.

## Evidence-first operating rule
- Never report progress without a commit, PR, CI/test result, artifact, or exact verified blocker.
- If meaningful development Evidence is unchanged for two consecutive checks, audit in this order: repository/write permission -> remote branch/PR/commit and possible local-only work -> Actions/CI -> SSOT/handoff reachability -> integration owner/next-action trigger -> remote push/integration path.
- Classify the exact verified cause and execute the smallest safe corrective action immediately when approval is not required.
- Local-only work is UNVERIFIED until pushed.
- Do not merge main, deploy Production, incur cost, rotate/access secrets, publish externally, or perform destructive changes without explicit user approval.
