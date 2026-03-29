"""Tier 2 memory — cross-agent context within a pipeline run.

When Agent A hands off to Agent B, this module builds a context
summary of A's output and injects it into B's prompt automatically.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PipelineMemory:
    """Cross-agent memory for a single pipeline run.

    Stores per-agent outputs and pipeline-level facts.  On handoff,
    builds a context string (optionally summarized) for the next agent.
    """

    def __init__(
        self,
        run_id: str,
        summarize_handoffs: bool = True,
    ) -> None:
        self.run_id = run_id
        self._summarize_handoffs = summarize_handoffs
        self._agent_outputs: dict[str, str] = {}
        self._facts: dict[str, Any] = {}

    def record_agent_output(self, agent_role: str, output: str) -> None:
        """Record an agent's output for cross-agent context injection."""
        self._agent_outputs[agent_role] = output

    async def build_handoff_context(
        self,
        from_role: str,
        to_role: str,
        client: Any,
        max_chars: int = 2000,
    ) -> str:
        """Build context string from one agent's output for the next.

        If ``summarize_handoffs`` is True and the output exceeds
        ``max_chars``, uses Ministral-3B to summarize (cheapest tier).
        Otherwise returns the raw output truncated.
        """
        output = self._agent_outputs.get(from_role, "")
        if not output:
            return f"Context from {from_role}: [no output recorded]"

        content: str
        if self._summarize_handoffs and len(output) > max_chars:
            try:
                response = await client.chat.complete_async(
                    model="ministral-3b-latest",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"Summarize the following output from agent "
                                f"'{from_role}' for agent '{to_role}'. "
                                "Keep key facts. Be concise."
                            ),
                        },
                        {"role": "user", "content": output[:max_chars * 2]},
                    ],
                )
                content = response.choices[0].message.content or output[:max_chars]
            except Exception:
                logger.warning(
                    "Handoff summarization failed — using truncated output",
                    exc_info=True,
                )
                content = output[:max_chars]
        else:
            content = output[:max_chars]

        return f"Context from {from_role}:\n{content}"

    def set_fact(self, key: str, value: Any) -> None:
        """Store a pipeline-level fact."""
        self._facts[key] = value

    def get_fact(self, key: str) -> Any | None:
        """Retrieve a pipeline-level fact."""
        return self._facts.get(key)

    def get_all_context(self) -> str:
        """Concatenate all agent outputs as a context string."""
        parts: list[str] = []
        for role, output in self._agent_outputs.items():
            parts.append(f"[{role}]:\n{output}")
        return "\n\n".join(parts)

    def reset(self) -> None:
        """Clear all stored outputs and facts."""
        self._agent_outputs.clear()
        self._facts.clear()
