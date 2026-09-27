# MODEL SCOUT misrouted team issues audit — 2026-09-27

## Live evidence

Autonomous run #589 (`36298243602`, main `bc8e5d18b8c1c9b6c3661819aff4573925659839`) completed with Evidence artifact `10925056484`, `results=[]`, `eligible_request_count=0`, `watchdog_requeued=[]`, `idle_reason=NO_ELIGIBLE_REQUESTS`. Registry artifact `10924623027` has unchanged digest `sha256:1863ba1ad5ffb26f4d4724454206f15d381da3ee31c77a5dcb2c2e3ece96996a`. This proves clean idle; it does not prove acquisition throughput.

Of 24 historical FAILED_TERMINAL entries, several are not MODEL SCOUT shopping requests. Verified current open examples:

- `ADAMBUILD-ai/arcos-engine#1`, `kimserv-core#5`, `mindle-media-ai#2`: `[MODEL SCOUT ROUTE]` team input requests that point to central issues. These collect real product data, not new acquisition work.
- `ADAMBUILD-ai/aura-engine#29`, `avora-engine#9`: `Direct model acquisition execution STEP 0` issues operated independently of MODEL SCOUT.
- `ADAMBUILD-ai/aura-engine#28`: direct official acquisition track that explicitly runs in parallel with MODEL SCOUT, not an autonomous scout queue item.

## Change

The issue classifier excludes only the explicit `[MODEL SCOUT ROUTE]` title and `Direct [Official] Model Acquisition` title patterns. On a fresh live fetch, already queued or terminal records for these exact source Issues move to `MISROUTED`. Their previous state/error are written to a durable `misrouted_requests` audit table, retry counts remain intact, and actual completed delivery/in-flight/ready evidence are untouched. Other central genuine requests remain in scope.

## Verification and limits

43 focused local tests PASS including route/direct classification, durable audit and idempotent live quarantine. Exact-head CI plus post-merge Evidence must prove expected quarantined fingerprints; no historical failure is automatically reopened. Real AURA #36 and AGRI #33 are still separate requests requiring candidate/runner investigation. AVORA #118 remains blocked by unavailable product inputs and a dedicated reuse adapter.

Source: [run #589](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36298243602).
