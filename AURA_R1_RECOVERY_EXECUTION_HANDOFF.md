# AURA R1 RECOVERY EXECUTION HANDOFF

Status source: GitHub Evidence only.

## Why this recovery handoff exists

Repeated Evidence-first checks found no new AURA implementation/output artifact after the prior SSOT repair and Issue #32 ownership assignment.

Verified classification: **EXECUTOR INACTIVITY**.

The following were re-verified before this handoff was created:

1. Repository health/write path: healthy. Connected principal has admin/maintain/push/pull permission.
2. Remote state before this recovery commit: `main` = `e04f169f4bff6a77c9f9d34cefda8ce9e52c5aea`; AURA branch = `466c50f265c76979185b47ad82e205ccb1f2f69c`; PR #31 open, mergeable, unmerged.
3. Actions/CI: healthy. Existing AURA PR head previously passed `tests`, `hf-e2e`, and `cli-smoke`; main recovery commit passed `tests`.
4. SSOT/handoff: healthy. `main/CURRENT_EXECUTION_CONTROL.md` marks AURA P0 ACTIVE and points to Issue #32 / PR #31 / `AURA_FINAL_EXECUTION_ORDER.md`.
5. Integration owner/trigger: present. Issue #32 is assigned to `ADAMBUILD-ai` and contains the executable next step.
6. Remote push/integration path: healthy. Same-repository AURA branch exists and is unprotected; push permission is available.

No local-only development is claimed because GitHub cannot verify it.

## Immediate executable micro-task — R1 only

Do not wait for PR #31 merge or another approval. Execute the smallest proof first:

**R1 architectural image / concept graphic validation**

Required outcome: at least **one real `TESTED_PASS` AURA asset** produced by an actual inference run using a real AURA input.

### Mandatory Evidence for the first R1 PASS

- model ID
- exact model revision/commit when available
- source URL / Hugging Face source identifier
- license and license decision
- input asset/path or reproducible input description
- actual output asset file
- inference settings / prompt / seed / relevant parameters
- runtime environment
- VRAM/RAM information when observable
- execution log
- file size
- SHA-256 of output
- explicit PASS/FAIL reason

`TESTED_PASS` is forbidden unless the real output file exists and the run is reproducible from the recorded settings/evidence.

### Failure handling

If the first R1 candidate fails because of missing weights, broken files, incompatible runtime, VRAM constraints, license status, or unusable output:

1. Record the failed candidate and exact verified failure.
2. Re-scout immediately in the same execution cycle.
3. Test the replacement candidate.
4. Continue until one valid R1 `TESTED_PASS` exists or an irreversible/user-approval blocker is reached.

Do not stop at `PASS 0`.

## Delivery location

Create/update the delivery package:

`AURA_MODEL_SCOUT_DELIVERY_20260913`

Minimum first-push contents:

- R1 JSON evidence
- R1 Markdown evidence
- actual R1 output asset
- input/settings/log/runtime/license/revision/SHA evidence

Push the Evidence to the active AURA branch / PR path so GitHub can verify it.

After the first R1 `TESTED_PASS` is present remotely, continue R2–R5 under Issue #32.

## Approval boundary

No extra approval is required for free/public Hugging Face scouting, download, execution testing, re-scouting, safe branch/PR updates, Evidence generation, and AURA handoff.

Ask for approval only for login/additional permission, paid cost/GPU, external publication, destructive/hard-to-reverse change, secret rotation, production deployment, or another irreversible action.
