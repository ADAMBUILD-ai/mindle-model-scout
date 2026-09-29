# AURA P0 Model Scout Request v3 — Architectural Visual / Drawing Understanding

Owner: 신작가님
Requester: AURA Commander
Priority: P0
Purpose: unblock AURA Milestone E/F final intelligence closeout.

Historical state:
- Florence-2 runtime was real but REJECT_QUALITY because captions were generic/repetitive.
- SigLIP and MiniLM are support-only and do not replace architecture-specific understanding.
- A previously acquired generic vision candidate may be benchmarked first if its pinned revision/license/hash evidence is intact; if it fails AURA benchmark, continue scouting automatically.

Required capability:
`ARCHITECTURAL_VISUAL_UNDERSTANDING_REPLACEMENT`

Required six classes:
- site plan
- floor plan
- section
- elevation
- aerial/perspective
- proposal page

Must ground:
- programme
- circulation
- mass/footprint relations
- level/section relations
- open-space hierarchy
- page hierarchy
- cross-view consistency

Forbidden:
- invented rooms/dimensions/programme
- fabricated materials/specifications
- generic caption-only PASS
- Florence-2 re-adoption merely because runtime works

Acquisition gate:
`REQUESTED -> FOUND -> DOWNLOADED -> PINNED_REVISION -> SHA256 -> LICENSE_SNAPSHOT -> ACQUIRED_VERSION_RIGHTS_PERSISTENCE -> RUNTIME -> AURA_6_CLASS_BENCHMARK -> TESTED_PASS -> DELIVERED`

Owner top rule:
Only adopt a model when the acquired exact version has evidence supporting continued use even if future upstream license/policy changes. If not proven: REJECT_AND_REPLACE.

Deliver:
- exact model ID/revision
- all files + SHA-256
- license snapshot/persistence evidence
- hardware/RAM/VRAM/runtime/cost
- raw outputs for all six classes
- grounded fact accuracy / relation reasoning / cross-view consistency / hallucination report
- KEEP / SUPPORT_ONLY / REJECT
- callback to AURA final Model Routing gate

Do not stop after one failed candidate while another allowed route exists.
