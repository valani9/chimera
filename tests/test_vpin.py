"""Unit tests for VPIN and cascade detection."""

import pytest
from datetime import datetime

from chimera.predator.vpin import VPINCalculator
from chimera.predator.cascade import CascadeDetector
from chimera.models.markets import Trade


def make_trade(side: str, size: float = 100.0, price: float = 0.5) -> Trade:
    return Trade(
        market_id="test-market",
        price=price,
        size=size,
        side=side,
        timestamp=datetime.utcnow(),
    )


class TestVPIN:
    def test_zero_vpin_with_no_trades(self):
        """No trades → VPIN is 0."""
        calc = VPINCalculator()
        assert calc.compute_vpin() == 0.0

    def test_balanced_flow_low_vpin(self):
        """Perfectly balanced buy/sell flow → low VPIN."""
        calc = VPINCalculator(bucket_size=10)
        for _ in range(100):
            calc.add_trade(make_trade("buy", 5))
            calc.add_trade(make_trade("sell", 5))
        vpin = calc.compute_vpin()
        assert vpin < 0.2

    def test_one_sided_flow_high_vpin(self):
        """All buys → high VPIN (all informed on same side)."""
        calc = VPINCalculator(bucket_size=10)
        for _ in range(200):
            calc.add_trade(make_trade("buy", 10))
        vpin = calc.compute_vpin()
        assert vpin > 0.7

    def test_imbalance_positive_on_all_buys(self):
        """All buys → positive order imbalance."""
        calc = VPINCalculator(bucket_size=10)
        for _ in range(100):
            calc.add_trade(make_trade("buy", 10))
        assert calc.compute_order_imbalance() > 0.8

    def test_imbalance_negative_on_all_sells(self):
        """All sells → negative order imbalance."""
        calc = VPINCalculator(bucket_size=10)
        for _ in range(100):
            calc.add_trade(make_trade("sell", 10))
        assert calc.compute_order_imbalance() < -0.8

    def test_vpin_in_zero_one(self):
        """VPIN must always be in [0, 1]."""
        calc = VPINCalculator(bucket_size=5)
        for i in range(500):
            side = "buy" if i % 3 != 0 else "sell"
            calc.add_trade(make_trade(side, 7))
        vpin = calc.compute_vpin()
        assert 0.0 <= vpin <= 1.0


class TestCascade:
    def test_no_cascade_on_balanced_flow(self):
        """Balanced buy/sell flow should not trigger cascade."""
        detector = CascadeDetector()
        last_signal = None
        for i in range(40):
            trade = make_trade("buy" if i % 2 == 0 else "sell")
            sig = detector.add_trade(trade)
            if sig:
                last_signal = sig
        # Score should be ~0.5 (balanced)
        score = detector.compute_cascade_score()
        assert score < 0.65

    def test_cascade_on_directional_flow(self):
        """Strong one-directional flow should trigger cascade detection."""
        detector = CascadeDetector()
        signals = []
        for _ in range(25):
            trade = make_trade("buy")
            sig = detector.add_trade(trade)
            if sig:
                signals.append(sig)
        assert len(signals) > 0
        assert detector.compute_cascade_score() >= 0.75

    def test_cascade_direction_is_buy(self):
        """All-buy cascade should report buy direction."""
        detector = CascadeDetector()
        last_signal = None
        for _ in range(25):
            sig = detector.add_trade(make_trade("buy"))
            if sig:
                last_signal = sig
        if last_signal:
            assert last_signal.data["direction"] == "buy"
