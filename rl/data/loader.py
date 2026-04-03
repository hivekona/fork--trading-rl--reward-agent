"""
Data loader — pre-processes ticker data with technical features for RL environment.
Caches to parquet for fast loading on subsequent runs.
"""
import os
import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "data_cache" / "rl_features"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def compute_features(df):
    """Add technical indicator features to OHLCV DataFrame."""
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    # SMAs
    for period in [8, 20, 50, 200]:
        df[f'SMA{period}'] = close.rolling(period).mean()
        df[f'pct_from_sma{period}'] = (close - df[f'SMA{period}']) / df[f'SMA{period}']

    # RSI
    for period in [5, 14]:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        df[f'RSI{period}'] = 100 - (100 / (1 + rs))

    # Rate of change
    for period in [5, 20]:
        df[f'ROC{period}'] = close.pct_change(period)

    # ATR as % of price
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    df['ATR14'] = tr.rolling(14).mean()
    df['ATR_pct'] = df['ATR14'] / close

    # Bollinger Band position (0 = at lower, 1 = at upper)
    bb_sma = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    df['BB_upper'] = bb_sma + 2 * bb_std
    df['BB_lower'] = bb_sma - 2 * bb_std
    bb_range = df['BB_upper'] - df['BB_lower']
    df['BB_position'] = (close - df['BB_lower']) / bb_range.replace(0, np.nan)
    df['BB_position'] = df['BB_position'].clip(0, 1)

    # Volume ratio
    df['Volume_Ratio'] = volume / volume.rolling(20).mean()

    # Daily return
    df['daily_return'] = close.pct_change()

    # Volatility (20d rolling std of returns)
    df['volatility_20d'] = df['daily_return'].rolling(20).std()

    # Z-scored SMA distances (rolling 50-day z-score of pct_from_sma)
    for period in [20, 50, 200]:
        col = f'pct_from_sma{period}'
        if col in df.columns:
            rolling_mean = df[col].rolling(50, min_periods=20).mean()
            rolling_std = df[col].rolling(50, min_periods=20).std()
            df[f'{col}_zscore'] = (df[col] - rolling_mean) / rolling_std.replace(0, np.nan)
            df[f'{col}_zscore'] = df[f'{col}_zscore'].clip(-3, 3)

    # Consecutive up/down day count (positive = up streak, negative = down streak)
    returns = close.pct_change()
    consecutive = pd.Series(0, index=df.index, dtype=float)
    streak = 0
    for i in range(len(returns)):
        if pd.isna(returns.iloc[i]):
            streak = 0
        elif returns.iloc[i] > 0:
            streak = streak + 1 if streak > 0 else 1
        elif returns.iloc[i] < 0:
            streak = streak - 1 if streak < 0 else -1
        else:
            streak = 0
        consecutive.iloc[i] = streak
    df['consecutive_days'] = consecutive

    return df


def load_spy_features():
    """Load SPY data with features for macro regime."""
    cache_path = CACHE_DIR / "SPY_features.parquet"
    if cache_path.exists():
        return pd.read_parquet(cache_path)

    df = yf.Ticker("SPY").history(start="1993-01-01", end="2026-12-31", auto_adjust=True)
    if df is None or df.empty:
        raise ValueError("Could not fetch SPY data")

    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    df = compute_features(df)

    # SPY-specific macro features
    df['SPY_ROC20'] = df['ROC20']
    df['SPY_above_200sma'] = (df['Close'] > df['SMA200']).astype(float)
    df['SPY_above_50sma'] = (df['Close'] > df['SMA50']).astype(float)

    df.to_parquet(cache_path)
    return df


def load_vix():
    """Load VIX data."""
    cache_path = CACHE_DIR / "VIX.parquet"
    if cache_path.exists():
        return pd.read_parquet(cache_path)

    df = yf.Ticker("^VIX").history(start="1993-01-01", end="2026-12-31", auto_adjust=True)
    if df is not None and not df.empty:
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df.to_parquet(cache_path)
        return df
    return None


def load_ticker(symbol, start="2000-01-01", end="2026-04-02"):
    """Load and cache a single ticker with features."""
    cache_path = CACHE_DIR / f"{symbol}.parquet"

    if cache_path.exists():
        return pd.read_parquet(cache_path)

    try:
        df = yf.Ticker(symbol).history(start=start, end=end, auto_adjust=True)
        if df is None or len(df) < 400:
            return None

        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df = compute_features(df)

        # Add SPY and VIX data aligned to this ticker's dates
        spy = load_spy_features()
        vix = load_vix()

        if spy is not None:
            for col in ['SPY_ROC20', 'SPY_above_200sma', 'SPY_above_50sma']:
                if col in spy.columns:
                    df[col] = spy[col].reindex(df.index, method='ffill')

        if vix is not None:
            df['VIX'] = vix['Close'].reindex(df.index, method='ffill')
            df['VIX_norm'] = df['VIX'] / 50  # normalize roughly to 0-1 range

        df.to_parquet(cache_path)
        return df

    except Exception as e:
        logger.warning(f"Failed to load {symbol}: {e}")
        return None


def load_universe(ticker_file="mega_universe.json", max_tickers=None):
    """Load all tickers in the universe with features.

    Returns dict of {symbol: DataFrame}.
    """
    import orjson

    ticker_path = PROJECT_ROOT / "tickers_to_scan" / ticker_file
    with open(ticker_path, "rb") as f:
        tickers = orjson.loads(f.read())

    if max_tickers:
        tickers = tickers[:max_tickers]

    logger.info(f"Loading {len(tickers)} tickers...")
    data = {}
    for i, sym in enumerate(tickers):
        if i % 100 == 0:
            logger.info(f"  {i}/{len(tickers)} loaded ({len(data)} valid)")
        df = load_ticker(sym)
        if df is not None:
            data[sym] = df

    logger.info(f"Loaded {len(data)} / {len(tickers)} tickers")
    return data
