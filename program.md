# Trading Strategy Optimization — Beat VOO

## Goal

Find a trading strategy that BEATS VOO (S&P 500 buy-and-hold) every month.
Not just overall return — beat it EVERY MONTH. When VOO goes up, match it.
When VOO goes down, beat it by losing less or making money.

## Metric: Regret vs Best-of-Both

```
For each month:
  regret = max(0, voo_return - my_return)
  
score = total_return - (sum_of_monthly_regret × 500)

Beat VOO in a month: regret = 0 (perfect)
Trail VOO by 5%: regret = 5% (heavily penalized)
Sit in cash during bull month: massive regret
Sit in cash during crash: zero regret (you beat VOO)
```

## What To Modify

The strategy file: `custom_strategies/sma_crossovers.py`
The config: `config.py` (allocation, stop loss, etc.)

## Universe

3,589 tickers (mega_universe.json): S&P 500 + Russell 2000/3000 + Nasdaq + 
inverse ETFs + commodities + bonds + volatility products.

## What Champions Actually Do (READ THIS)

The best traders (US Investing Championship winners) consistently beat the 
market with these principles:

**Stock Selection (80% of the edge):**
- Only buy stocks with ACCELERATING quarterly earnings (EPS growth increasing)
- Buy leaders in leading sectors (relative strength > 80)
- Buy stocks near 52-week highs, not beaten-down losers
- Buy stocks in stage 2 uptrends (price > 50 SMA > 200 SMA)

**Risk Management:**
- Cut losses at 6-8% with no exceptions
- No single position > 7% of portfolio
- Max 1% of total capital at risk per trade

**Regime Awareness:**
- Don't trade when the broad market is below 200 SMA
- Reduce exposure when VIX is elevated
- Be fully invested in confirmed uptrends — don't sit in cash during bull markets

**Key Insight: The best traders are FULLY INVESTED during bull markets.**
Sitting in cash is the biggest mistake — it creates massive regret vs VOO.
They beat VOO by being in BETTER stocks than the index, not by timing 
entries and exits on the index itself.

## The Fundamental Data

Quarterly earnings data is cached in `data_cache/fundamentals/` for all tickers.
Use `from helpers.fundamentals import enrich_with_fundamentals` to add 
earnings columns to any ticker's DataFrame:
- Revenue_QoQ, Revenue_YoY, Revenue_Acceleration
- EPS_QoQ, EPS_YoY, EPS_Acceleration  
- ProfitMargin, Margin_Change
- EarningsAccelerating (bool), MarginsExpanding (bool)
- Sector, Industry

## Evaluation

```bash
bash eval/eval.sh
```

Score is printed to stdout. Higher is better. VOO baseline is approximately 0
(matching VOO = zero regret but zero excess return).

## Strategy Ideas to Explore

1. Earnings momentum — only buy stocks where EPS growth is accelerating
2. Sector rotation — overweight leading sectors, underweight lagging
3. Full investment in uptrends — don't sit in cash when market is bullish
4. Inverse ETF rotation in bear markets — make money when market drops
5. Stage 2 filter — only buy stocks in confirmed uptrends
6. Relative strength ranking — buy the strongest stocks, not the cheapest
7. Combine fundamentals + technicals (what the champions do)
