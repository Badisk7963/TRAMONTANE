"""SSE streaming utilities for Tramontane pipelines.

Wraps pipeline execution with Server-Sent Events emission.
Always emits ``done`` as the final event so clients know to close.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel

from tramontane.core.exceptions import BudgetExceededError
from tramontane.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


class SSEEvent(BaseModel):
    """A single Server-Sent Event."""

    event: str
    data: dict[str, Any]
    id: str | None = None
    retry: int | None = None

    def to_sse_string(self) -> str:
        """Format as a proper SSE string."""
        parts: list[str] = []
        if self.id is not None:
            parts.append(f"id: {self.id}")
        parts.append(f"event: {self.event}")
        parts.append(f"data: {json.dumps(self.data)}")
        if self.retry is not None:
            parts.append(f"retry: {self.retry}")
        return "\n".join(parts) + "\n\n"


def _sse(event: str, data: dict[str, Any], event_id: str | None = None) -> str:
    """Quick helper to format an SSE event string."""
    return SSEEvent(event=event, data=data, id=event_id).to_sse_string()


class PipelineStreamer:
    """Wraps a Pipeline run with SSE event emission.

    Emits events: pipeline_start, agent_start, agent_complete,
    handoff, pipeline_complete, error, budget_exceeded, done.
    """

    def __init__(self, pipeline: Pipeline, run_id: str | None = None) -> None:
        self._pipeline = pipeline
        self._run_id = run_id or uuid.uuid4().hex

    async def stream(self, input_text: str) -> AsyncGenerator[str, None]:
        """Execute the pipeline and yield SSE events."""
        yield _sse("pipeline_start", {
            "run_id": self._run_id,
            "pipeline": self._pipeline.name,
            "agents": list(self._pipeline.agents.keys()),
        })

        try:
            pipe_run = await self._pipeline.run(input_text=input_text)

            # Emit per-agent events from the run record
            for i, agent_role in enumerate(pipe_run.agents_used):
                model = pipe_run.models_used[i] if i < len(pipe_run.models_used) else "auto"
                yield _sse("agent_start", {
                    "agent": agent_role,
                    "model": model,
                    "run_id": self._run_id,
                })
                yield _sse("agent_complete", {
                    "agent": agent_role,
                    "cost_eur": pipe_run.total_cost_eur / max(len(pipe_run.agents_used), 1),
                })

                # Emit handoff if not the last agent
                if i < len(pipe_run.agents_used) - 1:
                    yield _sse("handoff", {
                        "from": agent_role,
                        "to": pipe_run.agents_used[i + 1],
                    })

            yield _sse("pipeline_complete", {
                "total_cost_eur": pipe_run.total_cost_eur,
                "run_id": self._run_id,
                "status": pipe_run.status.value,
                "output": pipe_run.output or "",
            })

        except BudgetExceededError as exc:
            yield _sse("budget_exceeded", {
                "detail": str(exc),
                "run_id": self._run_id,
            })

        except Exception as exc:
            yield _sse("error", {
                "detail": str(exc),
                "run_id": self._run_id,
            })

        yield _sse("done", {"run_id": self._run_id})

    @staticmethod
    async def heartbeat() -> AsyncGenerator[str, None]:
        """Yield ping events every 15s to keep the connection alive."""
        while True:
            await asyncio.sleep(15)
            yield _sse("ping", {})
