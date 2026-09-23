# MODEL SCOUT Throughput Acceleration Inspection

Date: 2026-09-23  
Branch: `improvement/model-scout-throughput-20260923`  
Evidence head inspected: `bc61f46060b7c09e0f460f7a8d3e65bab13eadd8`  
Verdict: **VERIFY_REQUIRED — do not mark PR Ready**

## Passed gates

- Lane A and Lane B are separated in state, execution, and Evidence.
- Three demand-backed, non-core models reached `ACQUIRED_VERIFIED` from real downloaded bytes.
- The live acquisition window reached peak concurrency 3.
- The identical acquisition rerun suppressed all three duplicates and performed zero redownloads.
- A blocked geospatial Lane B request (#55) did not stop unrelated Lane A acquisitions.
- Existing valid request #48 completed the preserved `ACQUIRED_VERIFIED → TESTED_PASS → CALLBACK_SENT → DELIVERED` path again without a duplicate callback.
- Exact implementation head `769fee3fe6e7d834bff400e23ba5bcccd42d7bc8` passed tests, cli-smoke, hf-e2e, and the live acquisition workflow.

## Acquired models

| Model | Exact revision | License | File / bytes | SHA-256 |
|---|---|---|---:|---|
| `openai/whisper-tiny` | `169d4a4341b33bc18d8881c4b69c2e104e1cc0af` | Apache-2.0 | `model.safetensors` / 151,061,672 | `7ebd0e69e78190ffe1438491fa05cc1f5c1aa3a4c4db3bc1723adbb551ea2395` |
| `BAAI/bge-small-en-v1.5` | `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` | MIT | `model.safetensors` / 133,466,304 | `3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad` |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | `233902d25c440f23af6f7d6e94d2946bac0bee0a` | Apache-2.0 | `model.safetensors` / 90,870,598 | `821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae` |

Registry: `evidence/model-registry.json`  
All three entries record source, exact revision, approved license, `trust_remote_code_required=false`, timestamps, cache location, originating requests, consuming teams, size, and SHA-256.

## Parallelism, isolation, and idempotency

- Live acquisition run: `35822286499` — SUCCESS.
- Peak concurrency: 3; overlapping window: 1.687 seconds.
- Durations: BGE 1.687 s, cross-encoder 1.403 s, Whisper 1.581 s.
- Rerun: 3 `DUPLICATE_SUPPRESSED`, 0 duplicate registry rows, 0 redownloads.
- Isolation: Issue #55 remains `VERIFY_REQUIRED` for three real georeferenced fixtures while all three unrelated acquisitions completed.
- Evidence: `evidence/parallel-acquisition-evidence-20260923.json`, `evidence/acquisition-validation-isolation-20260923.json`, and `evidence/throughput-idempotency-20260923.json`.

## Delivery proof

- Request: `ADAMBUILD-ai/mindle-model-scout#48`.
- hf-e2e run: `35822286527` — SUCCESS.
- Runtime evidence artifact: `10733993058`; zip SHA-256 `82283da4dcf41c81738bafb35099b9b45a76d8a17ef17ed93cdee6d587513c56`.
- Input SHA-256: `6d3ad8f580a93cecbbdf329eb04a4c007aebb3e558571b6b2d7b9fb03fcd592d`.
- Output SHA-256: `ba19277f7d6744d01ae3867e7330a39ea46295c31490c892f95c7a1772472104`.
- Callback: https://github.com/ADAMBUILD-ai/avora-engine/issues/7#issuecomment-5749074105
- Ledger transition: `TESTED_PASS → DELIVERED`; callback timestamp 2026-09-23T05:26:22Z.
- Rerun found the same route fingerprint, suppressed the duplicate, and left duplicate count at zero.
- Evidence: `evidence/delivery-lane-closeout-20260923.json`.

## Exact-head CI

For implementation head `769fee3fe6e7d834bff400e23ba5bcccd42d7bc8`:

| Check | Run | Result |
|---|---:|---|
| tests | `35822286495` | SUCCESS |
| cli-smoke | `35822286544` | SUCCESS |
| hf-e2e | `35822286527` | SUCCESS |
| live acquisition | `35822286499` | SUCCESS |

The evidence export commit `bc61f46060b7c09e0f460f7a8d3e65bab13eadd8` was authored by `github-actions[bot]`; GitHub classified its pull-request checks as `action_required`. A final human-authored evidence/report commit must receive fresh exact-head CI before closeout.

## Benchmark boundary

Before: acquisition was serial, coupled to Lane B, schedule-first, and dependency installation repeated each cycle.  
Measured now: three real acquisitions overlapped at peak 3 and completed in a 1.687-second parallel window; the cache/idempotency rerun avoided three downloads. The verified delivery workflow took approximately 102 seconds from runner start to the `DELIVERED` ledger record. No percentage improvement is claimed because an equivalent measured serial baseline is unavailable.

## Unresolved closeout gates

1. **Immediate Issue-event proof cannot be produced safely from this unmerged branch.** GitHub loads `issues` and `repository_dispatch` workflow triggers from the default branch. The default branch still contains only schedule/workflow-dispatch/push triggers. Proving an actual Issue event therefore requires merging or otherwise writing the workflow to `main`, which is expressly outside this directive's authorization boundary.
2. The self-hosted dependency fingerprint cache has structural coverage but lacks a measured cold-bootstrap versus cache-hit duration from the updated workflow on the default branch.
3. Fresh exact-head CI is required after this report/evidence commit.

These are exact blockers, not PASS claims. PR #69 must remain Draft until they are resolved. No production acceptance is inferred from acquisition alone.

## Failed execution and correction history

- First live acquisition run `35821990014` failed before download with `ModuleNotFoundError: No module named 'src'`.
- Root cause: direct script execution placed `scripts/`, not the repository root, on `sys.path`.
- Correction: `769fee3fe6e7d834bff400e23ba5bcccd42d7bc8` makes the runner resolve and insert its repository root.
- Safe rerun `35822286499` succeeded with all three candidates; no candidate substitution was needed.

## Safety confirmation

- No main merge.
- No production deployment.
- No secret exposure.
- No force push.
- No paid action.
- No unreviewed remote code execution.
