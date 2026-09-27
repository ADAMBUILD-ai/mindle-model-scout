# MODEL SCOUT — AVORA cross-product reuse next work

1. Keep the accepted Blender 4.5.14 LTS renderer and pyrender rejection as AVORA's current decision. Do not restart renderer acquisition absent a new product failure.
2. Resolve central Issue #118 through a dedicated reuse runner, using the exact previously acquired SAM2.1 and SigLIP revisions and package hashes plus ADAM diagnostic tooling. Reuse the package bytes and captured license snapshots; verify each before execution. No arbitrary remote code.
3. Obtain the exact AVORA GLB and V2/V3 render, Blender object-ID/depth masks and, for reference similarity, an owner-approved reference. Verify SHA-256 against the issue before testing. Missing inputs stay BLOCKED_INPUT with no retry exhaustion; do not substitute a synthetic scene or an unrelated image.
4. Run SAM visible-region IoU/latency and SigLIP repeated-render consistency. Run reference similarity only with approved reference. ADAM tools are diagnostic only, never final PBR renderer. Record runtime and input/output hashes, geometry immutability, license and PASS/SUPPORT_ONLY/REJECT per lane.
5. Write immutable Evidence and callback to AVORA Issue #8, then TESTED_PASS and DELIVERED only for a fully verified product lane. Keep AVORA material finish decision independent.
6. Verify tests, cli-smoke and hf-e2e plus post-merge autonomous Evidence and live registry. Report exact run/job/artifact IDs and any remaining blocked inputs.
