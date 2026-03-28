"""Entity and relationship extraction using LLMs for RIPPLE subsystem.

Extracts (subject, relation, object) triples from news text to
dynamically extend the knowledge graph.
"""

from __future__ import annotations

import json
from chimera.hydra.llm_backends import create_backend
from chimera.config import settings


EXTRACTION_PROMPT = """Extract entities and causal relationships from this news text.

NEWS TEXT:
{text}

Return a JSON object with:
```json
{{
    "entities": [
        {{"name": "Entity Name", "type": "person|country|organization|concept|event"}}
    ],
    "relationships": [
        {{
            "source": "Entity A",
            "target": "Entity B",
            "relation": "verb describing causal relationship",
            "weight": 0.1-1.0
        }}
    ],
    "primary_topic": "One-line summary of the main event"
}}
```

Focus on CAUSAL relationships (X causes/affects/threatens/supports Y).
Ignore trivial relationships. Weight reflects strength of causal link.
Return at most 5 entities and 5 relationships."""


async def extract_entities_and_relations(text: str) -> dict:
    """Extract entities and relationships from news text using an LLM.

    Returns dict with 'entities', 'relationships', and 'primary_topic'.
    """
    # Use the cheapest/fastest available backend
    try:
        if settings.openai_api_key:
            backend = create_backend("openai", "gpt-4o-mini")
        elif settings.anthropic_api_key:
            backend = create_backend("anthropic", "claude-sonnet-4-20250514")
        elif settings.google_api_key:
            backend = create_backend("google", "gemini-2.0-flash")
        else:
            return _fallback_extraction(text)

        result = await backend.complete_json(
            system="You are an entity and relationship extraction system. Be precise and concise.",
            user=EXTRACTION_PROMPT.format(text=text[:1000]),
            temperature=0.2,
            max_tokens=500,
        )

        return {
            "entities": result.get("entities", []),
            "relationships": result.get("relationships", []),
            "primary_topic": result.get("primary_topic", ""),
        }
    except Exception as e:
        print(f"[RIPPLE/EXTRACT] Error: {e}")
        return _fallback_extraction(text)


def _fallback_extraction(text: str) -> dict:
    """Simple keyword-based extraction fallback (no LLM needed)."""
    entities = []
    text_lower = text.lower()

    # Known entity detection
    known_entities = {
        "trump": ("Trump", "person"),
        "biden": ("Biden", "person"),
        "putin": ("Putin", "person"),
        "xi jinping": ("Xi Jinping", "person"),
        "zelensky": ("Zelensky", "person"),
        "ukraine": ("Ukraine", "country"),
        "russia": ("Russia", "country"),
        "china": ("China", "country"),
        "taiwan": ("Taiwan", "country"),
        "iran": ("Iran", "country"),
        "nato": ("NATO", "organization"),
        "fed": ("Fed Chair", "person"),
        "federal reserve": ("Interest Rates", "concept"),
        "tariff": ("Tariffs", "concept"),
        "sanction": ("Sanctions", "concept"),
        "bitcoin": ("Bitcoin", "concept"),
        "oil": ("Oil Prices", "concept"),
        "recession": ("Recession", "concept"),
        "inflation": ("Inflation", "concept"),
        "ceasefire": ("Ceasefire", "concept"),
        "nuclear": ("Nuclear Weapons", "concept"),
        "semiconductor": ("Semiconductor Supply", "concept"),
    }

    found = []
    for keyword, (name, etype) in known_entities.items():
        if keyword in text_lower:
            found.append({"name": name, "type": etype})

    return {
        "entities": found[:5],
        "relationships": [],
        "primary_topic": text[:100],
    }
