"""HYDRA Judge: Final synthesis agent for the debate."""

from __future__ import annotations

from chimera.config import settings
from chimera.hydra.llm_backends import create_backend
from chimera.hydra.prompts import JUDGE_SYNTHESIS
from chimera.models.forecasts import AgentVote, DebateRound


async def run_judge(
    round1: DebateRound,
    challenge_text: str,
    round2: DebateRound,
) -> dict:
    """Run the Judge synthesis (Round 3).

    The Judge sees all rounds and produces the final probability.
    Uses Claude for strongest reasoning capabilities.
    """
    judge_cfg = settings.hydra.agents["judge"]
    backend = create_backend(judge_cfg.backend, judge_cfg.model)

    # Build Round 1 summary
    r1_lines = []
    for v in round1.votes:
        r1_lines.append(
            f"- {v.agent_name} ({v.agent_role}): {v.probability:.1%} "
            f"(confidence: {v.confidence:.0%}) — {v.reasoning}"
        )
    round1_summary = "\n".join(r1_lines)

    # Build Round 2 summary
    r2_lines = []
    for v in round2.votes:
        r2_lines.append(
            f"- {v.agent_name} ({v.agent_role}): {v.probability:.1%} "
            f"(confidence: {v.confidence:.0%}) — {v.reasoning}"
        )
    round2_summary = "\n".join(r2_lines)

    # Stability analysis: how much did each agent change?
    stability_lines = []
    r1_map = {v.agent_name: v.probability for v in round1.votes}
    for v in round2.votes:
        r1_prob = r1_map.get(v.agent_name, 0.5)
        delta = v.probability - r1_prob
        stability = "STABLE" if abs(delta) < 0.05 else f"SHIFTED {delta:+.1%}"
        stability_lines.append(f"- {v.agent_name}: {stability}")
    stability_analysis = "\n".join(stability_lines)

    prompt = JUDGE_SYNTHESIS.format(
        round1_summary=round1_summary,
        challenge_text=challenge_text,
        round2_summary=round2_summary,
        stability_analysis=stability_analysis,
    )

    result = await backend.complete_json(
        system="You are THE JUDGE — the final decision-maker in a multi-agent forecasting debate. You must produce a precise, well-calibrated probability estimate.",
        user=prompt,
        temperature=settings.hydra.temperature_judge,
        max_tokens=settings.hydra.max_tokens_judge,
    )

    return result
