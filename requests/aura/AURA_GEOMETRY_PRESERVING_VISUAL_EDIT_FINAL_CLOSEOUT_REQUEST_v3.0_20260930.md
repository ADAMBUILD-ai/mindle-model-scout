# AURA P0 Model Scout Request v3 — Geometry-Preserving Controlled Visual Edit

Owner: 신작가님
Requester: AURA Commander
Priority: P0
Purpose: unblock AURA Milestone E/F visual-quality closeout.

Historical state:
- SAM 2.1 is verified support for protected-region segmentation/scope only.
- Gochang direct generated candidates improved material/light/atmosphere direction but changed locked architecture and were rejected.
- SigLIP + OpenCV was TESTED_PASS as safe reference/edit QA fallback, but is not the missing high-quality generative/edit capability.
- Qwen/FLUX/SDXL/ControlNet family names are candidates only, never automatic authorization.

Required capability:
`GEOMETRY_PRESERVING_CONTROLLED_VISUAL_GENERATION_EDIT`

Hard benchmark:
- explicit edit mask
- protected geometry mask
- building count unchanged
- layout/relative positions unchanged
- footprint/topology unchanged
- protected edge/pixel delta = 0
- E1 outside-mask delta = 0
- edit/protected intersection = 0
- visible improvement in material / landscape / lighting / people / atmosphere / rendering quality

Acquisition gate:
`REQUESTED -> FOUND -> DOWNLOADED -> PINNED_REVISION -> SHA256 -> LICENSE_SNAPSHOT -> ACQUIRED_VERSION_RIGHTS_PERSISTENCE -> RUNTIME -> GEOMETRY_LOCK_BENCHMARK -> VISUAL_AB -> TESTED_PASS -> DELIVERED`

Owner top rule:
Only adopt a model when the acquired exact version has evidence supporting continued use even if future upstream license/policy changes. If not proven: REJECT_AND_REPLACE.

Preferred execution:
- local / pinned / reproducible where feasible
- low-VRAM/quantized alternatives before paid API when quality is sufficient
- paid/API route requires separate cost evidence and does not bypass license/persistence gate

Any building-count/layout/footprint/protected-region drift = REJECT.

Deliver:
- exact model ID/revision/files/SHA
- license snapshot/persistence evidence
- hardware/RAM/VRAM/runtime/cost
- deterministic command/settings
- source/mask/protected-mask hashes
- all output hashes
- geometry metrics
- inside/outside diff
- visual A/B
- KEEP / SUPPORT_ONLY / REJECT
- callback to AURA final Model Routing gate

Do not stop after one failed candidate while another allowed route exists.
