"""Tramontane — Mistral-native agent orchestration framework."""

from __future__ import annotations

import logging

__version__ = "0.2.1"
__author__ = "Bleucommerce SAS"
__license__ = "MIT"

# Library best practice: let the user configure logging.
logging.getLogger("tramontane").addHandler(logging.NullHandler())

# Public API — convenience imports (after logging setup intentionally)
from tramontane.core.agent import Agent, AgentResult, RunContext, StreamEvent  # noqa: E402
from tramontane.core.pipeline import Pipeline  # noqa: E402
from tramontane.core.profiles import FleetProfile  # noqa: E402
from tramontane.core.simulate import (  # noqa: E402
    PipelineSimulation,
    simulate_agent,
    simulate_pipeline,
)
from tramontane.router.router import MistralRouter  # noqa: E402
from tramontane.router.telemetry import FleetTelemetry, RoutingOutcome  # noqa: E402

__all__ = [
    "Agent",
    "AgentResult",
    "PipelineSimulation",
    "RunContext",
    "StreamEvent",
    "Pipeline",
    "FleetProfile",
    "MistralRouter",
    "simulate_agent",
    "simulate_pipeline",
    "FleetTelemetry",
    "RoutingOutcome",
    "__version__",
]
