"""CHIMERA Core: Signal Fusion Engine.

Combines intelligence from HYDRA, PREDATOR, and RIPPLE into a final
trade decision using log-odds aggregation, GJP extremizing, and
fractional Kelly position sizing.

Mathematical references:
- Log-odds aggregation: Tetlock & Gardner, "Superforecasting" (2015)
- Extremizing transform: Baron et al., "Two Reasons to Make Aggregated
  Probability Forecasts More Extreme" (2014)
- Kelly criterion: Kelly, "A New Interpretation of Information Rate" (1956)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from chimera.config import settings
from chimera.models.forecasts import DebateResult, MicrostructureAnalysis, RippleEffect
from chimera.models.trades import TradeDecision


@dataclass
class WeightedForecast:
    probability: float
    weight: float
    source: str


def prob_to_logodds(p: float) -> float:
    """Convert probability to log-odds. Clamp to avoid infinities.

    log-odds = ln(p / (1 - p))
    """
    cfg = settings.fusion
    p = max(cfg.prob_clamp_min, min(cfg.prob_clamp_max, p))
    return math.log(p / (1.0 - p))


def logodds_to_prob(lo: float) -> float:
    """Convert log-odds back to probability.

    p = 1 / (1 + exp(-lo))
    """
    return 1.0 / (1.0 + math.exp(-lo))


def aggregate_forecasts(forecasts: list[WeightedForecast]) -> float:
    """Weighted log-odds aggregation.

    Each forecast is converted to log-odds space, weighted, averaged,
    then converted back to probability. This respects the symmetry
    between an event and its complement — a property that simple
    averaging in probability space does NOT have.

    Formula:
        lo_agg = sum(w_i * logodds(p_i)) / sum(w_i)
        p_agg = sigmoid(lo_agg)
    """
    if not forecasts:
        return 0.5

    total_weight = sum(f.weight for f in forecasts)
    if total_weight == 0:
        return 0.5

    weighted_logodds = sum(
        f.weight * prob_to_logodds(f.probability) for f in forecasts
    ) / total_weight

    return logodds_to_prob(weighted_logodds)


def extremize(p: float, d: float | None = None) -> float:
    """Apply GJP extremizing transform.

    The Good Judgment Project discovered that aggregated forecasts are
    systematically under-confident. The extremizing transform corrects
    this by pushing probabilities AWAY from 50%.

    Formula (in log-odds space):
        lo_ext = d * logodds(p)
        p_ext = sigmoid(lo_ext)

    Parameters:
        p: Input probability (0, 1)
        d: Extremizing parameter. d > 1 pushes away from 0.5.
           d = 1.0 is identity. Typical GJP values: 1.5 - 2.5.
           For small ensembles (3-6 agents), d = 1.5 is appropriate.

    Why it works: When aggregating independent information sources, the
    aggregate "knows" more than any individual. d approximates this
    information-theoretic correction.
    """
    if d is None:
        d = settings.fusion.extremize_d
    lo = prob_to_logodds(p)
    return logodds_to_prob(lo * d)


def kelly_fraction(
    estimated_prob: float,
    market_price: float,
    kelly_multiplier: float | None = None,
    max_bet_fraction: float | None = None,
) -> float:
    """Fractional Kelly position sizing for binary prediction markets.

    Kelly criterion maximizes long-run log-wealth growth. Full Kelly is
    too aggressive for noisy estimates, so we use fractional Kelly
    (typically 25%).

    For binary markets (pay p, receive 1 if correct):
        f* = (estimated_prob - market_price) / (1 - market_price)

    This is the Kelly fraction of bankroll to bet. We then apply:
        bet = f* × kelly_multiplier × bankroll

    Returns:
        Positive float for YES bets, negative for NO bets, 0 for HOLD.
    """
    cfg = settings.fusion
    if kelly_multiplier is None:
        kelly_multiplier = cfg.kelly_multiplier
    if max_bet_fraction is None:
        max_bet_fraction = cfg.max_bet_fraction

    # Check YES side
    if estimated_prob > market_price:
        edge = estimated_prob - market_price
        f_star = edge / (1.0 - market_price)
        return min(f_star * kelly_multiplier, max_bet_fraction)

    # Check NO side
    no_prob = 1.0 - estimated_prob
    no_price = 1.0 - market_price
    if no_prob > no_price:
        edge = no_prob - no_price
        f_star = edge / (1.0 - no_price)
        return -min(f_star * kelly_multiplier, max_bet_fraction)

    return 0.0


def compute_edge(estimated_prob: float, market_price: float) -> tuple[float, str]:
    """Compute edge and direction.

    Returns:
        (edge_magnitude, direction) where direction is "YES", "NO", or "HOLD"
    """
    yes_edge = estimated_prob - market_price
    no_edge = (1.0 - estimated_prob) - (1.0 - market_price)

    if abs(yes_edge) < settings.fusion.edge_threshold:
        return 0.0, "HOLD"

    if yes_edge > 0:
        return yes_edge, "YES"
    else:
        return abs(yes_edge), "NO"


def fuse(
    debate: DebateResult | None = None,
    microstructure: MicrostructureAnalysis | None = None,
    ripple_effects: list[RippleEffect] | None = None,
    market_price: float = 0.5,
    market_id: str = "",
    market_question: str = "",
    bankroll: float | None = None,
) -> TradeDecision:
    """Full CHIMERA fusion pipeline.

    1. Collect weighted forecasts from HYDRA and PREDATOR
    2. Aggregate in log-odds space
    3. Apply RIPPLE adjustment
    4. Extremize (GJP transform)
    5. Compute edge and Kelly sizing
    6. Return trade decision
    """
    if bankroll is None:
        bankroll = settings.bankroll
    cfg = settings.fusion

    # ── Step 1: Collect forecasts ──
    forecasts: list[WeightedForecast] = []

    hydra_prob = 0.5
    hydra_confidence = 0.5
    if debate:
        hydra_prob = debate.judge_probability
        hydra_confidence = debate.judge_confidence
        forecasts.append(WeightedForecast(
            probability=hydra_prob,
            weight=hydra_confidence * 2.0,  # HYDRA is primary signal
            source="hydra",
        ))

    predator_signal = 0.5
    predator_confidence = 0.5
    if microstructure:
        # Convert microstructure into directional probability signal
        # Order imbalance: positive = buy pressure = higher YES probability
        predator_signal = 0.5 + (microstructure.order_imbalance * 0.2)
        predator_signal = max(0.1, min(0.9, predator_signal))

        # Confidence based on VPIN (high VPIN = someone knows something)
        predator_confidence = min(microstructure.vpin, 0.9)
        if microstructure.whale_detected:
            predator_confidence = min(predator_confidence + 0.15, 0.95)

        forecasts.append(WeightedForecast(
            probability=predator_signal,
            weight=predator_confidence * 1.0,
            source="predator",
        ))

    if not forecasts:
        return TradeDecision(
            market_id=market_id,
            market_question=market_question,
            direction="HOLD",
            estimated_probability=0.5,
            market_price=market_price,
            edge=0.0,
            kelly_fraction=0.0,
            bet_amount=0.0,
            confidence=0.0,
            rationale="Insufficient signals",
        )

    # ── Step 2: Log-odds aggregation ──
    raw_aggregate = aggregate_forecasts(forecasts)

    # ── Step 3: RIPPLE adjustment ──
    ripple_adjustment = 0.0
    if ripple_effects:
        for effect in ripple_effects:
            ripple_adjustment += effect.adjustment
        ripple_adjustment = max(-0.3, min(0.3, ripple_adjustment))

    adjusted_lo = prob_to_logodds(raw_aggregate) + ripple_adjustment
    adjusted = logodds_to_prob(adjusted_lo)

    # ── Step 4: Extremize ──
    final_prob = extremize(adjusted, d=cfg.extremize_d)

    # ── Step 5: Edge & Kelly ──
    edge, direction = compute_edge(final_prob, market_price)
    k_frac = kelly_fraction(final_prob, market_price)
    bet_amount = abs(k_frac) * bankroll

    # ── Step 6: Confidence gate ──
    overall_confidence = (hydra_confidence + predator_confidence) / 2
    if overall_confidence < cfg.min_confidence:
        direction = "HOLD"
        bet_amount = 0.0

    signals_used = []
    if debate:
        signals_used.append("HYDRA")
    if microstructure:
        signals_used.append("PREDATOR")
    if ripple_effects:
        signals_used.append("RIPPLE")

    return TradeDecision(
        market_id=market_id,
        market_question=market_question,
        direction=direction,
        estimated_probability=final_prob,
        market_price=market_price,
        edge=edge,
        kelly_fraction=k_frac,
        bet_amount=round(bet_amount, 2),
        confidence=overall_confidence,
        rationale=(
            f"Fused {len(forecasts)} signals. "
            f"Raw: {raw_aggregate:.3f} → Adjusted: {adjusted:.3f} → "
            f"Extremized: {final_prob:.3f}. "
            f"Edge: {edge:.1%} ({direction}). "
            f"Kelly: {abs(k_frac):.1%} of bankroll = ${bet_amount:.2f}"
        ),
        signals_used=signals_used,
        hydra_probability=hydra_prob,
        predator_signal=predator_signal,
        ripple_adjustment=ripple_adjustment,
        raw_aggregate=raw_aggregate,
        extremized_probability=final_prob,
    )
