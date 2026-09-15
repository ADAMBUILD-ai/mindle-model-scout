# LIVE CROSS-REPO E2E — 2026-09-15

Targets:
- ADAMBUILD-ai/agri-ai-business-platform — MODEL SCOUT request issue
- ADAMBUILD-ai/adam-build — MODEL SCOUT request issues #38/#39/#40

Execution path under proof:
source issue discovery -> normalization/dedupe -> persistent queue -> existing scout core -> durable evidence -> GitHub issue callback -> DELIVERED.

Required evidence:
- callback comment IDs/URLs in both source repositories
- queue fingerprints and final states
- duplicate suppression proof
- retry-safe callback proof
- GitHub Actions run + artifact

Boundary:
- This lifecycle proves SCOUT_RESULT automation, not runtime TESTED_PASS.
- Runtime TESTED_PASS still requires real output/log/settings/runtime/license/hash evidence.
