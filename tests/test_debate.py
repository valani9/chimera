"""Unit tests for HYDRA debate components."""

import pytest
from unittest.mock import AsyncMock, patch

from chimera.hydra.llm_backends import _extract_json


class TestJsonExtraction:
    """Test the JSON extraction helper."""

    def test_direct_json(self):
        result = _extract_json('{"probability": 0.65, "confidence": 0.7}')
        assert result["probability"] == 0.65

    def test_markdown_code_block(self):
        text = '```json\n{"probability": 0.72, "confidence": 0.8}\n```'
        result = _extract_json(text)
        assert result["probability"] == 0.72

    def test_json_embedded_in_text(self):
        text = 'Here is my analysis: {"probability": 0.55, "confidence": 0.6, "reasoning": "test"}'
        result = _extract_json(text)
        assert result["probability"] == 0.55

    def test_invalid_returns_error_dict(self):
        result = _extract_json("This is not JSON at all")
        assert "error" in result or "raw" in result


class TestLogOddsSymmetry:
    """Verify key mathematical properties hold across the pipeline."""

    def test_aggregate_is_symmetric(self):
        """Aggregation is symmetric: swapping Bull↔Bear probabilities → same result."""
        from chimera.core.fusion import aggregate_forecasts, WeightedForecast

        forecasts_ab = [
            WeightedForecast(0.7, 1.0, "a"),
            WeightedForecast(0.4, 1.0, "b"),
        ]
        forecasts_ba = [
            WeightedForecast(0.4, 1.0, "a"),
            WeightedForecast(0.7, 1.0, "b"),
        ]
        result_ab = aggregate_forecasts(forecasts_ab)
        result_ba = aggregate_forecasts(forecasts_ba)
        assert result_ab == pytest.approx(result_ba, rel=1e-6)
