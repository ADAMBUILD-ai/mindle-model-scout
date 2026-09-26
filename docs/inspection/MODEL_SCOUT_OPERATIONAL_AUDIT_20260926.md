# MODEL SCOUT operational audit — 2026-09-26

## Verified execution

- Main commit: `d9d86667f213565c1a65be98544fe007088c33e6` (PR #98).
- Autonomous execution: [run 36240490427](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36240490427), execution Evidence artifact ID `10905364220`, live registry artifact ID `10905324285`.
- Execution Evidence: `idle_reason=DISCOVERY_PARTIAL_FAILURE`, `discovery_access.status=DEGRADED_REPOSITORY_ACCESS`, `results=[]`, `eligible_request_count=0`.
- Direct issue discovery returned HTTP 404 for `ADAMBUILD-ai/aura-engine`, `ADAMBUILD-ai/avora-engine`, and `ADAMBUILD-ai/axiom-engine`. This is the runner credential's access result; do not interpret 404 as proof that the repositories or requests do not exist. Other configured repositories were accessible.
- Durable queue snapshot: 20 `FAILED_TERMINAL`, 18 `DELIVERED` historical records. Those callbacks do not demonstrate current product acceptance. This cycle produced zero new acquisitions and zero product `TESTED_PASS` deliveries.
- Live registry: six `ACQUIRED_VERIFIED` models and one `VERIFY_REQUIRED` entry; `validation_status=PENDING` for the acquired models. The registry is runner-local and was uploaded as an artifact; the path itself is not an independently portable binary package.
- Historical binary handoff was independently verified for three ZIPs in PR #95 / run 36238567666. Do not count those existing artifacts as new acquisitions from this run.

## Code fixes applied

PR #98 paginates open Issues rather than stopping silently at the first 100, records incomplete repository discovery as a failure, and includes repository access status in the cycle Evidence and Actions summary. Local test suite: 168 passed; PR #98 test, CLI smoke, and HF E2E workflows passed. This is diagnostic integrity and intake completeness; it does not grant cross-repository access.

## Remaining blockers and next execution

1. **Repository access (operator action).** Grant the existing `MODEL_SCOUT_CROSS_REPO_TOKEN` read access to Issues and repository metadata for the three 404 repositories, or install the existing GitHub App on those three repositories with the same minimal permissions. Verify from the self-hosted runner's credential, without printing the token: issue-list HTTP 200 for each repo and presence of AURA #35/#36 in discovery diagnostics. This access expansion needs explicit owner approval; do not substitute a personal token or claim it is fixed by code.
2. **Real product input.** AURA #35/#36 need image/document fixtures and acceptance criteria. Keep `validation_status=PENDING` until CPU execution on the team's real input, `TESTED_PASS` and independent `DELIVERED` Evidence exist. The prior Florence-2 negative baseline must not be relabeled as success.
3. **Acquisition throughput.** `MODEL_SCOUT_ACQUISITION_CONCURRENCY=3` is present in the workflow but is not read by `run_autonomous_cycle` / `run_runtime_cycle`. The live request path processes up to four eligible requests sequentially. Wire bounded concurrency only after preserving SQLite queue transitions, evidence durability, deduplication, callback ordering, and runner cache isolation; add a timed integration test using distinct request fingerprints.
4. **Truthful health gate.** Current workflow can finish green while discovery is degraded. Use `discovery_access.status` as a separate required operational gate after uploading Evidence, and distinguish permission faults from model failures. Avoid treating a green workflow as product delivery.
5. **Existing backlog.** Triage 20 terminal failures against their original issue and retry history. Do not automatically reset terminal state or count the 18 historical callbacks as current product delivery.

## Closeout criteria

Run the exact main commit after access correction; show HTTP 200 for all required repositories, AURA direct Issue intake, new per-model exact revision, official license, downloaded files and SHA-256, CPU result, durable model ZIP, and product `TESTED_PASS → DELIVERED` on a genuine acceptance fixture. Re-download the ZIP independently and verify hashes. Require all CI checks and record failed or terminal items separately.