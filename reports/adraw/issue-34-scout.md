# ADRAW Issue 34 P0 Scout Report

Date: 2026-09-13 UTC  
Request: #34  
Status: PARTIAL_TESTED_PASS

## Decision

ADRAW deterministic geometry, units, axes, floor coverage, identity and lineage remain authoritative. Scout resources are isolated behind optional QA adapters and feature flags. The core Full Chain operates without them.

| P0 role | Top candidate | License gate | Runtime gate | Status | ADRAW boundary |
| --- | --- | --- | --- | --- | --- |
| 3D object classification QA | PointNeXt OpenPoints | MIT | Offline; CPU smoke possible; training GPU-heavy | VERIFY_REQUIRED | Mesh-to-point QA adapter |
| Edge silhouette occlusion QA | OpenCV Canny baseline then DexiNed | Apache-2.0 / MIT | OpenCV not installed here; DexiNed weights and exact revision not pinned | VERIFY_REQUIRED | Raster disagreement QA only |
| Floorplan vector CAD QA | ezdxf 1.4.4 | MIT | Offline; Python 3.10+; actual DXF reopen tested | TESTED_PASS | DXF reopen audit adapter |

## Tested evidence

The Work track generated five actual AVORA floor-datum DXF files from source GLB SHA-256 `0be848494463478e4694428ec3949af45960272ce7c0a881a2d7c4a57d72c9b9`. ezdxf 1.4.4 reopened every file with `auditErrors=0`, `auditFixes=0`, and `$INSUNITS=6`.

| Floor | LINE entities | DXF SHA-256 |
| --- | ---: | --- |
| 1F | 620 | `4a8c29c285a20a69f35edb521f885e715f05b870101e65e2c5ebde4387bbf735` |
| 2F | 98 | `7bd35406544be5a29f9ff2f831500c05195ba76e32a7fd2f8ad01e647cc50df8` |
| 3F | 553 | `513e0a07501482e4febc2f2b572b8efd799e1eeb2af7df8c60415c619d8c8461` |
| 4F | 232 | `4b308b9678f743baf1bc188438c07aecd9e5d9f5a549c8e55b5de5c2ab1a8702` |
| ROOF | 44 | `483169b1af55da3d40c1629e907c465266e7610ae086eeb5ca347a6d3d5ec4b4` |

## Alternative and rejected candidates

- Point Transformer V3 / Pointcept: MIT, strong scene segmentation candidate; deferred because its documented CUDA/FlashAttention environment is unsuitable for the current Windows MX330 target.
- DINOv2 ViT-S/14: Apache-2.0 code; individual weight license and exact revision still require pinning. Optional multi-view anomaly QA.
- PiDiNet: environment and evaluation toolchain are older than DexiNed; excluded from P0.
- ScanNet and S3DIS: access terms require separate review; research-only until commercial rights are confirmed.
- CubiCasa5K: old runtime and large data footprint; license requires legal review. Research-only.
- FloorPlanCAD: CC BY-NC 4.0 annotations/site and source drawing rights limitations; rejected for commercial product training.
- Intel FloorSet: Apache-2.0 code and CC BY 4.0 dataset; acceptable future synthetic topology QA, but weak real CAD symbol coverage.
- Shapely: BSD-3-Clause; future deterministic topology QA tool.
- BlenderProc: useful for synthetic depth/instance ground truth, but licensing and Blender subprocess requirements move it to P1.

## Resource and promotion gates

Exact source commits, model revisions, weight hashes, license hashes, Windows CPU/GPU/RAM measurements, offline replay and actual AVORA A/B results are required before any model promotion. Download or model-card inspection alone is not TESTED_PASS. Commercially unclear and noncommercial data remain excluded.

## Handoff

Work integration order: ezdxf reopen/audit first, OpenCV deterministic edge baseline second, PointNeXt embedding smoke third, DexiNed A/B only after exact revision and weight/license evidence. Each adapter must be removable and must not write AVORA canonical data.
