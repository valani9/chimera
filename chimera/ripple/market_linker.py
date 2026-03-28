"""Market linker: semantic matching between signals and Polymarket markets."""

from __future__ import annotations

import numpy as np

from chimera.config import settings
from chimera.models.events import Signal
from chimera.models.markets import Market


class MarketLinker:
    """Links signals to relevant Polymarket markets using embeddings."""

    def __init__(self, embedder=None):
        self._embedder = embedder
        self._market_embeddings: dict[str, np.ndarray] = {}

    def set_embedder(self, embedder):
        self._embedder = embedder

    def embed_markets(self, markets: list[Market]):
        """Pre-compute embeddings for all market questions."""
        if not self._embedder or not markets:
            return

        questions = [m.question for m in markets]
        embeddings = self._embedder.embed_texts(questions)

        for i, market in enumerate(markets):
            self._market_embeddings[market.id] = embeddings[i]
            market.question_embedding = embeddings[i].tolist()

    def find_matching_markets(
        self,
        signal: Signal,
        markets: list[Market],
        threshold: float | None = None,
        top_k: int = 5,
    ) -> list[tuple[Market, float]]:
        """Find markets that match a signal using cosine similarity."""
        if threshold is None:
            threshold = settings.oracle.market_match_threshold

        if not self._embedder:
            return self._keyword_match(signal, markets, top_k)

        # Embed the signal text
        signal_text = f"{signal.title}. {signal.detail}"
        signal_emb = self._embedder.embed_texts([signal_text])[0]

        # Compare against all market embeddings
        matches = []
        for market in markets:
            market_emb = self._market_embeddings.get(market.id)
            if market_emb is None:
                continue

            similarity = float(np.dot(signal_emb, market_emb) / (
                np.linalg.norm(signal_emb) * np.linalg.norm(market_emb) + 1e-8
            ))

            if similarity >= threshold:
                matches.append((market, similarity))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]

    def _keyword_match(
        self, signal: Signal, markets: list[Market], top_k: int
    ) -> list[tuple[Market, float]]:
        """Fallback keyword matching when embedder is not available."""
        signal_words = set(signal.title.lower().split() + signal.detail.lower().split())
        signal_words -= {"the", "a", "an", "is", "in", "on", "at", "to", "for", "of", "and", "or"}

        matches = []
        for market in markets:
            question_words = set(market.question.lower().split())
            overlap = len(signal_words & question_words)
            if overlap > 0:
                score = overlap / max(len(signal_words), 1)
                matches.append((market, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]
