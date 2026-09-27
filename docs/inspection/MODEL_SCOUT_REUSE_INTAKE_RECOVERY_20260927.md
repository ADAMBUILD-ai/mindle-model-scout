# MODEL SCOUT reuse intake recovery — 2026-09-27

## Observed production failure

- Autonomous run #584 (`36296358052`, main `a78369638f2921f68a32b4b1ddda58cd830196c8`) completed green, but its Evidence artifact `10923539631` had no results and did not contain central Issue #118 in its 46 queued records.
- The issue uses `[P1][AVORA][REUSE]` and specifies pinned AURA SAM2.1/SigLIP and ADAM packages. Its title/body do not contain the generic MODEL SCOUT request marker, so discovery silently omitted it. The central repository was fetched twice because configured and canonical names differed only by case.
- AVORA Commander accepted Blender 4.5.14 LTS / EEVEE Next as a renderer and rejected pyrender in Issue #115's latest review comment. No renderer rescout is requested. AVORA's remaining mapping integrity/material finish work belongs to avora-engine.

## Fix

- Case-insensitive repository dedupe in intake.
- Narrow central `[REUSE]` request recognition when pinned revision/SHA is present. Generic repository issues are not newly admitted.
- Reuse requests enter persistent queue and return `BLOCKED_INPUT` with the exact missing AVORA render/GLB and Blender object masks or approved reference. They do not run generic Hub search, exhaust retries, or claim TESTED_PASS/DELIVERED.

## Verification and remaining work

- Focused unit tests: 17 passed locally, including #118 ingestion, no generic rescout, stable BLOCKED_INPUT, retry count zero.
- CI and post-merge autonomous run must be checked against the exact proposed head before operational acceptance.
- To perform the actual product test, connect accessible exact V2/V3 AVORA images, GLB and Blender object-ID/depth masks to a dedicated reuse runtime; verify pinned package bytes, license snapshot, hashes and metric outputs. Until then, #118 stays BLOCKED_INPUT and no AVORA result is promoted.
- Historical queue entries and stale Issue #115 status are preserved; no terminal reset or invented delivery.

Sources: [run #584](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36296358052), [Issue #118](https://github.com/ADAMBUILD-ai/mindle-model-scout/issues/118), [Issue #115 review](https://github.com/ADAMBUILD-ai/mindle-model-scout/issues/115#issuecomment-5852720404).

## Post-merge operational verification

- PR #119 merged to main `747bc28181e0b0a65b4b6d1d5b8af32d94b666f6`. Exact PR head `f6fa7c3066df2a8a60c83a412c25d70ef6394957`: tests #344, cli-smoke #222, hf-e2e #227 all SUCCESS.
- Post-merge autonomous run #585 (`36297045667`) completed SUCCESS on that main SHA. Evidence artifact `10924071505`, digest `sha256:5e7b7dedb432c36f25fc74faba6e0174c48c129f7c3e37c0d31f0de9c1055a60`, independently inspected.
- Issue #118 fingerprint `c8e0fa020f33e218e41d9b07b21b6f44888409d58b10c69249d562f4e4f7bd49` entered queue as AVORA pinned reuse; result `BLOCKED_INPUT`, retry_count=0, with exact input/mask/reference reason. No generic Hub rescout, product output, TESTED_PASS or DELIVERED.
- Live registry artifact `10924785525` retained digest `sha256:1863ba1ad5ffb26f4d4724454206f15d381da3ee31c77a5dcb2c2e3ece96996a`; no new acquired model. Queue now contains 47 entries: 24 FAILED_TERMINAL, 19 DELIVERED, 3 BLOCKED_INPUT, 1 historical QUEUED. Historical #115 model fingerprint remains queued with retry_count=2; accepted AVORA Blender outcome is not yet reconciled into the old queue state.
- This confirms intake recovery only. The dedicated product reuse runtime and exact input transfer remain open work; run success must not be read as product delivery.
