"""Kelly criterion utilities and risk management.

Provides the adaptive fractional Kelly sizing with multiple
adjustment multipliers for robust position sizing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from chimera.config import settings


@dataclass
class KellyMultipliers:
    """Seven adjustment multipliers for adaptive Kelly sizing.

    Each multiplier scales the raw Kelly fraction to account for
    real-world factors that the basic Kelly formula ignores.
    """
    confidence: float = 1.0        # From HYDRA debate consensus (0.5 - 1.5)
    drawdown_heat: float = 1.0     # Reduces sizing during drawdowns (0.3 - 1.0)
    market_timeline: float = 1.0   # Markets closing soon get smaller bets (0.5 - 1.0)
    volatility_regime: float = 1.0 # High vol = smaller bets (0.5 - 1.0)
    category_perf: float = 1.0     # Track record by category (0.7 - 1.3)
    liquidity: float = 1.0         # Thin markets = smaller bets (0.3 - 1.0)
    whale_alignment: float = 1.0   # +8% when whales agree, -2% when they disagree

    @property
    def combined(self) -> float:
        return (
            self.confidence
            * self.drawdown_heat
            * self.market_timeline
            * self.volatility_regime
            * self.category_perf
            * self.liquidity
            * self.whale_alignment
        )


def adaptive_kelly(
    estimated_prob: float,
    market_price: float,
    bankroll: float,
    multipliers: KellyMultipliers | None = None,
) -> dict:
    """Full adaptive Kelly position sizing.

    Returns a dict with the sizing breakdown for transparency.
    """
    cfg = settings.fusion
    if multipliers is None:
        multipliers = KellyMultipliers()

    # Raw Kelly
    if estimated_prob > market_price:
        direction = "YES"
        edge = estimated_prob - market_price
        raw_kelly = edge / (1.0 - market_price)
    elif (1.0 - estimated_prob) > (1.0 - market_price):
        direction = "NO"
        edge = (1.0 - estimated_prob) - (1.0 - market_price)
        raw_kelly = edge / market_price
    else:
        return {
            "direction": "HOLD",
            "raw_kelly": 0.0,
            "adjusted_kelly": 0.0,
            "bet_fraction": 0.0,
            "bet_amount": 0.0,
            "edge": 0.0,
            "multipliers": multipliers,
        }

    # Apply fractional Kelly + multipliers
    adjusted_kelly = raw_kelly * cfg.kelly_multiplier * multipliers.combined

    # Cap at max bet fraction
    bet_fraction = min(adjusted_kelly, cfg.max_bet_fraction)
    bet_amount = bet_fraction * bankroll

    return {
        "direction": direction,
        "raw_kelly": raw_kelly,
        "adjusted_kelly": adjusted_kelly,
        "bet_fraction": bet_fraction,
        "bet_amount": round(bet_amount, 2),
        "edge": edge,
        "multipliers": multipliers,
    }


def compute_drawdown_heat(
    current_bankroll: float,
    peak_bankroll: float,
    max_heat: float = 0.3,
) -> float:
    """Scale down betting during drawdowns.

    Returns a multiplier between max_heat and 1.0.
    At 20% drawdown, reduces to ~0.5. At 50% drawdown, reduces to max_heat.
    """
    if peak_bankroll <= 0:
        return 1.0

    drawdown = 1.0 - (current_bankroll / peak_bankroll)
    if drawdown <= 0:
        return 1.0

    # Linear scaling from 1.0 at 0% drawdown to max_heat at 50% drawdown
    return max(max_heat, 1.0 - (drawdown / 0.5) * (1.0 - max_heat))


def compute_liquidity_multiplier(
    total_depth: float,
    bet_amount: float,
    max_impact: float = 0.02,
) -> float:
    """Scale down if our order would move the market too much.

    If bet_amount > max_impact * total_depth, we'd cause significant
    price impact. Scale down to stay within max_impact.
    """
    if total_depth <= 0:
        return 0.3

    impact = bet_amount / total_depth
    if impact <= max_impact:
        return 1.0

    return max(0.3, max_impact / impact)
