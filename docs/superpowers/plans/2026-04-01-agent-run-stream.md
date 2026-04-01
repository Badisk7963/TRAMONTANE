# Agent.run_stream() Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add token-by-token streaming to `Agent` so ArkhosAI can show live HTML generation (the "Lovable feeling").

**Architecture:** `Agent.run_stream()` is an `AsyncGenerator` that wraps `client.chat.stream_async()` from the Mistral SDK (v2.1.3). It yields `StreamEvent` Pydantic models — one per token chunk — then a final "complete" event carrying the full `AgentResult`. All the same pre-flight logic as `run()` (model resolution, budget check, message building) runs before the first yield. Post-stream, actual cost is computed from `CompletionChunk.usage` on the final chunk.

**Tech Stack:** Python 3.12, mistralai 2.1.3 (`client.chat.stream_async` → `EventStreamAsync[CompletionEvent]`), Pydantic v2, pytest-asyncio, respx for mocking.

---

## Mistral SDK Streaming API (verified from installed v2.1.3)

```
client.chat.stream_async(model=..., messages=...)
  → EventStreamAsync[CompletionEvent]   (async context manager + async iterator)

CompletionEvent.data: CompletionChunk
  CompletionChunk.id: str
  CompletionChunk.model: str
  CompletionChunk.choices: List[CompletionResponseStreamChoice]
  CompletionChunk.usage: Optional[UsageInfo]   ← populated on final chunk

CompletionResponseStreamChoice.index: int
CompletionResponseStreamChoice.delta: DeltaMessage
CompletionResponseStreamChoice.finish_reason: Optional[str]

DeltaMessage.content: Optional[str]   ← the token text
DeltaMessage.tool_calls: Optional[List[ToolCall]]

UsageInfo.prompt_tokens: Optional[int]
UsageInfo.completion_tokens: Optional[int]
```

**Usage pattern:**
```python
async with await client.chat.stream_async(model=m, messages=msgs) as stream:
    async for event in stream:
        chunk = event.data                    # CompletionChunk
        token = chunk.choices[0].delta.content  # str | None
        if chunk.usage:                       # final chunk
            input_tokens = chunk.usage.prompt_tokens
            output_tokens = chunk.usage.completion_tokens
```

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `tramontane/core/agent.py` | Modify | Add `StreamEvent` model + `run_stream()` method |
| `tramontane/__init__.py` | Modify | Export `StreamEvent` |
| `tests/test_agent.py` | Modify | Add streaming tests |
| `tramontane/__init__.py` | Modify | Bump `__version__` to `"0.1.5"` |
| `pyproject.toml` | Modify | Bump `version` to `"0.1.5"` |
| `CHANGELOG.md` | Modify | Add v0.1.5 entry |

---

### Task 1: Add StreamEvent model

**Files:**
- Modify: `tramontane/core/agent.py` (after `AgentResult` class, ~line 41)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_agent.py` at the end of the file:

```python
class TestStreamEvent:
    """StreamEvent model."""

    def test_token_event(self) -> None:
        from tramontane.core.agent import StreamEvent

        e = StreamEvent(type="token", token="hello", model_used="mistral-small")
        assert e.type == "token"
        assert e.token == "hello"
        assert e.result is None

    def test_complete_event_with_result(self) -> None:
        from tramontane.core.agent import StreamEvent

        result = AgentResult(output="done", model_used="mistral-small")
        e = StreamEvent(type="complete", result=result, model_used="mistral-small")
        assert e.type == "complete"
        assert e.result is not None
        assert e.result.output == "done"

    def test_error_event(self) -> None:
        from tramontane.core.agent import StreamEvent

        e = StreamEvent(type="error", error="API failed")
        assert e.type == "error"
        assert e.error == "API failed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_agent.py::TestStreamEvent -v`
Expected: FAIL — `ImportError: cannot import name 'StreamEvent'`

- [ ] **Step 3: Write StreamEvent model**

In `tramontane/core/agent.py`, add after the `AgentResult` class (after line 41):

```python
class StreamEvent(BaseModel):
    """Event emitted during streaming agent execution.

    Yielded by Agent.run_stream() — one per token chunk, then
    a final 'complete' event carrying the full AgentResult.
    """

    type: Literal["start", "token", "complete", "error"]
    token: str = ""
    model_used: str = ""
    result: AgentResult | None = None
    error: str = ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_agent.py::TestStreamEvent -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add tramontane/core/agent.py tests/test_agent.py
git commit -m "feat: add StreamEvent model for token-by-token streaming"
```

---

### Task 2: Implement run_stream()

**Files:**
- Modify: `tramontane/core/agent.py` (add method to Agent class, after `run()`)
- Modify: `tests/test_agent.py` (add streaming tests)

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_agent.py`:

```python
class TestRunStream:
    """Agent.run_stream() streaming execution."""

    @pytest.mark.asyncio
    async def test_empty_input_raises(self, sample_agent: Agent) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            async for _ in sample_agent.run_stream(""):
                pass

    @pytest.mark.asyncio
    async def test_budget_checked_before_streaming(self) -> None:
        """Budget check fires before any streaming starts."""
        a = Agent(
            role="R", goal="G", backstory="B",
            model="mistral-large",
            budget_eur=0.0000001,  # impossibly tight
        )
        from tramontane.core.agent import StreamEvent

        events: list[StreamEvent] = []
        async for event in a.run_stream("Analyze everything in detail " * 100):
            events.append(event)
        # Should get exactly one error event (budget exceeded)
        assert len(events) == 1
        assert events[0].type == "error"
        assert "budget" in events[0].error.lower() or "Budget" in events[0].error

    @pytest.mark.asyncio
    async def test_missing_api_key_yields_error(self) -> None:
        """Missing API key yields an error event, not an exception."""
        import os

        a = Agent(role="R", goal="G", backstory="B", model="mistral-small")
        original = os.environ.pop("MISTRAL_API_KEY", None)
        try:
            from tramontane.core.agent import StreamEvent

            events: list[StreamEvent] = []
            async for event in a.run_stream("hello"):
                events.append(event)
            assert len(events) == 1
            assert events[0].type == "error"
            assert "MISTRAL_API_KEY" in events[0].error
        finally:
            if original:
                os.environ["MISTRAL_API_KEY"] = original
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_agent.py::TestRunStream -v`
Expected: FAIL — `AttributeError: 'Agent' object has no attribute 'run_stream'`

- [ ] **Step 3: Implement run_stream()**

In `tramontane/core/agent.py`, add `AsyncGenerator` to imports at the top of the file. Change:

```python
from typing import Any, Callable, Literal
```

to:

```python
from collections.abc import AsyncGenerator
from typing import Any, Callable, Literal
```

Then add this method to the `Agent` class, right after the `run()` method (after the line `return AgentResult(`...closing block):

```python
    async def run_stream(
        self,
        input_text: str,
        *,
        router: Any | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        run_id: str | None = None,
        spent_eur: float = 0.0,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Execute this agent with token-by-token streaming.

        Yields StreamEvent objects as tokens are generated.
        The final event has type="complete" with a full AgentResult.
        Errors are yielded as type="error" events (never raised).

        Same pre-flight as run(): model resolution, budget check,
        message building. Post-stream actual cost uses real token counts.

        Args:
            input_text: The user/handoff message to process.
            router: Optional MistralRouter for model="auto" resolution.
            conversation_history: Prior messages to include as context.
            run_id: Trace identifier (generated if not provided).
            spent_eur: Total already spent by Pipeline (for budget check).

        Yields:
            StreamEvent with type in ("start", "token", "complete", "error").
        """
        import anyio
        from mistralai.client import Mistral

        # -- Input validation --
        if not input_text or not input_text.strip():
            yield StreamEvent(
                type="error",
                error=f"Agent '{self.role}': input_text must be a non-empty string",
            )
            return
        if self.budget_eur is not None and self.budget_eur < 0:
            yield StreamEvent(
                type="error",
                error=f"Agent '{self.role}': budget_eur must be >= 0, got {self.budget_eur}",
            )
            return

        rid = run_id or uuid.uuid4().hex[:12]

        # 1. Resolve model
        model_alias = self.model
        if model_alias == "auto" and router is not None:
            try:
                routing_decision = await router.route(
                    prompt=input_text,
                    agent_budget_eur=self.budget_eur,
                    locale=self.locale,
                )
                model_alias = routing_decision.primary_model
            except Exception as exc:
                yield StreamEvent(type="error", error=str(exc))
                return

        model_info = MISTRAL_MODELS.get(model_alias)
        api_model = model_info.api_id if model_info else model_alias

        # 2. Build messages
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt()},
        ]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": input_text})

        # 3. Pre-call budget check
        if model_info:
            est_cost = self._estimate_call_cost(messages, model_info)
            try:
                self.check_budget(est_cost, spent_eur=spent_eur)
            except BudgetExceededError as exc:
                yield StreamEvent(type="error", error=str(exc))
                return

        # 4. API key check
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            yield StreamEvent(
                type="error",
                error="MISTRAL_API_KEY environment variable is not set",
            )
            return

        # 5. Yield start event
        yield StreamEvent(type="start", model_used=model_alias)

        # 6. Stream from Mistral with retry + backoff
        client = Mistral(api_key=api_key)
        start_time = time.monotonic()
        full_output = ""
        input_tokens = 0
        output_tokens = 0

        for attempt in range(self.max_retry_limit + 1):
            try:
                stream = await client.chat.stream_async(
                    model=api_model,
                    messages=messages,  # type: ignore[arg-type]
                )
                async with stream as event_stream:
                    async for event in event_stream:
                        chunk = event.data
                        if chunk.choices:
                            delta = chunk.choices[0].delta
                            token_text = str(delta.content) if delta.content else ""
                            if token_text:
                                full_output += token_text
                                yield StreamEvent(
                                    type="token",
                                    token=token_text,
                                    model_used=model_alias,
                                )
                        # Final chunk carries usage info
                        if chunk.usage:
                            input_tokens = chunk.usage.prompt_tokens or 0
                            output_tokens = chunk.usage.completion_tokens or 0
                break  # success

            except Exception as exc:
                if attempt >= self.max_retry_limit:
                    yield StreamEvent(type="error", error=str(exc))
                    return
                wait = min(2 ** attempt, 30)
                logger.warning(
                    "[%s] Stream error (attempt %d/%d): %s — retrying in %ds",
                    rid, attempt + 1, self.max_retry_limit + 1, exc, wait,
                )
                await anyio.sleep(wait)

        duration = time.monotonic() - start_time

        # 7. Calculate actual cost
        actual_cost = 0.0
        if model_info:
            actual_cost = (
                (input_tokens / 1_000_000) * model_info.cost_per_1m_input_eur
                + (output_tokens / 1_000_000) * model_info.cost_per_1m_output_eur
            )

        logger.debug(
            "[%s] stream agent=%s model=%s tokens=%d/%d cost=EUR %.6f dur=%.2fs",
            rid, self.role, model_alias, input_tokens, output_tokens,
            actual_cost, duration,
        )

        # 8. Yield complete event with full AgentResult
        yield StreamEvent(
            type="complete",
            model_used=model_alias,
            result=AgentResult(
                output=full_output,
                model_used=model_alias,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_eur=actual_cost,
                duration_seconds=round(duration, 3),
                tool_calls=[],
                reasoning_used=self.reasoning,
            ),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_agent.py::TestRunStream -v`
Expected: 3 PASSED

- [ ] **Step 5: Run ruff + mypy**

Run: `uv run ruff check . && uv run mypy tramontane/`
Expected: All checks passed, no issues

- [ ] **Step 6: Commit**

```bash
git add tramontane/core/agent.py tests/test_agent.py
git commit -m "feat: add Agent.run_stream() for token-by-token streaming"
```

---

### Task 3: Update exports

**Files:**
- Modify: `tramontane/__init__.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_agent.py`:

```python
class TestPublicExports:
    """Package-level exports."""

    def test_stream_event_importable_from_package(self) -> None:
        from tramontane import StreamEvent

        e = StreamEvent(type="start", model_used="mistral-small")
        assert e.type == "start"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_agent.py::TestPublicExports -v`
Expected: FAIL — `ImportError: cannot import name 'StreamEvent' from 'tramontane'`

- [ ] **Step 3: Update __init__.py**

In `tramontane/__init__.py`, change:

```python
from tramontane.core.agent import Agent, AgentResult  # noqa: E402
```

to:

```python
from tramontane.core.agent import Agent, AgentResult, StreamEvent  # noqa: E402
```

And change `__all__` from:

```python
__all__ = [
    "Agent",
    "AgentResult",
    "Pipeline",
    "MistralRouter",
    "__version__",
]
```

to:

```python
__all__ = [
    "Agent",
    "AgentResult",
    "StreamEvent",
    "Pipeline",
    "MistralRouter",
    "__version__",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_agent.py::TestPublicExports -v`
Expected: PASSED

- [ ] **Step 5: Commit**

```bash
git add tramontane/__init__.py tests/test_agent.py
git commit -m "feat: export StreamEvent from tramontane package"
```

---

### Task 4: Version bump and changelog

**Files:**
- Modify: `pyproject.toml:3` (version field)
- Modify: `tramontane/__init__.py:7` (__version__)
- Modify: `CHANGELOG.md` (prepend new entry)

- [ ] **Step 1: Bump version in pyproject.toml**

In `pyproject.toml`, change line 3:

```toml
version = "0.1.4"
```

to:

```toml
version = "0.1.5"
```

- [ ] **Step 2: Bump version in __init__.py**

In `tramontane/__init__.py`, change line 7:

```python
__version__ = "0.1.4"
```

to:

```python
__version__ = "0.1.5"
```

- [ ] **Step 3: Add CHANGELOG entry**

Prepend to `CHANGELOG.md` (after the `# Changelog` heading, before `## v0.1.3`):

```markdown
## v0.1.5 (2026-04-01)

### Added
- **Agent.run_stream()** — Token-by-token async streaming via Mistral SDK's
  `chat.stream_async()`. Yields `StreamEvent` objects (start/token/complete/error).
  Enables live preview in ArkhosAI and any SSE-based frontend.
- **StreamEvent** model — Pydantic model for streaming events, exported from
  `tramontane` package.

### Fixed
- **Router classifier validation** — Online classifier output is now validated
  and normalized before routing. Invalid task types (e.g. "design", "creative",
  "analysis") are remapped to valid types. Unknown types default to "general".
  Added `VALID_TASK_TYPES`, `TASK_TYPE_ALIASES`, `_validate_task_type()`.
- **Budget pre-estimation too aggressive** — `_estimate_call_cost()` multipliers
  reduced (output: 2.0→1.2 reasoning, 1.5→0.8 general; overhead: 1.4→1.1).
  `check_budget()` now uses 2x tolerance (soft pre-call guard). Prevents
  BudgetExceededError on affordable ministral-3b calls with tight budgets.
- **TaskType enum updated** — Removed "creative"/"analysis" (unmapped in router),
  added "classification"/"voice" with proper routing and quality floors.

### Validated
- 74 + 7 = 81 unit tests passing
- ruff clean, mypy clean
```

- [ ] **Step 4: Run full validation**

```bash
uv run ruff check .
uv run mypy tramontane/
uv run pytest tests/ -v
```

Expected: All checks passed, 81 tests, 0 failures

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tramontane/__init__.py CHANGELOG.md
git commit -m "release: v0.1.5 — streaming, classifier validation, budget fix"
```

---

### Task 5: Build, publish, and tag

**Files:** None (release operations only)

- [ ] **Step 1: Build the package**

```bash
uv build
```

Expected: `dist/tramontane-0.1.5.tar.gz` and `dist/tramontane-0.1.5-py3-none-any.whl`

- [ ] **Step 2: Verify the build**

```bash
python3 -c "
import zipfile, sys
whl = 'dist/tramontane-0.1.5-py3-none-any.whl'
with zipfile.ZipFile(whl) as z:
    names = z.namelist()
    assert any('agent.py' in n for n in names), 'agent.py missing'
    # Read __init__.py to verify version
    for n in names:
        if n.endswith('__init__.py') and 'tramontane' in n:
            content = z.read(n).decode()
            assert '0.1.5' in content, f'version mismatch in {n}'
            print(f'OK: {n} contains 0.1.5')
print(f'OK: {len(names)} files in wheel')
"
```

- [ ] **Step 3: Publish to PyPI**

```bash
uv publish
```

- [ ] **Step 4: Git tag and push**

```bash
git tag v0.1.5
git push origin main --tags
```

- [ ] **Step 5: Verify on PyPI**

```bash
pip index versions tramontane 2>/dev/null || pip install tramontane==0.1.5 --dry-run
```
