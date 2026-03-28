"""Forecasting and debate data models for HYDRA subsystem."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AgentVote(BaseModel):
    agent_name: str
    agent_role: str = ""
    llm_backend: str = ""
    probability: float  # 0-1
    confidence: float  # 0-1
    reasoning: str = ""
    key_evidence: list[str] = Field(default_factory=list)
    round_number: int = 1


class DebateRound(BaseModel):
    round_number: int
    votes: list[AgentVote] = Field(default_factory=list)
    challenge_text: str = ""  # Contrarian's challenge in round 2


class DebateResult(BaseModel):
    market_id: str
    market_question: str = ""
    rounds: list[DebateRound] = Field(default_factory=list)
    judge_probability: float = 0.5
    judge_confidence: float = 0.5
    judge_reasoning: str = ""
    dissenting_view: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_llm_calls: int = 0
    total_tokens_used: int = 0


class MicrostructureAnalysis(BaseModel):
    market_id: str
    vpin: float = 0.0  # Volume-synced probability of informed trading
    order_imbalance: float = 0.0  # -1 to 1 (negative = sell pressure)
    whale_detected: bool = False
    whale_direction: str = ""  # "buy" or "sell"
    whale_size: float = 0.0
    cascade_score: float = 0.0  # 0-1
    cascade_direction: str = ""
    spread: float = 0.0
    depth_ratio: float = 0.0  # bid_depth / ask_depth
    liquidity_score: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RippleEffect(BaseModel):
    source_entity: str
    target_market_id: str
    target_market_question: str = ""
    relationship_chain: list[str] = Field(default_factory=list)
    impact_score: float = 0.0  # 0-1, decays with depth
    depth: int = 0
    adjustment: float = 0.0  # probability adjustment in log-odds
