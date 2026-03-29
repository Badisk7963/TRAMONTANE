"""Tests for tramontane.core.agent."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from tramontane.core.agent import Agent
from tramontane.core.exceptions import BudgetExceededError


class TestAgentInstantiation:
    """Agent construction and defaults."""

    def test_defaults(self, sample_agent: Agent) -> None:
        assert sample_agent.model == "auto"
        assert sample_agent.streaming is True
        assert sample_agent.gdpr_level == "none"
        assert sample_agent.budget_eur is None
        assert sample_agent.memory is True
        assert sample_agent.max_iter == 20

    def test_custom_fields(self) -> None:
        a = Agent(
            role="Dev",
            goal="Code",
            backstory="Expert",
            model="devstral-small",
            budget_eur=0.05,
            reasoning=True,
            locale="fr",
        )
        assert a.model == "devstral-small"
        assert a.budget_eur == 0.05
        assert a.reasoning is True
        assert a.locale == "fr"


class TestSystemPrompt:
    """system_prompt() output."""

    def test_basic(self, sample_agent: Agent) -> None:
        prompt = sample_agent.system_prompt()
        assert "Role: Researcher" in prompt
        assert "Goal:" in prompt
        assert "Backstory:" in prompt

    def test_with_date(self) -> None:
        a = Agent(role="R", goal="G", backstory="B", inject_date=True)
        prompt = a.system_prompt()
        assert "Current date and time:" in prompt

    def test_with_reasoning(self) -> None:
        a = Agent(role="R", goal="G", backstory="B", reasoning=True)
        prompt = a.system_prompt()
        assert "step by step" in prompt.lower()


class TestCostControl:
    """Budget checking and cost estimation."""

    def test_estimate_cost_known_model(self, sample_agent: Agent) -> None:
        cost = sample_agent.estimate_cost(1000, 500, "mistral-small")
        assert cost > 0
        assert isinstance(cost, float)

    def test_check_budget_under_limit(self, budget_agent: Agent) -> None:
        budget_agent.check_budget(0.0005)  # Should not raise

    def test_check_budget_over_limit(self, budget_agent: Agent) -> None:
        with pytest.raises(BudgetExceededError):
            budget_agent.check_budget(0.002)

    def test_register_cost_accumulates(self, budget_agent: Agent) -> None:
        budget_agent.register_cost(0.0003)
        budget_agent.register_cost(0.0003)
        remaining = budget_agent.remaining_budget()
        assert remaining is not None
        assert remaining < 0.001

    def test_remaining_budget_none_when_no_budget(self, sample_agent: Agent) -> None:
        assert sample_agent.remaining_budget() is None

    def test_remaining_budget_decrements(self, budget_agent: Agent) -> None:
        budget_agent.register_cost(0.0005)
        remaining = budget_agent.remaining_budget()
        assert remaining is not None
        assert abs(remaining - 0.0005) < 1e-9


class TestMistralParams:
    """to_mistral_params() output."""

    def test_keys(self, sample_agent: Agent) -> None:
        params = sample_agent.to_mistral_params()
        assert "name" in params
        assert "instructions" in params


class TestFromYaml:
    """YAML loading."""

    def test_loads_correctly(self) -> None:
        data = {
            "role": "Coder",
            "goal": "Write code",
            "backstory": "Expert dev",
            "model": "devstral-small",
            "budget_eur": 0.01,
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False,
        ) as f:
            yaml.dump(data, f)
            f.flush()
            agent = Agent.from_yaml(f.name)

        assert agent.role == "Coder"
        assert agent.model == "devstral-small"
        assert agent.budget_eur == 0.01
        Path(f.name).unlink()
