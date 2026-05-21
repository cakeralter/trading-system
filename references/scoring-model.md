# Scoring Model

## Table of Contents

- Score weights
- Grade bands
- Hard filters
- Component scoring guidance
- Batch CSV fields

## Score Weights

The score measures how well a candidate fits the trading system. It is not a return forecast.

| Dimension | Points | Purpose |
|---|---:|---|
| Market environment | 20 | Decide whether the system allows active risk |
| Trend structure | 20 | Prefer non-broken, upward or constructive structures |
| Buy point quality | 20 | Reward planned pullback, breakout, reversal, or low-absorption setups |
| Risk/reward | 15 | Require first target near or above 2R |
| Volume behavior | 10 | Confirm breakout strength or pullback contraction |
| Liquidity | 5 | Avoid difficult entries/exits and excessive slippage |
| Sector/theme strength | 5 | Favor candidates aligned with persistent market leadership |
| Portfolio fit | 5 | Penalize excessive concentration or duplicated logic |
| Total | 100 | Rule-compliance score |

## Grade Bands

| Score | Grade | Meaning |
|---:|---|---|
| 85-100 | High-quality candidate | Strong fit, still requires valid execution and risk sizing |
| 70-84 | Watchlist candidate | Usable only if buy point confirms and risk stays controlled |
| 60-69 | Wait for confirmation | Conditions are incomplete or mediocre |
| Below 60 | Eliminated or low priority | Does not fit the system well enough |

## Hard Filters

Apply hard filters before ranking.

| Filter | Result |
|---|---|
| No valid stop-loss | Eliminate |
| First target below 2R | Eliminate or mark observation-only |
| Liquidity too low | Eliminate |
| Trend clearly broken | Eliminate |
| Market score below 4 with normal/aggressive sizing | Block new aggressive trade |
| Sector or logic exposure would exceed 25% | Reduce size or reject |
| User is in a circuit-breaker state | Block new trades until reset condition is met |

## Component Scoring Guidance

### Market Environment: 20

Convert market score 0-10 into points:

```text
market_points = market_score / 10 * 20
```

Market score interpretation:

| Market score | State | Action |
|---:|---|---|
| 0-3 | Weak | 0%-30% total exposure; usually no new offensive trade |
| 4-6 | Range-bound | 30%-50% total exposure; lower frequency |
| 7-10 | Strong | 50%-80% total exposure; still only planned setups |

### Trend Structure: 20

Use direct component score if the user provides `trend_score`. Otherwise derive from available data:

| Condition | Points |
|---|---:|
| Price above 20-day moving average | +7 |
| Price above 60-day moving average | +7 |
| 20-day moving average above or rising toward 60-day moving average | +3 |
| Price has not broken key support | +3 |

If price is below both 20-day and 60-day averages and support is broken, score trend low and consider hard elimination.

### Buy Point Quality: 20

Use direct `buy_point_score` when provided. Otherwise score by setup:

| Setup | Points |
|---|---:|
| Planned pullback near support, no support break | 14-18 |
| Volume breakout above resistance | 15-20 |
| Reversal after contraction and confirmation candle | 12-16 |
| Low absorption for ETF/core asset | 10-15 |
| Chasing far above support | 0-8 |

### Risk/Reward: 15

Calculate:

```text
R = abs(entry - stop_loss)
target_r = abs(first_target - entry) / R
```

| First target R | Points |
|---:|---:|
| Below 2R | 0 and hard filter |
| 2.0-2.49R | 10 |
| 2.5-2.99R | 12 |
| 3R or above | 15 |

### Volume Behavior: 10

| Condition | Points |
|---|---:|
| Breakout volume >= 1.5x 20-day average | 9-10 |
| Constructive volume >= 1.3x average | 7-8 |
| Pullback volume <= 0.8x average | 7-9 |
| Neutral volume | 4-6 |
| Breakdown or distribution volume | 0-3 |

### Liquidity, Sector, Portfolio Fit

Use user-provided score when available. Otherwise:

- Liquidity should be high enough for normal entry/exit without meaningful slippage.
- Sector/theme strength improves the score only when the theme has persisted for at least 3 trading days.
- Portfolio fit is low when the candidate duplicates an existing position or breaches sector/logic exposure limits.

## Batch CSV Fields

Recommended columns for `scripts/score_candidates.py`:

```text
symbol,name,price,entry,stop_loss,target1,ma20,ma60,volume,avg_volume_20,
support,resistance,market_score,trend_score,buy_point_score,volume_score,
liquidity_score,sector_score,portfolio_score,sector,current_sector_exposure
```

The script can derive several scores when direct component scores are missing, but better data produces better scoring.
