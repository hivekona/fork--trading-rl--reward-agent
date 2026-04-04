#!/bin/bash
set -e

# Hive evaluation script — Regret vs Best-of-Both metric
#
# The agent is scored on how well it matches or beats VOO every month.
# Sitting in cash during a bull month = heavy regret penalty.
# Beating VOO during a crash = zero regret (perfect).
#
# Score = total_return - (monthly_regret_vs_VOO × 500)

cd "$(dirname "$0")/../.."
source venv/bin/activate 2>/dev/null || true

echo "=== Running Backtest ==="
python main.py 2>&1 | tail -5

echo ""
echo "=== Scoring: Regret vs Best-of-Both ==="
python scripts/verify_regret.py 2>&1
