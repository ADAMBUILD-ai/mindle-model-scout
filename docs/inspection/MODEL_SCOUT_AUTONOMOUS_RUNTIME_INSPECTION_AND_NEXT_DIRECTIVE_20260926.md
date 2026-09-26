# MODEL SCOUT autonomous execution inspection and next action — 2026-09-26 08:55 KST

## Verified runtime evidence
- Current main head `0f1c9c9f40d6b8596c986035ed7725fda36179f7` contains PR #84 merge `32bd31346ce137b276a2c9f8a4df47229cfb7b85`.
- Run #467 (`36201919028`, 08:40 KST) completed SUCCESS on that head. Downloaded evidence artifact `10891669702` and live registry artifact `10892620214`.
- The cycle has `results: []`, `watchdog_requeued: []`, queue `DELIVERED: 14`, `FAILED_TERMINAL: 20`. No newly completed request, acquisition or delivery in this run.
- Central #68 has two terminal queue records with retry_count 66 and 46. Central #82 is FAILED_TERMINAL with retry_count 3 and has no Issue comments. Run #468 (`36202868386`, 08:55 KST) subsequently completed SUCCESS. Its live registry artifact `10892319023` has the same digest `sha256:1777bf1d3b094607506bd5d85d80077de34d642cfcfabd4af905a17b3e7066e6` as #467, so it added no registry entry. Its execution Evidence artifact `10892378765` was downloaded: `results: []`, `watchdog_requeued: []`, queue `FAILED_TERMINAL: 20`, `DELIVERED: 14`. Thus #468 also made no new model progress.
- Live registry contains four ACQUIRED_VERIFIED records with validation_status PENDING: BAAI/bge-m3, nickmuchi/deberta-v3-base-finetuned-finance-text-classification, pyannote/wespeaker-voxceleb-resnet34-LM, sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2. These pre-existing records are not four new acquisitions from #467.
- The pyannote entry claims revision `4.12.2` and its only 'downloaded file' is installed `trimesh/__init__.py` (2,433 bytes), not a pyannote model weight. Its ACQUIRED_VERIFIED assertion is therefore unsupported by this artifact.
- The runtime executor in `src/model_scout/runtime_executors.py` accepts reported `model_id`, `revision`, `source`, `license` and `_downloaded_files` from the executor output, hashes any existing reported file, then writes ACQUIRED_VERIFIED without checking that the file belongs to the selected model/revision. This explains the pyannote false-positive risk.
- AURA binary handoff package verification is documented separately in `docs/inspection/MODEL_SCOUT_AURA_HANDOFF_POST_MAIN_REVIEW_20260926.md`. Package integrity is not product TESTED_PASS or DELIVERED.

## Immediate corrective directive
1. Guard acquisition registration: selected model ID, immutable 40-character Hub revision, source and license must agree with official pinned metadata; a runner output must not override identity. Require at least one actual model weight/binary inside the pinned snapshot; reject unrelated Python/site-packages files, symlink escapes and empty or metadata-only downloads. Persist source license snapshot and hash. If proof is missing, leave acquisition VERIFY_REQUIRED/FAILED_RETRYABLE, never ACQUIRED_VERIFIED.
2. Add a regression fixture matching the pyannote/trimesh false positive and a valid MiniLM pinned snapshot. Test spoofed model ID/revision/license and path escape. Run tests, cli-smoke, hf-e2e and inspect new runtime evidence on the merged head.
3. Reconcile the existing pyannote registry record with source evidence. Do not delete evidence; mark its acquisition VERIFY_REQUIRED until the actual pinned model bytes and license are independently verified.
4. Distinguish administrative execution issues (#68, #82) from executable model requests. Terminal queue items require cause-specific triage; do not silently report SUCCESS for zero-result cycles as model-scouter productivity.
5. Complete AURA Issue #82 transfer, independent Drive re-download/hash, real Gochang input inference and product callback before TESTED_PASS → DELIVERED. No paid resources, arbitrary remote code, permission expansion or destructive operation.

Decision: scheduler operational; acquisition/registry integrity and real-request throughput need correction. No new acquisition or delivery proven by run #467.

## Correction and post-merge operational verification — 2026-09-26 15:42 KST

- PR #85 merged to main as `e7fd98b234dae4c58819f92ce845077a14fe521c`.
- Runtime registration now requires selected exact 40-hex revision, nonempty model weight and card within that model's pinned Hub snapshot; component fallback cannot register ACQUIRED_VERIFIED. Legacy unsupported rows are demoted with Evidence retained.
- Local full suite: 155 passed. PR checks: tests #36223856929, hf-e2e #36223856932, cli-smoke #36223856928 all SUCCESS. Post-main tests #36223992581 SUCCESS.
- Autonomous run #469 (`36224458749`) used exact merge commit `e7fd98b` and completed SUCCESS. Downloaded Evidence artifact `10900376153` and live registry artifact `10900196508`.
- In the actual uploaded registry, `pyannote/wespeaker-voxceleb-resnet34-LM` changed from ACQUIRED_VERIFIED to VERIFY_REQUIRED with reason `missing pinned model bytes or model-card evidence`. The other three legacy entries remain ACQUIRED_VERIFIED/PENDING. No prior Evidence was deleted.
- The same cycle still has `results: []`, `watchdog_requeued: []`, queue FAILED_TERMINAL 20 / DELIVERED 14. New acquisitions 0, new TESTED_PASS 0, new DELIVERED 0. This fix closes the **false acquisition classification**, not the **zero-throughput** issue.

Decision: acquisition classification fix DEPLOYED_AND_RUNTIME_VERIFIED; new-request throughput and AURA product delivery remain OPEN.
