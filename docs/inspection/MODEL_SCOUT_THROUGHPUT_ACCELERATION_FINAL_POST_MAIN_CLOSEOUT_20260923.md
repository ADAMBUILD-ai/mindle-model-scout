# MODEL SCOUT Throughput Acceleration — Final Post-Main Closeout

Date: 2026-09-23

Repository: `ADAMBUILD-ai/mindle-model-scout`

Directive: `MODEL_SCOUT_CALLBACK_403_EVENT_PRIORITY_RUNTIME_FINALIZATION_DIRECTIVE_v8.0_20260923.md`

Merged PR: #70

Main merge commit: `56a4337b510d8ad560864b2c7809f9b2be175242`

## Verdict

`MODEL_SCOUT V8 SAFE FIXES: PASS`

`FINAL LIVE FOLLOW-UP: BLOCKED_EXTERNAL_RUNTIME — self-hosted runner mindle-model-scout is Offline; run 35836381547 remains queued.`

The prior broad token-permission blocker is resolved for same-repository callbacks. No token rotation or permission expansion was needed. Final unconditional closeout remains withheld only because the runner went offline before the unique-nonce request-complete rerun and external-callback retest.

## Implemented fixes

- Same-repository callbacks use `github.token`; cross-repository discovery/callback uses `MODEL_SCOUT_CROSS_REPO_TOKEN`.
- Credential routing fails closed and never exposes token values.
- The exact event Issue is fetched and processed before backlog without increasing the cycle limit.
- `scipy==1.17.1` is pinned for Windows CPython 3.11 and NumPy 2.4.6 compatibility.
- HF 500/502/503/504 and transient network failures retry at most three times; 4xx responses fail immediately.

## Verification

| Gate | Result | Evidence |
|---|---|---|
| Focused tests | PASS | 25 passed |
| Full tests | PASS | 133 passed |
| exact-head tests | PASS | run `35833685500` |
| exact-head cli-smoke | PASS | run `35833685719` |
| exact-head hf-e2e | PASS | run `35833685593` |
| Geometry runtime | PASS | SciPy 1.17.1; section vertices 8 |
| Event priority | PASS | Issues #72/#73 are the first result in runs `35833994943`/`35835517822` |
| Local callback | PASS | Issue #54 comment `5791190970` |
| Callback idempotency | PASS | no second callback for the delivered fingerprint |
| License/runtime gate | PASS fail-closed | generic Issues #72/#73 were not falsely promoted |

## Live proof detail

Issue #72 triggered run `35833994943`; artifact `10738876852` shows its fingerprint as the first cycle result. Its verbose search produced zero executable candidates and was correctly classified `FAILED_RETRYABLE`.

Issue #73 triggered run `35835517822`; artifact `10738849626` again shows the event fingerprint first. The generic worker returned component scope, so the request-complete gate correctly rejected promotion.

Main push run `35833961980` retried existing same-repository `EVIDENCE_READY` delivery and wrote Issue #54 callback comment `5791190970`. The comment contains verified `TESTED_PASS` runtime output, revisions, licenses, SHA-256 hashes, and Windows CPU evidence. This proves the HTTP 403 root cause was token-role collision and that the local-token route works.

The delivered fingerprint did not create another callback during runs `35833994943` and `35835517822`, proving idempotency.

## Remaining exact blocker

Issue #54 received nonce `v8-local-callback-20260923-0818` to force a fresh request-complete fingerprint. GitHub created run `35836381547`, but repository settings report runner `mindle-model-scout` as **Offline** and the run remains queued.

Required external action: restore the existing runner service. This needs no code change, paid resource, token rotation, permission expansion, deletion, or force push. After reconnection, allow run `35836381547` to finish, then retest one already-authorized external callback repository if required.

## Safety

No force push, deletion, production deployment, paid compute, secret disclosure, secret rotation, or permission expansion was performed. Remote code execution remains disabled.

## Evidence paths

- `evidence/immediate-trigger-main-proof-20260923.json`
- `evidence/runner-bootstrap-cache-main-proof-20260923.json`
- `evidence/post-main-regression-proof-20260923.json`
- `docs/inspection/MODEL_SCOUT_THROUGHPUT_ACCELERATION_FINAL_POST_MAIN_CLOSEOUT_20260923.md`
