#!/bin/bash
set -e

# Hive evaluation script for Trading RL Agent
# Trains the agent and evaluates on validation set
# Outputs batting_score to stdout for Hive leaderboard

cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true

echo "=== Training RL Agent ==="

# Train with current configuration
python rl/agent/train.py \
    --max-tickers 500 \
    --total-timesteps 500000 \
    --eval-freq 25000 \
    --train-start 2000-01-01 \
    --train-end 2024-06-30 \
    --val-start 2024-07-01 \
    --val-end 2025-06-30 \
    2>&1 | tee rl/results/train.log

echo ""
echo "=== Evaluating on Validation Set ==="

# Evaluate best model and compute batting average
python3 -c "
import sys
sys.path.insert(0, '.')
import numpy as np
from math import sqrt
from stable_baselines3 import PPO
from rl.env.trading_env import TradingEnv
from rl.data.loader import load_universe

# Load
data = load_universe('mega_universe.json', max_tickers=500)
model = PPO.load('rl/results/best_model')

config = {
    'ticker_data': data,
    'initial_capital': 100000,
    'max_position_pct': 0.07,
    'stop_loss_pct': 0.08,
    'dd_halt_pct': 0.10,
    'transaction_cost': 0.001,
    'start_date': '2024-07-01',
    'end_date': '2025-06-30',
    'augment': False,
    'crash_injection_prob': 0,
    'episode_length': 252,
}
env = TradingEnv(config)

# Run 100 evaluation episodes
all_trades = []
all_monthly = {}
equities = []

for ep in range(100):
    obs, info = env.reset()
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, truncated, info = env.step(action)
        if truncated:
            break
    all_trades.extend(env.episode_trades)
    for k, v in env.monthly_pnl.items():
        all_monthly[k] = all_monthly.get(k, 0) + v
    equities.append(info.get('equity', 100000))

# Compute batting average
total_months = len(all_monthly)
profitable_months = sum(1 for v in all_monthly.values() if v > 0)
monthly_wr = profitable_months / total_months if total_months > 0 else 0

wins = [t for t in all_trades if t['profit'] > 0]
losses = [t for t in all_trades if t['profit'] <= 0]
gross_profit = sum(t['profit'] for t in wins) if wins else 0
gross_loss = abs(sum(t['profit'] for t in losses)) if losses else 1
pf = min(gross_profit / max(gross_loss, 1), 20)

avg_equity = np.mean(equities)
total_return = max((avg_equity - 100000) / 100000 * 100, 1)

# Max drawdown estimate from trade losses
cumulative = 0
peak = 0
max_dd = 0
for t in all_trades:
    cumulative += t['profit']
    if cumulative > peak:
        peak = cumulative
    dd = (peak - cumulative) / max(peak, 1) if peak > 0 else 0
    max_dd = max(max_dd, dd)
max_dd = min(max_dd, 0.95)

# Batting score
score = (monthly_wr ** 3) * pf * sqrt(total_return) * ((1 - max_dd) ** 2)

print(f'batting_score: {score:.4f}')
print(f'monthly_win_rate: {monthly_wr:.4f}')
print(f'profit_factor: {pf:.4f}')
print(f'total_return_pct: {total_return:.2f}')
print(f'max_drawdown: {max_dd:.4f}')
print(f'total_trades: {len(all_trades)}')
print(f'trade_win_rate: {len(wins)/len(all_trades):.4f}' if all_trades else 'trade_win_rate: 0')
" 2>&1

echo ""
echo "=== Evaluation Complete ==="
