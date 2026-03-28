"""HYDRA agent definitions and individual agent execution."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from chimera.config import settings
from chimera.hydra.llm_backends import LLMBackend, create_backend
from chimera.hydra.prompts import AGENT_PROMPTS, AGENT_RESPONSE_FORMAT, MARKET_CONTEXT
from chimera.models.forecasts import AgentVote


@dataclass
class DebateAgent:
    """A single HYDRA debate agent with its LLM backend and role."""
    name: str
    role: str
    backend: LLMBackend
    system_prompt: str

    async def forecast(
        self,
        market_question: str,
        market_price: float,
        category: str,
        signals_summary: str,
        best_bid: float = 0.0,
        best_ask: float = 1.0,
        spread: float = 1.0,
        bid_depth: float = 0.0,
        ask_depth: float = 0.0,
        temperature: float = 0.7,
        max_tokens: int = 500,
        round_number: int = 1,
    ) -> AgentVote:
        """Run this agent's forecast on a market."""
        context = MARKET_CONTEXT.format(
            question=market_question,
            market_price=market_price,
            category=category,
            signals_summary=signals_summary,
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
        )

        user_prompt = f"{context}\n\n{AGENT_RESPONSE_FORMAT}"

        try:
            result = await self.backend.complete_json(
                system=self.system_prompt,
                user=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return AgentVote(
                agent_name=self.name,
                agent_role=self.role,
                llm_backend=type(self.backend).__name__,
                probability=max(0.01, min(0.99, float(result.get("probability", 0.5)))),
                confidence=max(0.0, min(1.0, float(result.get("confidence", 0.5)))),
                reasoning=result.get("reasoning", ""),
                key_evidence=result.get("key_evidence", []),
                round_number=round_number,
            )
        except Exception as e:
            return AgentVote(
                agent_name=self.name,
                agent_role=self.role,
                llm_backend=type(self.backend).__name__,
                probability=0.5,
                confidence=0.2,
                reasoning=f"Error during analysis: {str(e)[:100]}",
                round_number=round_number,
            )

    async def revise(
        self,
        challenge_text: str,
        original_prob: float,
        original_reasoning: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AgentVote:
        """Revise forecast after Contrarian challenge (Round 2)."""
        from chimera.hydra.prompts import AGENT_REVISION

        user_prompt = AGENT_REVISION.format(
            challenge_text=challenge_text,
            original_prob=original_prob,
            original_reasoning=original_reasoning,
        )

        try:
            result = await self.backend.complete_json(
                system=self.system_prompt,
                user=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return AgentVote(
                agent_name=self.name,
                agent_role=self.role,
                llm_backend=type(self.backend).__name__,
                probability=max(0.01, min(0.99, float(result.get("probability", 0.5)))),
                confidence=max(0.0, min(1.0, float(result.get("confidence", 0.5)))),
                reasoning=result.get("reasoning", ""),
                key_evidence=result.get("key_evidence", []),
                round_number=2,
            )
        except Exception as e:
            return AgentVote(
                agent_name=self.name,
                agent_role=self.role,
                probability=original_prob,
                confidence=0.3,
                reasoning=f"Revision failed: {str(e)[:100]}. Maintaining original position.",
                round_number=2,
            )


def create_agents() -> dict[str, DebateAgent]:
    """Create the full HYDRA agent roster from config."""
    agents = {}
    hydra_cfg = settings.hydra

    for role, agent_cfg in hydra_cfg.agents.items():
        if role == "judge":
            continue  # Judge is handled separately

        system_prompt = AGENT_PROMPTS.get(role, AGENT_PROMPTS["quant"])
        backend = create_backend(agent_cfg.backend, agent_cfg.model)

        agents[role] = DebateAgent(
            name=agent_cfg.name,
            role=role,
            backend=backend,
            system_prompt=system_prompt,
        )

    return agents
