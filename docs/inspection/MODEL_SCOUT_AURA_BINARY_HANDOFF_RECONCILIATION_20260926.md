# MODEL SCOUT AURA binary handoff reconciliation — 2026-09-26

## Decision

PARTIAL / VERIFY_REQUIRED. Packaging is real; AURA product delivery remains blocked by
the independent handoff receipt and product-input validation. Do not promote a green
workflow or `BINARY_PACKAGE_READY` to `TESTED_PASS` or `DELIVERED`.

## GitHub and Drive evidence inspected

- PR #83 passed `tests`, `hf-e2e`, and `cli-smoke`, but its branch diverged from
  main and would remove the newer chunk workflow if taken as a file replacement.
- Main matrix run 36128115552 (commit 75a938b) uploaded four model artifacts:
  OCR 10860363349 (13,523,064 bytes), SAM2.1 10860193471 (155,953,467),
  MiniLM 10860448298 (499,583,581), SigLIP 10860598228 (815,891,776).
  Artifact size alone does not prove a complete package.
- The main matrix OCR ZIP was inspected: exact `inference.onnx` exists and its
  SHA-256 is `92f0b7785e64fc9090106a241cf4c1eb97472824558272751b88a2a4476d3a08`,
  but that particular slim ZIP has no full license text or runtime script.
- The separate Drive OCR package, file ID `1qvO8loRoqi3EqYZ93trXdO3Nit0P-dy8`,
  was independently downloaded. ZIP SHA-256:
  `a22dab5f82550d650dbddb2721cb04d8499db56729dc97bec19c29d0a762669f`.
  It contains `inference.onnx` (13,418,787 bytes, SHA-256 above), `inference.yml`,
  exact revision `5c6f574b8e2230adf4287b33e736d71b9fabd28e`, Apache-2.0
  canonical license snapshot, model-card snapshot, per-file hashes and runtime
  script. This is a different ZIP from the main matrix artifact and its whole-ZIP
  SHA has not been matched to the original builder's upload receipt.
- A local CPU-only smoke ran the Drive package's ONNX script with a generated
  `GOCHANG P04` text image. Input SHA-256:
  `97262a7067dabb13761f7c510bef8d4a6c5c919f349479bb7d9fc1f7ad5f7823`.
  Output: `{'text': 'cYaaYlowb', 'confidence': 0.5858111414644454}`;
  output SHA-256:
  `22e8684b9235310997c831a0bee787e38b7fd1692e17a6ab44c02014139d25b1`.
  This verifies execution, not useful OCR quality or real Gochang-page E2E.
- Drive folder `1w_i977M_dP52H9X839OZlh_Odb1PRSTK` also contains one SigLIP
  chunk and an older status JSON. No `AURA_MODEL_HANDOFF_READY_v63.json` was found.
- Autonomous run 36142447159 (main 75a938b): `results: []`; queue states
  DELIVERED 14, FAILED_TERMINAL 19, QUEUED 1. Issue #82 was terminal after 3
  retries; Issue #68 remained queued after 44 watchdog retries. Issue #81 was
  absent. Live runtime registry artifact contained four older records, with
  validation `PENDING`, and does not count this packaging as a new acquisition.

## Fixes in this reconciliation

- Preserve the latest main's chunk workflow and pinned SAM/Florence entries.
- Fail slim/full packaging on missing binaries, card, pinned SHA mismatch, or
  incomplete selected package; include license snapshot and safe runtime scripts;
  propagate builder exit codes through the workflow.
- Exclude central execution and binary-handoff directives from generic search
  intake; their dedicated workflows remain responsible for delivery.
- Bound stale watchdog retries; terminalize exhausted queue items without
  erasing historical evidence.

## Remaining acceptance gates

1. Run the fixed packaging workflow and independently inspect every ZIP and
   upload ID; validate exact revision, full license text, all SHA-256 values,
   executable runtime requirements, and archive checksum after Drive transfer.
2. Produce the Commander handoff receipt `AURA_MODEL_HANDOFF_READY_v63.json`.
3. Only then run actual P04/P07/P10/P11 copies against the frozen baseline and
   preserve input/output SHA, settings, latency and adoption decision.
4. Update the live model registry and callback with distinct
   `ACQUIRED_VERIFIED`, `TESTED_PASS`, and `DELIVERED` evidence. Current new
   cycle counts remain 0, 0, and 0 respectively.

No paid GPU or arbitrary remote model code is authorized.
