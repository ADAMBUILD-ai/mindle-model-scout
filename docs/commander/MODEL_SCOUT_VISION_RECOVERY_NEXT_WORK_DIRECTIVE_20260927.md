# MODEL SCOUT next Work directive — 2026-09-27 KST

## Purpose
Continue the real AURA #35 request on main after PR #105–#108, using Evidence, without redoing completed work or claiming delivery from a green workflow.

## Immediate execution
1. Read `docs/inspection/MODEL_SCOUT_VISION_RECOVERY_INSPECTION_20260927.md` and the newest autonomous run artifact. Confirm exact main SHA and the one-time recovery marker `aura-35-vision-adapter-v1-20260927` remains used exactly once.
2. At the next ordinary due run inspect AURA #35 state, retry_count, `results`, selected model ID/revision, selection diagnostics, actual files/size/SHA-256, README/LICENSE snapshot, license persistence evidence, CPU output, registry delta and callback. A successful workflow without these items is **NO_NEW_ACQUISITION**.
3. If candidates remain weightless or incompatible, adjust search ranking/preflight to prefer an official, open, executable vision model and try other eligible pinned candidates within normal worker limits. Keep `trust_remote_code=False`. Do not weaken ALLOWED_LICENSES or invent a TESTED_PASS. Add deterministic regression tests for the failure and check tests, cli-smoke, hf-e2e before merge.
4. If acquisition is proven, record ACQUIRED_VERIFIED with exact revision and all file hashes. Run the six AURA architectural input classes separately; only product-specific acceptance may become TESTED_PASS→DELIVERED. Notify the source issue with actual artifact and callback evidence under existing authorized workflow.
5. Inspect AURA #36 separately for license/revision compliant alternatives; preserve terminal audit until a concrete compatible candidate and explicit targeted recovery plan exist.
6. Save new run IDs, artifact IDs, registry before/after and failure reason in an updated inspection document. Maintain the prior closeout criteria: 3 new unique acquired models, one real TESTED_PASS→DELIVERED, dedupe, CI PASS. If unmet, mark VERIFY_REQUIRED and continue permitted fixes.

## Boundaries
No paid GPU/API, new secrets/permissions, destructive reset, force push or blanket terminal requeue. Normal CPU runner and existing backoff only. The development team receives verified Evidence, not a status-only handoff.
