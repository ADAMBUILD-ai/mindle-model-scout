# MODEL SCOUT verified postmortem — 2026-09-16

## Executive finding
The unattended trigger/runner/queue persistence work succeeded, but the project was closed against the wrong completion target. The production-adjacent live cycle does **not** execute generic download/runtime TESTED_PASS work, and the newly created central team request Issues #47-#58 are not present in the durable queue snapshot from run 35088886275.

## Verified evidence
1. `.github/workflows/autonomous-model-scout.yml` only invokes `scripts/run_autonomous_cycle.py` with `MODEL_SCOUT_CONFIGURED_REPOS`.
2. `src/model_scout/live_automation.py` explicitly states that the live cycle intentionally does **not** perform runtime TESTED_PASS execution; it only ingests/scouts/callbacks and advances its delivery ledger to FOUND.
3. `src/model_scout/runtime_validation.py` contains a valid TESTED_PASS validator, but it is not wired into `run_live_cycle`.
4. `scripts/run_fast_delivery.py` is a one-off hard-coded AGRI path for `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, not a generic worker for arbitrary queued requests.
5. Run `35088886275` completed SUCCESS, but its artifact queue contains only four old requests from `ADAMBUILD-ai/adam-build` and `ADAMBUILD-ai/agri-ai-business-platform`; `results=[]`; Issues #47-#58 are absent.
6. Issues #47 and #50 remain open with zero comments, corroborating that the central team requests were not ingested/callbacked.
7. Issue #36 itself remains OPEN and its original acceptance requires request ingestion + dispatcher + TESTED_PASS runner + callback evidence.

## Root causes
### RC-1 — Completion criteria drift
We treated recurring workflow SUCCESS, durable state, and watchdog scheduling as if they proved the requested business lifecycle. They prove orchestration availability only.

### RC-2 — Intake source mismatch
Issue discovery is restricted to `MODEL_SCOUT_CONFIGURED_REPOS`. The central request Issues #47-#58 were created in `ADAMBUILD-ai/mindle-model-scout`, but the current durable queue evidence does not contain them. Either the central repo is not configured for discovery or those issues are not being passed to discovery. This must be verified and corrected before closeout.

### RC-3 — Runtime executor not integrated
`run_live_cycle()` stops after scout/callback evidence and explicitly excludes runtime TESTED_PASS. `runtime_validation.py` exists as an isolated component, but no generic runner connects candidate selection -> immutable download -> local runtime -> output/hash evidence -> TESTED_PASS -> delivery.

### RC-4 — One-off success was generalized incorrectly
The fast delivery path demonstrated one real model lifecycle for AGRI, but it is hard-coded to one model/request. That proof cannot establish that arbitrary ADAM/AVORA/ADRAW/MEDIA/KIMSEOBANG/NAS/etc requests are executable.

### RC-5 — Scheduler debugging consumed effort after the business-path gap was already documented
Issue #36 already described the request-ingestion and TESTED_PASS worker gaps. We spent excessive time on cron/service/watchdog gates while the generic worker gap remained unresolved.

## Corrective implementation order
P0-A. Make Issues #47-#58 discoverable now: include `ADAMBUILD-ai/mindle-model-scout` in the configured discovery source or directly ingest the central issues into the durable queue. Verify queue snapshot contains their fingerprints.

P0-B. Add a generic execution worker after candidate selection. For each queued request, it must select a candidate, pin revision/commit, download safely, run a request-specific local smoke/validation adapter, generate output file + SHA-256 + runtime/hardware/settings/license evidence, then call the TESTED_PASS validator.

P0-C. Wire `runtime_validation.run_runtime_validation` into the autonomous orchestration. Safe/free/local/non-destructive work auto-runs. Login/cost/permission/secret/production/external publication/destructive requirements become `BLOCKED_APPROVAL` only.

P0-D. Replace the hard-coded AGRI fast-delivery script as evidence for generic autonomy with adapter-based executors (embedding, OCR, image segmentation/edit, STT, geometry/tool CLI, etc.).

P0-E. End-to-end acceptance must use at least three heterogeneous real requests from the new team set, including one model download/inference request and one program/tool request. Required lifecycle: `REQUESTED -> FOUND -> DOWNLOADED -> TESTED_PASS -> DELIVERED`, with callback to the originating issue.

## Closeout rule
Do not declare FINAL CLOSEOUT from workflow SUCCESS, queue idle, artifact upload, watchdog success, or a single hard-coded model delivery. Close only when the generic path consumes actual #47-#58 requests and produces verified output/hash/runtime/license/callback evidence.
