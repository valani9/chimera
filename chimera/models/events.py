"""Event and signal data models for ORACLE subsystem."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SignalType(str, Enum):
    NEWS_CLUSTER = "news_cluster"
    WIKIPEDIA_SPIKE = "wikipedia_spike"
    CLOUDFLARE_ANOMALY = "cloudflare_anomaly"
    GOV_CHANGE = "gov_change"
    VPIN_SPIKE = "vpin_spike"
    WHALE_MOVE = "whale_move"
    CASCADE = "cascade"
    CROSS_MARKET = "cross_market"
    RIPPLE_EFFECT = "ripple_effect"


class SignalSource(str, Enum):
    ORACLE = "oracle"
    PREDATOR = "predator"
    RIPPLE = "ripple"
    HYDRA = "hydra"


class NewsArticle(BaseModel):
    url: str
    title: str
    content: str = ""
    source: str = ""
    published_at: datetime = Field(default_factory=datetime.utcnow)
    embedding: list[float] | None = None


class NewsCluster(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    articles: list[NewsArticle] = Field(default_factory=list)
    summary: str = ""
    centroid_embedding: list[float] | None = None
    velocity: float = 0.0  # articles per minute
    source_diversity: int = 0  # unique source count
    novelty_score: float = 0.0  # distance from known clusters
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Signal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: SignalSource
    signal_type: SignalType
    score: float = 0.0  # normalized 0-1 importance
    title: str = ""
    detail: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    matched_market_ids: list[str] = Field(default_factory=list)
