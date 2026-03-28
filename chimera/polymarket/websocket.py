"""Polymarket WebSocket feed for real-time price and trade updates."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Callable, Awaitable

from chimera.config import settings
from chimera.models.markets import Trade


class PolymarketWebSocket:
    """Subscribes to Polymarket's real-time WebSocket feed.

    Provides live orderbook updates and trade executions for
    monitored markets.
    """

    def __init__(self):
        self._ws = None
        self._subscribed_market_ids: set[str] = set()
        self._trade_callbacks: list[Callable[[Trade], Awaitable[None]]] = []
        self._price_callbacks: list[Callable[[str, float], Awaitable[None]]] = []
        self._running = False

    def on_trade(self, callback: Callable[[Trade], Awaitable[None]]):
        """Register a callback for new trade events."""
        self._trade_callbacks.append(callback)

    def on_price(self, callback: Callable[[str, float], Awaitable[None]]):
        """Register a callback for price updates."""
        self._price_callbacks.append(callback)

    def subscribe(self, market_id: str):
        """Add a market to the subscription list."""
        self._subscribed_market_ids.add(market_id)

    def unsubscribe(self, market_id: str):
        """Remove a market from the subscription list."""
        self._subscribed_market_ids.discard(market_id)

    async def connect(self):
        """Connect to Polymarket WebSocket and start receiving events."""
        try:
            import websockets

            self._running = True
            async with websockets.connect(settings.polymarket.ws_url) as ws:
                self._ws = ws

                # Subscribe to all monitored markets
                for market_id in self._subscribed_market_ids:
                    sub_msg = json.dumps({
                        "assets_ids": [market_id],
                        "type": "market",
                    })
                    await ws.send(sub_msg)

                # Listen for events
                while self._running:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
                        await self._handle_message(msg)
                    except asyncio.TimeoutError:
                        # Send keepalive ping
                        await ws.ping()

        except Exception as e:
            print(f"[WS] Connection error: {e}")
            self._running = False

    async def _handle_message(self, raw: str):
        """Parse and dispatch incoming WebSocket messages."""
        try:
            data = json.loads(raw)
            event_type = data.get("event_type", "")

            if event_type == "last_trade_price":
                market_id = data.get("asset_id", "")
                price = float(data.get("price", 0))
                for cb in self._price_callbacks:
                    await cb(market_id, price)

            elif event_type == "trade":
                trade = Trade(
                    market_id=data.get("market", ""),
                    price=float(data.get("price", 0)),
                    size=float(data.get("size", 0)),
                    side="buy" if data.get("side", "").upper() == "BUY" else "sell",
                    timestamp=datetime.utcnow(),
                )
                for cb in self._trade_callbacks:
                    await cb(trade)

        except Exception as e:
            print(f"[WS] Message parse error: {e}")

    async def disconnect(self):
        """Close the WebSocket connection."""
        self._running = False
        if self._ws:
            await self._ws.close()
