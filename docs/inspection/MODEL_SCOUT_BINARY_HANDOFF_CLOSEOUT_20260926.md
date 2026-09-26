# MODEL SCOUT binary handoff inspection — 2026-09-26

## Actual execution
PR [#95](https://github.com/ADAMBUILD-ai/mindle-model-scout/pull/95) merged as `3977a1d7ebf047a668b49365a6ba79284733d46e`. Local suite 164 PASS and the PR tests, cli-smoke and hf-e2e workflows each passed. The [exact-main binary handoff run #36238567666](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36238567666) completed SUCCESS with all three self-hosted Windows jobs successful. Each job rechecked its live registry row and actual cached bytes, created an exact-revision ZIP with a manifest, uploaded it, downloaded the GitHub artifact again, and verified the ZIP SHA-256 and every member's size/SHA-256. No model remote code was executed by the packager.

| Model / consumer | Exact revision, license | Binary artifact ID | ZIP bytes and SHA-256 | Independent receipt artifact ID; member count |
| --- | --- | ---: | --- | --- |
| `intfloat/multilingual-e5-small` / KIMSERV and AXIOM | `614241f622f53c4eeff9890bdc4f31cfecc418b3`, MIT | `10905172342` | 493,294,817; `4fc6640b06ae33ea5ed41c456d6ed256ba50fe8c5ff161c0cd9d00458759517f` | `10905660548`; 7 |
| `sentence-transformers/distiluse-base-multilingual-cased-v2` / NAS | `bfe45d0732ca50787611c0fe107ba278c7f3f889`, Apache-2.0 | `10905636127` | 541,911,157; `8bb03b4f633e02e92461960abe02bdfa8a60e91b4c2be612e49125570361729d` | `10905357314`; 7 |
| `openai/whisper-tiny` / MEDIA | `169d4a4341b33bc18d8881c4b69c2e104e1cc0af`, Apache-2.0 | `10904947669` | 155,458,247; `de0258f8ef61515c8ad3f15195cfedf856dceda657a4ef4ebb7056793a5de4ef` | `10904867910`; 12 |

The six artifacts are associated with the exact run and commit above. The ZIPs include the pinned cached model snapshot, exact-revision README/model-card and `MODEL_HANDOFF_MANIFEST.json`. The receipt status for each is `INDEPENDENT_DOWNLOAD_VERIFIED`; its `product_validation_status` is `PENDING`. GitHub Actions retention is 30 days. These are real downloadable binaries, not paths to a private runner cache or a status-only callback.

## Remaining gates, without promotion
- `ACQUIRED_VERIFIED` and independent binary download have been proven for these three distinct models. KIMSERV/AXIOM reuse one identical e5-small snapshot. The old 20 broad/administrative `FAILED_TERMINAL` requests remain quarantined; latest autonomous cycles report zero eligible and no duplicate execution.
- Product teams must run their real acceptance inputs, record output SHA-256 and metrics, then explicitly mark `TESTED_PASS` and complete the product callback/delivery. The MEDIA synthetic sine wave produced repeated hallucinated Korean text; it is a CPU component smoke, not Korean STT quality evidence. No parent request is fully `DELIVERED` merely because a scoped component callback exists.
- The package preserves the exact model-card/license metadata. Where upstream did not publish a full license text in the snapshot, the package does not invent one. Review the acquired-version usage-rights persistence condition and full license terms before commercial release. No legal approval is asserted here.
- GitHub Actions ZIPs expire after 30 days. A separately authorized permanent/private HF archive and an independent restore proof remain necessary for long-term preservation. Three-to-four concurrent **acquisition** on the autonomous CPU path is also not proven by the packaging job's matrix.
