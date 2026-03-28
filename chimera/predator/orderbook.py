"""Orderbook analysis for PREDATOR subsystem.

Analyzes order book depth, spread dynamics, and imbalance
to detect market microstructure signals.
"""

from __future__ import annotations

from chimera.models.markets import OrderBook


def analyze_orderbook(ob: OrderBook) -> dict:
    """Analyze an orderbook snapshot for microstructure signals.

    Returns a dict with:
    - spread: bid-ask spread
    - mid_price: midpoint price
    - imbalance: order book imbalance (-1 to 1)
    - depth_ratio: bid_depth / ask_depth
    - liquidity_score: overall liquidity (0-1)
    - tight_market: whether spread is acceptably tight
    """
    ob.compute_metrics()

    # Order book imbalance: positive = more bids (bullish)
    total_depth = ob.total_bid_depth + ob.total_ask_depth
    if total_depth > 0:
        imbalance = (ob.total_bid_depth - ob.total_ask_depth) / total_depth
    else:
        imbalance = 0.0

    # Depth ratio
    depth_ratio = ob.total_bid_depth / ob.total_ask_depth if ob.total_ask_depth > 0 else 1.0

    # Liquidity score (higher = more liquid)
    # Based on depth and spread
    spread_score = max(0, 1.0 - ob.spread / 0.1)  # 0.1 spread = 0 score
    depth_score = min(1.0, total_depth / 10000)  # $10K depth = max score
    liquidity_score = (spread_score * 0.5 + depth_score * 0.5)

    return {
        "spread": ob.spread,
        "mid_price": ob.mid_price,
        "best_bid": ob.best_bid,
        "best_ask": ob.best_ask,
        "imbalance": imbalance,
        "depth_ratio": depth_ratio,
        "total_bid_depth": ob.total_bid_depth,
        "total_ask_depth": ob.total_ask_depth,
        "liquidity_score": liquidity_score,
        "tight_market": ob.spread < 0.05,
    }


def detect_wall(ob: OrderBook, threshold_pct: float = 0.3) -> dict | None:
    """Detect large orders (walls) in the orderbook.

    A wall is a single order representing >threshold_pct of total depth
    on that side of the book.
    """
    # Check bid side
    for level in ob.bids:
        if ob.total_bid_depth > 0 and level.size / ob.total_bid_depth > threshold_pct:
            return {
                "side": "bid",
                "price": level.price,
                "size": level.size,
                "pct_of_depth": level.size / ob.total_bid_depth,
            }

    # Check ask side
    for level in ob.asks:
        if ob.total_ask_depth > 0 and level.size / ob.total_ask_depth > threshold_pct:
            return {
                "side": "ask",
                "price": level.price,
                "size": level.size,
                "pct_of_depth": level.size / ob.total_ask_depth,
            }

    return None
