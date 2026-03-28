"""Configuration management for CHIMERA."""

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


def _load_yaml() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}


_yaml = _load_yaml()


class OracleConfig(BaseModel):
    rss_poll_interval_seconds: int = 60
    gdelt_poll_interval_seconds: int = 900
    wikipedia_poll_interval_seconds: int = 300
    cloudflare_poll_interval_seconds: int = 900
    dedup_threshold: float = 0.85
    dedup_num_perm: int = 128
    cluster_min_size: int = 3
    novelty_threshold: float = 0.6
    market_match_threshold: float = 0.45
    rss_feeds: list[str] = Field(default_factory=list)
    wikipedia_watchlist: list[str] = Field(default_factory=list)
    cloudflare_countries: list[str] = Field(default_factory=list)


class HydraAgentConfig(BaseModel):
    name: str
    backend: str
    model: str


class HydraConfig(BaseModel):
    debate_rounds: int = 3
    temperature_agents: float = 0.7
    temperature_judge: float = 0.3
    max_tokens_per_agent: int = 500
    max_tokens_judge: int = 800
    agents: dict[str, HydraAgentConfig] = Field(default_factory=dict)


class FusionConfig(BaseModel):
    extremize_d: float = 1.5
    edge_threshold: float = 0.05
    kelly_multiplier: float = 0.25
    max_bet_fraction: float = 0.05
    prob_clamp_min: float = 0.005
    prob_clamp_max: float = 0.995
    min_confidence: float = 0.3


class PredatorConfig(BaseModel):
    vpin_bucket_size: int = 50
    vpin_window: int = 200
    whale_threshold_pct: float = 0.10
    cascade_window_trades: int = 20
    cascade_threshold: float = 0.75
    min_market_volume_24h: float = 10000


class PolymarketConfig(BaseModel):
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    clob_api_url: str = "https://clob.polymarket.com"
    ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    max_markets: int = 100


class RippleConfig(BaseModel):
    max_depth: int = 3
    decay_factor: float = 0.6
    min_relevance: float = 0.3


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


class Settings(BaseSettings):
    # API Keys (from .env)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    polymarket_api_key: str = ""
    polymarket_secret: str = ""
    polymarket_passphrase: str = ""
    private_key: str = ""  # Polygon wallet private key

    # Subsystem configs (from config.yaml)
    oracle: OracleConfig = Field(default_factory=lambda: OracleConfig(**_yaml.get("oracle", {})))
    hydra: HydraConfig = Field(default_factory=lambda: HydraConfig(**_yaml.get("hydra", {})))
    fusion: FusionConfig = Field(default_factory=lambda: FusionConfig(**_yaml.get("fusion", {})))
    predator: PredatorConfig = Field(default_factory=lambda: PredatorConfig(**_yaml.get("predator", {})))
    polymarket: PolymarketConfig = Field(default_factory=lambda: PolymarketConfig(**_yaml.get("polymarket", {})))
    ripple: RippleConfig = Field(default_factory=lambda: RippleConfig(**_yaml.get("ripple", {})))
    server: ServerConfig = Field(default_factory=lambda: ServerConfig(**_yaml.get("server", {})))

    # Runtime state
    bankroll: float = 1000.0
    paper_trading: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
