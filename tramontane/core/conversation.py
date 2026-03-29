"""Conversation management wrapping the Mistral Conversations API.

Tracks every exchange with token counts, costs, and GDPR awareness.
Uses client.beta.conversations.start_async / append_async from the
mistralai SDK v2.x.
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

    Uses the Conversations API: ``start_async`` to begin, ``append_async``
    to continue.  The ``inputs`` parameter takes a plain string.
    Response ``outputs`` contains ``MessageOutputEntry`` objects with
    ``.content`` and ``.role``.
    """

    def __init__(
        self,
        api_key: str | None = None,
        store_on_cloud: bool = True,
        gdpr_level: str = "none",
    ) -> None:
        import os

        self._api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        self._store_on_cloud = store_on_cloud
        self._gdpr_level = gdpr_level
        self._client: Any = None
        self._history: dict[str, list[ConversationEntry]] = defaultdict(list)

    def _get_client(self) -> Any:
        """Return (and cache) the Mistral client."""
        if self._client is None:
            from mistralai.client import Mistral

            self._client = Mistral(api_key=self._api_key)
        return self._client

    # -- Public API --------------------------------------------------------

    async def start(
        self,
        agent_id: str,
        agent_role: str,
        first_message: str,
        model: str = "mistral-small-latest",
        instructions: str | None = None,
        handoff_execution: str = "client",
    ) -> str:
        """Start a new conversation via the Conversations API.

        Returns the conversation_id.
        """
        client = self._get_client()
        conversation_id = uuid.uuid4().hex
        content = first_message

        try:
            response = await client.beta.conversations.start_async(
                inputs=first_message,
                model=model,
                instructions=instructions,
                store=self._store_on_cloud,
            )
            conversation_id = response.conversation_id or conversation_id
            content = self._extract_output(response)

        except Exception:
            logger.debug(
                "Conversations API unavailable — falling back to chat completions",
            )
            content = await self._chat_fallback(
                client, model, instructions, first_message,
            )

        entry = ConversationEntry(
            conversation_id=conversation_id,
            agent_id=agent_id,
            agent_role=agent_role,
            entry_type="message.output",
            content=content,
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

        content = ""
        model_used: str | None = None

        try:
            response = await client.beta.conversations.append_async(
                conversation_id=conversation_id,
                inputs=message,
                store=self._store_on_cloud,
            )
            content = self._extract_output(response)
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
        )
        self._history[conversation_id].append(entry)
        return entry

    async def stream_append(
        self,
        conversation_id: str,
        message: str,
    ) -> AsyncGenerator[str, None]:
        """Yield token chunks as they arrive from the conversation."""
        client = self._get_client()
        total_content = ""
        model_used: str | None = None

        try:
            stream = client.beta.conversations.append_stream_async(
                conversation_id=conversation_id,
                inputs=message,
                store=self._store_on_cloud,
            )
            async for event in stream:
                # Extract text chunks from stream events
                text = self._extract_stream_chunk(event)
                if text:
                    total_content += text
                    yield text
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

    # -- Internal helpers --------------------------------------------------

    @staticmethod
    def _extract_output(response: Any) -> str:
        """Extract text content from a ConversationResponse."""
        outputs = getattr(response, "outputs", None) or []
        parts: list[str] = []
        for out in outputs:
            content = getattr(out, "content", None)
            if content:
                parts.append(str(content))
            elif hasattr(out, "text"):
                parts.append(str(out.text))
        return "\n".join(parts) if parts else ""

    @staticmethod
    def _extract_stream_chunk(event: Any) -> str:
        """Extract a text chunk from a streaming event."""
        if hasattr(event, "data"):
            data = event.data
            if hasattr(data, "content"):
                return str(data.content)
        if hasattr(event, "content"):
            return str(event.content)
        return ""

    @staticmethod
    async def _chat_fallback(
        client: Any,
        model: str,
        instructions: str | None,
        message: str,
    ) -> str:
        """Fallback to standard chat completions when Conversations API is unavailable."""
        messages: list[dict[str, str]] = []
        if instructions:
            messages.append({"role": "system", "content": instructions})
        messages.append({"role": "user", "content": message})

        response = await client.chat.complete_async(
            model=model,
            messages=messages,
        )
        return str(response.choices[0].message.content or "")
