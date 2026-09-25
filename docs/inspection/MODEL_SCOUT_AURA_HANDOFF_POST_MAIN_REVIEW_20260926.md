# MODEL SCOUT AURA handoff post-main review — 2026-09-26

## Applied code and CI

PR #84 merged as `32bd31346ce137b276a2c9f8a4df47229cfb7b85`.
PR checks `tests` (36189805995), `hf-e2e` (36189806014), and
`cli-smoke` (36189806012) all completed successfully. Local suite: 152 passed.
PR #83 was closed as superseded because its older file tree omitted the chunk
workflow and pinned SAM/Florence additions.

## Post-main packaging run

Workflow run `36190104748` used exact head `32bd313`. All four package jobs
completed successfully and uploaded artifacts:

| Model key | Artifact ID | Artifact bytes | GitHub artifact digest |
| --- | ---: | ---: | --- |
| OCR | 10887458409 | 13,536,837 | `sha256:1296b1952678ba75393bd4e3c1552699dccd351845da52e235de0a701fe08cf7` |
| SAM2.1 | 10887169457 | 155,962,557 | `sha256:ee182fa7756aed24d652290059f0e4181c0217914edacd97a44276af36f4016a` |
| MiniLM | 10886914642 | 499,586,985 | `sha256:78253f65e96f70b3e4ee437598ccd758f89e929bde50e648189b641f2ea8172a` |
| SigLIP | 10887518283 | 815,899,871 | `sha256:727c7a3da609f28f68f56a79372adc4d9ac92aeb5e7289a43303295ca69b8477` |

The OCR GitHub artifact was independently downloaded and opened. Its inner ZIP
`AURA_OCR_HANDOFF_5c6f574b8e22.zip` has SHA-256
`fb8a6cc55460dcc72c2d678b3b18499c6448887c1acbeaac6f3b95941934671d`,
matching the package index. All 12 listed internal SHA256SUMS entries matched;
ZIP integrity test found no corrupt entry. It includes exact model revision
`5c6f574b8e2230adf4287b33e736d71b9fabd28e`, actual `inference.onnx`
(13,418,787 bytes; SHA-256
`92f0b7785e64fc9090106a241cf4c1eb97472824558272751b88a2a4476d3a08`),
`inference.yml`, Apache-2.0 license text and persistence record, model-card
snapshot, runtime script and pinned requirements. Cache lock files were excluded.

The previous Drive OCR package was separately downloaded and CPU-executed on a
synthetic input; that run is an execution smoke, not a Gochang quality pass.
The new GitHub OCR ZIP has **not** yet been uploaded to and re-downloaded from
Drive. The other three large artifacts' inner ZIPs have **not** been independently
opened here; their contents must not be inferred from artifact size alone.

## Open gates

- Independent re-download/hash inspection of SAM2.1, MiniLM and SigLIP packages.
- Exact new package transfer to Drive and comparison with GitHub inner-ZIP SHA,
  then `AURA_MODEL_HANDOFF_READY_v63.json` receipt under Issue #82.
- AURA's actual frozen Gochang input/output A/B, quality decision and callback.
- Post-merge autonomous run proving administrative intake exclusion and bounded
  stale retries. The most recent inspected autonomous run used old head `75a938b`.
- Live registry and queue transitions: this package-only execution must not be
  counted as a new `ACQUIRED_VERIFIED`, `TESTED_PASS` or `DELIVERED` entry yet.

Current decision: CODE_AND_OCR_PACKAGE_VERIFIED / AURA_DELIVERY_VERIFY_REQUIRED.
