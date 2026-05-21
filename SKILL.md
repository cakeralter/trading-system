---
name: trading-system
description: Trading system execution, candidate scoring, position sizing, risk checks, trade plan generation, holding review, and weekly/monthly trade replay based on a low-frequency swing trading framework. Use when the user asks to screen or score stocks/ETFs, evaluate whether a trade fits their system, calculate stop-loss/target/R-multiple/position size, create a pre-trade plan, review holdings, classify trade mistakes, or summarize trade records.
---

# Trading System

## Boundary

Use this skill as a rules executor, not as a promise of returns or a discretionary stock picker.

- Do not present outputs as financial advice, guaranteed signals, or instructions to buy/sell.
- Do not invent live market data. If price, volume, moving averages, sector strength, or account data are missing, ask for them or state the assumption explicitly.
- If the user asks for current or latest market data and tools are available, verify with current data before scoring.
- Keep conclusions in system language: `high-quality candidate`, `watchlist`, `wait for confirmation`, `eliminated`, `risk check failed`.

## Load References

Load only the references needed for the request:

- `references/scoring-model.md`: use for candidate screening, stock/ETF scoring, grades, hard filters, and score explanations.
- `references/risk-rules.md`: use for position sizing, stop loss, R-multiple, portfolio risk, concentration, and circuit breakers.
- `references/templates.md`: use for pre-trade plans, scoring reports, holding reviews, and weekly/monthly review outputs.
- `references/trading-system-manual.md`: use when the user asks for the full framework, detailed rule rationale, or changes to the trading system itself.

Use `scripts/score_candidates.py` for batch CSV scoring when the user provides a candidate table or asks to score many symbols deterministically.

## Workflow

### 1. Determine Task Type

Classify the request into one of these tasks:

| Task | Action |
|---|---|
| Candidate scoring | Score symbols with the scoring model; apply hard filters before ranking |
| Single trade check | Check market score, trend, buy point, stop, target, R multiple, and position size |
| Position sizing | Calculate risk-based buy amount and percent of account |
| Holding review | Calculate current R, stop/target status, moving stop, and portfolio risk |
| Trade replay | Classify mistakes, calculate R result, and identify execution errors |
| Weekly/monthly review | Calculate win rate, average win R, average loss R, expectancy, drawdown, and execution rate |
| System editing | Update rules while preserving risk boundaries and documenting the changed rule |

### 2. Validate Inputs

Before giving a scored conclusion, check whether the required inputs exist.

Minimum inputs for a single trade:

- account equity
- max account risk per trade
- symbol/name
- entry or planned buy price
- stop-loss price
- first target price
- market score or market state
- current holdings or sector exposure when portfolio risk matters

Minimum inputs for candidate scoring:

- symbol/name
- price or planned entry
- stop loss
- first target
- market score
- enough trend/volume/liquidity data to score, or explicit user-provided component scores

If inputs are incomplete, provide a partial check and list missing fields. Do not fabricate a final score when key data is absent.

### 3. Apply Hard Filters First

Eliminate or block aggressive action before scoring when any hard filter is triggered:

- no valid stop-loss level
- first target is below 2R unless the user explicitly marks it as a non-trading observation
- liquidity is too low to enter/exit normally
- trend is clearly broken
- market score is below 4 and the plan still uses normal/aggressive sizing
- sector/logic exposure would exceed the system's concentration limit
- user is in a circuit-breaker state such as consecutive losses, drawdown breach, or repeated stop-loss violation

### 4. Score and Explain

For scoring tasks, use the 100-point model in `references/scoring-model.md`.

Return:

- total score and grade
- hard filter status
- strengths
- risks
- missing data or assumptions
- trade plan draft when enough data exists
- position size when account/risk inputs exist

Avoid overprecision. Scores are rule-compliance scores, not probability forecasts.

### 5. Calculate Risk

Use the core formula from `references/risk-rules.md`:

```text
buy_amount = account_equity * max_account_risk_per_trade / stop_loss_pct
```

Also calculate:

- stop-loss percentage
- initial 1R
- first target R multiple
- worst-case loss amount
- position as a percent of account
- total theoretical portfolio loss if holding data exists

### 6. Review and Replay

For trade reviews:

- calculate realized R
- classify errors using A-G categories from `references/templates.md`
- separate normal system losses from execution errors
- identify one or two concrete rule changes or behavior constraints

For weekly/monthly reviews:

- calculate win rate
- average win R
- average loss R
- expectancy
- plan execution rate
- A-F mistake ratio
- drawdown and circuit-breaker status

## Output Discipline

Use concise, structured outputs. Prefer tables for scores and risk calculations.

End with a system-status conclusion, for example:

- `Conclusion: passes risk check; remains a watchlist candidate until buy point confirms.`
- `Conclusion: eliminated by hard filter because first target is only 1.4R.`
- `Conclusion: position size must be reduced because sector exposure would exceed 25%.`

Do not end by telling the user to buy or sell.
