"""Ripple propagation engine for RIPPLE subsystem.

Connects news events to the knowledge graph and propagates
effects to find impacted Polymarket markets.
"""

from __future__ import annotations

import asyncio
from chimera.models.events import Signal, NewsCluster
from chimera.models.forecasts import RippleEffect
from chimera.models.markets import Market
from chimera.ripple.graph import CausalGraph
from chimera.ripple.extractor import extract_entities_and_relations


class RippleEngine:
    """Connects news events to knowledge graph and finds affected markets."""

    def __init__(self, graph: CausalGraph | None = None):
        self.graph = graph or CausalGraph()

    async def process_signal(
        self,
        signal: Signal,
        markets: list[Market],
    ) -> list[RippleEffect]:
        """Process a signal through the knowledge graph.

        1. Extract entities from the signal
        2. Add new entities/relationships to the graph
        3. Run ripple analysis from trigger entities
        4. Match ripple targets to Polymarket markets
        """
        # Extract entities from signal text
        text = f"{signal.title}. {signal.detail}"
        extraction = await extract_entities_and_relations(text)

        # Add new entities and relationships to graph
        for entity in extraction.get("entities", []):
            self.graph.add_entity(entity["name"], entity.get("type", "concept"))

        for rel in extraction.get("relationships", []):
            self.graph.add_relationship(
                rel["source"], rel["target"],
                rel.get("relation", "affects"),
                rel.get("weight", 0.5),
            )

        # Run ripple analysis from each extracted entity
        all_effects: list[RippleEffect] = []
        for entity in extraction.get("entities", []):
            effects = self.graph.ripple_analysis(entity["name"])
            all_effects.extend(effects)

        # Match ripple targets to actual Polymarket markets
        matched_effects = self._match_to_markets(all_effects, markets)

        return matched_effects

    def _match_to_markets(
        self,
        effects: list[RippleEffect],
        markets: list[Market],
    ) -> list[RippleEffect]:
        """Match ripple effect targets to Polymarket markets using keyword matching."""
        matched = []

        for effect in effects:
            # Get the target entity name from the last relationship in chain
            if not effect.relationship_chain:
                continue

            last_link = effect.relationship_chain[-1]
            target = last_link.split("--> ")[-1] if "--> " in last_link else ""

            for market in markets:
                question_lower = market.question.lower()
                target_lower = target.lower()

                if target_lower in question_lower or any(
                    word in question_lower
                    for word in target_lower.split()
                    if len(word) > 3
                ):
                    matched_effect = RippleEffect(
                        source_entity=effect.source_entity,
                        target_market_id=market.id,
                        target_market_question=market.question,
                        relationship_chain=effect.relationship_chain,
                        impact_score=effect.impact_score,
                        depth=effect.depth,
                        adjustment=effect.adjustment,
                    )
                    matched.append(matched_effect)

        # Deduplicate by market (keep highest impact)
        seen_markets: dict[str, RippleEffect] = {}
        for effect in matched:
            if effect.target_market_id not in seen_markets or effect.impact_score > seen_markets[effect.target_market_id].impact_score:
                seen_markets[effect.target_market_id] = effect

        return list(seen_markets.values())

    def get_graph_data(self) -> dict:
        """Get graph data for dashboard visualization."""
        return self.graph.to_dict()
