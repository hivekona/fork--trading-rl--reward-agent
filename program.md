# Trading RL Agent — Hive Task

## Goal
Train an RL agent that maximizes the **Batting Average score** on held-out validation data:

```
score = monthly_win_rate^3 × profit_factor × sqrt(total_return) × (1 - max_drawdown)^2
```

This rewards CONSISTENCY (profitable almost every month) over raw returns.

## The Artifact
`rl/env/trading_env.py` — the Gymnasium environment (state space, reward function, constraints)
`rl/agent/train.py` — the training script (hyperparameters, network architecture)

## Hard Constraints (DO NOT REMOVE)
These are enforced by the environment and cannot be disabled:
1. **Force sell below 200 SMA** — mandatory exit
2. **8% stop loss** per position
3. **10% portfolio drawdown halt** — no new entries
4. **No buying below 200 SMA**

## What Agents Can Modify

### Agent Specializations

**"reward" agent** — Experiment with reward function design:
- `rl/env/trading_env.py` → reward computation in `step()` and `_episode_bonus()`
- Penalty weights, bonus structures, reward horizon
- Do NOT modify hard constraints

**"features" agent** — Experiment with state space:
- `rl/env/trading_env.py` → `_get_obs()` method
- `rl/data/loader.py` → `compute_features()` function
- Add/remove/transform features
- Update N_FEATURES and FEATURE_NAMES accordingly

**"architect" agent** — Experiment with training:
- `rl/agent/train.py` → network architecture, hyperparameters
- Network size (--net flag), learning rate, batch size, episodes
- PPO vs other algorithms

## Data
- **Universe**: 3,589 tickers (S&P 500 + Russell 2000 + Nasdaq + multi-asset ETFs)
- **Training**: 2000-01-01 to 2024-06-30
- **Validation**: 2024-07-01 to 2025-06-30 (score on THIS)
- **Test**: 2025-07-01 to 2026-04-01 (LOCKED — never train or eval on this)

## Evaluation
```bash
bash eval/eval.sh
```
This trains the agent and evaluates on the validation set.
Score is printed to stdout as `batting_score: <number>`.

## Current Best
Baseline PPO (16-16 network, 200 tickers, 500K steps):
- 53% trade win rate, 1.89x win/loss ratio
- Batting score: TBD (first full evaluation pending)

## Tips
- Smaller networks (16-16) generalize better than larger ones
- The agent tends to learn "do nothing" first — reward shaping is critical
- Episode length of 252 days (1 year) works well for diverse training
- Data augmentation (noise, synthetic crashes) helps robustness
- Check `hive task context` to see what other agents are trying
