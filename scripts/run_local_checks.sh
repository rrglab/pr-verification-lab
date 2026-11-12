#!/usr/bin/env bash
# Local-only, evidence-producing Quality Factory verification.
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== Public scope =="
python scripts/check_public_scope.py
echo "== Python compile =="
python -m compileall -q scripts tests
echo "== Unit tests =="
python -m unittest discover -s tests -v
run_optional() {
  local name="$1"; shift
  if command -v "$name" >/dev/null 2>&1; then
    echo "== $name =="
    "$@"
  else
    echo "SKIPPED: $name is not installed"
  fi
}
run_optional ruff ruff check scripts tests
run_optional bandit bandit -q -r scripts tests -ll
if command -v yamllint >/dev/null 2>&1 && [[ -d .github ]]; then
  run_optional yamllint yamllint -d '{extends: relaxed, rules: {line-length: disable, truthy: disable}}' .github
fi
if command -v shellcheck >/dev/null 2>&1; then
  mapfile -d '' scripts_to_check < <(git ls-files -z '*.sh')
  if (( ${#scripts_to_check[@]} )); then shellcheck "${scripts_to_check[@]}"; fi
fi
if [[ -f requirements.txt ]] && command -v pip-audit >/dev/null 2>&1; then
  pip-audit -r requirements.txt
elif [[ -f pyproject.toml ]] && command -v pip-audit >/dev/null 2>&1; then
  pip-audit .
fi
if [[ -f package.json ]]; then
  if [[ ! -f package-lock.json ]]; then echo 'FAIL: missing package-lock.json'; exit 1; fi
  npm ci --ignore-scripts
  npm audit --audit-level=high
  npm run --if-present lint
  npm run --if-present typecheck
  npm test --if-present
fi
if command -v detect-secrets >/dev/null 2>&1; then
  temp_report="$(mktemp)"
  trap 'rm -f "$temp_report"' EXIT
  detect-secrets scan --all-files > "$temp_report"
  python -c 'import json,sys; d=json.load(open(sys.argv[1])); assert not d["results"], "Possible secrets detected"' "$temp_report"
else
  echo "SKIPPED: detect-secrets is not installed"
fi
if command -v zizmor >/dev/null 2>&1 && [[ -d .github/workflows ]]; then
  zizmor .github/workflows --format plain
fi
echo "Local checks finished. Review SKIPPED tools before promoting changes."
