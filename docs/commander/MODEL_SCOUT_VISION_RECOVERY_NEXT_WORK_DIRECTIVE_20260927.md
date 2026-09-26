# MODEL SCOUT next Work directive — 2026-09-27 KST

## Purpose
Continue AURA #35 from its proven component acquisition on main `e5fc8aabd4e29f47c4ce011387ca330745a2c49b` into the separate product-validation lane, without redoing acquisition or promoting a callback state to product acceptance.

## Immediate execution
1. Read the paired inspection and autonomous run #555 artifact. Treat `Salesforce/blip-image-captioning-base@82a37760796d32b1411fe092ab5d4e227313294b` as already `ACQUIRED_VERIFIED`; do not download a moving revision or rerun the recovery markers.
2. Package the exact four verified files with the same-revision model card/license evidence and manifest. Re-download the package independently and compare every SHA-256 before product execution.
3. Run all six real AURA classes: site plan, floor plan, section, elevation, aerial-perspective and proposal page. Capture raw outputs, grounded facts, programme/circulation/mass/level/page hierarchy/cross-view consistency, omissions, contradictions, hallucinations, latency and hardware.
4. Compare against the existing Florence-2 `REJECT_QUALITY` negative baseline. BLIP must earn a reproducible KEEP/SUPPORT_ONLY/REJECT decision; a generic caption, successful process exit or component callback cannot become TESTED_PASS.
5. Only if every required acceptance check passes, persist registry `validation_status=TESTED_PASS`, execute the product callback and record the distinct TESTED_PASS → DELIVERED receipt. Otherwise retain `PENDING` or record the quality rejection with raw Evidence and continue scouting another safe exact-revision candidate.
6. Inspect AURA #36 separately for license/revision compliant alternatives; preserve terminal audit until a concrete compatible candidate and targeted recovery plan exist.
7. Save product run IDs, package artifact ID/digest, independent download receipt, benchmark evidence and registry delta in an updated inspection. Maintain the overall closeout criteria: 3 new unique acquired models, one real product TESTED_PASS → DELIVERED, dedupe and CI PASS.

## Boundaries
No paid GPU/API, new secrets/permissions, destructive reset, force push or blanket terminal requeue. Normal CPU runner and existing backoff only. The development team receives verified Evidence, not a status-only handoff.
