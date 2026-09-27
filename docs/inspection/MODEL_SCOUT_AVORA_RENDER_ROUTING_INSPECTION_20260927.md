# MODEL SCOUT AVORA render routing inspection — 2026-09-27 KST

## Observed production failure

Main `9edbd3bfb5d00c4b50336b72d9e5ccb45e5c8024`, autonomous run [#576](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36292204684) Evidence artifact `10922457952`: genuine central AVORA Issue #115 was normalized with product/team/capability `UNKNOWN`, resource `model` and callback to the central issue. Its body mentioned an older OCR model as negative context, and the generic Hub search returned no runnable candidate. State: `FAILED_RETRYABLE` retry_count 0. Run [#577](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36292808895) on the same main processed zero requests; the failure persisted. Live registry remained seven ACQUIRED_VERIFIED/PENDING plus one VERIFY_REQUIRED/PENDING. No AVORA render acquisition, real GLB test, TESTED_PASS or product delivery occurred.

## Code correction

The request parser now treats titled mapping/render/PBR program requests as `tool`, derives AVORA product/team and `GLB_PBR_MAPPING_RENDER` when the form is absent, and the executor routes by primary capability before historical OCR text. Tool requests no longer widen to HF `all`. Dedicated discovery reads only a fixed pyrender/trimesh/open3d allowlist from official PyPI JSON and exposes exact release version and distribution SHA-256. PyPI self-reported license classifiers remain `LICENSE_REVIEW_REQUIRED`; no wheel is executed or recorded as ACQUIRED_VERIFIED solely from metadata. The runtime reports that an exact fixture and verified program package/runtime are required.

Focused tests: 61 passed locally. CI and actual post-merge run remain to be recorded on the PR.

## Unfinished gate

Issue #115 requests an exact `AVORA-final-pre-render-candidate-v2.glb` SHA-256 `a9d40b35953b4d0d3e3c7ffcc19850f067945a45647f5ebf8c3cf490f6f4a171`. The request supplies a filename and hash, not a downloadable fixture. Do not fabricate that GLB or grant product PASS. A second implementation must acquire and license-audit exact program distributions, execute at least two eligible candidates on the independently hashed fixture, render site ground, verify geometry/glass and preserve reproducible output. Retain the existing failed row for audit; a corrected request identity will be independently queued.
