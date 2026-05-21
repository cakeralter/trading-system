# Risk Rules

## Table of Contents

- Core formulas
- Personal risk profiles
- Position sizing
- Stop-loss rules
- Portfolio limits
- Circuit breakers

## Core Formulas

```text
stop_loss_pct = abs(entry - stop_loss) / entry
initial_1R = abs(entry - stop_loss)
target_r = abs(first_target - entry) / initial_1R
buy_amount = account_equity * max_account_risk_per_trade / stop_loss_pct
worst_case_loss = buy_amount * stop_loss_pct
position_pct = buy_amount / account_equity
```

If `stop_loss_pct` is zero or negative, the trade is invalid.

## Personal Risk Profiles

| Parameter | Conservative | Balanced | Aggressive |
|---|---:|---:|---:|
| Max account risk per trade | 0.3%-0.5% | 0.5%-1% | 1%-1.5% |
| Max daily loss | 1% | 1.5% | 2% |
| Max weekly loss | 2% | 3% | 4% |
| Monthly warning drawdown | 3% | 5% | 8% |
| Monthly forced reduction drawdown | 5% | 8% | 10% |

Use balanced defaults unless the user specifies otherwise.

## Position Sizing

Risk-based sizing is mandatory:

```text
buy_amount = account_equity * max_account_risk_per_trade / stop_loss_pct
```

Then apply symbol-type caps:

| Type | Position cap | Risk suggestion |
|---|---:|---:|
| Broad ETF | 10%-20% | 0.3%-0.8% |
| Sector ETF | 5%-15% | 0.5%-1% |
| Leading stock | 5%-15% | 0.5%-1% |
| High-volatility stock | 3%-8% | 0.3%-0.8% |
| Test position | 2%-5% | 0.2%-0.5% |

If calculated size exceeds the cap, reduce to the cap. If calculated size is too small to matter, the stop is too wide or the setup is not efficient.

## Stop-Loss Rules

| Type | Typical stop range | Rule |
|---|---:|---|
| Broad ETF | 3%-5% | Reduce/exit at planned risk level |
| Sector ETF | 5%-8% | Execute at planned stop |
| Stable stock | 5%-8% | Execute on technical break or risk limit |
| High-volatility stock | 7%-10% | Reduce size rather than expanding risk |
| Test position | 3%-5% | Exit quickly when wrong |

Technical stops take priority when they better represent strategy invalidation:

- key support break
- 20-day moving average break that cannot recover
- high-volume breakdown candle
- buy thesis invalidated
- market risk overrides individual thesis

## Portfolio Limits

| Risk item | Limit |
|---|---:|
| Same sector | <= 25% of account equity |
| Same logic/theme | <= 25% of account equity |
| High-volatility sector | <= 15%-20% |
| Total theoretical loss if all stops hit | <= 3%-5% of account equity |
| Same sector/theme theoretical loss | <= 1.5%-2% of account equity |
| One-day new exposure | <= 20% of account equity |

When holdings are available, calculate total theoretical loss rather than only checking position percentages.

## Circuit Breakers

| Trigger | Action |
|---|---|
| Single-day loss > 1.5% | Stop new entries that day |
| 3 consecutive losing trades | Stop new entries for 3 trading days |
| Weekly loss > 3% | Cap next week's total exposure at 30% |
| Monthly drawdown > 5% | Cap total exposure at 20% |
| Monthly drawdown > 8% | Pause new real-money entries; review at least 20 historical trades |
| 2 missed stop-loss executions | Pause trading until cause and corrective rule are written |

Circuit breakers override attractive setups.
