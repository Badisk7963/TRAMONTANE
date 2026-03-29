"""Shared fixtures for Tramontane tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from tramontane.core.agent import Agent
from tramontane.core.pipeline import Pipeline
from tramontane.router.classifier import ClassificationMode, TaskClassifier
from tramontane.router.router import MistralRouter


@pytest.fixture
def sample_agent() -> Agent:
    """A simple agent for unit tests."""
    return Agent(
        role="Researcher",
        goal="Research EU AI regulations",
        backstory="Expert policy analyst with 10 years experience",
    )


@pytest.fixture
def budget_agent() -> Agent:
    """An agent with a budget ceiling."""
    return Agent(
        role="Writer",
        goal="Write reports",
        backstory="Senior technical writer",
        budget_eur=0.001,
    )


@pytest.fixture
def offline_classifier() -> TaskClassifier:
    """Task classifier in OFFLINE mode (no API key needed)."""
    return TaskClassifier(mode=ClassificationMode.OFFLINE)


@pytest.fixture
def offline_router() -> MistralRouter:
    """Router using OFFLINE classifier."""
    return MistralRouter()


@pytest.fixture
def sample_pipeline() -> Pipeline:
    """A two-agent pipeline for testing."""
    agents = [
        Agent(role="researcher", goal="Research", backstory="Expert"),
        Agent(role="analyst", goal="Analyze", backstory="Expert"),
    ]
    return Pipeline(
        name="test_pipeline",
        agents=agents,
        handoffs=[("researcher", "analyst")],
        budget_eur=0.10,
    )


@pytest.fixture
def test_db(tmp_path: Path) -> str:
    """Temporary database path, auto-cleaned by pytest."""
    return str(tmp_path / "test.db")
