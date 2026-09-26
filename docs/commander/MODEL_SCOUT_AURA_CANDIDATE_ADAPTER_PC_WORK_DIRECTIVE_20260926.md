# PC WORK EXECUTION DIRECTIVE — MODEL SCOUT AURA candidate adapters (2026-09-26)

**Repository:** `ADAMBUILD-ai/mindle-model-scout`. **Base:** latest main at or after `9b2030fa8625f289cb31edd410590b09e48cdb57`. **Source evidence:** autonomous run [#532](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36243562533), Evidence artifact `10906294305`, registry `10906893061`. This directive continues the exact failure inspection in `docs/inspection/MODEL_SCOUT_AURA_RETRY_INSPECTION_20260926.md`.

## Already completed; do not repeat

Cross-repo Issue access is HTTP 200 for ADAM, ADRAW, AURA, AVORA, AXIOM and the remaining required teams. AURA #35/#36 normalize and reach search. PR #101 removed form-path and Owner/NER misclassification; PR #102 rejects visibly unrelated image-generation models; PR #103 enables a deliberate manual zero-backoff recovery. Local full suite 174 pass at #102; CI tests, CLI smoke and HF E2E passed on #101–#103. The six pre-existing acquired registry rows and three historical ZIP handoffs are not new acquisitions.

## PC work sequence

1. On a new branch, add candidate-aware visual understanding CPU execution for AURA #35, with `trust_remote_code=False`, immutable Hub revision, same-revision card/license, actual files and SHA-256. Do not route a non-TrOCR model to `TrOCRProcessor`. Verify config/processor compatibility before large downloads and skip incompatible candidates with per-candidate failure evidence. Keep product acceptance PENDING until all six real fixture classes pass AURA's criteria.
2. For AURA #36, investigate alternative officially distributed control/edit models with a clearly allowed license and preserved acquired-version rights. The four model candidates in run #532 were all `license:other`; do not download or waive this gate. Use the genuine P04 v56.1 protected-region benchmark before any product PASS.
3. Preserve durable queue state. #35 and #36 are `FAILED_RETRYABLE` at retry_count 2/3; do not issue another zero-backoff run until code and candidate changes are ready. Use a bounded test with fixture input and explicit failure diagnostics first.
4. Wire real 3–4 acquisition concurrency only after isolating SQLite claims, evidence writes and callback delivery. Repair the Windows Actions cache tar path warning and verify a restore/save hit.
5. Open PR with changes, tests and actual Evidence. After CI 3/3 PASS and approved merge policy, run exact main and inspect artifacts. Keep counts for newly ACQUIRED_VERIFIED, TESTED_PASS and DELIVERED separate; re-download binary ZIP and check hashes independently.

## Closeout gate

No PASS from a green Action alone. Require a documented model ID, exact revision, original license and perpetual acquired-version use basis, real downloaded weights, per-file SHA-256, reproducible CPU output, product acceptance evidence and independent delivery. Record `VERIFY_REQUIRED` or rejection if any gate remains unresolved. No GPU, paid compute, remote code, new repository rights or destructive queue reset without explicit approval.
