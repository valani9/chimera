"""HYDRA Debate Orchestrator.

Runs the full 3-round adversarial debate protocol:
  Round 1: Independent forecasts (parallel, 5 agents)
  Round 2: Contrarian challenge + agent revisions
  Round 3: Judge synthesis → final probability

Uses different LLM providers (Claude, GPT-4o, Gemini) across agents
for genuine cognitive diversity.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from chimera.config import settings
from chimera.hydra.agents import DebateAgent, create_agents
from chimera.hydra.judge import run_judge
from chimera.hydra.llm_backends import create_backend
from chimera.hydra.prompts import CONTRARIAN_CHALLENGE
from chimera.models.forecasts import AgentVote, DebateResult, DebateRound
from chimera.models.events import Signal


class DebateOrchestrator:
    """Orchestrates the full HYDRA multi-agent debate."""

    def __init__(self):
        self.agents = create_agents()
        self._debate_log: list[DebateResult] = []

    async def run_debate(
        self,
        market_question: str,
        market_price: float,
        market_id: str = "",
        category: str = "",
        signals: list[Signal] | None = None,
        best_bid: float = 0.0,
        best_ask: float = 1.0,
        spread: float = 1.0,
        bid_depth: float = 0.0,
        ask_depth: float = 0.0,
    ) -> DebateResult:
        """Run the full 3-round debate.

        Returns a DebateResult with the Judge's final probability.
        """
        signals_summary = self._format_signals(signals)
        total_calls = 0

        # ── ROUND 1: Independent forecasts (parallel) ──
        round1_tasks = []
        for role, agent in self.agents.items():
            round1_tasks.append(
                agent.forecast(
                    market_question=market_question,
                    market_price=market_price,
                    category=category,
                    signals_summary=signals_summary,
                    best_bid=best_bid,
                    best_ask=best_ask,
                    spread=spread,
                    bid_depth=bid_depth,
                    ask_depth=ask_depth,
                    temperature=settings.hydra.temperature_agents,
                    max_tokens=settings.hydra.max_tokens_per_agent,
                    round_number=1,
                )
            )

        round1_votes = await asyncio.gather(*round1_tasks)
        total_calls += len(round1_tasks)
        round1 = DebateRound(round_number=1, votes=list(round1_votes))

        # ── ROUND 2: Contrarian challenge + revisions ──
        # Step 2a: Contrarian generates challenge
        challenge_text = await self._run_contrarian_challenge(round1)
        total_calls += 1
        round1.challenge_text = challenge_text

        # Step 2b: Each agent revises (parallel)
        revision_tasks = []
        for vote in round1.votes:
            agent = self.agents.get(vote.agent_role)
            if agent:
                revision_tasks.append(
                    agent.revise(
                        challenge_text=challenge_text,
                        original_prob=vote.probability,
                        original_reasoning=vote.reasoning,
                        temperature=settings.hydra.temperature_agents,
                        max_tokens=settings.hydra.max_tokens_per_agent,
                    )
                )

        round2_votes = await asyncio.gather(*revision_tasks)
        total_calls += len(revision_tasks)
        round2 = DebateRound(round_number=2, votes=list(round2_votes))

        # ── ROUND 3: Judge synthesis ──
        judge_result = await run_judge(round1, challenge_text, round2)
        total_calls += 1

        result = DebateResult(
            market_id=market_id,
            market_question=market_question,
            rounds=[round1, round2],
            judge_probability=max(0.01, min(0.99, float(judge_result.get("probability", 0.5)))),
            judge_confidence=max(0.0, min(1.0, float(judge_result.get("confidence", 0.5)))),
            judge_reasoning=judge_result.get("reasoning", ""),
            dissenting_view=judge_result.get("dissenting_view", ""),
            total_llm_calls=total_calls,
        )

        self._debate_log.append(result)
        return result

    async def _run_contrarian_challenge(self, round1: DebateRound) -> str:
        """Have the Contrarian challenge Round 1 results."""
        # Build summary of Round 1
        r1_lines = []
        for v in round1.votes:
            r1_lines.append(
                f"- {v.agent_name} ({v.agent_role}): {v.probability:.1%} — {v.reasoning}"
            )
        round1_summary = "\n".join(r1_lines)

        contrarian_agent = self.agents.get("contrarian")
        if not contrarian_agent:
            return "No contrarian agent available."

        prompt = CONTRARIAN_CHALLENGE.format(round1_summary=round1_summary)

        try:
            result = await contrarian_agent.backend.complete_json(
                system="You are THE CONTRARIAN — an adversarial forecasting agent.",
                user=prompt,
                temperature=settings.hydra.temperature_agents,
                max_tokens=settings.hydra.max_tokens_per_agent,
            )
            return result.get("challenge", str(result))
        except Exception as e:
            return f"Challenge generation failed: {e}"

    def _format_signals(self, signals: list[Signal] | None) -> str:
        if not signals:
            return "No specific signals detected."

        lines = []
        for s in signals[:5]:  # Top 5 signals
            lines.append(f"- [{s.signal_type.value}] {s.title}: {s.detail} (score: {s.score:.2f})")
        return "\n".join(lines)

    def get_debate_log(self) -> list[DebateResult]:
        return list(self._debate_log)

    def get_last_debate(self) -> DebateResult | None:
        return self._debate_log[-1] if self._debate_log else None
