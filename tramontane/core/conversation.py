"""Conversation management wrapping the Mistral Conversations API.

Tracks every exchange with token counts, costs, and GDPR awareness.
Uses client.beta.conversations and client.beta.agents from the
mistralai SDK.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class ConversationEntry(BaseModel):
    """A single entry (message, tool call, handoff, or error) in a conversation."""

    entry_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    conversation_id: str
    agent_id: str | None = None
    agent_role: str | None = None
    entry_type: str  # message.output | tool.execution | agent.handoff | error
    content: str
    model_used: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_eur: float = 0.0
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


# ---------------------------------------------------------------------------
# ConversationManager
# ---------------------------------------------------------------------------


class ConversationManager:
    """Manages Mistral conversations with token/cost tracking.

    Wraps the mistralai SDK beta endpoints for agent creation and
    conversation management.  When ``store_on_cloud`` is False the
    ``store=False`` flag is passed on all API calls (GDPR-friendly).
    """

    def __init__(
        self,
        api_key: str | None = None,
        store_on_cloud: bool = True,
        gdpr_level: str = "none",
    ) -> None:
        self._api_key = api_key
        self._store_on_cloud = store_on_cloud
        self._gdpr_level = gdpr_level

        # Client created lazily on first API call (typed Any — no SDK stubs)
        self._client: Any = None

        # Local history keyed by conversation_id
        self._history: dict[str, list[ConversationEntry]] = defaultdict(list)

    # -- Lazy client -------------------------------------------------------

    def _get_client(self) -> Any:
        """Return (and cache) the Mistral client."""
        if self._client is None:
            from mistralai import Mistral

            self._client = Mistral(api_key=self._api_key)
        return self._client

    # -- Public API --------------------------------------------------------

    async def start(
        self,
        agent_id: str,
        agent_role: str,
        first_message: str,
        handoff_execution: str = "client",
    ) -> str:
        """Start a new conversation with the given agent.

        Returns the conversation_id.
        """
        client = self._get_client()
        conversation_id = uuid.uuid4().hex

        try:
            response = await client.beta.conversations.start(
                agent_id=agent_id,
                message=first_message,
                handoff_execution=handoff_execution,
                store=self._store_on_cloud,
            )
            if hasattr(response, "conversation_id"):
                conversation_id = response.conversation_id
        except Exception:
            logger.warning(
                "Failed to start conversation via API — using local tracking",
                exc_info=True,
            )

        entry = ConversationEntry(
            conversation_id=conversation_id,
            agent_id=agent_id,
            agent_role=agent_role,
            entry_type="message.output",
            content=first_message,
        )
        self._history[conversation_id].append(entry)

        logger.debug(
            "Conversation %s started with agent %s (%s)",
            conversation_id, agent_id, agent_role,
        )
        return conversation_id

    async def append(
        self,
        conversation_id: str,
        message: str,
        agent_id: str | None = None,
    ) -> ConversationEntry:
        """Append a message to the conversation and return the response entry."""
        client = self._get_client()

        input_tokens = 0
        output_tokens = 0
        content = ""
        model_used: str | None = None

        try:
            response = await client.beta.conversations.append(
                conversation_id=conversation_id,
                message=message,
                store=self._store_on_cloud,
            )
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                content = choice.message.content or ""
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                input_tokens = getattr(usage, "prompt_tokens", 0)
                output_tokens = getattr(usage, "completion_tokens", 0)
            model_used = getattr(response, "model", None)
        except Exception:
            logger.warning(
                "Failed to append to conversation %s via API",
                conversation_id,
                exc_info=True,
            )
            content = message

        entry = ConversationEntry(
            conversation_id=conversation_id,
            agent_id=agent_id,
            entry_type="message.output",
            content=content,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        self._history[conversation_id].append(entry)
        return entry

    async def stream_append(
        self,
        conversation_id: str,
        message: str,
    ) -> AsyncGenerator[str, None]:
        """Yield token chunks as they arrive from the conversation.

        Records final token count on completion.
        """
        client = self._get_client()
        total_content = ""
        input_tokens = 0
        output_tokens = 0
        model_used: str | None = None

        try:
            stream = await client.beta.conversations.append(
                conversation_id=conversation_id,
                message=message,
                store=self._store_on_cloud,
                stream=True,
            )
            async for chunk in stream:
                if hasattr(chunk, "choices") and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        total_content += delta.content
                        yield delta.content
                if hasattr(chunk, "usage") and chunk.usage:
                    input_tokens = getattr(
                        chunk.usage, "prompt_tokens", 0
                    )
                    output_tokens = getattr(
                        chunk.usage, "completion_tokens", 0
                    )
                model_used = getattr(chunk, "model", model_used)
        except Exception:
            logger.warning(
                "Streaming failed for conversation %s",
                conversation_id,
                exc_info=True,
            )

        entry = ConversationEntry(
            conversation_id=conversation_id,
            entry_type="message.output",
            content=total_content,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        self._history[conversation_id].append(entry)

    def get_history(self, conversation_id: str) -> list[ConversationEntry]:
        """Return all entries for a conversation."""
        return list(self._history.get(conversation_id, []))

    def total_cost(self, conversation_id: str) -> float:
        """Return total cost in EUR for a conversation."""
        return sum(
            e.cost_eur for e in self._history.get(conversation_id, [])
        )

    def clear(self, conversation_id: str) -> None:
        """Remove local history for a conversation."""
        self._history.pop(conversation_id, None)
