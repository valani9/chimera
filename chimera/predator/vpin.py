"""VPIN: Volume-Synchronized Probability of Informed Trading.

Academic reference: Easley, Lopez de Prado, O'Hara (2012)
"Flow Toxicity and Liquidity in a High-Frequency World"

VPIN measures the probability that market participants have
private information. It predicted the 2010 Flash Crash hours
in advance. We implement it for Polymarket order flow.
"""

from __future__ import annotations

import math
from collections import deque

from chimera.models.markets import Trade


class VPINCalculator:
    """Volume-synchronized probability of informed trading."""

    def __init__(self, bucket_size: int = 50, n_buckets: int = 50):
        self.bucket_size = bucket_size
        self.n_buckets = n_buckets
        self._trades: deque[Trade] = deque(maxlen=10000)
        self._buckets: deque[dict] = deque(maxlen=n_buckets)

    def add_trade(self, trade: Trade):
        """Add a trade to the stream."""
        self._trades.append(trade)
        self._try_form_bucket()

    def add_trades(self, trades: list[Trade]):
        """Add multiple trades."""
        for trade in trades:
            self._trades.append(trade)
        self._try_form_bucket()

    def _try_form_bucket(self):
        """Try to form volume buckets from accumulated trades."""
        current_volume = 0
        buy_volume = 0
        sell_volume = 0
        bucket_trades: list[Trade] = []

        for trade in self._trades:
            current_volume += trade.size
            if trade.side == "buy":
                buy_volume += trade.size
            else:
                sell_volume += trade.size
            bucket_trades.append(trade)

            if current_volume >= self.bucket_size:
                self._buckets.append({
                    "buy_volume": buy_volume,
                    "sell_volume": sell_volume,
                    "total_volume": current_volume,
                    "order_imbalance": abs(buy_volume - sell_volume),
                })
                # Reset for next bucket
                current_volume = 0
                buy_volume = 0
                sell_volume = 0
                bucket_trades = []

    def compute_vpin(self) -> float:
        """Compute current VPIN value.

        VPIN = (1/n) * sum(|V_buy_i - V_sell_i|) / V_bucket

        Returns a value between 0 and 1:
        - 0.0-0.3: Normal flow, no informed trading detected
        - 0.3-0.6: Elevated, possible informed activity
        - 0.6-1.0: High, probable informed trading
        """
        if len(self._buckets) < 2:
            return 0.0

        total_imbalance = sum(b["order_imbalance"] for b in self._buckets)
        total_volume = sum(b["total_volume"] for b in self._buckets)

        if total_volume == 0:
            return 0.0

        vpin = total_imbalance / total_volume
        return min(1.0, vpin)

    def compute_order_imbalance(self) -> float:
        """Compute directional order imbalance (-1 to +1).

        Positive = buy pressure (bullish)
        Negative = sell pressure (bearish)
        """
        if not self._buckets:
            return 0.0

        total_buy = sum(b["buy_volume"] for b in self._buckets)
        total_sell = sum(b["sell_volume"] for b in self._buckets)
        total = total_buy + total_sell

        if total == 0:
            return 0.0

        return (total_buy - total_sell) / total

    def reset(self):
        self._trades.clear()
        self._buckets.clear()
