#!/usr/bin/env python3
"""Score stock/ETF candidates against the trading-system rules.

This script intentionally scores rule compliance, not expected returns.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


WEIGHTS = {
    "market": 20.0,
    "trend": 20.0,
    "buy_point": 20.0,
    "risk_reward": 15.0,
    "volume": 10.0,
    "liquidity": 5.0,
    "sector": 5.0,
    "portfolio": 5.0,
}


def as_float(row: dict[str, str], key: str, default: float | None = None) -> float | None:
    value = row.get(key, "")
    if value is None:
        return default
    value = str(value).strip().replace("%", "")
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def scaled_component(row: dict[str, str], key: str, weight: float) -> float | None:
    raw = as_float(row, key)
    if raw is None:
        return None
    if raw <= weight:
        return clamp(raw, 0.0, weight)
    return clamp(raw / 100.0 * weight, 0.0, weight)


def derive_market(row: dict[str, str]) -> float:
    score = as_float(row, "market_score")
    if score is None:
        return 10.0
    return clamp(score, 0.0, 10.0) / 10.0 * WEIGHTS["market"]


def derive_trend(row: dict[str, str]) -> float:
    explicit = scaled_component(row, "trend_score", WEIGHTS["trend"])
    if explicit is not None:
        return explicit

    price = as_float(row, "price", as_float(row, "entry"))
    ma20 = as_float(row, "ma20")
    ma60 = as_float(row, "ma60")
    support = as_float(row, "support")

    points = 0.0
    if price is not None and ma20 is not None and price >= ma20:
        points += 7
    if price is not None and ma60 is not None and price >= ma60:
        points += 7
    if ma20 is not None and ma60 is not None and ma20 >= ma60:
        points += 3
    if price is not None and support is not None and price >= support:
        points += 3
    if all(v is None for v in (ma20, ma60, support)):
        return 10.0
    return clamp(points, 0.0, WEIGHTS["trend"])


def derive_buy_point(row: dict[str, str]) -> float:
    explicit = scaled_component(row, "buy_point_score", WEIGHTS["buy_point"])
    if explicit is not None:
        return explicit

    setup = row.get("setup", row.get("buy_type", "")).strip().lower()
    if "break" in setup or "突破" in setup:
        return 16.0
    if "pullback" in setup or "回踩" in setup:
        return 15.0
    if "reversal" in setup or "止跌" in setup:
        return 13.0
    if "low" in setup or "低吸" in setup:
        return 12.0
    return 10.0


def derive_volume(row: dict[str, str]) -> float:
    explicit = scaled_component(row, "volume_score", WEIGHTS["volume"])
    if explicit is not None:
        return explicit

    volume = as_float(row, "volume")
    avg = as_float(row, "avg_volume_20")
    if volume is None or avg in (None, 0):
        return 5.0
    ratio = volume / avg
    if ratio >= 1.5:
        return 10.0
    if ratio >= 1.3:
        return 8.0
    if ratio <= 0.8:
        return 7.0
    return 5.0


def derive_risk_reward(row: dict[str, str]) -> tuple[float, float | None, float | None]:
    entry = as_float(row, "entry", as_float(row, "price"))
    stop = as_float(row, "stop_loss", as_float(row, "stop"))
    target = as_float(row, "target1", as_float(row, "first_target"))
    if entry is None or stop is None or target is None or entry == stop:
        return 0.0, None, None
    one_r = abs(entry - stop)
    target_r = abs(target - entry) / one_r if one_r else None
    if target_r is None:
        return 0.0, one_r, None
    if target_r < 2:
        points = 0.0
    elif target_r < 2.5:
        points = 10.0
    elif target_r < 3:
        points = 12.0
    else:
        points = 15.0
    return points, one_r, target_r


def component(row: dict[str, str], key: str, weight: float, default: float) -> float:
    return scaled_component(row, key, weight) if scaled_component(row, key, weight) is not None else default


def grade(score: float) -> str:
    if score >= 85:
        return "high-quality candidate"
    if score >= 70:
        return "watchlist candidate"
    if score >= 60:
        return "wait for confirmation"
    return "eliminated or low priority"


def score_row(row: dict[str, str], account: float | None, risk_pct: float | None) -> dict[str, Any]:
    market_points = derive_market(row)
    trend_points = derive_trend(row)
    buy_point_points = derive_buy_point(row)
    risk_reward_points, one_r, target_r = derive_risk_reward(row)
    volume_points = derive_volume(row)
    liquidity_points = component(row, "liquidity_score", WEIGHTS["liquidity"], 3.0)
    sector_points = component(row, "sector_score", WEIGHTS["sector"], 3.0)
    portfolio_points = component(row, "portfolio_score", WEIGHTS["portfolio"], 3.0)

    total = sum(
        [
            market_points,
            trend_points,
            buy_point_points,
            risk_reward_points,
            volume_points,
            liquidity_points,
            sector_points,
            portfolio_points,
        ]
    )

    entry = as_float(row, "entry", as_float(row, "price"))
    stop = as_float(row, "stop_loss", as_float(row, "stop"))
    market_score = as_float(row, "market_score")
    exposure = as_float(row, "current_sector_exposure")

    flags: list[str] = []
    if stop is None:
        flags.append("no valid stop-loss")
    if target_r is None:
        flags.append("cannot calculate target R")
    elif target_r < 2:
        flags.append("first target below 2R")
    if liquidity_points <= 1:
        flags.append("liquidity too low")
    if trend_points <= 5:
        flags.append("trend likely broken")
    if market_score is not None and market_score < 4:
        flags.append("weak market; no aggressive new trade")
    if exposure is not None and exposure > 25:
        flags.append("sector exposure above 25%")

    suggested_buy_amount = None
    position_pct = None
    worst_case_loss = None
    if account and risk_pct and entry and stop and entry != 0:
        stop_loss_pct = abs(entry - stop) / entry
        if stop_loss_pct > 0:
            suggested_buy_amount = account * risk_pct / stop_loss_pct
            position_pct = suggested_buy_amount / account * 100
            worst_case_loss = suggested_buy_amount * stop_loss_pct

    return {
        "symbol": row.get("symbol", ""),
        "name": row.get("name", ""),
        "total_score": round(total, 2),
        "grade": grade(total),
        "hard_filters": "; ".join(flags),
        "market_points": round(market_points, 2),
        "trend_points": round(trend_points, 2),
        "buy_point_points": round(buy_point_points, 2),
        "risk_reward_points": round(risk_reward_points, 2),
        "volume_points": round(volume_points, 2),
        "liquidity_points": round(liquidity_points, 2),
        "sector_points": round(sector_points, 2),
        "portfolio_points": round(portfolio_points, 2),
        "initial_1r": round(one_r, 4) if one_r is not None else "",
        "target_r": round(target_r, 2) if target_r is not None and math.isfinite(target_r) else "",
        "suggested_buy_amount": round(suggested_buy_amount, 2) if suggested_buy_amount is not None else "",
        "position_pct": round(position_pct, 2) if position_pct is not None else "",
        "worst_case_loss": round(worst_case_loss, 2) if worst_case_loss is not None else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score candidates under trading-system rules.")
    parser.add_argument("input_csv", help="Candidate CSV path")
    parser.add_argument("--output", "-o", help="Output CSV path. Defaults to stdout.")
    parser.add_argument("--account", type=float, help="Account equity for position sizing")
    parser.add_argument(
        "--risk",
        type=float,
        default=None,
        help="Max account risk per trade as decimal or percent. Examples: 0.01 or 1",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of CSV")
    args = parser.parse_args()

    risk_pct = args.risk
    if risk_pct is not None and risk_pct >= 1:
        risk_pct = risk_pct / 100.0

    with Path(args.input_csv).open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    scored = [score_row(row, args.account, risk_pct) for row in rows]
    scored.sort(key=lambda item: item["total_score"], reverse=True)

    if args.json:
        output = json.dumps(scored, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 0

    fieldnames = list(scored[0].keys()) if scored else []
    if args.output:
        with Path(args.output).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(scored)
    else:
        writer = csv.DictWriter(__import__("sys").stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(scored)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
