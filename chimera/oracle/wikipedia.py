"""Wikipedia pageview anomaly detection for ORACLE subsystem.

Published in Nature: Wikipedia page view spikes predict stock market
movements before they happen. We use pageviews as a "collective
consciousness scanner" — unusual attention to topics related to
Polymarket questions is a leading indicator.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import httpx

from chimera.config import settings
from chimera.models.events import Signal, SignalType, SignalSource


WIKI_PAGEVIEWS_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"


async def check_wikipedia_anomalies() -> list[Signal]:
    """Check Wikipedia pageviews for anomalous spikes on watchlist articles."""
    signals = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        tasks = [
            _check_article(client, article)
            for article in settings.oracle.wikipedia_watchlist
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Signal):
            signals.append(result)

    return signals


async def _check_article(client: httpx.AsyncClient, article: str) -> Signal | None:
    """Check a single Wikipedia article for pageview anomalies."""
    now = datetime.utcnow()
    end = now.strftime("%Y%m%d00")
    start_recent = (now - timedelta(hours=6)).strftime("%Y%m%d00")
    start_baseline = (now - timedelta(days=7)).strftime("%Y%m%d00")

    headers = {"User-Agent": "CHIMERA/1.0 (research; prediction-markets)"}

    try:
        # Fetch recent pageviews (last 6 hours)
        recent_url = (
            f"{WIKI_PAGEVIEWS_API}/en.wikipedia.org/all-access/all-agents/"
            f"{article}/hourly/{start_recent}/{end}"
        )
        resp_recent = await client.get(recent_url, headers=headers)

        # Fetch baseline (last 7 days)
        baseline_url = (
            f"{WIKI_PAGEVIEWS_API}/en.wikipedia.org/all-access/all-agents/"
            f"{article}/daily/{start_baseline}/{end}"
        )
        resp_baseline = await client.get(baseline_url, headers=headers)

        if resp_recent.status_code != 200 or resp_baseline.status_code != 200:
            return None

        recent_data = resp_recent.json().get("items", [])
        baseline_data = resp_baseline.json().get("items", [])

        # Calculate recent average (hourly)
        recent_views = sum(item.get("views", 0) for item in recent_data)
        recent_hours = max(len(recent_data), 1)
        recent_avg = recent_views / recent_hours

        # Calculate baseline average (daily → hourly)
        baseline_views = sum(item.get("views", 0) for item in baseline_data)
        baseline_days = max(len(baseline_data), 1)
        baseline_hourly = (baseline_views / baseline_days) / 24

        if baseline_hourly <= 0:
            return None

        # Spike ratio
        spike_ratio = recent_avg / baseline_hourly

        # Only signal if views are 2x+ baseline
        if spike_ratio >= 2.0:
            score = min(1.0, (spike_ratio - 1.0) / 5.0)  # Normalize: 2x→0.2, 6x→1.0
            return Signal(
                source=SignalSource.ORACLE,
                signal_type=SignalType.WIKIPEDIA_SPIKE,
                score=score,
                title=f'Wikipedia spike: "{article.replace("_", " ")}"',
                detail=(
                    f"Pageviews {spike_ratio:.1f}x baseline "
                    f"({recent_avg:.0f}/hr vs {baseline_hourly:.0f}/hr normal)"
                ),
                data={
                    "article": article,
                    "spike_ratio": spike_ratio,
                    "recent_avg_hourly": recent_avg,
                    "baseline_avg_hourly": baseline_hourly,
                },
            )

    except Exception as e:
        print(f"[ORACLE/WIKI] Error checking {article}: {e}")

    return None
