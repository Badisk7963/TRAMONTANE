"""Tramontane custom exceptions.

Every Mistral API call must be wrapped in try/except catching these.
"""

from __future__ import annotations


class TramontaneError(Exception):
    """Base exception for all Tramontane errors."""


class BudgetExceededError(TramontaneError):
    """Raised when a pipeline or agent exceeds its EUR budget ceiling."""

    def __init__(
        self,
        budget_eur: float,
        spent_eur: float,
        pipeline_name: str,
        message: str | None = None,
    ) -> None:
        self.budget_eur = budget_eur
        self.spent_eur = spent_eur
        self.pipeline_name = pipeline_name
        super().__init__(
            message
            or (
                f"Budget exceeded for pipeline '{pipeline_name}': "
                f"spent €{spent_eur:.4f} of €{budget_eur:.4f}"
            )
        )


class AgentTimeoutError(TramontaneError):
    """Raised when an agent exceeds its maximum execution time."""

    def __init__(
        self,
        agent_role: str,
        timeout_seconds: int,
        message: str | None = None,
    ) -> None:
        self.agent_role = agent_role
        self.timeout_seconds = timeout_seconds
        super().__init__(
            message
            or f"Agent '{agent_role}' timed out after {timeout_seconds}s"
        )


class HandoffLoopError(TramontaneError):
    """Raised when a circular handoff is detected or max depth exceeded."""

    def __init__(
        self,
        agent_ids: list[str],
        depth: int,
        message: str | None = None,
    ) -> None:
        self.agent_ids = agent_ids
        self.depth = depth
        super().__init__(
            message
            or (
                f"Handoff loop detected at depth {depth}: "
                f"agents visited = {agent_ids}"
            )
        )


class HandoffError(TramontaneError):
    """Raised when a handoff between agents fails."""

    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        reason: str,
        message: str | None = None,
    ) -> None:
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.reason = reason
        super().__init__(
            message
            or f"Handoff from '{from_agent}' to '{to_agent}' failed: {reason}"
        )


class RouterError(TramontaneError):
    """Raised when the model router cannot resolve a model for the task."""

    def __init__(
        self,
        task_type: str,
        reason: str,
        message: str | None = None,
    ) -> None:
        self.task_type = task_type
        self.reason = reason
        super().__init__(
            message
            or f"Router error for task type '{task_type}': {reason}"
        )


class PIIDetectedError(TramontaneError):
    """Raised when PII is found in a field that must be clean."""

    def __init__(
        self,
        field: str,
        pii_type: str,
        message: str | None = None,
    ) -> None:
        self.field = field
        self.pii_type = pii_type
        super().__init__(
            message
            or f"PII detected in field '{field}': type={pii_type}"
        )


class AuditError(TramontaneError):
    """Raised when the audit log cannot be written."""


class PipelineValidationError(TramontaneError):
    """Raised when a pipeline YAML fails schema validation."""

    def __init__(
        self,
        pipeline_name: str,
        errors: list[str],
        message: str | None = None,
    ) -> None:
        self.pipeline_name = pipeline_name
        self.errors = errors
        super().__init__(
            message
            or (
                f"Pipeline '{pipeline_name}' validation failed: "
                f"{'; '.join(errors)}"
            )
        )


class ModelNotAvailableError(TramontaneError):
    """Raised when a requested Mistral model is unavailable."""

    def __init__(
        self,
        model: str,
        reason: str,
        message: str | None = None,
    ) -> None:
        self.model = model
        self.reason = reason
        super().__init__(
            message
            or f"Model '{model}' is not available: {reason}"
        )


class GDPRViolationError(TramontaneError):
    """Raised when a GDPR compliance rule is violated."""

    def __init__(
        self,
        violation_type: str,
        detail: str,
        message: str | None = None,
    ) -> None:
        self.violation_type = violation_type
        self.detail = detail
        super().__init__(
            message
            or f"GDPR violation ({violation_type}): {detail}"
        )
