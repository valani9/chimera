"""Trade execution wrapper combining risk checks + Polymarket trading."""

from __future__ import annotations

from chimera.core.risk import PortfolioState, check_risk_limits
from chimera.models.trades import TradeDecision, Execution
from chimera.polymarket.trading import TradeExecutor


class ChimeraExecutor:
    """Full execution pipeline: risk checks → order placement → logging."""

    def __init__(self, paper_trading: bool = True):
        self.trader = TradeExecutor(paper_trading=paper_trading)
        self.portfolio = PortfolioState()
        self._execution_log: list[Execution] = []

    async def execute(self, decision: TradeDecision) -> Execution:
        """Execute a trade decision with full risk management."""
        if decision.direction == "HOLD":
            return Execution(
                trade_decision=decision,
                status="cancelled",
                error="HOLD — no trade",
            )

        # Risk checks
        allowed, reason = check_risk_limits(decision, self.portfolio)
        if not allowed:
            print(f"[EXECUTOR] BLOCKED: {reason}")
            return Execution(
                trade_decision=decision,
                status="cancelled",
                error=f"Risk check failed: {reason}",
            )

        # Execute
        execution = await self.trader.execute(decision)
        self._execution_log.append(execution)

        if execution.status in ("filled", "simulated"):
            self.portfolio.trade_count += 1
            # Update bankroll (simulated P&L)
            self.portfolio.update_bankroll(-decision.bet_amount)  # Cost of trade

        return execution

    def get_portfolio_summary(self) -> dict:
        return {
            "bankroll": self.portfolio.bankroll,
            "total_pnl": self.portfolio.total_pnl,
            "trade_count": self.portfolio.trade_count,
            "win_rate": self.portfolio.win_rate,
            "max_drawdown": self.portfolio.max_drawdown,
            "current_drawdown": self.portfolio.current_drawdown,
            "active_positions": len(self.portfolio.positions),
        }

    def get_execution_log(self) -> list[Execution]:
        return list(self._execution_log)
