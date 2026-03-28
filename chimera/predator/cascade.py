"""Information cascade detection for PREDATOR subsystem.

Detects herding behavior in prediction markets where traders
follow each other rather than trading on independent information.
Cascades tend to overshoot and revert — exploitable alpha.
"""

from __future__ import annotations

from collections import deque

from chimera.config import settings
from chimera.models.markets import Trade
from chimera.models.events import Signal, SignalType, SignalSource


class CascadeDetector:
    """Detects information cascades in trade flow."""

    def __init__(self):
        self._recent_sides: deque[str] = deque(
            maxlen=settings.predator.cascade_window_trades
        )

    def add_trade(self, trade: Trade) -> Signal | None:
        """Process a trade and check for cascade formation."""
        self._recent_sides.append(trade.side)

        if len(self._recent_sides) < settings.predator.cascade_window_trades:
            return None

        score = self.compute_cascade_score()

        if score >= settings.predator.cascade_threshold:
            # Determine cascade direction
            buy_count = sum(1 for s in self._recent_sides if s == "buy")
            total = len(self._recent_sides)
            direction = "buy" if buy_count > total / 2 else "sell"

            return Signal(
                source=SignalSource.PREDATOR,
                signal_type=SignalType.CASCADE,
                score=score,
                title=f"Cascade detected: {direction}",
                detail=(
                    f"{buy_count}/{total} trades in same direction "
                    f"(score: {score:.2f}, threshold: {settings.predator.cascade_threshold})"
                ),
                data={
                    "market_id": trade.market_id,
                    "direction": direction,
                    "cascade_score": score,
                    "buy_count": buy_count,
                    "total_count": total,
                },
            )

        return None

    def compute_cascade_score(self) -> float:
        """Compute cascade score (0-1).

        Score = max(buy_ratio, sell_ratio) where ratio is the
        fraction of recent trades in one direction.

        0.5 = perfectly balanced (no cascade)
        1.0 = all trades in same direction (strong cascade)
        """
        if not self._recent_sides:
            return 0.0

        total = len(self._recent_sides)
        buy_count = sum(1 for s in self._recent_sides if s == "buy")
        buy_ratio = buy_count / total

        return max(buy_ratio, 1 - buy_ratio)

    def reset(self):
        self._recent_sides.clear()
