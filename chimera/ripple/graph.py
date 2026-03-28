"""RIPPLE: NetworkX-based causal knowledge graph.

Maps entities (people, organizations, countries, concepts) and their
causal relationships. When a news event triggers, the graph propagates
"ripple effects" to find second-order market impacts that the crowd
hasn't priced in.
"""

from __future__ import annotations

from collections import deque

import networkx as nx

from chimera.config import settings
from chimera.models.forecasts import RippleEffect


class CausalGraph:
    """Directed causal knowledge graph for second-order effect detection."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self._initialize_base_graph()

    def _initialize_base_graph(self):
        """Seed the graph with foundational geopolitical/economic relationships."""
        # ── Entities ──
        entities = [
            # Countries
            ("USA", {"type": "country"}),
            ("China", {"type": "country"}),
            ("Russia", {"type": "country"}),
            ("Ukraine", {"type": "country"}),
            ("Taiwan", {"type": "country"}),
            ("Iran", {"type": "country"}),
            ("EU", {"type": "organization"}),
            ("NATO", {"type": "organization"}),
            # People
            ("Trump", {"type": "person", "role": "US President"}),
            ("Xi Jinping", {"type": "person", "role": "Chinese President"}),
            ("Putin", {"type": "person", "role": "Russian President"}),
            ("Fed Chair", {"type": "person", "role": "Federal Reserve Chair"}),
            # Concepts
            ("Interest Rates", {"type": "concept"}),
            ("Inflation", {"type": "concept"}),
            ("Oil Prices", {"type": "concept"}),
            ("Tariffs", {"type": "concept"}),
            ("Sanctions", {"type": "concept"}),
            ("Recession", {"type": "concept"}),
            ("Bitcoin", {"type": "concept"}),
            ("S&P 500", {"type": "concept"}),
            ("USD Strength", {"type": "concept"}),
            ("Semiconductor Supply", {"type": "concept"}),
            ("Nuclear Weapons", {"type": "concept"}),
            ("Ceasefire", {"type": "concept"}),
        ]
        self.graph.add_nodes_from(entities)

        # ── Causal relationships ──
        edges = [
            # Fed & Economy
            ("Fed Chair", "Interest Rates", {"relation": "controls", "weight": 0.9}),
            ("Interest Rates", "Recession", {"relation": "influences", "weight": 0.7}),
            ("Interest Rates", "S&P 500", {"relation": "inversely_affects", "weight": 0.6}),
            ("Interest Rates", "Bitcoin", {"relation": "inversely_affects", "weight": 0.5}),
            ("Interest Rates", "USD Strength", {"relation": "strengthens", "weight": 0.7}),
            ("Inflation", "Interest Rates", {"relation": "pressures_up", "weight": 0.8}),
            ("Recession", "S&P 500", {"relation": "crashes", "weight": 0.8}),

            # Geopolitics
            ("Russia", "Ukraine", {"relation": "conflicts_with", "weight": 0.9}),
            ("Ceasefire", "Sanctions", {"relation": "may_reduce", "weight": 0.6}),
            ("Sanctions", "Oil Prices", {"relation": "increases", "weight": 0.7}),
            ("Sanctions", "Russia", {"relation": "pressures", "weight": 0.8}),
            ("China", "Taiwan", {"relation": "threatens", "weight": 0.7}),
            ("Taiwan", "Semiconductor Supply", {"relation": "critical_for", "weight": 0.9}),
            ("Semiconductor Supply", "S&P 500", {"relation": "affects", "weight": 0.5}),
            ("Iran", "Nuclear Weapons", {"relation": "pursues", "weight": 0.6}),
            ("Iran", "Oil Prices", {"relation": "affects", "weight": 0.6}),

            # Trade
            ("Trump", "Tariffs", {"relation": "imposes", "weight": 0.8}),
            ("Tariffs", "China", {"relation": "targets", "weight": 0.7}),
            ("Tariffs", "Inflation", {"relation": "increases", "weight": 0.6}),
            ("Tariffs", "S&P 500", {"relation": "depresses", "weight": 0.5}),
            ("Tariffs", "Recession", {"relation": "risk_of", "weight": 0.4}),

            # NATO
            ("NATO", "Russia", {"relation": "opposes", "weight": 0.8}),
            ("NATO", "Ukraine", {"relation": "supports", "weight": 0.7}),
            ("USA", "NATO", {"relation": "leads", "weight": 0.9}),

            # Oil
            ("Oil Prices", "Inflation", {"relation": "increases", "weight": 0.7}),
            ("Oil Prices", "Recession", {"relation": "risk_factor", "weight": 0.4}),

            # Crypto
            ("Recession", "Bitcoin", {"relation": "risk_asset_selloff", "weight": 0.4}),
            ("USD Strength", "Bitcoin", {"relation": "inversely_affects", "weight": 0.5}),
        ]
        self.graph.add_edges_from(edges)

    def add_entity(self, name: str, entity_type: str = "concept", **attrs):
        """Add an entity node to the graph."""
        self.graph.add_node(name, type=entity_type, **attrs)

    def add_relationship(self, source: str, target: str, relation: str, weight: float = 0.5):
        """Add a causal relationship between entities."""
        self.graph.add_edge(source, target, relation=relation, weight=weight)

    def ripple_analysis(
        self,
        trigger_entity: str,
        max_depth: int | None = None,
    ) -> list[RippleEffect]:
        """Run BFS ripple propagation from a trigger entity.

        Returns affected entities with decaying impact scores.
        """
        if max_depth is None:
            max_depth = settings.ripple.max_depth

        if trigger_entity not in self.graph:
            return []

        effects: list[RippleEffect] = []
        visited: set[str] = {trigger_entity}
        queue: deque[tuple[str, list[str], float, int]] = deque()

        # Initialize with direct neighbors
        for neighbor in self.graph.successors(trigger_entity):
            edge_data = self.graph[trigger_entity][neighbor]
            weight = edge_data.get("weight", 0.5)
            relation = edge_data.get("relation", "affects")
            queue.append((neighbor, [f"{trigger_entity} --{relation}--> {neighbor}"], weight, 1))

        while queue:
            node, chain, impact, depth = queue.popleft()

            if node in visited:
                continue
            visited.add(node)

            if impact < settings.ripple.min_relevance:
                continue

            effects.append(RippleEffect(
                source_entity=trigger_entity,
                target_market_id="",  # Filled by market_linker
                target_market_question="",
                relationship_chain=chain,
                impact_score=impact,
                depth=depth,
                adjustment=impact * 0.1 * (1 if "increases" in chain[-1] or "strengthens" in chain[-1] else -1),
            ))

            # Continue BFS if within depth limit
            if depth < max_depth:
                for neighbor in self.graph.successors(node):
                    if neighbor not in visited:
                        edge_data = self.graph[node][neighbor]
                        new_weight = impact * edge_data.get("weight", 0.5) * settings.ripple.decay_factor
                        relation = edge_data.get("relation", "affects")
                        new_chain = chain + [f"{node} --{relation}--> {neighbor}"]
                        queue.append((neighbor, new_chain, new_weight, depth + 1))

        # Sort by impact score
        effects.sort(key=lambda e: e.impact_score, reverse=True)
        return effects

    def get_node_data(self) -> list[dict]:
        """Get all nodes with their attributes for visualization."""
        nodes = []
        for node, data in self.graph.nodes(data=True):
            nodes.append({"id": node, **data})
        return nodes

    def get_edge_data(self) -> list[dict]:
        """Get all edges with their attributes for visualization."""
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({"source": source, "target": target, **data})
        return edges

    def to_dict(self) -> dict:
        """Serialize graph for JSON transmission to dashboard."""
        return {
            "nodes": self.get_node_data(),
            "edges": self.get_edge_data(),
        }
