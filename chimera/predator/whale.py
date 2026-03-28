"""Whale detection for PREDATOR subsystem.

Detects unusually large orders that indicate institutional or
informed trader activity.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta

from chimera.config import settings
from chimera.models.markets import Trade
from chimera.models.events import Signal, SignalType, SignalSource


class WhaleDetector:
    """Detects whale (large) orders in the trade stream."""

    def __init__(self):
        self._trade_history: deque[Trade] = deque(maxlen=5000)
        self._whale_alerts: list[Signal] = []

    def add_trade(self, trade: Trade) -> Signal | None:
        """Process a trade and check if it's a whale order."""
        self._trade_history.append(trade)

        # Calculate running average trade size
        avg_size = self._get_average_size()
        if avg_size <= 0:
            return None

        threshold = avg_size * (1.0 / settings.predator.whale_threshold_pct)

        if trade.size >= threshold:
            signal = Signal(
                source=SignalSource.PREDATOR,
                signal_type=SignalType.WHALE_MOVE,
                score=min(1.0, trade.size / (threshold * 3)),
                title=f"Whale {trade.side}: ${trade.size:,.0f}",
                detail=(
                    f"Large {trade.side} order of ${trade.size:,.0f} "
                    f"({trade.size / avg_size:.1f}x average) "
                    f"@ {trade.price:.3f}"
                ),
                data={
                    "market_id": trade.market_id,
                    "side": trade.side,
                    "size": trade.size,
                    "price": trade.price,
                    "vs_average": trade.size / avg_size,
                },
            )
            self._whale_alerts.append(signal)
            return signal

        return None

    def get_whale_consensus(self, window_minutes: int = 30) -> dict:
        """Analyze recent whale activity for directional consensus.

        Returns dict with:
        - direction: "buy", "sell", or "mixed"
        - whale_count: number of whale orders
        - total_volume: total whale volume
        - buy_pct: percentage of whale volume that's buying
        """
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_whales = [
            s for s in self._whale_alerts
            if s.timestamp >= cutoff
        ]

        if not recent_whales:
            return {"direction": "neutral", "whale_count": 0, "total_volume": 0, "buy_pct": 0.5}

        buy_vol = sum(s.data["size"] for s in recent_whales if s.data.get("side") == "buy")
        sell_vol = sum(s.data["size"] for s in recent_whales if s.data.get("side") == "sell")
        total = buy_vol + sell_vol
        buy_pct = buy_vol / total if total > 0 else 0.5

        if buy_pct > 0.65:
            direction = "buy"
        elif buy_pct < 0.35:
            direction = "sell"
        else:
            direction = "mixed"

        return {
            "direction": direction,
            "whale_count": len(recent_whales),
            "total_volume": total,
            "buy_pct": buy_pct,
        }

    def _get_average_size(self) -> float:
        if not self._trade_history:
            return 0.0
        return sum(t.size for t in self._trade_history) / len(self._trade_history)

    def get_alerts(self) -> list[Signal]:
        return list(self._whale_alerts)
