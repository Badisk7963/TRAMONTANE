"""Fleet profile presets for common deployment strategies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FleetProfile(str, Enum):
    """Pre-configured fleet strategies."""

    BUDGET = "budget"
    BALANCED = "balanced"
    QUALITY = "quality"
    UNIFIED = "unified"


@dataclass
class ProfileConfig:
    """Configuration derived from a fleet profile."""

    default_model: str
    default_reasoning_effort: str | None
    force_model_map: dict[str, str]
    description: str


PROFILE_CONFIGS: dict[FleetProfile, ProfileConfig] = {
    FleetProfile.BUDGET: ProfileConfig(
        default_model="mistral-small-4",
        default_reasoning_effort="none",
        force_model_map={
            "classification": "ministral-3b",
            "bulk": "ministral-3b",
        },
        description="Cheapest: ~EUR 0.001/agent avg",
    ),
    FleetProfile.BALANCED: ProfileConfig(
        default_model="auto",
        default_reasoning_effort=None,
        force_model_map={},
        description="Smart routing: router decides everything",
    ),
    FleetProfile.QUALITY: ProfileConfig(
        default_model="mistral-small-4",
        default_reasoning_effort="high",
        force_model_map={
            "code": "devstral-2",
            "research": "mistral-large-3",
        },
        description="Best quality: ~EUR 0.005/agent avg",
    ),
    FleetProfile.UNIFIED: ProfileConfig(
        default_model="mistral-small-4",
        default_reasoning_effort=None,
        force_model_map={},
        description="One model: mistral-small-4 for everything",
    ),
}


def apply_profile(
    profile: FleetProfile,
    agent_model: str,
    task_type: str | None = None,
) -> tuple[str, str | None]:
    """Apply a fleet profile to determine model and reasoning effort."""
    config = PROFILE_CONFIGS[profile]
    if task_type and task_type in config.force_model_map:
        return config.force_model_map[task_type], None
    model = agent_model if agent_model != "auto" else config.default_model
    return model, config.default_reasoning_effort
