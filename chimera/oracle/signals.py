"""ORACLE signal normalization and emission.

Orchestrates all data sources (RSS, GDELT, Wikipedia, Cloudflare)
and converts raw data into normalized Signal objects for the
CHIMERA pipeline.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from chimera.config import settings
from chimera.models.events import Signal, SignalType, SignalSource, NewsCluster
from chimera.oracle.rss import fetch_rss_feeds
from chimera.oracle.gdelt import fetch_gdelt_events
from chimera.oracle.wikipedia import check_wikipedia_anomalies
from chimera.oracle.cloudflare import check_internet_health
from chimera.oracle.dedup import ArticleDeduplicator
from chimera.oracle.clustering import EventClusterer


class OracleEngine:
    """Orchestrates all ORACLE data sources and emits normalized signals."""

    def __init__(self):
        self.deduplicator = ArticleDeduplicator()
        self.clusterer = EventClusterer()
        self._signal_history: list[Signal] = []

    async def scan(self) -> list[Signal]:
        """Run a single scan cycle across all data sources.

        Returns new signals detected in this cycle.
        """
        signals: list[Signal] = []

        # ── Parallel data collection ──
        rss_task = fetch_rss_feeds()
        gdelt_task = fetch_gdelt_events()
        wiki_task = check_wikipedia_anomalies()
        cf_task = check_internet_health()

        rss_articles, gdelt_articles, wiki_signals, cf_signals = await asyncio.gather(
            rss_task, gdelt_task, wiki_task, cf_task,
            return_exceptions=True,
        )

        # ── Process RSS + GDELT articles ──
        all_articles = []
        if isinstance(rss_articles, list):
            all_articles.extend(rss_articles)
        if isinstance(gdelt_articles, list):
            all_articles.extend(gdelt_articles)

        if all_articles:
            # Deduplicate
            unique_articles = self.deduplicator.deduplicate(all_articles)

            # Cluster into events
            if unique_articles:
                clusters = self.clusterer.cluster_articles(unique_articles)

                # Convert significant clusters to signals
                for cluster in clusters:
                    if (
                        cluster.novelty_score >= settings.oracle.novelty_threshold
                        or cluster.velocity > 2.0
                        or cluster.source_diversity >= 3
                    ):
                        signal = Signal(
                            source=SignalSource.ORACLE,
                            signal_type=SignalType.NEWS_CLUSTER,
                            score=self._score_cluster(cluster),
                            title=cluster.summary,
                            detail=(
                                f"{len(cluster.articles)} articles, "
                                f"{cluster.velocity:.1f}/min velocity, "
                                f"{cluster.source_diversity} sources, "
                                f"novelty: {cluster.novelty_score:.2f}"
                            ),
                            data={
                                "cluster_id": cluster.id,
                                "article_count": len(cluster.articles),
                                "velocity": cluster.velocity,
                                "source_diversity": cluster.source_diversity,
                                "novelty": cluster.novelty_score,
                                "top_sources": list(set(a.source for a in cluster.articles))[:5],
                            },
                        )
                        signals.append(signal)

        # ── Add Wikipedia signals ──
        if isinstance(wiki_signals, list):
            signals.extend(wiki_signals)

        # ── Add Cloudflare signals ──
        if isinstance(cf_signals, list):
            signals.extend(cf_signals)

        # Sort by score (highest first)
        signals.sort(key=lambda s: s.score, reverse=True)
        self._signal_history.extend(signals)

        if signals:
            print(f"[ORACLE] Scan complete: {len(signals)} new signals detected")
        return signals

    def _score_cluster(self, cluster: NewsCluster) -> float:
        """Score a news cluster's importance (0-1)."""
        # Weighted combination of velocity, diversity, and novelty
        velocity_score = min(1.0, cluster.velocity / 5.0)  # 5+ articles/min = max
        diversity_score = min(1.0, cluster.source_diversity / 5.0)  # 5+ sources = max
        novelty_score = cluster.novelty_score

        return (velocity_score * 0.3 + diversity_score * 0.3 + novelty_score * 0.4)

    def get_signal_history(self) -> list[Signal]:
        return list(self._signal_history)

    def get_recent_signals(self, n: int = 20) -> list[Signal]:
        return self._signal_history[-n:]

    def get_embedder(self):
        """Get the sentence transformer model for market matching."""
        return self.clusterer
