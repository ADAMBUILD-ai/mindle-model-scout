# CURRENT EXECUTION CONTROL

Status source: actual GitHub runs, uploaded artifacts and the live registry. This is the executor-facing current gate; historical directives and PR #69 are not current merge blockers.

## Verified code baseline — 2026-09-26

- Repository: `ADAMBUILD-ai/mindle-model-scout`.
- Verified binary handoff code baseline: `3977a1d7ebf047a668b49365a6ba79284733d46e` (PR #95). Its exact-head run proof remains valid.
- Newer main `40cede7fd76b09cef4ad56c408a56677d63af4cf` (PR #96) adds discovery diagnostics; inspect a post-merge autonomous run before asserting that change works in service.
- Earlier recovery PRs #86–#92, inspection #93, binary handoff #95 and discovery diagnostics #96 are merged. The user authorized main merges; no obsolete “merge forbidden” instruction applies.
- Cross-repository intake, Team Router, bounded retries, durable queue, source-grounded scoped requests, exact-model selection, license/revision/bytes/SHA gates, CPU component validation and runner cache remain in service.

## Live Evidence and state

- Autonomous [run #36228054744](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36228054744): the third newly acquired distinct model, `openai/whisper-tiny`, completed its component path. The later [run #36237993543](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36237993543) reported `NO_ELIGIBLE_REQUESTS`, zero new results, no duplicate processing; queue 18 scoped/historical callbacks `DELIVERED` and 20 old `FAILED_TERMINAL` quarantined.
- Newly acquired distinct models: `intfloat/multilingual-e5-small` (KIMSERV; AXIOM reuses the same bytes), `sentence-transformers/distiluse-base-multilingual-cased-v2` (NAS), `openai/whisper-tiny` (MEDIA). Exact revisions, license snapshots, original weight hashes and CPU component output are in `docs/inspection/MODEL_SCOUT_MULTITEAM_RECOVERY_INSPECTION_20260926.md` and the linked run artifacts.
- [Binary handoff run #36238567666](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36238567666) at exact main `3977a1d` passed all three self-hosted packaging jobs and independent GitHub artifact re-download/file-hash checks. Model ZIP IDs: e5-small `10905172342`, NAS distiluse `10905636127`, MEDIA Whisper `10904947669`. Independent receipt IDs: `10905660548`, `10905357314`, `10904867910`. Full SHA/size and 30-day retention are in `docs/inspection/MODEL_SCOUT_BINARY_HANDOFF_CLOSEOUT_20260926.md`.
- The live registry has six `ACQUIRED_VERIFIED` and one `VERIFY_REQUIRED` (old pyannote false positive). **All seven registry validation statuses are `PENDING`**. Component callbacks do not establish full parent product `DELIVERED`.

## Lane A — acquisition and artifact preservation

`DISCOVERED → LICENSE_OK → REVISION_PINNED → DOWNLOADED → SHA256_VERIFIED → ACQUIRED_VERIFIED → BINARY_PACKAGE_VERIFIED`

Do not label a candidate acquired without actual pinned Hub model bytes and model-card/license evidence. The ZIP job rechecks cache bytes, uploads an exact snapshot, and independently downloads and hashes the artifact. GitHub package retention is 30 days; long-term private storage and restore proof remain open. Never execute unreviewed remote code.

## Lane B — product validation and final delivery

`ACQUIRED_VERIFIED → real team input/output and measured acceptance → TESTED_PASS → product callback → DELIVERED`

Obtain actual team fixtures and acceptance thresholds. In particular, MEDIA's synthetic 440 Hz audio yielded repetitive hallucinated text; it only proves the CPU path executes. Do not promote it to Korean STT quality PASS. KIMSERV, NAS, AXIOM, MEDIA parent requests remain product-validation pending.

## Next executable work and honest blockers

1. Preserve all existing acquired model rows and binary artifacts; never blanket reset 20 terminal fingerprints. Triage the real unresolved capability in each open parent/team Issue into a bounded, source-grounded request, one at a time.
2. Prove 3–4 concurrent **new acquisition** on the autonomous CPU path; the successful 3-job binary packaging matrix is a separate handoff step and not acquisition throughput proof.
3. Attach real product fixtures and output metrics, advance at least one request through genuine `TESTED_PASS → DELIVERED` with idempotent receipt. Where fixtures are unavailable, record `BLOCKED_INPUT` and continue another executable request.
4. Preserve exact acquired-version license/card evidence and get the rights-persistence condition reviewed before commercial release. Preserve an independently restored private long-term model archive; expiring GitHub artifacts are not permanent storage.
5. Keep tests, cli-smoke, hf-e2e and exact-main run Evidence green; classify internal failed requests in the Actions summary and do not treat a green workflow alone as model PASS.

## Approval boundaries

Continue routine reversible code, tests, PR and authorized main merge. Pause for a new paid service, expanded permissions, secret rotation, destructive deletion, force push, or unapproved production/public release. No approval is inferred for a commercial model release from a component smoke or ZIP.
