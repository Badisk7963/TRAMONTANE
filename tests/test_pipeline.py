"""Tests for tramontane.core — pipeline, handoff, workflow."""

from __future__ import annotations

import pytest

from tramontane.core.agent import Agent
from tramontane.core.exceptions import (
    BudgetExceededError,
    HandoffLoopError,
    PipelineValidationError,
)
from tramontane.core.handoff import HandoffEdge, HandoffEvent, HandoffGraph, HandoffInterceptor
from tramontane.core.pipeline import Pipeline
from tramontane.core.workflow import Workflow, WorkflowStep, step


class TestHandoffGraph:
    """HandoffGraph validation and queries."""

    def test_creates_graph(self, sample_pipeline: Pipeline) -> None:
        assert sample_pipeline.handoff_graph is not None
        assert len(sample_pipeline.handoff_graph.edges) == 1

    def test_allowed_handoffs(self, sample_pipeline: Pipeline) -> None:
        allowed = sample_pipeline.handoff_graph.get_allowed_handoffs("researcher")
        assert "analyst" in allowed

    def test_depth_from(self, sample_pipeline: Pipeline) -> None:
        depth = sample_pipeline.handoff_graph.depth_from("researcher")
        assert depth == 1

    def test_mermaid_output(self, sample_pipeline: Pipeline) -> None:
        mermaid = sample_pipeline.handoff_graph.to_mermaid()
        assert "graph LR" in mermaid
        assert "researcher" in mermaid
        assert "analyst" in mermaid

    def test_entry_roles(self, sample_pipeline: Pipeline) -> None:
        entries = sample_pipeline.handoff_graph.entry_roles()
        assert "researcher" in entries

    def test_circular_handoff_detected(self) -> None:
        with pytest.raises(HandoffLoopError):
            HandoffGraph([
                HandoffEdge(from_agent_role="a", to_agent_role="b"),
                HandoffEdge(from_agent_role="b", to_agent_role="a"),
            ])

    def test_too_deep_handoff(self) -> None:
        edges = [
            HandoffEdge(from_agent_role=f"agent_{i}", to_agent_role=f"agent_{i + 1}")
            for i in range(15)
        ]
        with pytest.raises(HandoffLoopError):
            HandoffGraph(edges)


class TestHandoffInterceptor:
    """HandoffInterceptor budget and graph checks."""

    @pytest.mark.asyncio
    async def test_blocks_over_budget(self) -> None:
        graph = HandoffGraph([
            HandoffEdge(from_agent_role="a", to_agent_role="b"),
        ])
        interceptor = HandoffInterceptor(
            graph=graph,
            budget_tracker={"a": 0.15},
        )
        event = HandoffEvent(
            handoff_id="h1",
            from_agent_role="a",
            to_agent_role="b",
            conversation_id="c1",
            timestamp=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
        )
        with pytest.raises(BudgetExceededError):
            await interceptor.intercept(event, pipeline_budget_eur=0.10)


class TestPipeline:
    """Pipeline construction and validation."""

    def test_creates_with_agents(self, sample_pipeline: Pipeline) -> None:
        assert len(sample_pipeline.agents) == 2
        assert "researcher" in sample_pipeline.agents

    def test_invalid_role_in_handoff(self) -> None:
        agents = [Agent(role="a", goal="G", backstory="B")]
        with pytest.raises(PipelineValidationError):
            Pipeline(
                name="bad",
                agents=agents,
                handoffs=[("a", "nonexistent")],
            )

    def test_from_yaml(self) -> None:
        import tempfile

        import yaml

        data = {
            "name": "test_yaml",
            "agents": [
                {"role": "r1", "goal": "G1", "backstory": "B1"},
                {"role": "r2", "goal": "G2", "backstory": "B2"},
            ],
            "handoffs": [{"from": "r1", "to": "r2"}],
            "budget_eur": 0.05,
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False,
        ) as f:
            yaml.dump(data, f)
            f.flush()
            p = Pipeline.from_yaml(f.name)

        assert p.name == "test_yaml"
        assert len(p.agents) == 2
        assert p.budget_eur == 0.05


class TestWorkflow:
    """Workflow step management."""

    def test_topological_sort(self) -> None:
        agent = Agent(role="test", goal="G", backstory="B")

        async def step_a() -> str:
            return "a"

        async def step_b() -> str:
            return "b"

        steps = [
            WorkflowStep(step_id="b", name="step_b", fn=step_b, agent=agent, depends_on=["a"]),
            WorkflowStep(step_id="a", name="step_a", fn=step_a, agent=agent),
        ]
        wf = Workflow(name="test", steps=steps)
        order = [s.step_id for s in wf._step_order]
        assert order.index("a") < order.index("b")

    def test_step_decorator(self) -> None:
        @step(model="ministral-7b", budget_eur=0.001)
        async def my_step() -> str:
            return "done"

        assert getattr(my_step, "_is_step") is True
        assert getattr(my_step, "_step_model") == "ministral-7b"
