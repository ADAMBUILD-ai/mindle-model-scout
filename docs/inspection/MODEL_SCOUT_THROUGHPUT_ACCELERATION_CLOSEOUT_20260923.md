# MODEL SCOUT Throughput Acceleration Inspection

Date: 2026-09-23  
Branch: `improvement/model-scout-throughput-20260923`  
Synchronization source HEAD: `c1cb79b61ebab3a540d12a7caa2ce8874bc76d2e`
Final synchronization HEAD and fresh CI: recorded on PR #69 after this report commit
Verdict: **PRE_MERGE_GATES_PASS / DEFAULT_BRANCH_ACTIVATION_REQUIRED**

## Passed gates

- Lane A and Lane B are separated in state, execution, and Evidence.
- Three demand-backed, non-core models reached `ACQUIRED_VERIFIED` from real downloaded bytes.
- The live acquisition window reached peak concurrency 3.
- The identical acquisition rerun suppressed all three duplicates and performed zero redownloads.
- A blocked geospatial Lane B request (#55) did not stop unrelated Lane A acquisitions.
- Existing valid request #48 completed the preserved `ACQUIRED_VERIFIED → TESTED_PASS → CALLBACK_SENT → DELIVERED` path again without a duplicate callback.
- Exact pre-synchronization implementation head `22451bf5f4e08738b7c339f00d4a45429b39e7e9` passed tests, cli-smoke, and hf-e2e. The final synchronization commit receives a separate fresh exact-head run recorded on PR #69.

## Acquired models

| Model | Exact revision | License | File / bytes | SHA-256 |
|---|---|---|---:|---|
| `openai/whisper-tiny` | `169d4a4341b33bc18d8881c4b69c2e104e1cc0af` | Apache-2.0 | `model.safetensors` / 151,061,672 | `7ebd0e69e78190ffe1438491fa05cc1f5c1aa3a4c4db3bc1723adbb551ea2395` |
| `BAAI/bge-small-en-v1.5` | `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` | MIT | `model.safetensors` / 133,466,304 | `3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad` |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | `233902d25c440f23af6f7d6e94d2946bac0bee0a` | Apache-2.0 | `model.safetensors` / 90,870,598 | `821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae` |

Registry: `evidence/model-registry.json`  
All three entries record source, exact revision, approved license, `trust_remote_code_required=false`, timestamps, cache location, originating requests, consuming teams, size, and SHA-256.

## Parallelism, isolation, and idempotency

- Latest live acquisition run: `35823260028` — SUCCESS.
- Peak concurrency: 3; overlapping window: 4.21 seconds.
- Durations: BGE 1.151 s, cross-encoder 1.493 s, Whisper 4.21 s.
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

## Exact-head CV

For pre-synchronization implementation head `22451bf5f4e08738b7c339f00d4a45429b39e7e9`:

| Check | Run | Result |
|---|---:|---|
| tests | `35823504489` | SUCCESS |
| cli-smoke | `35823504502` | SUCCESS |
| hf-e2e | `35823504495` | SUCCESS |
| latest live acquisition | `35823260028` | SUCCESS |

Fresh tests, cli-smoke, and hf-e2e for the human-authored synchronization commit are mandatory before Ready-for-review transition. Their exact HEAD and run IDs are recorded in the PR body and closeout comment because a Git commit cannot embed its own content-derived SHA.

## Benchmark boundary

Before: acquisition was serial, coupled to Lane B, schedule-first, and dependency installation repeated each cycle.  
Measured now: three real acquisitions overlapped at peak 3 and completed in a 4.21-second parallel window; the cache/idempotency rerun avoided three downloads. The verified delivery workflow took approximately 102 seconds from runner start to the `DELIVERED` ledger record. No percentage improvement is claimed because an equivalent measured serial baseline is unavailable.

## Pre-merge PASS

- Acquisition architecture and Lane A/Lane B separation.
- Three new `ACQUIRED_VERIFIED` models with exact revisions, licenses, sizes, and SHA-256.
- Real peak concurrency 3 and verified redownload suppression.
- Blocked Lane B isolation.
- Request-specific delivery and callback idempotency.
- Exact-head tests, cli-smoke, and hf-e2e, subject to the final synchronization run recorded on PR #69.

## Post-merge required

1. **Immediate Issue-event proof cannot be produced safely from this unmerged branch.** GitHub loads `issues` and `repository_dispatch` workflow triggers from the default branch. The default branch still contains only schedule/workflow-dispatch/push triggers. Proving an actual Issue event therefore requires merging or otherwise writing the workflow to `main`, which is expressly outside this directive's authorization boundary.
2. The self-hosted dependency fingerprint cache has structural coverage but lacks a measured cold-bootstrap versus cache-hit duration from the updated workflow on the default branch.
These are explicit default-branch activation gates, not pre-merge defects. After fresh synchronization-head CI succeeds, PR #69 may be marked Ready for review but must not be merged without commander approval. No production acceptance is inferred from acquisition alone.

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
