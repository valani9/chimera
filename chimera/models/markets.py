"""Market and orderbook data models for Polymarket integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OrderBookLevel(BaseModel):
    price: float
    size: float


class OrderBook(BaseModel):
    market_id: str
    asset_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    bids: list[OrderBookLevel] = Field(default_factory=list)
    asks: list[OrderBookLevel] = Field(default_factory=list)
    best_bid: float = 0.0
    best_ask: float = 1.0
    mid_price: float = 0.5
    spread: float = 1.0
    total_bid_depth: float = 0.0
    total_ask_depth: float = 0.0

    def compute_metrics(self) -> None:
        if self.bids:
            self.best_bid = max(b.price for b in self.bids)
            self.total_bid_depth = sum(b.size for b in self.bids)
        if self.asks:
            self.best_ask = min(a.price for a in self.asks)
            self.total_ask_depth = sum(a.size for a in self.asks)
        if self.bids and self.asks:
            self.mid_price = (self.best_bid + self.best_ask) / 2
            self.spread = self.best_ask - self.best_bid


class Trade(BaseModel):
    market_id: str
    price: float
    size: float
    side: str  # "buy" or "sell"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Market(BaseModel):
    id: str
    condition_id: str = ""
    question: str = ""
    description: str = ""
    category: str = ""
    end_date: str = ""
    active: bool = True
    closed: bool = False
    volume_24h: float = 0.0
    liquidity: float = 0.0
    yes_price: float = 0.5
    no_price: float = 0.5
    yes_token_id: str = ""
    no_token_id: str = ""
    neg_risk: bool = False
    question_embedding: list[float] | None = None
    tags: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def display_price(self) -> float:
        return self.yes_price


class Position(BaseModel):
    market_id: str
    market_question: str = ""
    side: str  # "YES" or "NO"
    size: float = 0.0
    avg_entry_price: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    opened_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total_pnl(self) -> float:
        return self.unrealized_pnl + self.realized_pnl
