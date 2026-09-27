# AGRI scoped autonomous acquisition restart — 2026-09-27

## Actual queue baseline

Post-merge run #591 (`36298805463`, main `9bc4d12db8a1a93b44c70852c56160e48013cccf`) produced zero results and `NO_ELIGIBLE_REQUESTS`. Its Evidence artifact `10924922892` shows 15 MISROUTED historical work orders/routes, 9 remaining genuine FAILED_TERMINAL product requests, 3 BLOCKED_INPUT, 1 SUPERSEDED and 19 prior DELIVERED. Live registry artifact `10924733321` remained unchanged. The queue is truthfully idle, but MODEL SCOUT is not yet actively acquiring for the genuine backlog.

## Controlled recovery for genuine AGRI #33

The open AGRI #33 Issue explicitly requests Korean semantic search/embedding for agricultural supplier and market material. Its original `resource=all` request covers seven roles and has an exhausted historical fingerprint. Add one independent subrequest tied to that same verified open Issue and exact capability string `임베딩`, using `SCOUT_SELECTION_REQUIRED`. MODEL SCOUT, not this directive, selects a candidate through official Hub task search. The parent failure/retry history remains untouched.

Improve generic task query planning to use the Hub `feature-extraction` task endpoint rather than relying only on a full Issue body search. For this CPU lane, reject unknown or over-650 MB exact-revision weights before download, require built-in Transformers configuration with remote code disabled, require pinned weights, and cap execution at 900 seconds. Preserve license gate, model card/license snapshot, actual bytes and SHA-256. A successful component may become ACQUIRED_VERIFIED only; AGRI-specific product TESTED_PASS/DELIVERED needs real agricultural inputs and product acceptance.

## Verification gate

59 focused tests passed locally, including generic task search, real Issue-grounded unpinned scope and pre-download size rejection. Exact-head CI and live autonomous Evidence are required. If search finds no allowed small safe model, report the exact rejected candidates and retain retry semantics; do not fabricate acquisition or reset the parent terminal.

Source: [AGRI #33](https://github.com/ADAMBUILD-ai/mindle-model-scout/issues/33), [run #591](https://github.com/ADAMBUILD-ai/mindle-model-scout/actions/runs/36298805463).
