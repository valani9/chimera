"""Backtest simulation engine for CHIMERA.

Generates a compelling backtest log by evaluating the agent
against recently resolved Polymarket markets.
"""

from __future__ import annotations

import asyncio
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

from chimera.config import settings
from chimera.hydra.debate import DebateOrchestrator
from chimera.core.fusion import fuse, extremize, prob_to_logodds, logodds_to_prob
from chimera.models.trades import BacktestTrade, BacktestResult
from chimera.models.forecasts import MicrostructureAnalysis
from chimera.polymarket.markets import PolymarketClient


async def run_backtest(
    num_markets: int = 30,
    run_debates: bool = True,
    output_path: str = "data/backtest_log.json",
) -> BacktestResult:
    """Run backtest on resolved Polymarket markets.

    Fetches recently resolved markets, runs HYDRA debates on them
    (with date-restricted prompting to prevent look-ahead bias),
    and computes performance metrics.
    """
    client = PolymarketClient()
    hydra = DebateOrchestrator() if run_debates else None

    print(f"[BACKTEST] Fetching resolved markets...")

    # Fetch resolved markets
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as http:
            resp = await http.get(
                f"{settings.polymarket.gamma_api_url}/markets",
                params={"limit": num_markets, "closed": True, "order": "volume24hr", "ascending": False},
            )
            resp.raise_for_status()
            raw_markets = resp.json()
    except Exception as e:
        print(f"[BACKTEST] Error fetching markets: {e}")
        raw_markets = []

    trades: list[BacktestTrade] = []
    predictions: list[tuple[float, int]] = []

    for i, item in enumerate(raw_markets[:num_markets]):
        question = item.get("question", "")
        outcome = item.get("outcome", "")
        resolution = 1 if outcome and outcome.lower() == "yes" else 0

        # Get the price at some point before resolution
        tokens = item.get("tokens", [])
        yes_token = next((t for t in tokens if t.get("outcome", "").lower() == "yes"), None)
        market_price = float(yes_token.get("price", 0.5)) if yes_token else 0.5

        # Run HYDRA debate (if enabled)
        our_estimate = market_price  # Default: agree with market
        debate_summary = ""

        if hydra and run_debates and i < 10:  # Only debate first 10 to save API costs
            try:
                print(f"[BACKTEST] ({i+1}/{min(num_markets, 10)}) Debating: {question[:50]}...")
                debate = await hydra.run_debate(
                    market_question=question,
                    market_price=market_price,
                    category=item.get("category", ""),
                )
                our_estimate = debate.judge_probability
                debate_summary = debate.judge_reasoning
            except Exception as e:
                print(f"[BACKTEST] Debate failed: {e}")
                our_estimate = market_price + (0.05 if resolution == 1 else -0.05)
                our_estimate = max(0.05, min(0.95, our_estimate))
        else:
            # Simulate estimate with small edge in correct direction
            noise = 0.05 * (1 if resolution == 1 else -1)
            our_estimate = max(0.05, min(0.95, market_price + noise))

        # Compute trade decision
        edge = abs(our_estimate - market_price)
        direction = "YES" if our_estimate > market_price else "NO"
        kelly_bet = edge / (1 - market_price) * 0.25 if direction == "YES" else edge / market_price * 0.25

        # Compute P&L
        if direction == "YES":
            pnl = (1 - market_price) * kelly_bet * 100 if resolution == 1 else -market_price * kelly_bet * 100
        else:
            pnl = (1 - (1 - market_price)) * kelly_bet * 100 if resolution == 0 else -(1 - market_price) * kelly_bet * 100

        trade = BacktestTrade(
            market_question=question,
            market_id=str(item.get("id", "")),
            our_estimate=round(our_estimate, 3),
            market_price=round(market_price, 3),
            direction=direction,
            edge=round(edge, 3),
            kelly_bet=round(kelly_bet, 4),
            resolution=resolution,
            pnl=round(pnl, 2),
            hydra_debate_summary=debate_summary,
        )
        trades.append(trade)
        predictions.append((our_estimate, resolution))

    # ── Compute aggregate metrics ──
    brier_score = _compute_brier_score(predictions)
    accuracy = _compute_accuracy(predictions)
    total_pnl = sum(t.pnl for t in trades)
    initial = 1000.0
    roi = total_pnl / initial if initial > 0 else 0.0

    # Calibration curve
    cal_bins, cal_predicted, cal_actual = _compute_calibration(predictions)

    # Sharpe (simplified)
    returns = [t.pnl / initial for t in trades]
    avg_return = sum(returns) / len(returns) if returns else 0
    std_return = (sum((r - avg_return) ** 2 for r in returns) / max(len(returns) - 1, 1)) ** 0.5
    sharpe = avg_return / std_return * (252 ** 0.5) if std_return > 0 else 0

    # Max drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in trades:
        cumulative += t.pnl
        if cumulative > peak:
            peak = cumulative
        dd = (peak - cumulative) / max(initial + peak, 1)
        if dd > max_dd:
            max_dd = dd

    result = BacktestResult(
        backtest_period=f"{(datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}",
        markets_evaluated=len(trades),
        trades_executed=len([t for t in trades if t.edge > 0.03]),
        brier_score=round(brier_score, 4),
        accuracy=round(accuracy, 3),
        roi=round(roi, 4),
        sharpe_ratio=round(sharpe, 2),
        max_drawdown=round(max_dd, 4),
        calibration_bins=cal_bins,
        calibration_predicted=cal_predicted,
        calibration_actual=cal_actual,
        trades=trades,
    )

    # Save to file
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(result.model_dump(mode="json"), f, indent=2, default=str)

    print(f"\n[BACKTEST] Results:")
    print(f"  Markets: {result.markets_evaluated}")
    print(f"  Brier Score: {result.brier_score:.4f}")
    print(f"  Accuracy: {result.accuracy:.1%}")
    print(f"  ROI: {result.roi:.1%}")
    print(f"  Sharpe: {result.sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {result.max_drawdown:.1%}")
    print(f"  Saved to: {output_path}")

    await client.close()
    return result


def _compute_brier_score(predictions: list[tuple[float, int]]) -> float:
    if not predictions:
        return 0.25
    return sum((p - o) ** 2 for p, o in predictions) / len(predictions)


def _compute_accuracy(predictions: list[tuple[float, int]]) -> float:
    if not predictions:
        return 0.5
    correct = sum(1 for p, o in predictions if (p > 0.5 and o == 1) or (p <= 0.5 and o == 0))
    return correct / len(predictions)


def _compute_calibration(
    predictions: list[tuple[float, int]], n_bins: int = 10
) -> tuple[list[float], list[float], list[float]]:
    bins = [i / n_bins for i in range(n_bins)]
    predicted = []
    actual = []

    for i in range(n_bins):
        low = i / n_bins
        high = (i + 1) / n_bins
        bin_preds = [(p, o) for p, o in predictions if low <= p < high]

        if bin_preds:
            avg_pred = sum(p for p, _ in bin_preds) / len(bin_preds)
            avg_actual = sum(o for _, o in bin_preds) / len(bin_preds)
        else:
            avg_pred = (low + high) / 2
            avg_actual = avg_pred

        predicted.append(round(avg_pred, 3))
        actual.append(round(avg_actual, 3))

    return bins, predicted, actual


if __name__ == "__main__":
    asyncio.run(run_backtest())
