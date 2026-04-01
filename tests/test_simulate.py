"""Tests for tramontane.core.simulate — pipeline cost simulation."""

from __future__ import annotations

from tramontane.core.agent import Agent
from tramontane.core.simulate import simulate_agent, simulate_pipeline


class TestSimulateAgent:
    """simulate_agent() cost estimation."""

    def test_returns_cost_estimate(self) -> None:
        a = Agent(role="Writer", goal="Write", backstory="Expert", model="mistral-small")
        sim = simulate_agent(a, "Write a blog post about AI in Europe")
        assert sim.estimated_cost_eur > 0
        assert sim.model_predicted == "mistral-small"
        assert sim.estimated_input_tokens > 0
        assert sim.estimated_output_tokens > 0

    def test_code_model_higher_output(self) -> None:
        a = Agent(role="Coder", goal="Code", backstory="Dev", model="devstral-small")
        sim = simulate_agent(a, "Write a sorting function")
        # Code models estimate 4x output vs 2x for general
        assert sim.estimated_output_tokens > sim.estimated_input_tokens

    def test_auto_model_without_router(self) -> None:
        a = Agent(role="R", goal="G", backstory="B", model="auto")
        sim = simulate_agent(a, "Hello")
        # Falls back to mistral-small when no router provided
        assert sim.model_predicted == "mistral-small"

    def test_auto_model_with_router(self, offline_router) -> None:  # type: ignore[no-untyped-def]
        a = Agent(role="R", goal="G", backstory="B", model="auto")
        sim = simulate_agent(a, "write a Python function", router=offline_router)
        # Router should pick a code model
        assert sim.model_predicted in ("devstral-small", "devstral-2")

    def test_budget_warning(self) -> None:
        a = Agent(
            role="R", goal="G", backstory="B",
            model="mistral-large",
            budget_eur=0.0000001,
        )
        sim = simulate_agent(a, "Analyze everything " * 50)
        assert any("exceeds" in w for w in sim.warnings)

    def test_cascade_warning(self) -> None:
        a = Agent(
            role="R", goal="G", backstory="B",
            model="devstral-small",
            cascade=["devstral-2"],
            validate_output=lambda r: True,
        )
        sim = simulate_agent(a, "hello")
        assert any("cascade" in w.lower() for w in sim.warnings)

    def test_progressive_effort_label(self) -> None:
        a = Agent(
            role="R", goal="G", backstory="B",
            model="mistral-small-4",
            reasoning_strategy="progressive",
        )
        sim = simulate_agent(a, "hello")
        assert sim.reasoning_effort is not None
        assert "progressive" in sim.reasoning_effort


class TestSimulatePipeline:
    """simulate_pipeline() cost estimation."""

    def test_pipeline_sums_costs(self) -> None:
        agents = [
            Agent(role="Planner", goal="Plan", backstory="Expert", model="mistral-small"),
            Agent(role="Builder", goal="Build", backstory="Dev", model="devstral-small"),
            Agent(role="Reviewer", goal="Review", backstory="QA", model="mistral-small"),
        ]
        sim = simulate_pipeline(agents, "Build an app")
        assert sim.total_estimated_cost_eur > 0
        assert len(sim.agents) == 3
        assert len(sim.models_predicted) == 3
        # Sum of agent costs equals total
        agent_sum = sum(a.estimated_cost_eur for a in sim.agents)
        assert abs(agent_sum - sim.total_estimated_cost_eur) < 0.000001

    def test_pipeline_over_budget(self) -> None:
        agents = [
            Agent(role="R", goal="G", backstory="B", model="mistral-large"),
        ]
        sim = simulate_pipeline(agents, "x" * 10000, budget_eur=0.0000001)
        assert sim.budget_status == "over_budget"
        assert any("exceeds" in w for w in sim.warnings)

    def test_pipeline_within_budget(self) -> None:
        agents = [
            Agent(role="R", goal="G", backstory="B", model="ministral-3b"),
        ]
        sim = simulate_pipeline(agents, "hello", budget_eur=10.0)
        assert sim.budget_status == "within_budget"

    def test_importable_from_package(self) -> None:
        from tramontane import simulate_agent, simulate_pipeline

        a = Agent(role="R", goal="G", backstory="B", model="mistral-small")
        assert simulate_agent(a, "hi").estimated_cost_eur >= 0
        assert simulate_pipeline([a], "hi").total_estimated_cost_eur >= 0
