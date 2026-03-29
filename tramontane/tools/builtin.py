"""Built-in tools wrapping Mistral native connectors and local utilities.

All tools are auto-registered on the global registry at module load.
"""

from __future__ import annotations

import ast
import datetime
import operator

from tramontane.tools.registry import ToolCategory, TramontaneTool, registry

# ---------------------------------------------------------------------------
# Mistral built-in tools (no Python callable — handled by Mistral API)
# ---------------------------------------------------------------------------

web_search = TramontaneTool(
    name="web_search",
    description="Search the web for current information",
    category=ToolCategory.WEB_SEARCH,
    is_builtin=True,
    cost_estimate_eur_per_call=0.0002,
    json_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
        },
        "required": ["query"],
    },
)

code_interpreter = TramontaneTool(
    name="code_interpreter",
    description="Execute Python code in a secure sandbox",
    category=ToolCategory.CODE_EXECUTION,
    is_builtin=True,
    cost_estimate_eur_per_call=0.0005,
    json_schema={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to execute"},
        },
        "required": ["code"],
    },
)

image_generation = TramontaneTool(
    name="image_generation",
    description="Generate images using FLUX via Mistral",
    category=ToolCategory.IMAGE_GENERATION,
    is_builtin=True,
    cost_estimate_eur_per_call=0.01,
    json_schema={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Image generation prompt"},
        },
        "required": ["prompt"],
    },
)

document_library = TramontaneTool(
    name="document_library",
    description="Search documents in Mistral document library",
    category=ToolCategory.DOCUMENT,
    is_builtin=True,
    cost_estimate_eur_per_call=0.0001,
    json_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Document search query"},
        },
        "required": ["query"],
    },
)

# ---------------------------------------------------------------------------
# Custom tools (Python callables)
# ---------------------------------------------------------------------------


def get_current_datetime() -> str:
    """Return the current UTC date and time in ISO format."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# -- Safe math evaluator ---------------------------------------------------

_BIN_OPS: dict[type[ast.operator], object] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

_UNARY_OPS: dict[type[ast.unaryop], object] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_node(node: ast.expr) -> float:
    """Recursively evaluate an AST expression node (arithmetic only)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    if isinstance(node, ast.BinOp):
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        op_fn = _BIN_OPS.get(type(node.op))
        if op_fn is None:
            msg = f"Unsupported operator: {type(node.op).__name__}"
            raise ValueError(msg)
        return float(op_fn(left, right))  # type: ignore[operator]

    if isinstance(node, ast.UnaryOp):
        val = _safe_eval_node(node.operand)
        op_fn = _UNARY_OPS.get(type(node.op))
        if op_fn is None:
            msg = f"Unsupported unary op: {type(node.op).__name__}"
            raise ValueError(msg)
        return float(op_fn(val))  # type: ignore[operator]

    msg = f"Unsupported expression: {ast.dump(node)}"
    raise ValueError(msg)


def calculate(expression: str) -> float:
    """Evaluate a mathematical expression safely (no arbitrary code execution)."""
    tree = ast.parse(expression, mode="eval")
    return _safe_eval_node(tree.body)


# ---------------------------------------------------------------------------
# Register everything on the global registry
# ---------------------------------------------------------------------------

registry.register(web_search)
registry.register(code_interpreter)
registry.register(image_generation)
registry.register(document_library)
registry.register_fn(get_current_datetime, category=ToolCategory.CUSTOM)
registry.register_fn(calculate, category=ToolCategory.CUSTOM)
