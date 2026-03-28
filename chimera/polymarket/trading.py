"""Polymarket CLOB trading: order placement and management."""

from __future__ import annotations

from chimera.config import settings
from chimera.models.trades import TradeDecision, Execution


class TradeExecutor:
    """Handles trade execution via Polymarket CLOB API.

    Supports both paper trading (simulation) and live trading.
    """

    def __init__(self, paper_trading: bool = True):
        self.paper_trading = paper_trading
        self._clob_client = None
        self._execution_log: list[Execution] = []

    def _init_clob_client(self):
        """Initialize the py-clob-client (lazy, only when needed for live trading)."""
        if self._clob_client is not None:
            return

        if self.paper_trading:
            return

        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import ApiCreds

            creds = ApiCreds(
                api_key=settings.polymarket_api_key,
                api_secret=settings.polymarket_secret,
                api_passphrase=settings.polymarket_passphrase,
            )
            self._clob_client = ClobClient(
                settings.polymarket.clob_api_url,
                key=settings.private_key,
                chain_id=137,  # Polygon mainnet
                creds=creds,
            )
        except Exception as e:
            print(f"[EXECUTOR] Failed to init CLOB client: {e}")
            self.paper_trading = True

    async def execute(self, decision: TradeDecision) -> Execution:
        """Execute a trade decision."""
        if decision.direction == "HOLD":
            return Execution(
                trade_decision=decision,
                status="cancelled",
                error="HOLD signal — no trade",
            )

        if self.paper_trading:
            return self._simulate_execution(decision)

        return await self._live_execution(decision)

    def _simulate_execution(self, decision: TradeDecision) -> Execution:
        """Paper trade: simulate fill at market price."""
        execution = Execution(
            trade_decision=decision,
            order_id=f"SIM-{decision.market_id[:8]}",
            fill_price=decision.market_price,
            fill_size=decision.bet_amount / decision.market_price if decision.market_price > 0 else 0,
            status="simulated",
        )
        self._execution_log.append(execution)
        print(
            f"[EXECUTOR] PAPER TRADE: {decision.direction} ${decision.bet_amount:.2f} "
            f"on '{decision.market_question[:50]}' @ {decision.market_price:.3f} "
            f"(edge: {decision.edge:.1%})"
        )
        return execution

    async def _live_execution(self, decision: TradeDecision) -> Execution:
        """Live trade via py-clob-client."""
        self._init_clob_client()

        if self._clob_client is None:
            return Execution(
                trade_decision=decision,
                status="cancelled",
                error="CLOB client not available",
            )

        try:
            from py_clob_client.clob_types import OrderArgs, OrderType
            from py_clob_client.order_builder.constants import BUY, SELL

            # Determine token and side
            if decision.direction == "YES":
                token_id = decision.market_id  # YES token
                side = BUY
            else:
                token_id = decision.market_id  # NO token
                side = BUY

            # Place limit order slightly above mid for fill probability
            limit_price = decision.market_price + 0.02

            order_args = OrderArgs(
                price=limit_price,
                size=decision.bet_amount / limit_price,
                side=side,
                token_id=token_id,
            )

            signed_order = self._clob_client.create_order(order_args)
            resp = self._clob_client.post_order(signed_order, OrderType.GTC)

            execution = Execution(
                trade_decision=decision,
                order_id=resp.get("orderID", ""),
                fill_price=limit_price,
                fill_size=decision.bet_amount / limit_price,
                status="pending",
            )
            self._execution_log.append(execution)
            return execution

        except Exception as e:
            return Execution(
                trade_decision=decision,
                status="cancelled",
                error=str(e),
            )

    def get_execution_log(self) -> list[Execution]:
        return list(self._execution_log)

    def get_total_pnl(self) -> float:
        return sum(
            e.trade_decision.bet_amount * e.trade_decision.edge
            for e in self._execution_log
            if e.status in ("filled", "simulated")
        )
