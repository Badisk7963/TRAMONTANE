"""Pipeline cost simulation — estimate cost before running."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from tramontane.core.agent import Agent
from tramontane.router.models import MISTRAL_MODELS

logger = logging.getLogger(__name__)


@dataclass
class AgentSimulation:
    """Simulated result for a single agent."""

    role: str
    model_predicted: str
    reasoning_effort: str | None = None
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost_eur: float = 0.0
    estimated_time_s: float = 0.0
    warnings: list[str] = field(default_factory=list)


@dataclass
class PipelineSimulation:
    """Simulated result for a full pipeline."""

    agents: list[AgentSimulation] = field(default_factory=list)
    total_estimated_cost_eur: float = 0.0
    total_estimated_time_s: float = 0.0
    models_predicted: list[str] = field(default_factory=list)
    budget_status: str = "within_budget"
    warnings: list[str] = field(default_factory=list)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English."""
    return max(1, len(text) // 4)


def simulate_agent(
    agent: Agent,
    input_text: str,
    router: Any | None = None,
) -> AgentSimulation:
    """Estimate the cost of running an agent without calling the API.

    Uses the agent's model config, budget, and input length to predict
    cost, model selection, and execution time.
    """
    # Determine model
    model_alias = agent.model
    if model_alias == "auto" and router is not None:
        decision = router.route_sync(
            prompt=input_text,
            budget=agent.budget_eur,
            locale=agent.locale,
            context=agent.routing_hint,
        )
        model_alias = decision.primary_model
    elif model_alias == "auto":
        model_alias = "mistral-small"  # default fallback

    model_info = MISTRAL_MODELS.get(model_alias)

    # Estimate tokens
    system_tokens = _estimate_tokens(
        f"{agent.role} {agent.goal} {agent.backstory}"
    )
    input_tokens = system_tokens + _estimate_tokens(input_text)

    # Estimate output (rough: 2x input for general, 4x for code)
    if model_info and any(s in model_info.strengths for s in ["code", "swe"]):
        output_tokens = input_tokens * 4
    else:
        output_tokens = input_tokens * 2

    # Cap at max_output_tokens
    max_out = agent.max_tokens or (model_info.max_output_tokens if model_info else 8192)
    output_tokens = min(output_tokens, max_out)

    # Calculate cost
    cost_in = model_info.cost_per_1m_input_eur if model_info else 0.10
    cost_out = model_info.cost_per_1m_output_eur if model_info else 0.30
    estimated_cost = (input_tokens / 1_000_000 * cost_in) + (
        output_tokens / 1_000_000 * cost_out
    )

    # Estimate time (rough: 50 tokens/sec for tier <=2, 30 for higher)
    tier = model_info.tier if model_info else 2
    tokens_per_sec = 50 if tier <= 2 else 30
    estimated_time = (input_tokens + output_tokens) / tokens_per_sec

    # Warnings
    warnings: list[str] = []
    if agent.budget_eur and estimated_cost > agent.budget_eur:
        warnings.append(
            f"Estimated cost EUR {estimated_cost:.4f} exceeds "
            f"agent budget EUR {agent.budget_eur}"
        )
    if agent.cascade:
        warnings.append(
            "Has cascade — may use more expensive model if validation fails"
        )

    # Reasoning effort
    effort: str | None = agent.reasoning_effort
    if agent.reasoning_strategy == "progressive":
        effort = "progressive (none->medium->high)"

    return AgentSimulation(
        role=agent.role,
        model_predicted=model_alias,
        reasoning_effort=effort,
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        estimated_cost_eur=round(estimated_cost, 6),
        estimated_time_s=round(estimated_time, 1),
        warnings=warnings,
    )


def simulate_pipeline(
    agents: list[Agent],
    input_text: str,
    budget_eur: float | None = None,
    router: Any | None = None,
) -> PipelineSimulation:
    """Estimate the cost of a full pipeline without calling any API.

    Args:
        agents: List of agents in execution order.
        input_text: The initial input prompt.
        budget_eur: Total pipeline budget (optional).
        router: MistralRouter instance for model="auto" agents.

    Returns:
        PipelineSimulation with cost and time estimates.
    """
    sim = PipelineSimulation()
    current_input = input_text

    for agent in agents:
        agent_sim = simulate_agent(agent, current_input, router)
        sim.agents.append(agent_sim)
        sim.total_estimated_cost_eur += agent_sim.estimated_cost_eur
        sim.total_estimated_time_s += agent_sim.estimated_time_s
        sim.models_predicted.append(agent_sim.model_predicted)
        sim.warnings.extend(agent_sim.warnings)

        # Next agent's input is roughly this agent's output
        current_input = "x" * (agent_sim.estimated_output_tokens * 4)

    sim.total_estimated_cost_eur = round(sim.total_estimated_cost_eur, 6)
    sim.total_estimated_time_s = round(sim.total_estimated_time_s, 1)

    if budget_eur is not None and sim.total_estimated_cost_eur > budget_eur:
        sim.budget_status = "over_budget"
        sim.warnings.append(
            f"Estimated total EUR {sim.total_estimated_cost_eur:.4f} "
            f"exceeds budget EUR {budget_eur}"
        )

    return sim
