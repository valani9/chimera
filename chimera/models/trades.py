"""Trade decision and execution data models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TradeDecision(BaseModel):
    market_id: str
    market_question: str = ""
    direction: Literal["YES", "NO", "HOLD"]
    estimated_probability: float
    market_price: float
    edge: float
    kelly_fraction: float
    bet_amount: float
    confidence: float
    rationale: str = ""
    signals_used: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Fusion breakdown (for waterfall display)
    hydra_probability: float = 0.5
    predator_signal: float = 0.5
    ripple_adjustment: float = 0.0
    raw_aggregate: float = 0.5
    extremized_probability: float = 0.5


class Execution(BaseModel):
    trade_decision: TradeDecision
    order_id: str = ""
    fill_price: float | None = None
    fill_size: float | None = None
    status: Literal["pending", "filled", "partial", "cancelled", "simulated"] = "pending"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: str = ""


class WaterfallStep(BaseModel):
    """A single step in the reasoning waterfall for dashboard display."""
    id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    phase: Literal["ORACLE", "HYDRA", "RIPPLE", "PREDATOR", "FUSION", "EXECUTE"]
    title: str
    detail: str = ""
    probability: float | None = None  # current estimate after this step
    probability_delta: float | None = None  # change from previous
    confidence: float | None = None
    metadata: dict = Field(default_factory=dict)


class BacktestTrade(BaseModel):
    market_question: str
    market_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    our_estimate: float
    market_price: float
    direction: str
    edge: float
    kelly_bet: float
    resolution: int | None = None  # 1=YES, 0=NO, None=unresolved
    pnl: float = 0.0
    hydra_debate_summary: str = ""


class BacktestResult(BaseModel):
    backtest_period: str = ""
    markets_evaluated: int = 0
    trades_executed: int = 0
    brier_score: float = 0.0
    accuracy: float = 0.0
    roi: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    calibration_bins: list[float] = Field(default_factory=list)
    calibration_predicted: list[float] = Field(default_factory=list)
    calibration_actual: list[float] = Field(default_factory=list)
    trades: list[BacktestTrade] = Field(default_factory=list)
