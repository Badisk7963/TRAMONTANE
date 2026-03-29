"""Tramontane Agent — the core unit of work.

Every agent wraps a Mistral model call with identity (role/goal/backstory),
budget control, GDPR awareness, and automatic model routing.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Callable, Literal

import yaml
from pydantic import BaseModel, ConfigDict, PrivateAttr

from tramontane.core.exceptions import BudgetExceededError
from tramontane.router.models import get_model


class Agent(BaseModel):
    """A single Tramontane agent backed by a Mistral model.

    Combines CrewAI-style identity (role/goal/backstory) with
    Tramontane-unique budget control, GDPR levels, and automatic
    model routing.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ── IDENTITY (required — CrewAI UX pattern) ──────────────────────
    role: str
    goal: str
    backstory: str

    # ── MODEL ROUTING (Tramontane-unique) ────────────────────────────
    model: str = "auto"
    function_calling_model: str = "auto"
    reasoning_model: str | None = None
    locale: str = "en"

    # ── TOOLS ────────────────────────────────────────────────────────
    tools: list[Any] = []
    allow_code_execution: bool = False
    code_execution_mode: Literal["safe", "unsafe"] = "safe"

    # ── EXECUTION GUARDS (from CrewAI) ───────────────────────────────
    max_iter: int = 20
    max_rpm: int | None = None
    max_execution_time: int | None = None  # seconds
    max_retry_limit: int = 3
    respect_context_window: bool = True

    # ── INTELLIGENCE FLAGS ───────────────────────────────────────────
    reasoning: bool = False
    max_reasoning_attempts: int | None = 3
    streaming: bool = True
    inject_date: bool = False
    allow_delegation: bool = False

    # ── MEMORY (from Agno) ───────────────────────────────────────────
    memory: bool = True
    add_history_to_context: bool = True
    learning: bool = False

    # ── COST CONTROL (Tramontane-unique) ─────────────────────────────
    budget_eur: float | None = None

    # ── GDPR (Tramontane-unique) ─────────────────────────────────────
    gdpr_level: Literal["none", "standard", "strict"] = "none"
    store_on_cloud: bool = True

    # ── OBSERVABILITY ────────────────────────────────────────────────
    audit_actions: bool = True
    verbose: bool = False
    step_callback: Callable[..., Any] | None = None

    # ── PRIVATE STATE ────────────────────────────────────────────────
    _mistral_agent_id: str | None = PrivateAttr(default=None)
    _conversation_id: str | None = PrivateAttr(default=None)
    _cost_tracker: float = PrivateAttr(default=0.0)
    _run_count: int = PrivateAttr(default=0)

    # ── COST METHODS ─────────────────────────────────────────────────

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_alias: str,
    ) -> float:
        """Estimate the EUR cost for a call given token counts and model alias."""
        model_info = get_model(model_alias)
        return (
            (input_tokens / 1_000_000) * model_info.cost_per_1m_input_eur
            + (output_tokens / 1_000_000) * model_info.cost_per_1m_output_eur
        )

    def check_budget(self, estimated_cost: float) -> None:
        """Raise BudgetExceededError if adding estimated_cost would exceed the budget."""
        if self.budget_eur is not None:
            projected = self._cost_tracker + estimated_cost
            if projected > self.budget_eur:
                raise BudgetExceededError(
                    budget_eur=self.budget_eur,
                    spent_eur=self._cost_tracker,
                    pipeline_name=self.role,
                )

    def remaining_budget(self) -> float | None:
        """Return remaining budget in EUR, or None if no budget is set."""
        if self.budget_eur is None:
            return None
        return self.budget_eur - self._cost_tracker

    def register_cost(self, cost_eur: float) -> None:
        """Record a cost and check whether budget is now exceeded."""
        self._cost_tracker += cost_eur
        self.check_budget(0.0)

    # ── PROMPT BUILDING ──────────────────────────────────────────────

    def system_prompt(self) -> str:
        """Build the system prompt from identity fields.

        Prepends UTC datetime if inject_date is True.
        Appends chain-of-thought instruction if reasoning is True.
        """
        parts: list[str] = []

        if self.inject_date:
            now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            parts.append(f"Current date and time: {now}")

        parts.append(f"Role: {self.role}")
        parts.append(f"Goal: {self.goal}")
        parts.append(f"Backstory: {self.backstory}")

        if self.reasoning:
            parts.append(
                "Think step by step. Show your reasoning before giving a final answer."
            )

        return "\n".join(parts)

    # ── MISTRAL API MAPPING ──────────────────────────────────────────

    def to_mistral_params(self) -> dict[str, Any]:
        """Return a dict ready for mistralai client agent creation.

        Maps Tramontane agent fields to the Mistral Agents API parameters.
        """
        params: dict[str, Any] = {
            "model": self.model if self.model != "auto" else None,
            "name": self.role,
            "instructions": self.system_prompt(),
        }

        if self.tools:
            params["tools"] = self.tools

        if self.max_execution_time is not None:
            params["timeout"] = self.max_execution_time

        return params

    # ── YAML LOADING ─────────────────────────────────────────────────

    @classmethod
    def from_yaml(cls, path: str) -> Agent:
        """Load an agent definition from a YAML file.

        The YAML file should contain a mapping of Agent field names to values.
        """
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls(**data)
