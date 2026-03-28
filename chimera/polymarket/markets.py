"""Polymarket Gamma API: Market discovery, metadata, and caching."""

from __future__ import annotations

import asyncio
from datetime import datetime

import httpx

from chimera.config import settings
from chimera.models.markets import Market, OrderBook, OrderBookLevel


class PolymarketClient:
    """Unified client for Polymarket Gamma + CLOB APIs."""

    def __init__(self):
        self.gamma_url = settings.polymarket.gamma_api_url
        self.clob_url = settings.polymarket.clob_api_url
        self._http = httpx.AsyncClient(timeout=30.0)
        self._market_cache: dict[str, Market] = {}

    async def close(self):
        await self._http.aclose()

    # ── Gamma API: Market Discovery ──

    async def fetch_active_markets(self, limit: int = 100) -> list[Market]:
        """Fetch active markets from Gamma API."""
        markets = []
        try:
            resp = await self._http.get(
                f"{self.gamma_url}/markets",
                params={"limit": limit, "active": True, "closed": False},
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data:
                market = self._parse_market(item)
                if market:
                    markets.append(market)
                    self._market_cache[market.id] = market
        except Exception as e:
            print(f"[POLYMARKET] Error fetching markets: {e}")

        return markets

    async def fetch_market(self, market_id: str) -> Market | None:
        """Fetch a single market by ID."""
        if market_id in self._market_cache:
            return self._market_cache[market_id]

        try:
            resp = await self._http.get(f"{self.gamma_url}/markets/{market_id}")
            resp.raise_for_status()
            market = self._parse_market(resp.json())
            if market:
                self._market_cache[market.id] = market
            return market
        except Exception as e:
            print(f"[POLYMARKET] Error fetching market {market_id}: {e}")
            return None

    async def search_markets(self, query: str, limit: int = 20) -> list[Market]:
        """Search markets by keyword."""
        try:
            resp = await self._http.get(
                f"{self.gamma_url}/markets",
                params={"limit": limit, "active": True, "closed": False},
            )
            resp.raise_for_status()
            data = resp.json()

            query_lower = query.lower()
            results = []
            for item in data:
                question = item.get("question", "").lower()
                if query_lower in question:
                    market = self._parse_market(item)
                    if market:
                        results.append(market)
            return results
        except Exception as e:
            print(f"[POLYMARKET] Search error: {e}")
            return []

    # ── CLOB API: Orderbook & Pricing ──

    async def fetch_orderbook(self, token_id: str) -> OrderBook | None:
        """Fetch orderbook from CLOB API for a specific token."""
        try:
            resp = await self._http.get(
                f"{self.clob_url}/book",
                params={"token_id": token_id},
            )
            resp.raise_for_status()
            data = resp.json()

            ob = OrderBook(
                market_id=data.get("market", ""),
                asset_id=data.get("asset_id", token_id),
                bids=[OrderBookLevel(price=float(b["price"]), size=float(b["size"])) for b in data.get("bids", [])],
                asks=[OrderBookLevel(price=float(a["price"]), size=float(a["size"])) for a in data.get("asks", [])],
            )
            ob.compute_metrics()
            return ob
        except Exception as e:
            print(f"[POLYMARKET] Orderbook error for {token_id}: {e}")
            return None

    async def fetch_price(self, token_id: str) -> float | None:
        """Fetch current mid price for a token."""
        try:
            resp = await self._http.get(
                f"{self.clob_url}/midpoint",
                params={"token_id": token_id},
            )
            resp.raise_for_status()
            data = resp.json()
            return float(data.get("mid", 0.5))
        except Exception:
            return None

    async def fetch_price_history(
        self, token_id: str, interval: str = "1d", fidelity: int = 60
    ) -> list[dict]:
        """Fetch price history for a token."""
        try:
            resp = await self._http.get(
                f"{self.clob_url}/prices-history",
                params={
                    "market": token_id,
                    "interval": interval,
                    "fidelity": fidelity,
                },
            )
            resp.raise_for_status()
            return resp.json().get("history", [])
        except Exception:
            return []

    # ── Helpers ──

    def _parse_market(self, item: dict) -> Market | None:
        """Parse a Gamma API market response into our Market model."""
        try:
            tokens = item.get("tokens", [])
            yes_token = next((t for t in tokens if t.get("outcome", "").lower() == "yes"), None)
            no_token = next((t for t in tokens if t.get("outcome", "").lower() == "no"), None)

            return Market(
                id=str(item.get("id", "")),
                condition_id=item.get("conditionId", item.get("condition_id", "")),
                question=item.get("question", ""),
                description=item.get("description", ""),
                category=item.get("category", ""),
                end_date=item.get("endDate", item.get("end_date", "")),
                active=item.get("active", True),
                closed=item.get("closed", False),
                volume_24h=float(item.get("volume24hr", item.get("volume_24h", 0)) or 0),
                liquidity=float(item.get("liquidity", 0) or 0),
                yes_price=float(yes_token.get("price", 0.5)) if yes_token else 0.5,
                no_price=float(no_token.get("price", 0.5)) if no_token else 0.5,
                yes_token_id=yes_token.get("token_id", "") if yes_token else "",
                no_token_id=no_token.get("token_id", "") if no_token else "",
                neg_risk=item.get("neg_risk", False),
                tags=item.get("tags", []) or [],
                raw=item,
            )
        except Exception as e:
            print(f"[POLYMARKET] Parse error: {e}")
            return None

    def get_cached_markets(self) -> list[Market]:
        """Return all cached markets."""
        return list(self._market_cache.values())

    def get_cached_market(self, market_id: str) -> Market | None:
        return self._market_cache.get(market_id)
