# CURRENT EXECUTION CONTROL

Status source: GitHub Evidence only. This file exists so the next executor can continue without chat-memory dependency.

## Current integrated state
- Repository: ADAMBUILD-ai/mindle-model-scout
- Default branch: main
- SCOUT-GATE-02A (PR #20): completed and merged.
- SCOUT-GATE-02B (PR #22): completed and merged.
- SCOUT-GATE-03 final product hardening (Issue #23 / PR #24): completed and merged.
- SCOUT-GATE-04 multi-resource redevelopment (Work handoff / PR #25): completed and merged.
- Gate 04 merge commit: `6a5044baebb45240c9cdd18e38ba8d5c152c1109`.
- Common FastAPI layer (PR #27) merged at `3938711f6806053329a0062a5114dbfdb96eba07`.
- Local Web UI was replayed onto main as `0a1e5390a2f7b210829b6dd629b60571e680e514` and connected to the common API at `0fca08955d23eec0de57d9a01539fb81032e8103`.

## Current validation recovery
The two UI/API commits reached `main` directly rather than through a pull request. The normal `tests` workflow ran on `main@0fca08955d23eec0de57d9a01539fb81032e8103` and passed (`tests` run 34688013286; 45 passed, 1 warning), but `hf-e2e` and `cli-smoke` are configured for `pull_request` to `main` or manual dispatch and therefore did not run for those direct pushes.

Recovery action: validate the exact current main code through branch `recovery/ui-api-validation-20260912` and a PR to `main`, so `tests + hf-e2e + cli-smoke` execute together before declaring the UI/API integration fully verified.

## SCOUT-GATE-04 delivered behavior
- Hugging Face Model, Dataset, and Space resource scouting are integrated,
- CLI supports `--resource model|dataset|space|all`,
- multi-resource results are deduplicated by `(resource_type, model_id)`,
- Requirement Profile includes expanded task mappings, language hints, and library/framework hints,
- Dataset/Space resources are normalized into the common candidate shape with resource-aware source URLs,
- scoring exposes explainable popularity/task/metadata/license components in candidate reasons,
- commercial-use requests block non-commercial (`-nc` / non-commercial) licenses as `LICENSE_NOT_PERMITTED`,
- candidates with `LICENSE_NOT_PERMITTED`, `LICENSE_REVIEW_REQUIRED`, or `REJECT` are not selected as the recommended result,
- JSON and Markdown outputs include comparison/warning evidence,
- Watch identity is resource-aware so identical IDs from different resource types remain distinct,
- existing Model Scout behavior remains regression-covered.

## Gate 04 source handoff
Work local branch `redevelopment-audit` reported HEAD `a1de1c7` with 35 local tests PASS and live Dataset/Space PASS. The Work shell had no Git credential, so the source package was handed to the commander and integrated through GitHub branch `feat/redevelopment-audit-handoff`.

During commander review, one safety gap was corrected before merge: a commercially blocked `LICENSE_NOT_PERMITTED` candidate could otherwise be selected as `recommended`. JSON output was also strengthened to expose `recommended`, `comparison`, and `warnings`. Regression tests were added for both behaviors.

## Final validation evidence
PR #25 head `63e9c368e63f9c6e16c927513eea72dbbca44890`:
- `tests` run 34560887155 — SUCCESS
- live `hf-e2e` run 34560887144 — SUCCESS
- live `cli-smoke` run 34560887269 — SUCCESS
- artifact `model-scout-cli-smoke` id 10184255831
- artifact digest `sha256:2f2eb8c235734143877557caeb29c5b39b3ce47a5143e424e39bcc540b641ec3`

Post-merge main `6a5044baebb45240c9cdd18e38ba8d5c152c1109`:
- `tests` run 34560943307 — SUCCESS

## Product completion boundary
VERIFIED COMPLETE for the current Hugging Face multi-resource Scout scope:
Requirement -> resource selection (model/dataset/space/all) -> live Hugging Face search -> candidate normalization/deduplication -> requirement filtering -> license gate -> explainable scoring/ranking -> safe recommendation -> Model Cards -> JSON/Markdown comparison report, plus resource-aware persisted Watch/Delta and CLI artifact evidence.

Known limitation: license status is an engineering safety gate based on available Hugging Face metadata and simple policy rules, not a legal opinion. Unknown/proprietary licenses remain review-required.

## Active next execution gate
Issue #28 — `[REQUEST][WARREN–BUFFETT] 금융/주식용 HF 모델·데이터셋·Space 선행 스카우트 요청` — P0.

Next executable action after UI/API validation: run live Hugging Face scouting for all 11 WARREN/GATE/BUFFETT roles using `resource=model|dataset|space|all`, apply the license gate, write JSON + Markdown Scout reports, commit report paths/evidence, and reply to Issue #28 with exact candidate/report evidence. Do not claim completion until all 11 roles are mapped and evidence is committed.

## Evidence-first operating rule
- Never report development progress without a commit, PR, CI/test result, artifact, or exact verified blocker.
- If meaningful Evidence is unchanged for two consecutive checks, first verify whether a concrete executable gate exists.
- If a gate exists, audit: repository/permission -> remote branch/PR/commit -> possible local-only unpushed work -> Actions/CI -> instruction/SSOT/handoff reachability -> integration owner/next-action trigger -> push/integration path.
- Classify the exact failure before waiting and apply the smallest safe recovery action immediately when no representative approval is required.
- If no active gate exists, quiet time is not a development stall.
