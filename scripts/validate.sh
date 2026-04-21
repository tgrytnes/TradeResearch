#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

python3 -m compileall -q scripts
python3 -m json.tool config/futures_roll_policies.json >/dev/null

for script in scripts/*.sh; do
  bash -n "$script"
done

if [[ "${RUN_DOCKER_CHECKS:-0}" == "1" ]]; then
  scripts/verify_clickhouse_smoke.sh
fi

echo "Validation passed."
