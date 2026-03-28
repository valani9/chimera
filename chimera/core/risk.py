"""Portfolio risk management for CHIMERA Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from chimera.models.markets import Position
from chimera.models.trades import TradeDecision


@dataclass
class PortfolioState:
    """Tracks the portfolio state across the trading session."""
    bankroll: float = 1000.0
    peak_bankroll: float = 1000.0
    total_pnl: float = 0.0
    positions: list[Position] = field(default_factory=list)
    trade_count: int = 0
    win_count: int = 0
    max_drawdown: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def win_rate(self) -> float:
        return self.win_count / self.trade_count if self.trade_count > 0 else 0.0

    @property
    def current_drawdown(self) -> float:
        if self.peak_bankroll <= 0:
            return 0.0
        return 1.0 - (self.bankroll / self.peak_bankroll)

    def update_bankroll(self, pnl: float):
        self.bankroll += pnl
        self.total_pnl += pnl
        if self.bankroll > self.peak_bankroll:
            self.peak_bankroll = self.bankroll
        dd = self.current_drawdown
        if dd > self.max_drawdown:
            self.max_drawdown = dd


def check_risk_limits(
    decision: TradeDecision,
    portfolio: PortfolioState,
    max_positions: int = 10,
    max_single_bet_pct: float = 0.10,
    max_drawdown: float = 0.25,
    min_edge: float = 0.03,
) -> tuple[bool, str]:
    """Run risk checks before executing a trade.

    Returns (allowed, reason).
    """
    # Check 1: Maximum positions
    if len(portfolio.positions) >= max_positions:
        return False, f"Max positions ({max_positions}) reached"

    # Check 2: Maximum single bet size
    if decision.bet_amount > portfolio.bankroll * max_single_bet_pct:
        return False, f"Bet ${decision.bet_amount:.2f} exceeds {max_single_bet_pct:.0%} of bankroll"

    # Check 3: Maximum drawdown
    if portfolio.current_drawdown >= max_drawdown:
        return False, f"Drawdown {portfolio.current_drawdown:.1%} exceeds limit {max_drawdown:.0%}"

    # Check 4: Minimum edge
    if decision.edge < min_edge:
        return False, f"Edge {decision.edge:.1%} below minimum {min_edge:.0%}"

    # Check 5: Bankroll floor
    if portfolio.bankroll < 50:
        return False, "Bankroll below $50 minimum"

    # Check 6: Confidence floor
    if decision.confidence < 0.3:
        return False, f"Confidence {decision.confidence:.0%} too low"

    return True, "All risk checks passed"
