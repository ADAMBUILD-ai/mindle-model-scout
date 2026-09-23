# CURRENT EXECUTION CONTROL

Status source: GitHub Evidence only. This file is the executor-facing SSOT for the active MODEL SCOUT gate.

## Integrated baseline on main

- Repository: `ADAMBUILD-ai/mindle-model-scout`
- Verified baseline: `9d342e3bc8d5950b2513cb847a568fedbdd6ddc9`
- PR #62 and PR #64 are completed historical closeout Evidence.
- Cross-repository token, Team Router, ACK, callback, `TESTED_PASS → DELIVERED`, and delivery idempotency are preserved baselines.

## Active P0 gate

- Central Issue: #68
- Work branch: `improvement/model-scout-throughput-20260923`
- Draft PR: #69
- Directive: `docs/commander/MODEL_SCOUT_THROUGHPUT_ACCELERATION_MASTER_DIRECTIVE_v1.0_20260923.md`
- Main merge is not authorized.

The active mission is throughput improvement, not a rebuild.

### Lane A acquisition

`DISCOVERED → LICENSE_OK → REVISION_PINNED → DOWNLOADED → HASH_VERIFIED → ACQUIRED_VERIFIED`

Lane A completes without a consuming team's production fixture when exact revision, approved license, actual bytes, size, SHA-256, safe artifact policy, and durable registry entry are verified.

### Lane B product validation and delivery

`ACQUIRED_VERIFIED → TESTED_PASS → CALLBACK_SENT → DELIVERED`

Lane B requires request-specific real or approved representative input/output, runtime settings, output SHA-256, callback, and idempotent delivery Evidence. A blocked Lane B must not stall unrelated Lane A work.

## Current execution order

1. Preserve existing PASS Evidence and DELIVERED records.
2. Repair registry/state and split acquisition from product validation.
3. Run bounded parallel acquisition with default concurrency 3 and maximum 4.
4. Bind acquisition to the actual selected candidate; do not silently replace it with a fixed executor model.
5. Reject unknown licenses, unpinned revisions, SHA mismatches, and unreviewed remote code.
6. Trigger valid new requests immediately; retain the 15-minute schedule as watchdog/fallback.
7. Reuse unchanged runner dependencies through a requirements fingerprint cache.
8. Accept requests from the configured MINDLE development repository allow-list.
9. Prove at least three new unique `ACQUIRED_VERIFIED` models and one request through `TESTED_PASS → DELIVERED`.
10. Verify duplicate suppression, full tests, cli-smoke, hf-e2e, exact-head CI, and GitHub closeout Evidence.

## Completion authority

Completion requires `docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_CLOSEOUT_20260923.md` plus machine-readable Evidence under `evidence/`. PR #69 remains Draft until every gate passes. When all gates pass, mark Ready for review and stop for commander review. Do not merge main.

## Approval boundaries

Continue without intermediate approval except for paid resources, new login or permission scope, secret creation or rotation, external publication, production deployment, destructive or irreversible changes, force push, or main merge.
