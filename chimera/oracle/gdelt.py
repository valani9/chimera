"""GDELT event ingestion for ORACLE subsystem.

GDELT (Global Database of Events, Language, and Tone) monitors the world's
news media in 100+ languages, identifying events, locations, and themes
in near-real-time with 15-minute update cycles.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import httpx

from chimera.models.events import NewsArticle


GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


async def fetch_gdelt_events(
    query: str = "",
    timespan: str = "15min",
    max_records: int = 50,
    mode: str = "artlist",
) -> list[NewsArticle]:
    """Fetch recent events from GDELT DOC API.

    Args:
        query: Search query (empty = all events)
        timespan: Time window (e.g., "15min", "1h", "1d")
        max_records: Maximum articles to return
        mode: "artlist" for article list
    """
    params = {
        "query": query or "conflict OR election OR economy OR trade OR crisis",
        "mode": mode,
        "maxrecords": max_records,
        "timespan": timespan,
        "format": "json",
        "sort": "datedesc",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(GDELT_DOC_API, params=params)
            resp.raise_for_status()
            data = resp.json()

        articles = []
        for item in data.get("articles", []):
            pub_date = item.get("seendate", "")
            try:
                pub_dt = datetime.strptime(pub_date, "%Y%m%dT%H%M%SZ")
            except (ValueError, TypeError):
                pub_dt = datetime.utcnow()

            articles.append(NewsArticle(
                url=item.get("url", ""),
                title=item.get("title", ""),
                content=item.get("title", ""),  # GDELT artlist only gives titles
                source=item.get("domain", item.get("source", "GDELT")),
                published_at=pub_dt,
            ))

        return articles
    except Exception as e:
        print(f"[ORACLE/GDELT] Error: {e}")
        return []


async def fetch_gdelt_trending(theme: str = "") -> list[dict]:
    """Fetch trending themes/topics from GDELT."""
    params = {
        "query": theme or "",
        "mode": "timelinetone",
        "timespan": "1h",
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(GDELT_DOC_API, params=params)
            resp.raise_for_status()
            return resp.json().get("timeline", [])
    except Exception:
        return []
