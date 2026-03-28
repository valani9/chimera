"""RSS feed ingestion for ORACLE subsystem."""

from __future__ import annotations

import asyncio
from datetime import datetime

import feedparser
import httpx

from chimera.config import settings
from chimera.models.events import NewsArticle


async def fetch_rss_feeds() -> list[NewsArticle]:
    """Fetch and parse all configured RSS feeds."""
    articles = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        tasks = [_fetch_single_feed(client, url) for url in settings.oracle.rss_feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, list):
            articles.extend(result)

    return articles


async def _fetch_single_feed(client: httpx.AsyncClient, url: str) -> list[NewsArticle]:
    """Fetch and parse a single RSS feed."""
    try:
        resp = await client.get(url, follow_redirects=True)
        resp.raise_for_status()

        feed = await asyncio.to_thread(feedparser.parse, resp.text)

        articles = []
        for entry in feed.entries[:20]:  # Latest 20 per feed
            published = entry.get("published_parsed")
            pub_dt = datetime(*published[:6]) if published else datetime.utcnow()

            content = ""
            if hasattr(entry, "summary"):
                content = entry.summary
            elif hasattr(entry, "description"):
                content = entry.description

            # Strip HTML tags (basic)
            import re
            content = re.sub(r"<[^>]+>", "", content)

            articles.append(NewsArticle(
                url=entry.get("link", ""),
                title=entry.get("title", ""),
                content=content[:1000],  # Cap content length
                source=feed.feed.get("title", url),
                published_at=pub_dt,
            ))

        return articles
    except Exception as e:
        print(f"[ORACLE/RSS] Error fetching {url}: {e}")
        return []
