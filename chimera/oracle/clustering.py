"""News event clustering using sentence-transformers + HDBSCAN.

Groups deduplicated articles into coherent event clusters, then
scores each cluster by velocity, source diversity, and novelty.
"""

from __future__ import annotations

import numpy as np
from datetime import datetime

from chimera.config import settings
from chimera.models.events import NewsArticle, NewsCluster


class EventClusterer:
    """Cluster news articles into coherent events."""

    def __init__(self):
        self._model = None
        self._existing_centroids: list[np.ndarray] = []
        self._clusters: list[NewsCluster] = []

    def _get_model(self):
        """Lazy-load sentence transformer model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts using sentence-transformers."""
        model = self._get_model()
        return model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    def cluster_articles(self, articles: list[NewsArticle]) -> list[NewsCluster]:
        """Cluster articles into event groups using HDBSCAN."""
        if len(articles) < 2:
            if articles:
                cluster = NewsCluster(
                    articles=articles,
                    summary=articles[0].title,
                    velocity=1.0,
                    source_diversity=1,
                    novelty_score=1.0,
                )
                return [cluster]
            return []

        # Embed article titles + content snippets
        texts = [f"{a.title}. {a.content[:200]}" for a in articles]
        embeddings = self.embed_texts(texts)

        # Store embeddings on articles
        for i, article in enumerate(articles):
            article.embedding = embeddings[i].tolist()

        # Cluster with HDBSCAN
        try:
            import hdbscan
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=max(2, settings.oracle.cluster_min_size),
                min_samples=1,
                metric="cosine",
            )
            labels = clusterer.fit_predict(embeddings)
        except Exception:
            # Fallback: treat all as one cluster
            labels = np.zeros(len(articles), dtype=int)

        # Group articles by cluster label
        cluster_map: dict[int, list[tuple[NewsArticle, np.ndarray]]] = {}
        for i, label in enumerate(labels):
            if label == -1:
                continue  # Noise point
            if label not in cluster_map:
                cluster_map[label] = []
            cluster_map[label].append((articles[i], embeddings[i]))

        # Build NewsCluster objects
        new_clusters = []
        for label, items in cluster_map.items():
            cluster_articles = [a for a, _ in items]
            cluster_embeddings = np.array([e for _, e in items])
            centroid = cluster_embeddings.mean(axis=0)

            # Calculate metrics
            unique_sources = set(a.source for a in cluster_articles)
            timestamps = [a.published_at for a in cluster_articles]
            time_range = (max(timestamps) - min(timestamps)).total_seconds() / 60.0
            velocity = len(cluster_articles) / max(time_range, 1.0)

            # Novelty: distance from existing cluster centroids
            novelty = self._compute_novelty(centroid)

            # Summary: title of the most representative article (closest to centroid)
            distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
            representative_idx = np.argmin(distances)

            cluster = NewsCluster(
                articles=cluster_articles,
                summary=cluster_articles[representative_idx].title,
                centroid_embedding=centroid.tolist(),
                velocity=velocity,
                source_diversity=len(unique_sources),
                novelty_score=novelty,
            )
            new_clusters.append(cluster)

        # Update existing centroids
        for c in new_clusters:
            if c.centroid_embedding:
                self._existing_centroids.append(np.array(c.centroid_embedding))

        self._clusters.extend(new_clusters)
        return new_clusters

    def _compute_novelty(self, centroid: np.ndarray) -> float:
        """Compute novelty score as minimum distance to existing clusters."""
        if not self._existing_centroids:
            return 1.0

        distances = [
            float(np.linalg.norm(centroid - existing))
            for existing in self._existing_centroids
        ]
        min_distance = min(distances)

        # Normalize: 0 distance = 0 novelty, 1.5+ distance = 1.0 novelty
        return min(1.0, min_distance / 1.5)

    def get_clusters(self) -> list[NewsCluster]:
        return list(self._clusters)
