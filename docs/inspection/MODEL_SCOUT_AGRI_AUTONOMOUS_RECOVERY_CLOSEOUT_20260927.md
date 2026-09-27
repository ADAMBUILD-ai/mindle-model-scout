# AGRI autonomous recovery evidence and scoped queue cleanup — 2026-09-27

## Verified autonomous execution

[Run #598](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36300831867) executed main `a79af76602cb89fbc385e64527a05e1a9653308a` and uploaded [Evidence artifact 10926000773](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36300831867/artifacts/10926000773) and [live registry artifact 10925352618](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36300831867/artifacts/10925352618). Source intake access PASS. The Scout itself selected `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` at exact revision `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, Apache-2.0. The actual `model.safetensors` file was 470641600 bytes, SHA-256 `eaa086f0ffee582aeb45b36e34cdd1fe2d6de2bef61f8a559a1bbc9bd955917b`. README/model-card snapshot SHA-256 `1e98ea05b0de579fcaad3d625b62ea55647142ed674d5f5ebf1440e4bbbb6f23`; config and tokenizer hashes are in the artifact. Windows CPU embedding ran with return code 0, 384 dimensions, latency 0.690 seconds, and output SHA-256 `18247cf4c36994f24f311fd750d3b77e6fcc3c34c17ec2eb056dfdf9b5275337`.

AGRI #33 callback [comment 5853494838](https://github.com/ADAMBUILD-ai/mindle-model-scout/issues/33#issuecomment-5853494838) was posted and the queue's final state is `ACQUIRED_VERIFIED`. This model was already present in the registry for Issue #71; run #598 independently checked pinned files and CPU inference and added AGRI #33 as a consumer. The number of unique registry models remains 9; this is one new verified AGRI acquisition request, not one new unique model. Product validation remains `PENDING`; no AGRI real-input TESTED_PASS or product DELIVERED is asserted.

The older BAAI English-only acquisition remains binary-verified but AGRI suitability is `REJECT_QUALITY`, preserving its file proof. No license gate or remote-code gate was relaxed. Oversized multilingual-e5 variants were rejected by the 650 MB bound before download.

## Remaining operational defect and fix

The #598 snapshot still contained prior AGRI scoped search versions in `QUEUED` / `FAILED_RETRYABLE` even though the replacement had succeeded. They can waste retries. Reconcile only older queued/retryable scoped revisions matching the same source Issue, resource, capability and requested model ID into audited `SUPERSEDED`. Keep acquired evidence and other roles unchanged. Run the reconciliation before watchdog retries. This patch has focused local tests; the subsequent CI and autonomous run must confirm the audited cleanup.

Historical terminal and blocked requests remain intact. AURA/other product E2E needs corresponding real product inputs, fixtures and acceptance gates; component acquisition is not product delivery.
