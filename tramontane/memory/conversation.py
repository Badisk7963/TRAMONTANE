"""Tier 1 memory — in-session conversation state.

Manages local message history with automatic summarization of old
messages using Ministral-7B to keep context windows manageable.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConversationMemory:
    """In-session conversation memory with auto-summarization.

    When the history grows past ``summarize_threshold``, the oldest
    messages are compressed into a summary using Ministral-7B (cheap, fast).
    """

    def __init__(
        self,
        max_history: int = 20,
        summarize_threshold: int = 15,
    ) -> None:
        self._max_history = max_history
        self._summarize_threshold = summarize_threshold
        self._messages: list[dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self._messages.append({"role": role, "content": content})

        # Enforce max history by dropping oldest (non-summary) entries
        if len(self._messages) > self._max_history:
            self._messages = self._messages[-self._max_history:]

    def get_context(self, n_recent: int = 10) -> str:
        """Format the last N messages as a context string."""
        recent = self._messages[-n_recent:]
        return "\n".join(
            f"[{m['role']}]: {m['content']}" for m in recent
        )

    def should_summarize(self) -> bool:
        """Check if the history is long enough to trigger summarization."""
        return len(self._messages) >= self._summarize_threshold

    async def summarize_oldest(self, client: Any) -> None:
        """Summarize the oldest half of messages using Ministral-7B.

        Replaces the oldest messages with a single summary entry.
        The ``client`` should be a mistralai.Mistral instance.
        """
        if len(self._messages) < 4:
            return

        half = len(self._messages) // 2
        to_summarize = self._messages[:half]
        to_keep = self._messages[half:]

        context = "\n".join(
            f"[{m['role']}]: {m['content']}" for m in to_summarize
        )

        try:
            response = await client.chat.complete_async(
                model="ministral-8b-latest",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Summarize this conversation concisely. "
                            "Preserve key facts, decisions, and action items."
                        ),
                    },
                    {"role": "user", "content": context},
                ],
            )
            summary = response.choices[0].message.content or "[summary]"
        except Exception:
            logger.warning(
                "Conversation summarization failed — keeping raw history",
                exc_info=True,
            )
            return

        self._messages = [
            {"role": "system", "content": f"[Summary of earlier messages]: {summary}"},
            *to_keep,
        ]

    def clear(self) -> None:
        """Clear all conversation history."""
        self._messages.clear()

    def token_estimate(self) -> int:
        """Rough token estimate for current history."""
        total_words = sum(
            len(m["content"].split()) for m in self._messages
        )
        return int(total_words * 1.3)

    @property
    def message_count(self) -> int:
        """Number of messages in history."""
        return len(self._messages)
