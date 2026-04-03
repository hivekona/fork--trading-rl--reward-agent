# Features Patch — Experiment 2 (Best: 476.6 eval reward)

## Changes to FEATURE_NAMES and _get_obs()

Replace the 20-feature baseline with this 17-feature z-scored version:

### FEATURE_NAMES (replace existing):
```python
FEATURE_NAMES = [
    'sma20_zscore', 'sma50_zscore', 'sma200_zscore',
    'rsi14_norm',
    'roc20',
    'atr_pct', 'bb_position',
    'volume_ratio_norm',
    'consecutive_days_norm',
    'in_position', 'unrealized_pnl', 'days_held_norm',
    'cash_ratio', 'drawdown',
    'spy_above_200', 'vix_norm', 'spy_roc20',
]
```

### _get_obs() obs array (replace existing):
```python
obs = np.array([
    # Price features (3) — z-scored SMA distances (already clipped to [-3, 3])
    row.get('pct_from_sma20_zscore', 0) / 3.0,   # normalize to ~[-1, 1]
    row.get('pct_from_sma50_zscore', 0) / 3.0,
    row.get('pct_from_sma200_zscore', 0) / 3.0,

    # Momentum (2)
    row.get('RSI14', 50) / 100,
    row.get('ROC20', 0),

    # Volatility (3)
    row.get('ATR_pct', 0),
    row.get('BB_position', 0.5),
    min(row.get('Volume_Ratio', 1), 5) / 5,  # cap at 5x

    # Momentum streak (1) — consecutive up/down days, normalized
    np.clip(row.get('consecutive_days', 0) / 5.0, -1.0, 1.0),

    # Portfolio state (5)
    float(self.position > 0),
    np.clip(unrealized, -0.2, 0.5),
    min((self.step_idx - self.entry_step) / 20, 1.0) if self.position > 0 else 0,
    self.cash / equity if equity > 0 else 1.0,
    np.clip(drawdown, 0, 0.3),

    # Macro (3)
    row.get('SPY_above_200sma', 1.0),
    row.get('VIX_norm', 0.4),
    row.get('SPY_ROC20', 0),
], dtype=np.float32)
```

## Key Changes from Baseline:
1. **Z-scored SMA distances** instead of raw pct_from_sma — provides proper normalization
2. **Removed redundant features**: RSI5 (noisy), ROC5 (noisy), pct_from_sma8 (too short-term), volatility_20d (correlated with ATR_pct)
3. **Added consecutive_days_norm** — captures momentum streaks (positive = up, negative = down)
4. **Total: 17 features** (down from 20) — less overfitting with small 16-16 network

## Required: Delete feature cache after applying loader.py changes:
```bash
rm -rf /Users/joeyroth/july-backtester/data_cache/rl_features/
```
