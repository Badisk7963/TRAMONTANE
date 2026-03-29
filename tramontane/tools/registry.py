"""Tramontane tool registry — unified callable + JSON schema system.

Register Python callables (auto-generates Mistral JSON schema from
type hints) or raw JSON schemas for external tools.  One registration
call works everywhere.
"""

from __future__ import annotations

import enum
import inspect
import logging
import typing
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, ConfigDict
from rich import box
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# EU Premium palette
_CYAN = "#00D4EE"
_EMBER = "#FF6B35"
_FROST = "#DCE9F5"
_STORM = "#4A6480"
_WARN = "#FFB020"
_RIM = "#1C2E42"

_console = Console()

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


class ToolCategory(enum.Enum):
    """Category of a registered tool."""

    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    IMAGE_GENERATION = "image_generation"
    DOCUMENT = "document"
    DATABASE = "database"
    VOICE = "voice"
    CUSTOM = "custom"
    MCP = "mcp"


_CATEGORY_COLORS: dict[ToolCategory, str] = {
    ToolCategory.WEB_SEARCH: _CYAN,
    ToolCategory.CODE_EXECUTION: _WARN,
    ToolCategory.MCP: _EMBER,
    ToolCategory.CUSTOM: _FROST,
    ToolCategory.IMAGE_GENERATION: _CYAN,
    ToolCategory.DOCUMENT: _FROST,
    ToolCategory.DATABASE: _FROST,
    ToolCategory.VOICE: _CYAN,
}


class TramontaneTool(BaseModel):
    """A tool that can be called by Tramontane agents.

    Holds a Python callable AND/OR a Mistral JSON schema.
    Auto-generates the schema from type hints when created via
    ``from_callable()``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    category: ToolCategory = ToolCategory.CUSTOM
    fn: Callable[..., Any] | None = None
    json_schema: dict[str, Any] | None = None
    is_builtin: bool = False
    requires_api_key: str | None = None
    cost_estimate_eur_per_call: float = 0.0
    mcp_server_id: str | None = None

    def to_mistral_format(self) -> dict[str, Any]:
        """Return Mistral-compatible tool definition (function calling format)."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.json_schema or {},
            },
        }

    @classmethod
    def from_callable(
        cls,
        fn: Callable[..., Any],
        category: ToolCategory = ToolCategory.CUSTOM,
        description: str | None = None,
        **kwargs: Any,
    ) -> TramontaneTool:
        """Create a TramontaneTool by introspecting a Python callable.

        Builds the JSON schema from type hints and docstring automatically.
        """
        sig = inspect.signature(fn)
        try:
            hints = typing.get_type_hints(fn)
        except Exception:
            hints = {}

        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            hint = hints.get(param_name, str)
            origin = typing.get_origin(hint)
            base = origin if origin is not None else hint
            json_type = _TYPE_MAP.get(base, "string")
            properties[param_name] = {"type": json_type}
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "required": required,
        }

        doc = fn.__doc__ or ""
        desc = description or doc.split("\n")[0].strip() or fn.__name__

        return cls(
            name=fn.__name__,
            description=desc,
            category=category,
            fn=fn,
            json_schema=schema,
            **kwargs,
        )


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------


class ToolRegistry:
    """Central registry for all Tramontane tools.

    Stores TramontaneTool instances by name.  Auto-registers builtins
    when the module is first imported.
    """

    def __init__(self) -> None:
        self._tools: dict[str, TramontaneTool] = {}

    def register(self, tool: TramontaneTool) -> None:
        """Register a tool by name."""
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s [%s]", tool.name, tool.category.value)

    def register_fn(
        self,
        fn: Callable[..., Any],
        category: ToolCategory = ToolCategory.CUSTOM,
        **kwargs: Any,
    ) -> TramontaneTool:
        """Register a Python callable as a tool (auto-generates schema)."""
        tool = TramontaneTool.from_callable(fn, category=category, **kwargs)
        self.register(tool)
        return tool

    def tool(
        self, category: ToolCategory = ToolCategory.CUSTOM,
    ) -> Callable[[F], F]:
        """Decorator to register a function as a tool.

        Usage::

            @registry.tool(category=ToolCategory.CODE_EXECUTION)
            def my_tool(x: str) -> str: ...
        """

        def decorator(fn: F) -> F:
            self.register_fn(fn, category=category)
            return fn

        return decorator

    def get(self, name: str) -> TramontaneTool:
        """Look up a tool by name. Raises KeyError if not found."""
        if name not in self._tools:
            available = ", ".join(sorted(self._tools.keys()))
            msg = f"Tool '{name}' not found. Available: {available}"
            raise KeyError(msg)
        return self._tools[name]

    def list_tools(
        self, category: ToolCategory | None = None,
    ) -> list[TramontaneTool]:
        """List all registered tools, optionally filtered by category."""
        tools = list(self._tools.values())
        if category is not None:
            tools = [t for t in tools if t.category == category]
        return tools

    def to_mistral_tools(
        self, names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Return Mistral-format tool definitions for all or named tools."""
        if names is None:
            return [t.to_mistral_format() for t in self._tools.values()]
        return [self._tools[n].to_mistral_format() for n in names if n in self._tools]

    def display(self) -> None:
        """Display all registered tools — EU Premium Rich table."""
        table = Table(
            title="Tramontane Tool Registry",
            title_style=f"bold {_CYAN}",
            box=box.MINIMAL_HEAVY_HEAD,
            header_style=f"bold {_CYAN}",
            border_style=f"dim {_RIM}",
        )
        table.add_column("Name", style=_FROST)
        table.add_column("Category")
        table.add_column("Description", style=_STORM, max_width=45)
        table.add_column("Est. Cost/Call", justify="right", style=f"bold {_WARN}")

        for tool in self._tools.values():
            color = _CATEGORY_COLORS.get(tool.category, _FROST)
            table.add_row(
                tool.name,
                f"[{color}]{tool.category.value}[/]",
                tool.description[:45],
                f"€{tool.cost_estimate_eur_per_call:.4f}",
            )

        _console.print(table)


# Global registry instance
registry = ToolRegistry()


def _auto_register_builtins() -> None:
    """Import builtins to trigger auto-registration on the global registry."""
    try:
        import tramontane.tools.builtin  # noqa: F401
    except ImportError:
        pass


_auto_register_builtins()
