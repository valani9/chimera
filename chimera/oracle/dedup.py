"""MinHash LSH deduplication for news articles.

Uses locality-sensitive hashing to efficiently detect near-duplicate
articles across multiple news sources. This prevents the same story
from being counted multiple times in velocity calculations.
"""

from __future__ import annotations

from datasketch import MinHash, MinHashLSH

from chimera.config import settings
from chimera.models.events import NewsArticle


class ArticleDeduplicator:
    """MinHash LSH-based article deduplication."""

    def __init__(self):
        cfg = settings.oracle
        self.threshold = cfg.dedup_threshold
        self.num_perm = cfg.dedup_num_perm
        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        self._seen_keys: set[str] = set()

    def _make_minhash(self, text: str) -> MinHash:
        """Create a MinHash from text using 4-gram shingling."""
        m = MinHash(num_perm=self.num_perm)
        # 4-gram shingles
        text_lower = text.lower()
        for i in range(len(text_lower) - 3):
            shingle = text_lower[i:i + 4]
            m.update(shingle.encode("utf-8"))
        return m

    def is_duplicate(self, article: NewsArticle) -> bool:
        """Check if an article is a near-duplicate of one already seen."""
        text = f"{article.title} {article.content[:200]}"
        mh = self._make_minhash(text)

        # Check for near-duplicates
        key = f"{article.url}_{hash(article.title)}"

        if key in self._seen_keys:
            return True

        results = self.lsh.query(mh)
        if results:
            return True

        # Not a duplicate — add to index
        try:
            self.lsh.insert(key, mh)
            self._seen_keys.add(key)
        except ValueError:
            pass  # Key already exists

        return False

    def deduplicate(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        """Filter out duplicate articles from a batch."""
        unique = []
        for article in articles:
            if not self.is_duplicate(article):
                unique.append(article)
        return unique

    def reset(self):
        """Clear the deduplication index."""
        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        self._seen_keys.clear()
