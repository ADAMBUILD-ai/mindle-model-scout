# MODEL SCOUT live backlog recovery inspection — 2026-09-26

## Root cause and change
The pre-fix autonomous queue had 20 FAILED_TERMINAL, 14 historical DELIVERED and zero QUEUED/EVIDENCE_READY. Open central and team Issues still existed; broad multi-capability Issues were already exhausted as one fingerprint and therefore produced repeated SUCCESS/zero-result cycles.
PR #86 merged at `8a106206c4e56efdac9ce91b68053e8029f4d22b` and introduced one bounded, source-grounded scoped child of the still-open real KIMSERV #51 memory request. It did not blanket requeue the old terminal rows. Exact-model selection, false component acquisition rejection, durable failure detail and idle reason were added. Local 158 tests passed; PR tests #36225294596, cli-smoke #36225294665 and hf-e2e #36225294816 all SUCCESS.

## Actual post-main autonomous execution
Run #470 `36225436025` used exact merge commit `8a10620` and finished SUCCESS. Evidence artifact `10901110586`, live registry artifact `10901260137`. It recorded one scoped request `7af3bc5bdebc6fbd5244cf4dadadc146b35ddd30282acdaa6f297f02a405f026`: EVIDENCE_READY ACQUIRED_VERIFIED then callback DELIVERED to central KIMSERV Issue #51 comment 5844124013. The queue became FAILED_TERMINAL 20 / DELIVERED 15. This callback is a component handoff only; registry validation stays PENDING and no product TESTED_PASS is claimed.

| Evidence | Verified value |
| --- | --- |
| Model | `intfloat/multilingual-e5-small` |
| Exact Hub revision | `614241f622f53c4eeff9890bdc4f31cfecc418b3` |
| License | MIT metadata and README snapshot (497,538 bytes, SHA-256 `0038de97aee16258cecbad7ffda4b4febd6953e747a00e0ddbc8e6ed241e9c1c`) |
| Actual weight | `model.safetensors`, 470,641,600 bytes, SHA-256 `1a55775f53449dac10a2bcbc312469fac40b96d53198c407081a831f81c98477` |
| Independent official-file comparison | Hugging Face exact-revision HEAD reported X-Linked-Size 470,641,600 and X-Linked-ETag identical to the recorded weight SHA-256 |
| CPU runtime | Windows AMD64 / Python 3.11.9, embedding dimension 384, four sample sentences, ranked scores in Evidence, output SHA-256 `9966ad3a39e2832ca0a199c2c7b552b9399d1596b55e4437f6ce59ad29353c54` |
| Registry | New ACQUIRED_VERIFIED/PENDING entry; the prior pyannote false-positive remains VERIFY_REQUIRED |

## Remaining gates
- The runner-local cache is the current persistence location. Independently downloadable packaged storage and re-download proof are still required for a durable product handoff.
- Product-specific Korean memory retrieval input and acceptance metrics are absent. Do not mark TESTED_PASS or full KIMSERV Issue #51 DELIVERED merely because the scoped callback reached the Issue.
- The other terminal developer requests remain quarantined and need capability-level triage, safe alternatives and bounded execution. Three-to-four concurrent acquisition has not yet been proven on this autonomous path.
