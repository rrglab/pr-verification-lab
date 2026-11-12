# PR Verification Lab

Public isolated verification fixtures for Quality Factory. GitHub is storage and PR review; **no GitHub Actions required**.

## Tools

Run locally: `bash scripts/run_local_checks.sh`.

Required: Python unit tests, compileall, and public-scope policy.
Optional when installed: Ruff, Bandit, yamllint, ShellCheck, pip-audit, npm audit/lint/types/tests, detect-secrets, Zizmor. The runner reports skipped tools; skipped checks do not count as green evidence.

CodeRabbit can review public PRs independently of GitHub Actions. Dependabot configuration remains for dependency update proposals. CodeQL and other scanners may be used through their local CLIs where available, but have no active Actions workflows in this repository.

## Procedure

1. Confirm permission to publish every file. Use synthetic/original fixtures, not private repository mirrors.
2. Open a PR with a reproducible fixture and exact source/head SHA.
3. Run local checks on the exact PR head and record actual results, failures and skips.
4. Consider independent CodeRabbit findings, fix and retest.
5. Apply approved changes in the real target repository and run its own local tests before merge.

A green lab fixture is **not** proof that the target repository is green or production ready.
Do not copy customer data, secrets, internal URLs, production dumps or proprietary files here. Do not use public publishing to evade service licensing or usage terms.
